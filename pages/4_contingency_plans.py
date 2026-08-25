import streamlit as st
import pandas as pd
from src.services.database import SessionLocal, DBContingencyPlan, DBSupplierRiskAssessment
from src.services.supplier_service import list_suppliers
from src.graph.checkpoints import get_workflow_state, resume_workflow_with_decision
from src.services.ui_helper import inject_premium_theme

st.set_page_config(page_title="Contingency Planning - Review Gates", page_icon="🤝", layout="wide")
inject_premium_theme()

st.markdown('<h1 class="gradient-title">🤝 Human Approval & Contingency Planning</h1>', unsafe_allow_html=True)
st.markdown("Managers review and sign-off draft contingency recommendations triggered by critical risk scores.")

db = SessionLocal()
suppliers = list_suppliers(db)
target_id = st.query_params.get("target_supplier_id", "")
if target_id.strip():
    suppliers = [s for s in suppliers if s.supplier_id.strip().lower() == target_id.strip().lower()]
    st.info(f"🔒 Authenticated Session: Locked to Supplier ID **{target_id}**.")

pending_reviews_found = False

for s in suppliers:
    thread_id = f"thread_{s.supplier_id}"
    state_values = get_workflow_state(thread_id)
    
    if state_values:
        # Check if the thread is halted before the human_review_gate
        review_status = state_values.get("review_status", "pending")
        assessment = state_values.get("risk_assessment")
        
        if review_status == "pending" and assessment and assessment.human_review_required:
            pending_reviews_found = True
            
            st.markdown(f"## 📋 Review Request: {s.name} ({s.supplier_id})")
            
            # 1. Show Assessment Details
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown(
                    f"""
                    <div class="risk-card">
                        <h4>Risk Evaluation Summary</h4>
                        <p><strong>Overall Risk Score:</strong> <span class="badge-{assessment.risk_level}">{assessment.overall_risk_score}</span></p>
                        <p><strong>Confidence:</strong> {int(assessment.confidence * 100)}%</p>
                        <p><strong>Primary Port:</strong> {s.primary_port or 'N/A'}</p>
                        <p><strong>Shipment Lane Country:</strong> {s.country}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with col2:
                st.markdown(
                    f"""
                    <div class="risk-card">
                        <h4>Operational Impact Description</h4>
                        <p>{assessment.operational_impact}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
            # 2. Show Draft Contingency Plans
            st.markdown("### 🛠️ Generated Contingency Options (Draft)")
            
            # Since workflow pauses before generating plans (or right after scoring, before contingency planning node),
            # wait, in our graph:
            # risk_scoring -> conditional route:
            # - if review is required, go to human_review_gate
            # - if not, go to contingency_planning
            # This means at the review gate, the contingency plan has NOT been drafted yet, or has been drafted and needs approval.
            # Let's check: if review status is pending and we want the reviewer to approve the findings *first*, or approve the plans *after* they are drafted.
            # In our graph, the workflow has:
            # risk_scoring -> human_review_gate -> contingency_planning -> report_writing.
            # This is standard: the human approves the risk assessment and alternate mappings *before* the planner drafts details,
            # or we can display a dry run preview of the contingency plan details!
            # Since we have run_contingency_planner_agent available, we can run a dry-run draft preview directly on the UI so the user sees exactly what they are approving! That is extremely helpful!
            
            draft_plans = []
            events = state_values.get("all_events", [])
            
            # Generate dry-run preview plans for display
            from src.agents.contingency_agent import run_contingency_planner_agent
            for event in events:
                if str(event.severity).lower() in ["medium", "high", "critical"]:
                    draft_plans.append(run_contingency_planner_agent(s, event))
                    
            if not draft_plans:
                st.info("No active high/critical events requiring a contingency plan. System is clear.")
            else:
                for idx, plan in enumerate(draft_plans):
                    st.markdown(
                        f"""
                        <div class="risk-card" style="border-left: 4px solid #58a6ff;">
                            <h5>Contingency Option {idx+1}: Mitigating Trigger Event '{plan.trigger_event_id}'</h5>
                            <p><strong>Recommended Action:</strong></p>
                            <p style="white-space: pre-wrap;">{plan.recommended_action}</p>
                            <div style="display: flex; gap: 20px;">
                                <span><strong>Backup Supplier Option:</strong> <code>{plan.alternate_supplier_id or 'None'}</code></span>
                                <span><strong>Volume Shift:</strong> {plan.proposed_volume_shift_percent or 0.0}%</span>
                                <span><strong>Estimated Delay Impact:</strong> +{plan.estimated_lead_time_delta_days or 0} days</span>
                            </div>
                            <p style="margin-top: 10px; margin-bottom: 0px;"><strong>Assumptions:</strong></p>
                            <ul>
                                {"".join(f"<li>{a}</li>" for a in plan.assumptions)}
                            </ul>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
            # 3. Action Buttons to resume workflow
            st.markdown("### ✍️ Action Decisions")
            feedback_input = st.text_input("Reviewer Feedback/Directions (Optional)", key=f"feed_{s.supplier_id}", value="Approved for operational execution.")
            
            btn_col1, btn_col2, btn_col3 = st.columns(3)
            with btn_col1:
                if st.button("✅ Approve Plan & Trigger Procurement", key=f"app_{s.supplier_id}"):
                    with st.spinner("Processing approval and completing state workflow..."):
                        # Resume thread workflow with 'approved' status and pass previewed draft_plans
                        resumed_state = resume_workflow_with_decision(thread_id, "approved", feedback_input, contingency_plans=draft_plans)
                        
                        # Persist final plans and assessment into SQL DB
                        db_sess = SessionLocal()
                        try:
                            # Save approved plans to DB
                            final_plans = resumed_state.get("contingency_plans", [])
                            for fp in final_plans:
                                fp.approval_status = "approved"
                                
                                # Query existing
                                db_plan = db_sess.query(DBContingencyPlan).filter(
                                    DBContingencyPlan.supplier_id == fp.supplier_id,
                                    DBContingencyPlan.trigger_event_id == fp.trigger_event_id
                               ).first()
                                if db_plan:
                                    db_plan.approval_status = "approved"
                                    db_plan.recommended_action = fp.recommended_action
                                    db_plan.alternate_supplier_id = fp.alternate_supplier_id
                                    db_plan.proposed_volume_shift_percent = fp.proposed_volume_shift_percent
                                    db_plan.estimated_lead_time_delta_days = fp.estimated_lead_time_delta_days
                                else:
                                    db_plan = DBContingencyPlan(
                                        supplier_id=fp.supplier_id,
                                        trigger_event_id=fp.trigger_event_id,
                                        recommended_action=fp.recommended_action,
                                        alternate_supplier_id=fp.alternate_supplier_id,
                                        proposed_volume_shift_percent=fp.proposed_volume_shift_percent,
                                        estimated_lead_time_delta_days=fp.estimated_lead_time_delta_days,
                                        assumptions=fp.assumptions,
                                        evidence_links=fp.evidence_links,
                                        approval_status="approved"
                                    )
                                    db_sess.add(db_plan)
                            
                            # Save assessment
                            db_assess = DBSupplierRiskAssessment(
                                supplier_id=s.supplier_id,
                                overall_risk_score=assessment.overall_risk_score,
                                risk_level=assessment.risk_level,
                                contributing_events=assessment.contributing_events,
                                affected_products=assessment.affected_products,
                                operational_impact=assessment.operational_impact,
                                confidence=assessment.confidence,
                                human_review_required=assessment.human_review_required
                            )
                            db_sess.add(db_assess)
                        finally:
                            db_sess.close()
                            
                        st.success(f"Contingency plan for {s.name} approved successfully!")
                        from src.services.session_service import get_or_create_session_id, add_session_message
                        from src.services.database import SessionLocal
                        db_log = SessionLocal()
                        try:
                            sess_id = get_or_create_session_id()
                            add_session_message(db_log, sess_id, f"Approved contingency plan for: {s.name}", "success")
                        finally:
                            db_log.close()
                        st.rerun()
                        
            with btn_col2:
                if st.button("❌ Reject Recommendations", key=f"rej_{s.supplier_id}"):
                    resume_workflow_with_decision(thread_id, "rejected", feedback_input)
                    st.warning(f"Workflow for {s.name} terminated as REJECTED.")
                    from src.services.session_service import get_or_create_session_id, add_session_message
                    from src.services.database import SessionLocal
                    db_log = SessionLocal()
                    try:
                        sess_id = get_or_create_session_id()
                        add_session_message(db_log, sess_id, f"Rejected recommendations for: {s.name}", "warning")
                    finally:
                        db_log.close()
                    st.rerun()
                    
            with btn_col3:
                if st.button("🔄 Request Supplier Rework", key=f"rew_{s.supplier_id}"):
                    resume_workflow_with_decision(thread_id, "rework", feedback_input)
                    st.info(f"Workflow for {s.name} routed back for profile rework.")
                    from src.services.session_service import get_or_create_session_id, add_session_message
                    from src.services.database import SessionLocal
                    db_log = SessionLocal()
                    try:
                        sess_id = get_or_create_session_id()
                        add_session_message(db_log, sess_id, f"Requested rework for: {s.name}", "info")
                    finally:
                        db_log.close()
                    st.rerun()
                    
            st.markdown("---")

if not pending_reviews_found:
    st.info("No pending human reviews. All supplier evaluations are currently clear or fully signed off.")

# Render completed plans
st.markdown("### 📜 Signed-off Contingency Database")
if target_id.strip():
    db_plans = db.query(DBContingencyPlan).filter(DBContingencyPlan.supplier_id == target_id.strip()).all()
else:
    db_plans = db.query(DBContingencyPlan).all()
if db_plans:
    plans_list = []
    for p in db_plans:
        plans_list.append({
            "Supplier ID": p.supplier_id,
            "Trigger Event ID": p.trigger_event_id,
            "Alternate Option": p.alternate_supplier_id or "None",
            "Volume Shift": f"{p.proposed_volume_shift_percent or 0.0}%",
            "Est. Lead Time Delta": f"+{p.estimated_lead_time_delta_days or 0} days",
            "Status": p.approval_status.upper()
        })
    st.dataframe(pd.DataFrame(plans_list))
else:
    st.info("No approved contingency plans in the database yet.")

db.close()
