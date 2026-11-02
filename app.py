"""
PROCUREMENTIQ AI — Autonomous Procurement Risk & Negotiation Intelligence
Main Flask Application Entry Point.
Run with: python app.py
"""

import os
from pathlib import Path
from flask import Flask, render_template

from config import Config
from database.db import close_db, init_db
from database.seed import seed_database
from services.sample_data_service import generate_sample_documents

# Import Blueprint modules
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.procurement import procurement_bp
from routes.analysis import analysis_bp
from routes.suppliers import suppliers_bp
from routes.risks import risks_bp
from routes.costs import costs_bp
from routes.recommendations import recommendations_bp
from routes.workflow_routes import workflow_bp
from routes.reports import reports_bp
from routes.settings import settings_bp

from werkzeug.middleware.proxy_fix import ProxyFix

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Enable ProxyFix for reverse proxies (e.g. ngrok HTTPS tunnels)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Ensure required runtime folders exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(app.config['DATABASE_PATH'])), exist_ok=True)
    sample_dir = os.path.join(app.root_path, 'sample_documents')
    os.makedirs(sample_dir, exist_ok=True)

    # Initialize DB & Seed demo data automatically (does not wipe user data)
    with app.app_context():
        init_db(app)
        seed_database(force=False)
        generate_sample_documents(sample_dir)

    # Injected template variables for ngrok and Gemini status
    @app.context_processor
    def inject_global_vars():
        from services.gemini_service import get_gemini_api_key
        from services.matter_service import get_ngrok_api_key
        return {
            'ngrok_url': os.environ.get('NGROK_URL', 'https://calcium-excretion-pried.ngrok-free.dev'),
            'has_gemini_key': bool(get_gemini_api_key()),
            'has_ngrok_key': bool(get_ngrok_api_key())
        }

    # Template filter for formatting concise risk evidence and mitigations
    @app.template_filter('clean_bullets')
    def clean_bullets_filter(text, supplier_name=""):
        import re
        if not text:
            return []
        raw_parts = [p.strip() for p in re.split(r'\||\n|;', str(text)) if p.strip()]
        cleaned = []
        for p in raw_parts:
            item = p.strip()
            # Strip redundant vendor prefix
            if supplier_name:
                item = re.sub(rf'^{re.escape(supplier_name)}\s*[:\-]\s*', '', item, flags=re.IGNORECASE)
            item = re.sub(r'^[A-Z0-9\s&.,\'-]{3,35}?\s*[:\-]\s*', '', item)

            # Concise normalizations for common verbose risk strings
            item = re.sub(r'Historical delivery reliability concern:\s*', '', item, flags=re.IGNORECASE)
            item = re.sub(r'Historical ERP on-time delivery rate is\s*', 'On-time rate: ', item, flags=re.IGNORECASE)
            item = re.sub(r'Quoted (\d+)\s*months vs required (\d+)\s*months', r'Quoted \1 mo (req \2 mo)', item, flags=re.IGNORECASE)
            item = re.sub(r'Warranty terms satisfactory \((\d+)\s*months coverage\)', r'Warranty \1 mo verified', item, flags=re.IGNORECASE)
            item = re.sub(r'Require milestone-based weekly production check-ins and buffer inventory staging\.?', 'Weekly check-ins & buffer inventory staging', item, flags=re.IGNORECASE)
            item = re.sub(r'Conduct mandatory third-party ISO / factory compliance audit prior to PO execution\.?', 'Mandatory ISO compliance audit before PO', item, flags=re.IGNORECASE)
            item = re.sub(r'Negotiate extended warranty rider to satisfy mandatory (\d+)-month requirement\.?', r'Negotiate \1-mo warranty rider', item, flags=re.IGNORECASE)
            item = re.sub(r'Request formal commercial addendum clarifying Quote validity date\.?', 'Clarify quote validity date via addendum', item, flags=re.IGNORECASE)
            item = re.sub(r'Counter-propose 30% advance, 70% upon bill of lading receipt and port inspection\.?', 'Counter-propose 30% adv, 70% delivery', item, flags=re.IGNORECASE)
            item = re.sub(r'Mandate 100% pre-shipment factory acceptance testing \(FAT\) witnessed by third party\.?', 'Mandate 100% FAT testing before shipment', item, flags=re.IGNORECASE)

            item = item.strip().rstrip('.')
            if item and item not in cleaned:
                cleaned.append(item)
        return cleaned

    # Automatically bypass ngrok free warning header
    @app.after_request
    def add_ngrok_header(response):
        response.headers['ngrok-skip-browser-warning'] = 'true'
        return response

    # Register teardown function
    app.teardown_appcontext(close_db)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(procurement_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(suppliers_bp)
    app.register_blueprint(risks_bp)
    app.register_blueprint(costs_bp)
    app.register_blueprint(recommendations_bp)
    app.register_blueprint(workflow_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(settings_bp)

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("=" * 65)
    print("  PROCUREMENTIQ AI — AUTONOMOUS INTELLIGENCE PLATFORM")
    print("  Enterprise Soft Pastel UI & Six-Agent Decision Architecture")
    print(f"  Access live at: http://127.0.0.1:{port}/")
    print(f"  Default Demo Account: jahnavi@procurementiq.ai / Password123!")
    print("=" * 65)
    app.run(host='0.0.0.0', port=port, debug=True)
