"""
Supplier Research and Management Routes for PROCUREMENTIQ AI
Displays verified supplier profiles, historical ratings, on-time delivery rates, and risk histories.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from routes.auth import login_required
from database.db import query_db, execute_db

suppliers_bp = Blueprint('suppliers', __name__)

@suppliers_bp.route('/suppliers')
@login_required
def list_suppliers():
    search_q = request.args.get('q', '').strip()
    category_filter = request.args.get('category', '').strip()
    tier_filter = request.args.get('tier', '').strip()
    compliance_filter = request.args.get('compliance', '').strip()

    sql = "SELECT * FROM suppliers WHERE 1=1"
    params = []

    if search_q:
        sql += " AND (name LIKE ? OR code LIKE ? OR country LIKE ?)"
        params.extend([f"%{search_q}%", f"%{search_q}%", f"%{search_q}%"])
    if category_filter:
        sql += " AND category = ?"
        params.append(category_filter)
    if tier_filter:
        sql += " AND tier = ?"
        params.append(tier_filter)
    if compliance_filter:
        sql += " AND compliance_status = ?"
        params.append(compliance_filter)

    sql += " ORDER BY rating DESC, name ASC"
    suppliers = query_db(sql, params)

    # Categories for filter dropdown
    categories = query_db("SELECT DISTINCT category FROM suppliers WHERE category IS NOT NULL ORDER BY category")

    return render_template(
        'suppliers.html',
        suppliers=suppliers,
        search_q=search_q,
        category_filter=category_filter,
        tier_filter=tier_filter,
        compliance_filter=compliance_filter,
        categories=[c['category'] for c in categories]
    )

@suppliers_bp.route('/suppliers/<int:supplier_id>')
@login_required
def supplier_detail(supplier_id):
    supplier = query_db("SELECT * FROM suppliers WHERE id = ?", (supplier_id,), one=True)
    if not supplier:
        flash("Supplier record not found.", "danger")
        return redirect(url_for('suppliers.list_suppliers'))

    # Past quotations from this supplier
    quotations = query_db("""
        SELECT q.*, r.request_code, r.item_name
        FROM quotations q
        JOIN procurement_requests r ON q.request_id = r.id
        WHERE q.supplier_id = ? OR q.supplier_name LIKE ?
        ORDER BY q.id DESC
    """, (supplier_id, f"%{supplier['name']}%"))

    # Risk assessments associated with this supplier
    risks = query_db("""
        SELECT rk.*, r.request_code, r.item_name
        FROM risk_assessments rk
        JOIN procurement_requests r ON rk.request_id = r.id
        WHERE rk.supplier_name LIKE ?
        ORDER BY rk.id DESC
    """, (f"%{supplier['name']}%",))

    return render_template(
        'supplier_detail.html',
        supplier=supplier,
        quotations=quotations,
        risks=risks
    )

@suppliers_bp.route('/suppliers/new', methods=['GET', 'POST'])
@login_required
def add_supplier():
    user_id = session.get('user_id')
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip()
        country = request.form.get('country', 'USA').strip()
        category = request.form.get('category', 'Industrial Equipment').strip()
        tier = request.form.get('tier', 'Tier 1').strip()
        rating = float(request.form.get('rating') or 4.5)
        on_time = float(request.form.get('on_time_delivery_rate') or 95.0)
        defect = float(request.form.get('defect_rate') or 1.2)
        financial = request.form.get('financial_stability', 'Stable').strip()
        compliance = request.form.get('compliance_status', 'Verified').strip()
        contact_email = request.form.get('contact_email', '').strip()
        contact_phone = request.form.get('contact_phone', '').strip()
        notes = request.form.get('notes', '').strip()

        if not name:
            flash("Supplier name is required.", "danger")
            return render_template('supplier_form.html')

        execute_db("""
            INSERT INTO suppliers (
                user_id, name, code, country, category, tier, rating,
                on_time_delivery_rate, defect_rate, financial_stability,
                compliance_status, contact_email, contact_phone, notes, is_demo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """, (
            user_id, name, code or f"SUP-{name[:3].upper()}", country, category,
            tier, rating, on_time, defect, financial, compliance,
            contact_email, contact_phone, notes
        ))

        flash(f"Supplier '{name}' registered in procurement registry successfully!", "success")
        return redirect(url_for('suppliers.list_suppliers'))

    return render_template('supplier_form.html')
