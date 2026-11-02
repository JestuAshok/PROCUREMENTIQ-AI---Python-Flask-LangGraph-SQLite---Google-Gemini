"""
Procurement Request Routes for PROCUREMENTIQ AI
Handles creating new procurement requests, file uploads, and sample quotations loading.
"""

import os
import shutil
from datetime import datetime, date
from pathlib import Path
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from werkzeug.utils import secure_filename
from routes.auth import login_required
from database.db import query_db, execute_db
from services.quotation_extractor import extract_quotation_data
from services.sample_data_service import generate_sample_documents

procurement_bp = Blueprint('procurement', __name__)

def generate_request_code():
    today_year = datetime.now().year
    row = query_db("SELECT COUNT(*) as cnt FROM procurement_requests", one=True)
    next_idx = (row['cnt'] if row else 0) + 1
    return f"PR-{today_year}-{next_idx:03d}"

@procurement_bp.route('/requests/new', methods=['GET', 'POST'])
@login_required
def new_request():
    user_id = session.get('user_id')

    if request.method == 'POST':
        item_name = request.form.get('item_name', '').strip()
        category = request.form.get('category', '').strip()
        quantity_str = request.form.get('quantity', '1').strip()
        budget_str = request.form.get('budget', '0').strip()
        currency = request.form.get('currency', 'USD').strip()
        delivery_date = request.form.get('required_delivery_date', '').strip()
        delivery_location = request.form.get('delivery_location', '').strip()
        min_warranty_str = request.form.get('min_warranty_months', '12').strip()
        payment_terms_pref = request.form.get('payment_terms_pref', 'Net 30').strip()
        additional_requirements = request.form.get('additional_requirements', '').strip()

        errors = []
        if not item_name:
            errors.append("Item or equipment name is required.")
        if not category:
            errors.append("Product category is required.")

        try:
            quantity = int(quantity_str)
            if quantity <= 0:
                errors.append("Quantity must be a positive number (> 0).")
        except ValueError:
            errors.append("Quantity must be a valid integer.")

        try:
            budget = float(budget_str)
            if budget <= 0:
                errors.append("Maximum budget must be greater than zero.")
        except ValueError:
            errors.append("Maximum budget must be a valid number.")

        if not delivery_date:
            errors.append("Required delivery date cannot be empty.")
        if not delivery_location:
            errors.append("Delivery location cannot be empty.")

        try:
            min_warranty_months = int(min_warranty_str)
            if min_warranty_months < 0:
                errors.append("Minimum warranty months cannot be negative.")
        except ValueError:
            errors.append("Minimum warranty must be a valid number.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template(
                'new_request.html',
                item_name=item_name,
                category=category,
                quantity=quantity_str,
                budget=budget_str,
                currency=currency,
                required_delivery_date=delivery_date,
                delivery_location=delivery_location,
                min_warranty_months=min_warranty_str,
                payment_terms_pref=payment_terms_pref,
                additional_requirements=additional_requirements,
                generated_code=generate_request_code()
            )

        req_code = generate_request_code()

        req_id = execute_db("""
            INSERT INTO procurement_requests (
                request_code, user_id, item_name, category, quantity, budget,
                currency, required_delivery_date, delivery_location,
                min_warranty_months, payment_terms_pref, additional_requirements, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Draft')
        """, (
            req_code, user_id, item_name, category, quantity, budget,
            currency, delivery_date, delivery_location,
            min_warranty_months, payment_terms_pref, additional_requirements
        ))

        flash(f"Procurement Request {req_code} created successfully! You can now upload supplier quotations.", "success")
        return redirect(url_for('procurement.request_detail', request_id=req_id))

    return render_template('new_request.html', generated_code=generate_request_code())

@procurement_bp.route('/requests/<int:request_id>')
@login_required
def request_detail(request_id):
    user_id = session.get('user_id')
    req = query_db(
        "SELECT * FROM procurement_requests WHERE id = ? AND (user_id = ? OR ? = 1)",
        (request_id, user_id, user_id), one=True
    )
    if not req:
        flash("Procurement request not found or access denied.", "danger")
        return redirect(url_for('dashboard.dashboard_view'))

    quotations = query_db("""
        SELECT q.*, s.tier, s.rating as supplier_rating, s.compliance_status
        FROM quotations q
        LEFT JOIN suppliers s ON q.supplier_id = s.id
        WHERE q.request_id = ?
        ORDER BY q.id ASC
    """, (request_id,))

    # Check if agents have been run
    agent_run = query_db(
        "SELECT * FROM agent_runs WHERE request_id = ? ORDER BY id DESC LIMIT 1",
        (request_id,), one=True
    )

    return render_template(
        'request_detail.html',
        proc_req=req,
        quotations=quotations,
        agent_run=agent_run
    )

@procurement_bp.route('/requests/<int:request_id>/quotations', methods=['POST'])
@login_required
def upload_quotations(request_id):
    user_id = session.get('user_id')
    req = query_db(
        "SELECT * FROM procurement_requests WHERE id = ? AND (user_id = ? OR ? = 1)",
        (request_id, user_id, user_id), one=True
    )
    if not req:
        flash("Procurement request not found.", "danger")
        return redirect(url_for('dashboard.dashboard_view'))

    files = request.files.getlist('quotation_files')
    if not files or files[0].filename == '':
        flash("Please select at least one quotation document (PDF, XLSX, CSV).", "warning")
        return redirect(url_for('procurement.request_detail', request_id=request_id))

    upload_dir = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_dir, exist_ok=True)

    allowed_exts = current_app.config['ALLOWED_EXTENSIONS']
    uploaded_count = 0

    for file in files:
        if file and file.filename:
            filename = secure_filename(file.filename)
            ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
            if ext not in allowed_exts:
                flash(f"File '{filename}' skipped: Unsupported format. Allowed: PDF, XLSX, CSV.", "warning")
                continue

            save_path = os.path.join(upload_dir, f"{request_id}_{filename}")
            file.save(save_path)

            # Extract data using quotation_extractor
            extracted = extract_quotation_data(save_path, filename)

            # Match supplier or assign
            s_name = extracted.get('supplier_name', 'Not provided')
            s_row = query_db("SELECT id FROM suppliers WHERE name LIKE ? LIMIT 1", (f"%{s_name}%",), one=True)
            supplier_id = s_row['id'] if s_row else None

            import json
            missing_json = json.dumps(extracted.get('missing_fields', []))

            # Store quotation
            execute_db("""
                INSERT INTO quotations (
                    request_id, supplier_id, supplier_name, quotation_number,
                    item_description, unit_price, quantity, currency, discount_amount,
                    tax_rate, tax_amount, shipping_cost, installation_cost, other_charges,
                    total_cost, warranty_months, delivery_days, promised_delivery_date,
                    payment_terms, quote_validity_date, filename, file_path,
                    extraction_confidence, missing_fields
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request_id, supplier_id, s_name, extracted.get('quotation_number', 'QUO-000'),
                extracted.get('item_description', req['item_name']), extracted.get('unit_price', 0.0),
                extracted.get('quantity', req['quantity']), extracted.get('currency', req['currency']),
                extracted.get('discount_amount', 0.0), extracted.get('tax_rate', 0.0),
                extracted.get('tax_amount', 0.0), extracted.get('shipping_cost', 0.0),
                extracted.get('installation_cost', 0.0), extracted.get('other_charges', 0.0),
                extracted.get('total_cost', 0.0), extracted.get('warranty_months', 12),
                extracted.get('delivery_days', 30), extracted.get('promised_delivery_date', ''),
                extracted.get('payment_terms', 'Net 30'), extracted.get('quote_validity_date', ''),
                filename, save_path, extracted.get('extraction_confidence', 85.0), missing_json
            ))
            uploaded_count += 1

    if uploaded_count > 0:
        execute_db("""
            UPDATE procurement_requests
            SET status = 'Quotations Uploaded', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (request_id,))
        flash(f"Successfully processed {uploaded_count} quotation document(s). Review extracted details below.", "success")
        return redirect(url_for('analysis.review_quotations', request_id=request_id))

    return redirect(url_for('procurement.request_detail', request_id=request_id))

@procurement_bp.route('/requests/<int:request_id>/load-samples', methods=['POST'])
@login_required
def load_sample_quotations(request_id):
    """
    1-click testing: Loads the 3 pre-generated realistic quotation documents
    (Apex PDF, Global Electrics XLSX, Vanguard Dynamics CSV) into the request.
    """
    sample_dir = os.path.join(current_app.root_path, 'sample_documents')
    if not os.path.exists(sample_dir):
        generate_sample_documents(sample_dir)

    sample_files = [
        'quote_apex_industrial.pdf',
        'quote_global_electrics.xlsx',
        'quote_vanguard_dynamics.csv'
    ]

    upload_dir = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_dir, exist_ok=True)

    loaded = 0
    for s_file in sample_files:
        src = os.path.join(sample_dir, s_file)
        if os.path.exists(src):
            dest = os.path.join(upload_dir, f"{request_id}_{s_file}")
            shutil.copyfile(src, dest)
            extracted = extract_quotation_data(dest, s_file)

            s_name = extracted.get('supplier_name', 'Not provided')
            s_row = query_db("SELECT id FROM suppliers WHERE name LIKE ? LIMIT 1", (f"%{s_name}%",), one=True)
            supplier_id = s_row['id'] if s_row else None

            import json
            missing_json = json.dumps(extracted.get('missing_fields', []))

            execute_db("""
                INSERT INTO quotations (
                    request_id, supplier_id, supplier_name, quotation_number,
                    item_description, unit_price, quantity, currency, discount_amount,
                    tax_rate, tax_amount, shipping_cost, installation_cost, other_charges,
                    total_cost, warranty_months, delivery_days, promised_delivery_date,
                    payment_terms, quote_validity_date, filename, file_path,
                    extraction_confidence, missing_fields
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request_id, supplier_id, s_name, extracted.get('quotation_number', 'QUO-000'),
                extracted.get('item_description', 'Industrial Equipment'), extracted.get('unit_price', 0.0),
                extracted.get('quantity', 5), extracted.get('currency', 'USD'),
                extracted.get('discount_amount', 0.0), extracted.get('tax_rate', 5.0),
                extracted.get('tax_amount', extracted.get('tax_amount', 0.0)),
                extracted.get('shipping_cost', 0.0), extracted.get('installation_cost', 0.0),
                extracted.get('other_charges', 0.0), extracted.get('total_cost', 0.0),
                extracted.get('warranty_months', 24), extracted.get('delivery_days', 22),
                extracted.get('promised_delivery_date', ''), extracted.get('payment_terms', 'Net 30'),
                extracted.get('quote_validity_date', ''), s_file, dest,
                extracted.get('extraction_confidence', 95.0), missing_json
            ))
            loaded += 1

    execute_db("""
        UPDATE procurement_requests
        SET status = 'Quotations Uploaded', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (request_id,))

    flash(f"Loaded {loaded} realistic sample quotations (PDF, XLSX, CSV). Review and verify extracted data below.", "success")
    return redirect(url_for('analysis.review_quotations', request_id=request_id))

@procurement_bp.route('/requests/<int:request_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_request(request_id):
    user_id = session.get('user_id')
    req = query_db(
        "SELECT * FROM procurement_requests WHERE id = ? AND (user_id = ? OR ? = 1)",
        (request_id, user_id, user_id), one=True
    )
    if not req:
        flash("Procurement request not found.", "danger")
        return redirect(url_for('dashboard.dashboard_view'))

    if request.method == 'POST':
        item_name = request.form.get('item_name', '').strip()
        category = request.form.get('category', '').strip()
        quantity_str = request.form.get('quantity', '1').strip()
        budget_str = request.form.get('budget', '0').strip()
        currency = request.form.get('currency', 'USD').strip()
        delivery_date = request.form.get('required_delivery_date', '').strip()
        delivery_location = request.form.get('delivery_location', '').strip()
        min_warranty_str = request.form.get('min_warranty_months', '12').strip()
        payment_terms_pref = request.form.get('payment_terms_pref', 'Net 30').strip()
        additional_requirements = request.form.get('additional_requirements', '').strip()

        try:
            quantity = int(quantity_str)
            budget = float(budget_str)
            min_warranty_months = int(min_warranty_str)
        except ValueError:
            flash("Please verify numeric fields (quantity, budget, warranty).", "danger")
            return redirect(url_for('procurement.edit_request', request_id=request_id))

        execute_db("""
            UPDATE procurement_requests
            SET item_name = ?, category = ?, quantity = ?, budget = ?, currency = ?,
                required_delivery_date = ?, delivery_location = ?, min_warranty_months = ?,
                payment_terms_pref = ?, additional_requirements = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            item_name, category, quantity, budget, currency, delivery_date,
            delivery_location, min_warranty_months, payment_terms_pref,
            additional_requirements, request_id
        ))

        flash(f"Procurement request '{req['request_code']}' requirements updated.", "success")
        return redirect(url_for('workflow.view_workflow', request_id=request_id, step=1))

    return render_template(
        'new_request.html',
        item_name=req['item_name'],
        category=req['category'],
        quantity=req['quantity'],
        budget=req['budget'],
        currency=req['currency'],
        required_delivery_date=req['required_delivery_date'],
        delivery_location=req['delivery_location'],
        min_warranty_months=req['min_warranty_months'],
        payment_terms_pref=req['payment_terms_pref'],
        additional_requirements=req['additional_requirements'],
        generated_code=req['request_code'],
        is_edit=True,
        proc_req=req
    )
