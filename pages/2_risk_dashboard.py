import streamlit as st
import pandas as pd
import pydeck as pdk
from src.services.database import SessionLocal, DBSupplierRiskAssessment
from src.services.supplier_service import list_suppliers
from src.services.alert_service import list_active_risk_events
from src.graph.checkpoints import run_risk_monitor_workflow, get_workflow_state
from src.services.ui_helper import inject_premium_theme

st.set_page_config(page_title="Risk Dashboard - Supply Chain", page_icon="📈", layout="wide")
inject_premium_theme()

st.markdown('<h1 class="gradient-title">📈 Supply Chain Risk Dashboard</h1>', unsafe_allow_html=True)

db = SessionLocal()
suppliers = list_suppliers(db)
target_id = st.query_params.get("target_supplier_id", "")
if target_id.strip():
    suppliers = [s for s in suppliers if s.supplier_id.strip().lower() == target_id.strip().lower()]
    st.info(f"🔒 Authenticated Session: Locked to Supplier ID **{target_id}**.")
active_events = list_active_risk_events(db)

# 1. High-Level Summary Metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        f"""
        <div class="risk-card">
            <h4>Total Suppliers</h4>
            <div class="metric-value">{len(suppliers)}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

critical_alerts = sum(1 for e in active_events if str(e.severity).lower() == "critical")
high_alerts = sum(1 for e in active_events if str(e.severity).lower() == "high")

with col2:
    st.markdown(
        f"""
        <div class="risk-card alert-pulse">
            <h4>Critical Threats</h4>
            <div class="metric-value" style="color: #ff7b72;">{critical_alerts}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        f"""
        <div class="risk-card">
            <h4>High Alerts</h4>
            <div class="metric-value" style="color: #f77825;">{high_alerts}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# Retrieve assessments count
db_assessments = db.query(DBSupplierRiskAssessment).all()
if db_assessments:
    avg_risk = sum(a.overall_risk_score for a in db_assessments) / len(db_assessments)
elif active_events:
    # Compute average threat severity from active risk events when no suppliers are uploaded yet
    severity_scores = {"critical": 90.0, "high": 75.0, "medium": 50.0, "low": 20.0}
    avg_risk = sum(severity_scores.get(str(e.severity).lower(), 50.0) for e in active_events) / len(active_events)
else:
    avg_risk = 0.0

with col4:
    st.markdown(
        f"""
        <div class="risk-card">
            <h4>Avg Risk Index</h4>
            <div class="metric-value" style="color: {'#ff7b72' if avg_risk >= 50 else '#238636'}">{avg_risk:.1f}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("---")

# 2. Supplier Details & Execution trigger
if not suppliers:
    st.info("No suppliers found. Please upload suppliers on the Supplier Upload page.")
else:
    # Build Map Data
    map_data = []
    for s in suppliers:
        if s.latitude and s.longitude:
            # Check if there is an assessment
            assessment = next((a for a in db_assessments if a.supplier_id == s.supplier_id), None)
            score = assessment.overall_risk_score if assessment else 0.0
            risk_lvl = assessment.risk_level if assessment else "Clear"
            
            # Map colors based on risk
            color = [35, 134, 54]  # Green
            if risk_lvl == "critical":
                color = [218, 54, 51]  # Red
            elif risk_lvl == "high":
                color = [247, 120, 37]  # Orange
            elif risk_lvl == "medium":
                color = [210, 153, 34]  # Yellow
                
            map_data.append({
                "name": s.name,
                "latitude": s.latitude,
                "longitude": s.longitude,
                "risk_score": score,
                "risk_level": risk_lvl,
                "color": color,
                "port": s.primary_port or "N/A"
            })
            
    # PyDeck Map
    if map_data:
        st.markdown("### 🗺️ Geolocation Threat Map")
        df_map = pd.DataFrame(map_data)
        
        layer = pdk.Layer(
            "ScatterplotLayer",
            df_map,
            get_position="[longitude, latitude]",
            get_color="color",
            get_radius=150000,  # 150km radius
            pickable=True,
        )
        
        view_state = pdk.ViewState(
            latitude=df_map["latitude"].mean(),
            longitude=df_map["longitude"].mean(),
            zoom=2,
            pitch=0
        )
        
        r = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip={"text": "{name}\nPort: {port}\nRisk Level: {risk_level}\nScore: {risk_score}"}
        )
        st.pydeck_chart(r)
        
    st.markdown("---")
    
    col_sel, col_details = st.columns([1, 2])
    
    with col_sel:
        st.markdown("### 🔍 Select Supplier")
        selected_sup_name = st.selectbox("Supplier", options=[s.name for s in suppliers])
        selected_sup = next(s for s in suppliers if s.name == selected_sup_name)
        
        st.markdown(
            f"""
            **Supplier Details:**
            - ID: `{selected_sup.supplier_id}`
            - Country: `{selected_sup.country}`
            - Shipment Lead-Time: `{selected_sup.lead_time_days or 'N/A'} days`
            - Dependency Percent: `{selected_sup.dependency_percent or 'N/A'}%`
            """
        )
        
        # Trigger assessment button
        if st.button("🔄 Trigger Risk Monitoring Workflow"):
            with st.spinner("Executing State Workflow..."):
                thread_id = f"thread_{selected_sup.supplier_id}"
                raw_dict = {
                    "supplier_id": selected_sup.supplier_id,
                    "name": selected_sup.name,
                    "country": selected_sup.country,
                    "city_or_region": selected_sup.city_or_region,
                    "primary_port": selected_sup.primary_port,
                    "latitude": selected_sup.latitude,
                    "longitude": selected_sup.longitude,
                    "dependency_percent": selected_sup.dependency_percent,
                    "lead_time_days": selected_sup.lead_time_days,
                    "product_categories": selected_sup.product_categories,
                    "approved_alternate_supplier_ids": selected_sup.approved_alternate_supplier_ids
                }
                
                from src.services.session_service import get_or_create_session_id, add_session_message
                sess_id = get_or_create_session_id()
                add_session_message(db, sess_id, f"Started risk analysis workflow for: {selected_sup.name}", "info")
                
                # Execute graph workflow
                result = run_risk_monitor_workflow(raw_dict, thread_id)
                
                # Try to extract score
                score_str = ""
                if result and "risk_assessment" in result:
                    assessment_obj = result["risk_assessment"]
                    if hasattr(assessment_obj, "overall_risk_score"):
                        score_str = f" (Score: {assessment_obj.overall_risk_score})"
                        
                add_session_message(db, sess_id, f"Completed risk analysis for {selected_sup.name}{score_str}", "success")
                st.success("Workflow executed!")
                st.rerun()
                
    with col_details:
        st.markdown("### 📊 Active Assessment Status")
        
        # Fetch current db assessment
        assessment = next((a for a in db_assessments if a.supplier_id == selected_sup.supplier_id), None)
        
        # Check thread state
        thread_id = f"thread_{selected_sup.supplier_id}"
        state_values = get_workflow_state(thread_id)
        
        if state_values:
            review_status = state_values.get("review_status", "pending")
            
            if review_status == "pending" and state_values.get("risk_assessment") and state_values["risk_assessment"].human_review_required:
                st.warning(
                    f"🛑 **Human Approval Interrupt Gate Triggered!**\n"
                    f"A critical/high threat has been detected (Risk Score: {state_values['risk_assessment'].overall_risk_score}). "
                    f"Mitigation plan requires verification.\n"
                    f"Please navigate to page **🤝 4_contingency_plans** to approve or reject."
                )
                
            # Render assessment summary
            assessment_obj = state_values.get("risk_assessment") or assessment
            if assessment_obj:
                st.markdown(
                    f"""
                    <div class="risk-card">
                        <h4>Overall Risk Score: <span class="badge-{getattr(assessment_obj, 'risk_level', 'medium')}">{getattr(assessment_obj, 'overall_risk_score', 'N/A')}</span></h4>
                        <p><strong>Operational Impact:</strong> {getattr(assessment_obj, 'operational_impact', 'Pending evaluation.')}</p>
                        <p><strong>Confidence:</strong> {int(getattr(assessment_obj, 'confidence', 0.8) * 100)}%</p>
                        <p><strong>Review Status:</strong> {review_status.upper()}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.info("Risk evaluation in progress or pending workflow run.")
            
            # Show events contributing
            events = state_values.get("all_events", [])
            if events:
                st.markdown("**Contributing Risk Signals:**")
                for e in events:
                    st.markdown(f"- **{e.title}** ({e.severity.upper()}): {e.evidence_text} (*Source: {e.source_name}*)")
        else:
            if assessment:
                st.markdown(
                    f"""
                    <div class="risk-card">
                        <h4>Overall Risk Score: <span class="badge-{assessment.risk_level}">{assessment.overall_risk_score}</span></h4>
                        <p><strong>Operational Impact:</strong> {assessment.operational_impact}</p>
                        <p><strong>Confidence:</strong> {int(assessment.confidence * 100)}%</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.info("No active risk assessments completed for this supplier. Click the trigger button to evaluate.")
                
db.close()
