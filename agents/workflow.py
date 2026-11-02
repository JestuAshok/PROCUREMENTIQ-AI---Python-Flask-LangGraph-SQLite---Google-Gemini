"""
AI AGENT WORKFLOW ORCHESTRATOR FOR PROCUREMENTIQ AI
Coordinates all six specialized procurement agents sequentially with step-by-step execution.
Supports discrete single-step execution, persistent state machines, invalidation of stale steps,
and full persistence into SQLite.
"""

import os
import time
import json
import sqlite3
from datetime import datetime

from agents.requirement_parser import RequirementParserAgent
from agents.quote_analyzer import QuoteAnalyzerAgent
from agents.supplier_researcher import SupplierResearcherAgent
from agents.risk_assessor import RiskAssessorAgent
from agents.cost_optimizer import CostOptimizerAgent
from agents.procurement_advisor import ProcurementAdvisorAgent

try:
    from langgraph.graph import StateGraph, END
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False

class ProcurementWorkflowOrchestrator:
    def __init__(self, db_conn=None, llm_client=None):
        self.db_conn = db_conn
        self.llm_client = llm_client
        self.parser = RequirementParserAgent(llm_client)
        self.analyzer = QuoteAnalyzerAgent(llm_client)
        self.researcher = SupplierResearcherAgent(llm_client=llm_client)
        self.assessor = RiskAssessorAgent(llm_client)
        self.optimizer = CostOptimizerAgent(llm_client)
        self.advisor = ProcurementAdvisorAgent(llm_client)

    def _ensure_db(self):
        if not self.db_conn:
            from database.db import get_db
            self.db_conn = get_db()
        return self.db_conn

    def get_or_create_run(self, request_id, force_mode=None):
        """
        Retrieves the active agent_runs record or initializes a new one.
        """
        conn = self._ensure_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM agent_runs WHERE request_id = ? ORDER BY id DESC LIMIT 1", (request_id,))
        run_row = cur.fetchone()

        if run_row:
            return dict(run_row)

        is_demo = os.environ.get('DEMO_MODE', 'true').lower() in ('true', '1')
        api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('OPENAI_API_KEY') or os.environ.get('GROQ_API_KEY')
        mode = "LLM_LANGGRAPH" if (not is_demo and api_key and HAS_LANGGRAPH) else "DEMO_FALLBACK"
        if force_mode:
            mode = force_mode

        cur.execute("""
            INSERT INTO agent_runs (request_id, status, execution_mode, started_at)
            VALUES (?, 'In Progress', ?, CURRENT_TIMESTAMP)
        """, (request_id, mode))
        conn.commit()
        run_id = cur.lastrowid

        cur.execute("SELECT * FROM agent_runs WHERE id = ?", (run_id,))
        return dict(cur.fetchone())

    def execute_single_step(self, request_id, step_number, custom_weights=None, force_mode=None):
        """
        Executes ONLY the single specified step (1 through 6).
        Enforces server-side prerequisites, state persistence, and downstream step invalidation.
        """
        conn = self._ensure_db()
        cur = conn.cursor()

        # 1. Fetch procurement request
        cur.execute("SELECT * FROM procurement_requests WHERE id = ?", (request_id,))
        req_row = cur.fetchone()
        if not req_row:
            raise ValueError(f"Procurement request ID {request_id} not found.")
        req_data = dict(req_row)

        # 2. Get active agent run
        run_data = self.get_or_create_run(request_id, force_mode=force_mode)
        run_id = run_data['id']

        # Prevent duplicate simultaneous run if currently running
        if run_data.get('status') == 'Running':
            raise ValueError("Another agent is currently executing. Please wait for it to complete.")

        # Helper to load output of completed step
        def get_step_output(num):
            cur.execute("""
                SELECT * FROM agent_outputs
                WHERE run_id = ? AND agent_number = ? AND status = 'Completed'
                LIMIT 1
            """, (run_id, num))
            row = cur.fetchone()
            if not row:
                return None
            row_dict = dict(row)
            try:
                row_dict['full_json'] = json.loads(row_dict.get('full_output_json') or '{}')
            except Exception:
                row_dict['full_json'] = {}
            return row_dict

        # 3. Server-side prerequisite validation
        step1_out = get_step_output(1)
        step2_out = get_step_output(2)
        step3_out = get_step_output(3)
        step4_out = get_step_output(4)
        step5_out = get_step_output(5)

        if step_number == 1:
            pass  # Step 1 can always be run
        elif step_number == 2:
            if not step1_out:
                raise ValueError("Step 1 (Requirement Parser Agent) must be completed before running Step 2.")
            cur.execute("SELECT COUNT(*) as cnt FROM quotations WHERE request_id = ?", (request_id,))
            q_cnt = cur.fetchone()['cnt']
            if q_cnt == 0:
                raise ValueError("At least one supplier quotation must be uploaded before running Step 2 (Quote Analyzer).")
        elif step_number == 3:
            if not step2_out:
                raise ValueError("Step 2 (Quote Analyzer Agent) must be completed before running Step 3.")
        elif step_number == 4:
            if not step3_out:
                raise ValueError("Step 3 (Supplier Researcher Agent) must be completed before running Step 4.")
        elif step_number == 5:
            if not step4_out:
                raise ValueError("Step 4 (Risk Assessor Agent) must be completed before running Step 5.")
        elif step_number == 6:
            if not (step1_out and step2_out and step3_out and step4_out and step5_out):
                raise ValueError("Steps 1 through 5 must all be completed before running Step 6 (Procurement Advisor Agent).")
        else:
            raise ValueError(f"Invalid step number {step_number}. Must be between 1 and 6.")

        # 4. Invalidation of dependent downstream steps if re-running
        cur.execute("DELETE FROM agent_outputs WHERE run_id = ? AND agent_number > ?", (run_id, step_number))
        if step_number < 4:
            cur.execute("DELETE FROM risk_assessments WHERE request_id = ?", (request_id,))
        if step_number < 5:
            cur.execute("DELETE FROM cost_comparisons WHERE request_id = ?", (request_id,))
        if step_number < 6:
            cur.execute("DELETE FROM recommendations WHERE request_id = ?", (request_id,))
            cur.execute("UPDATE procurement_requests SET status = 'In Review' WHERE id = ?", (request_id,))
            cur.execute("UPDATE agent_runs SET status = 'In Progress' WHERE id = ?", (run_id,))
        conn.commit()

        # 5. Execute ONLY the target agent step
        step_result = None
        try:
            if step_number == 1:
                step_result = self.parser.execute(req_data)

            elif step_number == 2:
                cur.execute("SELECT * FROM quotations WHERE request_id = ?", (request_id,))
                quotes_list = [dict(q) for q in cur.fetchall()]
                parsed_reqs = step1_out['full_json'].get('structured_data', req_data)
                step_result = self.analyzer.execute(quotes_list, parsed_reqs)

            elif step_number == 3:
                normalized_quotes = step2_out['full_json'].get('normalized_quotes', [])
                step_result = self.researcher.execute(normalized_quotes, db_conn=conn)

            elif step_number == 4:
                parsed_reqs = step1_out['full_json'].get('structured_data', req_data)
                normalized_quotes = step2_out['full_json'].get('normalized_quotes', [])
                supplier_profiles = step3_out['full_json'].get('supplier_profiles', [])
                step_result = self.assessor.execute(normalized_quotes, supplier_profiles, parsed_reqs)

                # Persist to risk_assessments table
                cur.execute("DELETE FROM risk_assessments WHERE request_id = ?", (request_id,))
                for r in step_result.get('risk_assessments', []):
                    cur.execute("""
                        INSERT INTO risk_assessments (
                            request_id, quotation_id, supplier_name, overall_risk_score, risk_category,
                            delivery_risk, compliance_risk, dependency_risk, documentation_risk, commercial_terms_risk,
                            supporting_evidence, missing_evidence, recommended_mitigation
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        request_id, r.get('quotation_id'), r['supplier_name'], r['overall_risk_score'], r['risk_category'],
                        r.get('delivery_risk', 'Medium'), r.get('compliance_risk', 'Medium'),
                        r.get('dependency_risk', 'Medium'), r.get('documentation_risk', 'Medium'),
                        r.get('commercial_terms_risk', 'Medium'),
                        r.get('supporting_evidence', ''), r.get('missing_evidence', ''),
                        r.get('recommended_mitigation', '')
                    ))

            elif step_number == 5:
                parsed_reqs = step1_out['full_json'].get('structured_data', req_data)
                normalized_quotes = step2_out['full_json'].get('normalized_quotes', [])
                step_result = self.optimizer.execute(normalized_quotes, parsed_reqs)

                # Persist to cost_comparisons table
                cur.execute("DELETE FROM cost_comparisons WHERE request_id = ?", (request_id,))
                for c in step_result.get('cost_comparisons', []):
                    cur.execute("""
                        INSERT INTO cost_comparisons (
                            request_id, quotation_id, supplier_name, unit_price, quantity,
                            subtotal, discount_amount, net_subtotal, tax_amount, shipping_cost,
                            installation_cost, other_charges, estimated_total_cost, currency,
                            formulas_used, missing_cost_warnings
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        request_id, c.get('quotation_id'), c['supplier_name'], c['unit_price'], c['quantity'],
                        c['subtotal'], c['discount_amount'], c['net_subtotal'], c['tax_amount'], c['shipping_cost'],
                        c['installation_cost'], c['other_charges'], c['estimated_total_cost'], c['currency'],
                        c.get('formulas_used', ''), c.get('missing_cost_warnings', '')
                    ))

            elif step_number == 6:
                parsed_reqs = step1_out['full_json'].get('structured_data', req_data)
                normalized_quotes = step2_out['full_json'].get('normalized_quotes', [])
                supplier_profiles = step3_out['full_json'].get('supplier_profiles', [])
                risk_assessments = step4_out['full_json'].get('risk_assessments', [])
                cost_comparisons = step5_out['full_json'].get('cost_comparisons', [])

                step_result = self.advisor.execute(
                    parsed_reqs=parsed_reqs,
                    normalized_quotes=normalized_quotes,
                    supplier_profiles=supplier_profiles,
                    risk_assessments=risk_assessments,
                    cost_comparisons=cost_comparisons,
                    custom_weights=custom_weights
                )

                # Persist to recommendations table
                cur.execute("DELETE FROM recommendations WHERE request_id = ?", (request_id,))
                for rec in step_result.get('ranked_recommendations', []):
                    cur.execute("""
                        INSERT INTO recommendations (
                            request_id, quotation_id, supplier_name, rank, is_recommended,
                            overall_score, cost_score, delivery_score, risk_score, warranty_score,
                            weight_breakdown, satisfies_mandatory, disqualification_reasons,
                            key_advantages, main_disadvantages, explanation, negotiation_tips
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        request_id, rec.get('quotation_id'), rec['supplier_name'], rec['rank'],
                        1 if rec.get('is_recommended') else 0,
                        rec['overall_score'], rec['cost_score'], rec['delivery_score'],
                        rec['risk_score'], rec['warranty_score'],
                        rec.get('weight_breakdown', '{}'), 1 if rec.get('satisfies_mandatory') else 0,
                        rec.get('disqualification_reasons', ''),
                        rec.get('key_advantages', ''), rec.get('main_disadvantages', ''),
                        rec.get('explanation', ''), rec.get('negotiation_tips', '')
                    ))

                # Update status of request and agent run
                cur.execute("""
                    UPDATE procurement_requests
                    SET status = 'Recommendation Ready', updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (request_id,))

                cur.execute("""
                    UPDATE agent_runs
                    SET status = 'Completed', completed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (run_id,))

            # 6. Save agent output record
            self._save_single_output(run_id, request_id, step_result)
            conn.commit()

        except Exception as e:
            # Save failed status
            cur.execute("DELETE FROM agent_outputs WHERE run_id = ? AND agent_number = ?", (run_id, step_number))
            error_json = json.dumps({
                "agent_number": step_number,
                "agent_name": f"Agent {step_number}",
                "status": "Failed",
                "error_message": str(e)
            })
            cur.execute("""
                INSERT INTO agent_outputs (
                    run_id, request_id, agent_number, agent_name, purpose, status,
                    input_summary, output_summary, full_output_json, execution_duration_seconds,
                    warnings, evidence_references
                ) VALUES (?, ?, ?, ?, ?, 'Failed', 'Execution halted by error', ?, ?, 0.0, ?, 'Execution Error')
            """, (
                run_id, request_id, step_number, f"Agent {step_number}",
                "Single step execution failed", f"Error: {str(e)}", error_json, str(e)
            ))
            conn.commit()
            raise e

        return step_result

    def _save_single_output(self, run_id, request_id, res):
        conn = self._ensure_db()
        cur = conn.cursor()
        
        # Remove any existing output for this step in this run
        cur.execute("DELETE FROM agent_outputs WHERE run_id = ? AND agent_number = ?", (run_id, res['agent_number']))
        
        warnings_str = " | ".join(res.get('warnings', [])) if res.get('warnings') else "None"
        full_json = json.dumps(res, default=str)
        
        cur.execute("""
            INSERT INTO agent_outputs (
                run_id, request_id, agent_number, agent_name, purpose, status,
                input_summary, output_summary, full_output_json, execution_duration_seconds,
                warnings, evidence_references
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id, request_id, res['agent_number'], res['agent_name'], res['purpose'], res.get('status', 'Completed'),
            res.get('input_summary', ''), res.get('output_summary', ''), full_json,
            res.get('execution_duration_seconds', 0.0), warnings_str, res.get('evidence_references', '')
        ))
        conn.commit()

    def run_workflow(self, request_id, custom_weights=None, force_mode=None):
        """
        Backward-compatible batch execution running all 6 steps sequentially.
        """
        run_data = self.get_or_create_run(request_id, force_mode=force_mode)
        mode = run_data.get('execution_mode', 'DEMO_FALLBACK')
        start_t = time.time()
        results = []
        for step in range(1, 7):
            res = self.execute_single_step(request_id, step, custom_weights=custom_weights, force_mode=force_mode)
            results.append(res)
        
        tot_duration = round(time.time() - start_t, 2)
        return {
            "run_id": run_data['id'],
            "request_id": request_id,
            "status": "Completed",
            "execution_mode": mode,
            "total_duration_seconds": tot_duration,
            "agent_results": results,
            "recommended_supplier": results[-1].get('recommended_supplier')
        }
