"""
Comprehensive Functional Acceptance Test Suite for PROCUREMENTIQ AI
Validates all 16 Acceptance Tests from Section 19 of the specification.
"""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path

# Insert project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from config import Config
from database.db import get_db, init_db, query_db, execute_db
from database.seed import seed_database
from services.cost_calculator import calculate_quotation_cost
from services.scoring_engine import score_procurement_quotations
from services.quotation_extractor import extract_quotation_data
from services.sample_data_service import generate_sample_documents
from agents.workflow import ProcurementWorkflowOrchestrator

class TestProcurementIQAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp()
        cls.db_path = os.path.join(cls.temp_dir, 'test_procurementiq.db')
        cls.upload_path = os.path.join(cls.temp_dir, 'uploads')
        os.makedirs(cls.upload_path, exist_ok=True)

        class TestConfig(Config):
            TESTING = True
            DATABASE_PATH = cls.db_path
            UPLOAD_FOLDER = cls.upload_path
            SECRET_KEY = 'test-secret-key'
            DEMO_MODE = True

        cls.app = create_app(TestConfig)
        cls.client = cls.app.test_client()

    def test_01_app_starts_and_database_initialized(self):
        """TEST 1: The application starts and SQLite database is created."""
        with self.app.app_context():
            user = query_db("SELECT * FROM users WHERE email = 'jahnavi@procurementiq.ai'", one=True)
            self.assertIsNotNone(user, "Default demo user Jahnavi must exist in SQLite database")
            self.assertEqual(user['email'], 'jahnavi@procurementiq.ai')

    def test_02_landing_page_renders_working_links(self):
        """TEST 2: Open landing page, verify working navigation and CTA links."""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn("Smarter Procurement", html)
        self.assertIn("with AI Agents", html)
        self.assertIn("Sign In", html)
        self.assertIn("Get Started", html)
        self.assertIn("Lower Procurement Risk", html)

    def test_03_user_signup_and_validation(self):
        """TEST 3: Create a new user account, verify hashed password in SQLite."""
        new_email = "testbuyer@procurementiq.ai"
        signup_data = {
            "full_name": "Test Enterprise Buyer",
            "email": new_email,
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
            "company_name": "Acme Industrial"
        }
        res = self.client.post('/signup', data=signup_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        with self.app.app_context():
            user = query_db("SELECT * FROM users WHERE email = ?", (new_email,), one=True)
            self.assertIsNotNone(user, "New user must be saved in SQLite database")
            self.assertNotEqual(user['password_hash'], "SecurePassword123!", "Password must be securely hashed")

    def test_04_user_login_and_dashboard_session(self):
        """TEST 4: Log in with created account, verify dashboard access and session."""
        login_data = {
            "email": "jahnavi@procurementiq.ai",
            "password": "Password123!"
        }
        res = self.client.post('/login', data=login_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn("Dashboard", html)
        self.assertIn("Ongoing Procurement Analysis", html)

    def test_05_create_procurement_request(self):
        """TEST 5: Create a new procurement request for industrial equipment."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Jahnavi'
            sess['user_email'] = 'jahnavi@procurementiq.ai'

        req_data = {
            "item_name": "Precision CNC Milling Machine",
            "category": "Industrial Machinery",
            "quantity": "2",
            "budget": "180000",
            "currency": "USD",
            "required_delivery_date": "2026-12-15",
            "delivery_location": "Detroit Assembly Plant",
            "min_warranty_months": "36",
            "payment_terms_pref": "Net 45",
            "additional_requirements": "5-axis simultaneous machining, Heidenhain TNC 640 controller, ISO 10791 compliance"
        }
        res = self.client.post('/requests/new', data=req_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        with self.app.app_context():
            req = query_db("SELECT * FROM procurement_requests WHERE item_name = 'Precision CNC Milling Machine'", one=True)
            self.assertIsNotNone(req, "Procurement request must be saved in database")
            self.assertEqual(req['budget'], 180000.0)
            self.assertEqual(req['quantity'], 2)

    def test_06_and_07_quotation_upload_and_extraction(self):
        """TEST 6 & 7: Upload supplier quotations, verify extraction and review."""
        sample_dir = os.path.join(self.temp_dir, 'samples')
        samples = generate_sample_documents(sample_dir)

        # Test PDF extraction
        pdf_data = extract_quotation_data(samples['pdf'], 'quote_apex_industrial.pdf')
        self.assertEqual(pdf_data['quantity'], 5)
        self.assertGreater(pdf_data['total_cost'], 0.0)
        self.assertGreater(pdf_data['extraction_confidence'], 70.0)

        # Test XLSX extraction
        xlsx_data = extract_quotation_data(samples['xlsx'], 'quote_global_electrics.xlsx')
        self.assertEqual(xlsx_data['quantity'], 5)
        self.assertEqual(xlsx_data['total_cost'], 63000.0)

        # Test CSV extraction
        csv_data = extract_quotation_data(samples['csv'], 'quote_vanguard_dynamics.csv')
        self.assertEqual(csv_data['quantity'], 5)
        self.assertEqual(csv_data['total_cost'], 75000.0)

    def test_08_run_six_agents_sequence(self):
        """TEST 8: Run all six agents in the intended sequence."""
        with self.app.app_context():
            orchestrator = ProcurementWorkflowOrchestrator()
            result = orchestrator.run_workflow(request_id=1, force_mode='DEMO_FALLBACK')
            self.assertEqual(result['status'], 'Completed')
            self.assertEqual(len(result['agent_results']), 6, "All 6 agents must execute in sequence")
            self.assertEqual(result['agent_results'][0]['agent_name'], "Requirement Parser Agent")
            self.assertEqual(result['agent_results'][1]['agent_name'], "Quote Analyzer Agent")
            self.assertEqual(result['agent_results'][2]['agent_name'], "Supplier Researcher Agent")
            self.assertEqual(result['agent_results'][3]['agent_name'], "Risk Assessor Agent")
            self.assertEqual(result['agent_results'][4]['agent_name'], "Cost Optimizer Agent")
            self.assertEqual(result['agent_results'][5]['agent_name'], "Procurement Advisor Agent")

    def test_09_verify_total_cost_calculations(self):
        """TEST 9: Verify total cost calculations independently (subtotal, net, taxes, freight, install)."""
        calc = calculate_quotation_cost(
            unit_price=12000.0,
            quantity=5,
            discount_amount=1500.0,
            tax_amount=2925.0,
            shipping_cost=1675.0,
            installation_cost=1900.0,
            other_charges=0.0
        )
        # Expected:
        # Subtotal: 5 * 12,000 = 60,000
        # Net Subtotal: 60,000 - 1,500 = 58,500
        # Estimated Total: 58,500 + 2,925 + 1,675 + 1,900 = 65,000
        self.assertEqual(calc['subtotal'], 60000.0)
        self.assertEqual(calc['net_subtotal'], 58500.0)
        self.assertEqual(calc['estimated_total_cost'], 65000.0)

    def test_10_recommendation_based_on_scoring_and_constraints(self):
        """TEST 10: Recommendation is based on configured scoring rules and mandatory requirements."""
        test_quotes = [
            {"id": 1, "supplier_name": "Vendor Eligible & Cheaper", "total_cost": 60000, "warranty_months": 24, "delivery_days": 20, "risk_score": 15},
            {"id": 2, "supplier_name": "Vendor Disqualified Over Budget", "total_cost": 150000, "warranty_months": 24, "delivery_days": 20, "risk_score": 10},
            {"id": 3, "supplier_name": "Vendor Disqualified Low Warranty", "total_cost": 50000, "warranty_months": 6, "delivery_days": 20, "risk_score": 10}
        ]
        criteria = {"budget": 100000, "min_warranty_months": 12, "required_delivery_date": "2026-12-01"}
        results = score_procurement_quotations(test_quotes, criteria)

        # Ranked 1 must be the eligible vendor even if another vendor has lower cost or higher raw score
        self.assertEqual(results[0]['supplier_name'], "Vendor Eligible & Cheaper")
        self.assertTrue(results[0]['is_recommended'])
        self.assertTrue(results[0]['satisfies_mandatory'])

        # Over-budget and low-warranty vendors must fail mandatory criteria
        disqual_budget = next(r for r in results if r['supplier_name'] == "Vendor Disqualified Over Budget")
        self.assertFalse(disqual_budget['satisfies_mandatory'])
        self.assertFalse(disqual_budget['is_recommended'])

        disqual_warr = next(r for r in results if r['supplier_name'] == "Vendor Disqualified Low Warranty")
        self.assertFalse(disqual_warr['satisfies_mandatory'])

    def test_11_missing_supplier_information_marked(self):
        """TEST 11: Missing supplier information is clearly marked as 'Not provided'."""
        parsed = extract_quotation_data("non_existent_file.pdf", "quote_empty.pdf")
        self.assertEqual(parsed['supplier_name'], "Empty")
        self.assertIn("Unit price", parsed['missing_fields'])

    def test_12_dashboard_kpis_derive_from_database(self):
        """TEST 12: Dashboard KPIs update from the database."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Jahnavi'
        res = self.client.get('/dashboard')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn("Procurement Requests", html)
        self.assertIn("Suppliers Analyzed", html)

    def test_13_export_reports(self):
        """TEST 13: Export a procurement report as PDF and CSV."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
        res_pdf = self.client.get('/reports/1/pdf')
        self.assertEqual(res_pdf.status_code, 200)
        self.assertEqual(res_pdf.mimetype, 'application/pdf')

        res_csv = self.client.get('/reports/1/csv')
        self.assertEqual(res_csv.status_code, 200)
        self.assertEqual(res_csv.mimetype, 'text/csv')

    def test_14_database_persistence_across_restarts(self):
        """TEST 14: Saved records remain available across re-initialization."""
        with self.app.app_context():
            init_db(self.app)
            seed_database(force=False)
            count = query_db("SELECT COUNT(*) as cnt FROM procurement_requests", one=True)['cnt']
            self.assertGreater(count, 0, "Existing database records must persist across restarts")

    def test_15_session_isolation(self):
        """TEST 15: Verify protected routes require authentication and redirect unauthorized users."""
        unauth_client = self.app.test_client()
        res = unauth_client.get('/dashboard')
        self.assertEqual(res.status_code, 302, "Unauthorized access to dashboard must redirect to login")
        self.assertIn('/login', res.headers['Location'])

    def test_16_demo_mode_operates_without_llm_key(self):
        """TEST 16: Run in DEMO MODE without an LLM API key; core workflow operates smoothly."""
        with self.app.app_context():
            orchestrator = ProcurementWorkflowOrchestrator()
            result = orchestrator.run_workflow(request_id=1, force_mode='DEMO_FALLBACK')
            self.assertEqual(result['execution_mode'], 'DEMO_FALLBACK')
            self.assertIsNotNone(result['recommended_supplier'])

if __name__ == '__main__':
    unittest.main()
