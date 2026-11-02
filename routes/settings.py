"""
System and User Settings Routes for PROCUREMENTIQ AI
Allows configuring multi-criteria scoring weights, ngrok/Groq API key (for matter),
Google Gemini API key (for graphs), currency, and DEMO MODE.
"""

import os
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from routes.auth import login_required
from database.db import query_db, execute_db
from services.gemini_service import get_gemini_api_key, save_gemini_api_key, test_gemini_connection
from services.matter_service import get_ngrok_api_key, save_ngrok_api_key, test_ngrok_ai_connection

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings_view():
    user_id = session.get('user_id')

    user_settings = query_db("SELECT * FROM user_settings WHERE user_id = ?", (user_id,), one=True)
    if not user_settings:
        execute_db("""
            INSERT INTO user_settings (user_id, weight_cost, weight_delivery, weight_risk, weight_warranty, default_currency, demo_mode, gemini_api_key, ngrok_api_key)
            VALUES (?, 0.40, 0.25, 0.20, 0.15, 'USD', 1, '', '')
        """, (user_id,))
        user_settings = query_db("SELECT * FROM user_settings WHERE user_id = ?", (user_id,), one=True)

    if request.method == 'POST':
        try:
            w_cost = float(request.form.get('weight_cost', 0.40))
            w_deliv = float(request.form.get('weight_delivery', 0.25))
            w_risk = float(request.form.get('weight_risk', 0.20))
            w_warr = float(request.form.get('weight_warranty', 0.15))
            currency = request.form.get('default_currency', 'USD').strip()

            total_w = round(w_cost + w_deliv + w_risk + w_warr, 2)
            if abs(total_w - 1.0) > 0.05:
                flash(f"Scoring weights should sum to 1.0 (or 100%). Current sum: {total_w * 100:.0f}%. Normalized automatically.", "warning")

            execute_db("""
                UPDATE user_settings
                SET weight_cost = ?, weight_delivery = ?, weight_risk = ?, weight_warranty = ?,
                    default_currency = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (w_cost, w_deliv, w_risk, w_warr, currency, user_id))

            flash("Settings and decision weights saved successfully!", "success")
            return redirect(url_for('settings.settings_view'))
        except ValueError:
            flash("Invalid numeric value entered for scoring weights.", "danger")

    # Refresh current settings
    user_settings = query_db("SELECT * FROM user_settings WHERE user_id = ?", (user_id,), one=True)

    return render_template(
        'settings.html',
        settings=user_settings
    )


@settings_bp.route('/settings/test-gemini', methods=['POST'])
@login_required
def test_gemini():
    """
    AJAX endpoint to test Gemini API connection without exposing raw keys.
    """
    if 'api_key' in request.form:
        key = request.form.get('api_key', '').strip()
    elif request.is_json and 'api_key' in request.json:
        key = (request.json.get('api_key') or '').strip()
    else:
        key = get_gemini_api_key()

    success, msg = test_gemini_connection(key)
    if key and len(key) > 6:
        msg = msg.replace(key, "[PROTECTED_KEY]")
    return jsonify({
        "success": success,
        "message": msg
    })


@settings_bp.route('/settings/test-ngrok', methods=['POST'])
@login_required
def test_ngrok():
    """
    AJAX endpoint to test ngrok AI connection without exposing raw keys.
    """
    if 'api_key' in request.form:
        key = request.form.get('api_key', '').strip()
    elif request.is_json and 'api_key' in request.json:
        key = (request.json.get('api_key') or '').strip()
    else:
        key = get_ngrok_api_key()

    success, msg = test_ngrok_ai_connection(key)
    if key and len(key) > 6:
        msg = msg.replace(key, "[PROTECTED_KEY]")
    return jsonify({
        "success": success,
        "message": msg
    })
