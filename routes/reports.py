"""
Reports and Export Routes for PROCUREMENTIQ AI
Generates downloadable executive PDF and CSV reports from verified database records.
"""

import io
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, send_file
from routes.auth import login_required
from database.db import query_db
from services.report_service import generate_pdf_report, generate_csv_report

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
@login_required
def list_reports():
    user_id = session.get('user_id')
    requests_list = query_db("""
        SELECT r.*,
               (SELECT COUNT(*) FROM quotations q WHERE q.request_id = r.id) as quote_count,
               (SELECT COUNT(*) FROM recommendations rec WHERE rec.request_id = r.id) as rec_count,
               (SELECT supplier_name FROM recommendations rec WHERE rec.request_id = r.id AND rec.is_recommended = 1 LIMIT 1) as recommended_vendor
        FROM procurement_requests r
        WHERE r.user_id = ? OR r.user_id = 1
        ORDER BY r.id ASC
    """, (user_id,))

    return render_template('reports.html', requests_list=requests_list)

@reports_bp.route('/reports/<int:request_id>/pdf')
@login_required
def download_pdf(request_id):
    req = query_db("SELECT * FROM procurement_requests WHERE id = ?", (request_id,), one=True)
    if not req:
        flash("Procurement request not found.", "danger")
        return redirect(url_for('reports.list_reports'))

    quotations = query_db("SELECT * FROM quotations WHERE request_id = ?", (request_id,))
    costs = query_db("SELECT * FROM cost_comparisons WHERE request_id = ? ORDER BY estimated_total_cost ASC", (request_id,))
    risks = query_db("SELECT * FROM risk_assessments WHERE request_id = ?", (request_id,))
    recs = query_db("SELECT * FROM recommendations WHERE request_id = ? ORDER BY rank ASC", (request_id,))

    pdf_bytes = generate_pdf_report(
        request_data=dict(req),
        quotations_data=[dict(q) for q in quotations],
        costs_data=[dict(c) for c in costs],
        risks_data=[dict(r) for r in risks],
        recs_data=[dict(rc) for rc in recs]
    )

    filename = f"ProcurementIQ_Report_{req['request_code']}.pdf"
    as_attachment = request.args.get('download', '0') == '1'

    resp = send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=as_attachment,
        download_name=filename,
        max_age=0
    )
    disp_type = "attachment" if as_attachment else "inline"
    resp.headers["Content-Disposition"] = f'{disp_type}; filename="{filename}"; filename*=UTF-8\'\'{filename}'
    return resp

@reports_bp.route('/reports/<int:request_id>/csv')
@login_required
def download_csv(request_id):
    req = query_db("SELECT * FROM procurement_requests WHERE id = ?", (request_id,), one=True)
    if not req:
        flash("Procurement request not found.", "danger")
        return redirect(url_for('reports.list_reports'))

    quotations = query_db("SELECT * FROM quotations WHERE request_id = ?", (request_id,))
    costs = query_db("SELECT * FROM cost_comparisons WHERE request_id = ? ORDER BY estimated_total_cost ASC", (request_id,))
    risks = query_db("SELECT * FROM risk_assessments WHERE request_id = ?", (request_id,))
    recs = query_db("SELECT * FROM recommendations WHERE request_id = ? ORDER BY rank ASC", (request_id,))

    csv_text = generate_csv_report(
        request_data=dict(req),
        quotations_data=[dict(q) for q in quotations],
        costs_data=[dict(c) for c in costs],
        risks_data=[dict(r) for r in risks],
        recs_data=[dict(rc) for rc in recs]
    )

    filename = f"ProcurementIQ_Data_{req['request_code']}.csv"
    resp = send_file(
        io.BytesIO(csv_text.encode('utf-8-sig')),
        mimetype="text/csv; charset=utf-8",
        as_attachment=True,
        download_name=filename,
        max_age=0
    )
    resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"; filename*=UTF-8\'\'{filename}'
    return resp
