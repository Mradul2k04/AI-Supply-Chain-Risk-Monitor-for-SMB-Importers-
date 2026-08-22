import streamlit as st
import pandas as pd
from datetime import datetime
from src.services.database import SessionLocal
from src.services.alert_service import list_active_risk_events, save_risk_event
from guardrails.validators import validate_source_url
from src.schemas.risk_event import RiskEvent
from src.services.ui_helper import inject_premium_theme

st.set_page_config(page_title="Risk Events - Monitor", page_icon="🔔", layout="wide")
inject_premium_theme()

st.markdown('<h1 class="gradient-title">🔔 Risk Events & Evidence</h1>', unsafe_allow_html=True)
st.markdown("Review active geopolitical, weather, earthquake, and financial warning feeds. All signals are validated against security allowlists.")

db = SessionLocal()
events = list_active_risk_events(db)

# Form to trigger synthetic alert injection
st.markdown("### ➕ Inject Custom Risk Event (Testing)")
with st.form("custom_event_form"):
    title = st.text_input("Event Title", value="Port congestion strikes at Keelung hub")
    risk_type = st.selectbox("Risk Type", ["geopolitical", "weather", "earthquake", "port_disruption", "financial", "logistics"])
    severity = st.selectbox("Severity", ["low", "medium", "high", "critical"])
    region = st.text_input("Region Affected", value="Taiwan")
    source_name = st.text_input("Source Name", value="Global Logistics Desk")
    source_url = st.text_input("Source URL", value="https://reuters.com/news/taiwan-ports")
    evidence_text = st.text_area("Evidence Text", value="Dock workers union has staged a partial strike, disrupting container terminal exits.")
    confidence = st.slider("Confidence", 0.0, 1.0, 0.9)
    
    submitted = st.form_submit_button("Ingest Custom Risk Event")
    if submitted:
        import uuid
        new_event = RiskEvent(
            event_id=f"evt_custom_{uuid.uuid4().hex[:8]}",
            risk_type=risk_type,
            title=title,
            severity=severity,
            event_date=datetime.utcnow(),
            region=region,
            source_url=source_url,
            source_name=source_name,
            evidence_text=evidence_text,
            confidence=confidence
        )
        try:
            save_risk_event(db, new_event)
            st.success(f"Successfully ingested risk event: {new_event.title}")
            st.rerun()
        except Exception as e:
            st.error(f"Error ingesting event: {e}")

st.markdown("---")
st.markdown("### 📋 Active Risk Alerts")

if not events:
    st.info("No risk alerts active in the system. Use the form above to inject a custom alert for testing.")
else:
    for e in events:
        # Validate URL allowlist
        category = e.risk_type
        # Mapping for schema matching allowlist categories
        if category in ["port_disruption", "logistics"]:
            category = "geopolitical"
        elif category == "earthquake":
            category = "earthquake"
        is_allowed = validate_source_url(e.source_url, category)
        
        allowlist_badge = '<span style="color: #238636; font-weight: bold;">[Verified Source]</span>' if is_allowed else '<span style="color: #da3633; font-weight: bold;">[Block / Unverified Source]</span>'
        
        st.markdown(
            f"""
            <div class="risk-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="margin: 0;">{e.title}</h3>
                    <span class="badge-{e.severity}">{e.severity.upper()}</span>
                </div>
                <p style="margin-top: 10px; margin-bottom: 5px;"><strong>Classification:</strong> {e.risk_type.capitalize()} | <strong>Region:</strong> {e.region}</p>
                <p style="margin-bottom: 10px;"><strong>Evidence Snippet:</strong> <em>"{e.evidence_text}"</em></p>
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem; color: #8b949e;">
                    <div>
                        Source: <a href="{e.source_url}" target="_blank" style="color: #58a6ff;">{e.source_name}</a> {allowlist_badge}
                    </div>
                    <div>
                        Reported: {e.event_date.strftime('%Y-%m-%d %H:%M')} | Confidence: {int(e.confidence*100)}%
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

db.close()
