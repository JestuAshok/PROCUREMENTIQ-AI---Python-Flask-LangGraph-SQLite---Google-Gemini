"""
Authentication routes for PROCUREMENTIQ AI
Handles signup, login, session isolation, and logout.
"""

import re
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import query_db, execute_db

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please sign in to access your procurement dashboard.", "warning")
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard_view'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        company_name = request.form.get('company_name', 'Global Logistics & Mfg Corp').strip()

        # Validations
        errors = []
        if not full_name:
            errors.append("Full name is required.")
        if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            errors.append("A valid email address is required.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters long.")
        if password != confirm_password:
            errors.append("Passwords do not match.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template('signup.html', full_name=full_name, email=email, company_name=company_name)

        # Check existing user
        existing_user = query_db("SELECT id FROM users WHERE email = ?", (email,), one=True)
        if existing_user:
            flash("An account with this email address already exists. Please sign in.", "warning")
            return redirect(url_for('auth.login'))

        # Insert user
        password_hash = generate_password_hash(password)
        user_id = execute_db("""
            INSERT INTO users (email, password_hash, full_name, company_name, role)
            VALUES (?, ?, ?, ?, 'Procurement Specialist')
        """, (email, password_hash, full_name, company_name))

        # Insert default settings for user
        execute_db("""
            INSERT INTO user_settings (user_id, weight_cost, weight_delivery, weight_risk, weight_warranty, default_currency, demo_mode)
            VALUES (?, 0.40, 0.25, 0.20, 0.15, 'USD', 1)
        """, (user_id,))

        flash("Account created successfully! Please sign in with your credentials.", "success")
        return redirect(url_for('auth.login'))

    return render_template('signup.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard_view'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return render_template('login.html', email=email)

        user = query_db("SELECT * FROM users WHERE email = ?", (email,), one=True)
        if not user or not check_password_hash(user['password_hash'], password):
            flash("Invalid email or password. Please try again.", "danger")
            return render_template('login.html', email=email)

        # Session setup
        session.clear()
        session['user_id'] = user['id']
        session['user_name'] = user['full_name']
        session['user_email'] = user['email']
        session['user_role'] = user['role']
        session.permanent = remember

        flash(f"Welcome back, {user['full_name']}!", "success")
        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
        return redirect(url_for('dashboard.dashboard_view'))

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been signed out safely.", "info")
    return redirect(url_for('auth.login'))
