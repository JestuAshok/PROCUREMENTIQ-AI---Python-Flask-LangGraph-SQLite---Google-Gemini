"""
Test Suite for Step-by-Step Six AI Agent Execution with Analytics.
Tests discrete execution, state machine validation, invalidation, persistence, and reporting.
"""

import os
import sys
import unittest
import tempfile
from pathlib import Path

# Insert project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from config import Config
from database.db import query_db, execute_db
from agents.workflow import ProcurementWorkflowOrchestrator

class TestSequentialAgentWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp()
        cls.db_path = os.path.join(cls.temp_dir, 'test_workflow.db')
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

        # Login as demo user
        with cls.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_name'] = 'Jahnavi'
            sess['user_email'] = 'jahnavi@procurementiq.ai'
            sess['user_role'] = 'Procurement Lead'

    def test_01_view_workflow_initial_state(self):
        """Step 1 is ready, Steps 2-6 are locked initially."""
        with self.app.app_context():
            req = query_db("SELECT id FROM procurement_requests LIMIT 1", one=True)
            self.assertIsNotNone(req)
            req_id = req['id']

            # Reset outputs for clean testing
            execute_db("DELETE FROM agent_outputs WHERE request_id = ?", (req_id,))
            execute_db("DELETE FROM agent_runs WHERE request_id = ?", (req_id,))

        res = self.client.get(f'/agent-workflow/{req_id}')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn("AI Procurement Analysis", html)
        self.assertIn("Analyze supplier quotations through six specialized AI agents", html)
        self.assertIn("Step 0 of 6 completed", html)
        self.assertIn("Run Requirement Parser Agent", html)

    def test_02_cannot_skip_to_step_2_before_step_1(self):
        """Step skipping is blocked by server-side validation."""
        with self.app.app_context():
            req = query_db("SELECT id FROM procurement_requests LIMIT 1", one=True)
            req_id = req['id']

        # Attempt to run Step 2 directly
        res = self.client.post(f'/agent-workflow/{req_id}/step/2/run', follow_redirects=True)
        html = res.data.decode('utf-8')
        self.assertIn("Step 1 (Requirement Parser Agent) must be completed before running Step 2", html)

    def test_03_execute_step_1_only(self):
        """Execute only Step 1, verify outputs, paragraphs, tables, and next button."""
        with self.app.app_context():
            req = query_db("SELECT id FROM procurement_requests LIMIT 1", one=True)
            req_id = req['id']

        res = self.client.post(f'/agent-workflow/{req_id}/step/1/run', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn("Requirement Parser Agent executed successfully", html)
        self.assertIn("Step 1 of 6 completed", html)
        self.assertIn("Next: Quote Analyzer", html)
        self.assertIn("Requirement Classification Matrix", html)

        # Verify only Step 1 output exists in SQLite
        with self.app.app_context():
            outputs = query_db("SELECT agent_number, status FROM agent_outputs WHERE request_id = ?", (req_id,))
            self.assertEqual(len(outputs), 1)
            self.assertEqual(outputs[0]['agent_number'], 1)
            self.assertEqual(outputs[0]['status'], 'Completed')

    def test_04_execute_step_2_only(self):
        """Execute only Step 2, verify quotes table, price chart data, and next button."""
        with self.app.app_context():
            req = query_db("SELECT id FROM procurement_requests LIMIT 1", one=True)
            req_id = req['id']

        res = self.client.post(f'/agent-workflow/{req_id}/step/2/run', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn("Quote Analyzer Agent executed successfully", html)
        self.assertIn("Step 2 of 6 completed", html)
        self.assertIn("Supplier Quotation Extraction Ledger", html)
        self.assertIn("Next: Supplier Researcher", html)

        # Verify Steps 1 and 2 exist in SQLite
        with self.app.app_context():
            outputs = query_db("SELECT agent_number FROM agent_outputs WHERE request_id = ? ORDER BY agent_number", (req_id,))
            self.assertEqual([o['agent_number'] for o in outputs], [1, 2])

    def test_05_execute_step_3_only(self):
        """Execute only Step 3, verify evidence table and next button."""
        with self.app.app_context():
            req = query_db("SELECT id FROM procurement_requests LIMIT 1", one=True)
            req_id = req['id']

        res = self.client.post(f'/agent-workflow/{req_id}/step/3/run', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn("Supplier Researcher Agent executed successfully", html)
        self.assertIn("Step 3 of 6 completed", html)
        self.assertIn("Supplier Background & Evidence Ledger", html)
        self.assertIn("Next: Risk Assessor", html)

    def test_06_execute_step_4_only(self):
        """Execute only Step 4, verify risk register table, mitigations, and next button."""
        with self.app.app_context():
            req = query_db("SELECT id FROM procurement_requests LIMIT 1", one=True)
            req_id = req['id']

        res = self.client.post(f'/agent-workflow/{req_id}/step/4/run', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn("Risk Assessor Agent executed successfully", html)
        self.assertIn("Step 4 of 6 completed", html)
        self.assertIn("Procurement Risk Register & Action Plan", html)
        self.assertIn("Next: Cost Optimizer", html)

    def test_07_execute_step_5_only(self):
        """Execute only Step 5, verify deterministic cost breakdown and next button."""
        with self.app.app_context():
            req = query_db("SELECT id FROM procurement_requests LIMIT 1", one=True)
            req_id = req['id']

        res = self.client.post(f'/agent-workflow/{req_id}/step/5/run', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn("Cost Optimizer Agent executed successfully", html)
        self.assertIn("Step 5 of 6 completed", html)
        self.assertIn("Detailed Deterministic Landed Cost Breakdown", html)
        self.assertIn("Next: Procurement Advisor", html)

    def test_08_execute_step_6_only(self):
        """Execute Step 6, verify ranked vendor shortlist, 9-point narrative, and human decision form."""
        with self.app.app_context():
            req = query_db("SELECT id FROM procurement_requests LIMIT 1", one=True)
            req_id = req['id']

        res = self.client.post(f'/agent-workflow/{req_id}/step/6/run', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn("Procurement Advisor Agent executed successfully", html)
        self.assertIn("Step 6 of 6 completed", html)
        self.assertIn("Multi-Criteria Vendor Ranking Ledger", html)
        self.assertIn("Procurement Award & Decision Confirmation", html)
        self.assertIn("All 6 Agents Completed", html)

    def test_09_earlier_steps_remain_inspectable(self):
        """Users can click any earlier step and view its full output, tables, and charts."""
        with self.app.app_context():
            req = query_db("SELECT id FROM procurement_requests LIMIT 1", one=True)
            req_id = req['id']

        for step_num in range(1, 7):
            res = self.client.get(f'/agent-workflow/{req_id}?step={step_num}')
            self.assertEqual(res.status_code, 200)
            html = res.data.decode('utf-8')
            self.assertIn(f"AGENT 0{step_num}", html)
            self.assertIn("Execution Summary", html)
            self.assertIn("Natural-Language Explanation", html)
            self.assertIn("Key Findings", html)

    def test_10_rerun_step_3_invalidates_steps_4_to_6(self):
        """Re-running an earlier step invalidates dependent downstream steps."""
        with self.app.app_context():
            req = query_db("SELECT id FROM procurement_requests LIMIT 1", one=True)
            req_id = req['id']

        # Re-run Step 3
        res = self.client.post(f'/agent-workflow/{req_id}/step/3/run', follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        with self.app.app_context():
            outputs = query_db("SELECT agent_number FROM agent_outputs WHERE request_id = ? ORDER BY agent_number", (req_id,))
            numbers = [o['agent_number'] for o in outputs]
            self.assertEqual(numbers, [1, 2, 3], "Steps 4, 5, 6 must be invalidated/removed after re-running Step 3")

    def test_11_human_decision_recording(self):
        """Human approval records decision in decision_history."""
        with self.app.app_context():
            req = query_db("SELECT id FROM procurement_requests LIMIT 1", one=True)
            req_id = req['id']

        res = self.client.post(f'/agent-workflow/{req_id}/decision', data={
            'decision_action': 'approve',
            'recommended_supplier': 'Apex Industrial Solutions',
            'decision_reason': 'Approved top candidate meeting all requirements.'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn("Human procurement decision logged", html)

        with self.app.app_context():
            dh = query_db("SELECT * FROM decision_history WHERE request_id = ? ORDER BY id DESC LIMIT 1", (req_id,), one=True)
            self.assertIsNotNone(dh)
            self.assertEqual(dh['selected_supplier'], 'Apex Industrial Solutions')

if __name__ == '__main__':
    unittest.main()
