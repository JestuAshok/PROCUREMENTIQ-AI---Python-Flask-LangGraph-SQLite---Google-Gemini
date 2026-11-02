"""
AI Agent Workflow Routes for PROCUREMENTIQ AI
Implements discrete, sequential, step-by-step six-agent execution with persistent
state management, strict server-side order validation, detailed analytics, and human governance.
"""

import json
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from routes.auth import login_required
from database.db import query_db, execute_db, get_db
from agents.workflow import ProcurementWorkflowOrchestrator

workflow_bp = Blueprint('workflow', __name__)

AGENT_METADATA = [
    {
        "number": 1,
        "name": "Requirement Parser Agent",
        "short_name": "Requirement Parser",
        "purpose": "Convert procurement requests into structured, machine-readable evaluation criteria",
        "icon": "bi-file-earmark-text"
    },
    {
        "number": 2,
        "name": "Quote Analyzer Agent",
        "short_name": "Quote Analyzer",
        "purpose": "Extract, normalize, and validate supplier quotation information and data quality",
        "icon": "bi-file-earmark-spreadsheet"
    },
    {
        "number": 3,
        "name": "Supplier Researcher Agent",
        "short_name": "Supplier Researcher",
        "purpose": "Gather supplier background profiles, performance history, and evidence coverage",
        "icon": "bi-building-check"
    },
    {
        "number": 4,
        "name": "Risk Assessor Agent",
        "short_name": "Risk Assessor",
        "purpose": "Evaluate delivery, compliance, warranty, and commercial terms risks",
        "icon": "bi-shield-exclamation"
    },
    {
        "number": 5,
        "name": "Cost Optimizer Agent",
        "short_name": "Cost Optimizer",
        "purpose": "Calculate deterministic total procurement costs and budget feasibility",
        "icon": "bi-cash-coin"
    },
    {
        "number": 6,
        "name": "Procurement Advisor Agent",
        "short_name": "Procurement Advisor",
        "purpose": "Generate explainable weighted vendor rankings and formal award recommendations",
        "icon": "bi-award"
    }
]

@workflow_bp.route('/agent-workflow/<int:request_id>')
@workflow_bp.route('/workflow/<int:request_id>')
@login_required
def view_workflow(request_id):
    user_id = session.get('user_id')
    req = query_db(
        "SELECT * FROM procurement_requests WHERE id = ? AND (user_id = ? OR ? = 1)",
        (request_id, user_id, user_id), one=True
    )
    if not req:
        flash("Procurement request not found or access denied.", "danger")
        return redirect(url_for('dashboard.dashboard_view'))

    # Quotation count
    quotes_count = query_db(
        "SELECT COUNT(*) as cnt FROM quotations WHERE request_id = ?",
        (request_id,), one=True
    )['cnt']

    # Get or create active agent run
    orchestrator = ProcurementWorkflowOrchestrator()
    latest_run = orchestrator.get_or_create_run(request_id)
    run_id = latest_run['id']

    # Fetch all agent outputs for this run
    agent_outputs = query_db(
        "SELECT * FROM agent_outputs WHERE run_id = ? ORDER BY agent_number ASC",
        (run_id,)
    )
    outputs_by_number = {}
    for ao in agent_outputs:
        ao_dict = dict(ao)
        try:
            ao_dict['full_json'] = json.loads(ao_dict.get('full_output_json') or '{}')
        except Exception:
            ao_dict['full_json'] = {}
        outputs_by_number[ao_dict['agent_number']] = ao_dict

    # Determine step status machine: Locked, Ready, Running, Completed, Failed
    # Rules:
    # - Step 1 is Completed if output exists with status Completed; else Ready.
    # - Step 2 is Completed if output exists with Completed;
    #   if not completed: Ready if Step 1 is Completed, else Locked.
    # - Step N is Completed if output exists with Completed;
    #   if not completed: Ready if Step N-1 is Completed, else Locked.
    # - If output status == 'Failed', status is Failed.
    steps_state = []
    completed_count = 0

    for meta in AGENT_METADATA:
        num = meta['number']
        ao = outputs_by_number.get(num)
        status = "Locked"

        if ao:
            ao_status = ao.get('status', 'Completed')
            if ao_status == 'Completed':
                status = "Completed"
                completed_count += 1
            elif ao_status == 'Failed':
                status = "Failed"
            elif ao_status == 'Running':
                status = "Running"
            else:
                status = "Ready"
        else:
            if num == 1:
                status = "Ready"
            else:
                prev_ao = outputs_by_number.get(num - 1)
                if prev_ao and prev_ao.get('status') == 'Completed':
                    status = "Ready"
                else:
                    status = "Locked"

        steps_state.append({
            "number": num,
            "name": meta['name'],
            "short_name": meta['short_name'],
            "purpose": meta['purpose'],
            "icon": meta['icon'],
            "status": status,
            "is_completed": (status == "Completed"),
            "is_ready": (status == "Ready"),
            "is_failed": (status == "Failed"),
            "is_locked": (status == "Locked"),
            "output": ao.get('full_json') if ao else None,
            "output_summary": ao.get('output_summary') if ao else None,
            "input_summary": ao.get('input_summary') if ao else None,
            "execution_duration": ao.get('execution_duration_seconds', 0.0) if ao else 0.0,
            "warnings": ao.get('warnings') if ao and ao.get('warnings') != 'None' else None
        })

    # Determine active step to view
    requested_step = request.args.get('step', type=int)
    active_step = 1

    if requested_step and 1 <= requested_step <= 6:
        step_info = steps_state[requested_step - 1]
        # Allow viewing if Completed, Ready, Failed, or Running
        if not step_info['is_locked']:
            active_step = requested_step
        else:
            flash(f"Step {requested_step} is locked. You must complete prior steps first.", "warning")
            # Fall back to current ready or highest completed
            active_step = max(1, completed_count + 1 if completed_count < 6 else 6)
    else:
        # Default: first uncompleted ready/failed step, or step 6 if all completed
        first_actionable = next((s['number'] for s in steps_state if s['status'] in ('Ready', 'Failed', 'Running')), None)
        if first_actionable:
            active_step = first_actionable
        elif completed_count == 6:
            active_step = 6
        else:
            active_step = 1

    # Mark active step
    for s in steps_state:
        s['is_current'] = (s['number'] == active_step)

    active_step_data = steps_state[active_step - 1]

    # Load decision history if on Step 6
    decision_history = []
    if active_step == 6 or completed_count == 6:
        decision_history = query_db("""
            SELECT dh.*, u.full_name as user_name
            FROM decision_history dh
            JOIN users u ON dh.user_id = u.id
            WHERE dh.request_id = ?
            ORDER BY dh.id DESC
        """, (request_id,))

    return render_template(
        'agent_workflow.html',
        proc_req=req,
        latest_run=latest_run,
        steps_state=steps_state,
        completed_count=completed_count,
        active_step=active_step,
        active_step_data=active_step_data,
        quotes_count=quotes_count,
        decision_history=decision_history
    )

@workflow_bp.route('/agent-workflow/<int:request_id>/step/<int:step_number>/run', methods=['POST'])
@login_required
def run_single_step(request_id, step_number):
    user_id = session.get('user_id')
    req = query_db(
        "SELECT * FROM procurement_requests WHERE id = ? AND (user_id = ? OR ? = 1)",
        (request_id, user_id, user_id), one=True
    )
    if not req:
        flash("Procurement request not found or access denied.", "danger")
        return redirect(url_for('dashboard.dashboard_view'))

    if step_number < 1 or step_number > 6:
        flash("Invalid agent step requested.", "danger")
        return redirect(url_for('workflow.view_workflow', request_id=request_id))

    # Load custom weights if set
    settings_row = query_db("SELECT * FROM user_settings WHERE user_id = ?", (user_id,), one=True)
    custom_weights = None
    if settings_row:
        custom_weights = {
            'cost': settings_row['weight_cost'],
            'delivery': settings_row['weight_delivery'],
            'risk': settings_row['weight_risk'],
            'warranty': settings_row['weight_warranty']
        }

    orchestrator = ProcurementWorkflowOrchestrator()
    try:
        result = orchestrator.execute_single_step(
            request_id=request_id,
            step_number=step_number,
            custom_weights=custom_weights
        )
        agent_name = result.get('agent_name', f'Step {step_number}')
        flash(f"{agent_name} executed successfully in {result.get('execution_duration_seconds', 0.0)}s!", "success")
    except Exception as e:
        flash(f"Step {step_number} execution halted: {str(e)}", "danger")

    return redirect(url_for('workflow.view_workflow', request_id=request_id, step=step_number))

@workflow_bp.route('/agent-workflow/<int:request_id>/confirm-quotes', methods=['POST'])
@login_required
def confirm_quotes(request_id):
    user_id = session.get('user_id')
    req = query_db(
        "SELECT * FROM procurement_requests WHERE id = ? AND (user_id = ? OR ? = 1)",
        (request_id, user_id, user_id), one=True
    )
    if not req:
        flash("Procurement request not found.", "danger")
        return redirect(url_for('dashboard.dashboard_view'))

    execute_db("UPDATE quotations SET is_confirmed = 1 WHERE request_id = ?", (request_id,))
    flash("Quotation data confirmed and marked as reviewed for procurement analysis.", "success")
    return redirect(url_for('workflow.view_workflow', request_id=request_id, step=2))

@workflow_bp.route('/agent-workflow/<int:request_id>/decision', methods=['POST'])
@login_required
def record_decision(request_id):
    user_id = session.get('user_id')
    req = query_db(
        "SELECT * FROM procurement_requests WHERE id = ? AND (user_id = ? OR ? = 1)",
        (request_id, user_id, user_id), one=True
    )
    if not req:
        flash("Procurement request not found.", "danger")
        return redirect(url_for('dashboard.dashboard_view'))

    action = request.form.get('decision_action', 'approve')
    recommended_supplier = request.form.get('recommended_supplier', '').strip()
    selected_supplier = request.form.get('selected_supplier', '').strip()
    decision_reason = request.form.get('decision_reason', '').strip()

    if action == 'approve':
        selected_supplier = recommended_supplier
        was_overridden = 0
        if not decision_reason:
            decision_reason = "Approved AI recommended supplier based on comprehensive multi-agent evaluation."
    elif action == 'alternative':
        if not selected_supplier:
            flash("Please specify the alternative supplier selected.", "danger")
            return redirect(url_for('workflow.view_workflow', request_id=request_id, step=6))
        if not decision_reason:
            flash("A justification reason is required when selecting an alternative supplier.", "danger")
            return redirect(url_for('workflow.view_workflow', request_id=request_id, step=6))
        was_overridden = 1
    elif action == 'reject':
        selected_supplier = "None (All Rejected)"
        was_overridden = 1
        if not decision_reason:
            flash("A reason must be recorded when rejecting all supplier proposals.", "danger")
            return redirect(url_for('workflow.view_workflow', request_id=request_id, step=6))
    else:
        flash("Unrecognized decision action.", "danger")
        return redirect(url_for('workflow.view_workflow', request_id=request_id, step=6))

    execute_db("""
        INSERT INTO decision_history (
            request_id, user_id, recommended_supplier, selected_supplier,
            was_overridden, override_reason
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (request_id, user_id, recommended_supplier or "None", selected_supplier, was_overridden, decision_reason))

    execute_db("""
        UPDATE procurement_requests
        SET status = 'Completed', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (request_id,))

    flash(f"Human procurement decision logged: Award status recorded for '{selected_supplier}'.", "success")
    return redirect(url_for('workflow.view_workflow', request_id=request_id, step=6))

@workflow_bp.route('/agent-workflow/<int:request_id>/run', methods=['POST'], endpoint='run_workflow')
@workflow_bp.route('/agent-workflow/<int:request_id>/run-legacy', methods=['POST'], endpoint='run_workflow_legacy')
@login_required
def run_workflow(request_id):
    """
    Fallback for any legacy batch run triggers, redirects to Step 1.
    """
    return run_single_step(request_id, 1)

# Backwards compatibility alias
run_workflow_legacy = run_workflow
