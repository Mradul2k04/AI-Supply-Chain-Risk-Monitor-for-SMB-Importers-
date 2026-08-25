# Initialize logger setup first
from src.config.logger import setup_logging
import logging
import streamlit as st
import pandas as pd
import pydeck as pdk
from src.graph.workflow import initialize_system
from src.rag.ingestion import ingest_default_knowledge_base
from src.services.ui_helper import inject_premium_theme
from src.services.database import SessionLocal, DBSupplier, DBRiskEvent, DBContingencyPlan, DBSupplierRiskAssessment

st.set_page_config(
    page_title="AI Supply Chain Risk Monitor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize application components
@st.cache_resource
def setup_application():
    initialize_system()
    try:
        ingest_default_knowledge_base()
    except Exception as e:
        logging.warning(f"Could not seed default vector store: {e}")

setup_application()
inject_premium_theme()

# Header & Live System Status Badge
st.markdown(
    """
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
        <div>
            <div class="status-pill">
                <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background-color: #3fb950; margin-right: 8px;"></span>
                SYSTEM ONLINE &bull; 5 AGENT NODES ACTIVE &bull; CHROMADB GROUNDED
            </div>
            <h1 class="gradient-title" style="margin-top: 0; margin-bottom: 5px;">🛡️ AI Supply Chain Risk Monitor</h1>
            <p style="color: #8b949e; font-size: 1.15rem; margin-top: 0; margin-bottom: 25px;">
                Stateful Multi-Agent Disruption Scoring, Vector Intelligence (RAG), and Human-in-the-Loop Resiliency Planning
            </p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Fetch database metrics for live KPI cards
db = SessionLocal()
try:
    total_suppliers = db.query(DBSupplier).count()
    all_events = db.query(DBRiskEvent).all()
    active_events = len(all_events)
    pending_contingencies = db.query(DBContingencyPlan).filter(DBContingencyPlan.approval_status == "draft").count()
    risk_assessments = db.query(DBSupplierRiskAssessment).all()
    
    critical_high_count = sum(1 for ra in risk_assessments if ra.risk_level in ["critical", "high"])
    
    # Calculate weighted resiliency index score dynamically from database metrics
    if risk_assessments:
        avg_score = sum(ra.overall_risk_score for ra in risk_assessments) / len(risk_assessments)
        # Normalize to percentage scale
        risk_pct = avg_score * 100.0 if avg_score <= 1.0 else avg_score
        resiliency_index = max(0.0, min(100.0, round(100.0 - risk_pct, 1)))
    elif all_events:
        # Dynamically compute index from average threat severity when supplier assessments do not exist yet
        severity_impact = {"critical": 75.0, "high": 50.0, "medium": 30.0, "low": 10.0}
        avg_risk_impact = sum(severity_impact.get(str(e.severity).lower(), 35.0) for e in all_events) / len(all_events)
        resiliency_index = max(0.0, min(100.0, round(100.0 - avg_risk_impact, 1)))
    else:
        resiliency_index = 100.0
finally:
    db.close()

# Live Executive KPI Metrics Grid
k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">Monitored Vendors</div>
            <div class="kpi-value">{total_suppliers}</div>
            <div class="kpi-sub">🌐 100% Geocoded & Tracked</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with k2:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">Active Disruption Signals</div>
            <div class="kpi-value" style="color: {'#ff7b72' if critical_high_count > 0 else '#58a6ff'};">{active_events}</div>
            <div class="kpi-sub">⚡ GDELT, NOAA, SEC EDGAR</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with k3:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">Pending Human Reviews</div>
            <div class="kpi-value" style="color: {'#d29922' if pending_contingencies > 0 else '#3fb950'};">{pending_contingencies}</div>
            <div class="kpi-sub">🛑 Halted LangGraph Gate</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with k4:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">Resiliency Index</div>
            <div class="kpi-value" style="color: #3fb950;">{resiliency_index}%</div>
            <div class="kpi-sub">🛡️ Automated Contingency Ready</div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)

# Interactive Global Risk Overview Map
st.markdown("### 🌐 Live Global Supply Chain Risk Map")

db = SessionLocal()
try:
    suppliers_data = db.query(DBSupplier).all()
    map_rows = []
    
    for s in suppliers_data:
        if s.latitude and s.longitude:
            ra = db.query(DBSupplierRiskAssessment).filter(DBSupplierRiskAssessment.supplier_id == s.supplier_id).first()
            risk_lvl = ra.risk_level.lower() if ra else "low"
            risk_score = ra.overall_risk_score if ra else 0.15
            
            # Color coding RGB
            if risk_lvl == "critical":
                color = [218, 54, 51, 220]  # Red
            elif risk_lvl == "high":
                color = [247, 120, 37, 220]  # Orange
            elif risk_lvl == "medium":
                color = [210, 153, 34, 220]  # Yellow
            else:
                color = [35, 134, 54, 220]   # Green

            map_rows.append({
                "supplier_id": s.supplier_id,
                "name": s.name,
                "country": s.country,
                "city": s.city_or_region or "",
                "lat": s.latitude,
                "lon": s.longitude,
                "risk_level": risk_lvl.upper(),
                "risk_score": round(risk_score, 2),
                "color": color,
                "radius": 120000 if risk_lvl in ["critical", "high"] else 80000
            })
finally:
    db.close()

if map_rows:
    df_map = pd.DataFrame(map_rows)
    
    view_state = pdk.ViewState(
        latitude=df_map["lat"].mean() if not df_map.empty else 20.0,
        longitude=df_map["lon"].mean() if not df_map.empty else 0.0,
        zoom=1.5,
        pitch=30,
    )
    
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df_map,
        get_position=["lon", "lat"],
        get_color="color",
        get_radius="radius",
        pickable=True,
        opacity=0.8,
        stroked=True,
        filled=True,
        radius_scale=1,
        radius_min_pixels=8,
        radius_max_pixels=30,
        line_width_min_pixels=2,
        get_line_color=[255, 255, 255, 180]
    )
    
    tooltip = {
        "html": "<b>{name}</b> ({supplier_id})<br/>"
                "Location: {city}, {country}<br/>"
                "Risk Level: <b>{risk_level}</b> (Score: {risk_score})",
        "style": {"backgroundColor": "#161b22", "color": "#f0f6fc", "border": "1px solid #30363d", "borderRadius": "8px", "padding": "10px"}
    }
    
    r = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style="mapbox://styles/mapbox/dark-v10"
    )
    st.pydeck_chart(r, use_container_width=True)

st.markdown("---")

# Interactive Application Navigation Portal
st.markdown("### 🚀 Application Control Center")
st.markdown("Launch workspace modules to configure suppliers, trigger agent evaluations, and sign off on contingency plans:")

p1, p2, p3 = st.columns(3)

with p1:
    st.markdown(
        """
        <div class="portal-card">
            <div class="portal-icon">📤</div>
            <div class="portal-title">Supplier Onboarding</div>
            <div class="portal-desc">Import supplier catalogs, geocode factory locations, and define component dependencies.</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.page_link("pages/1_supplier_upload.py", label="Open Supplier Onboarding", icon="📤", use_container_width=True)

with p2:
    st.markdown(
        """
        <div class="portal-card">
            <div class="portal-icon">📈</div>
            <div class="portal-title">Risk Dashboard</div>
            <div class="portal-desc">Trigger multi-agent workflows, compute composite risk scores, and view threat breakdowns.</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.page_link("pages/2_risk_dashboard.py", label="Open Executive Dashboard", icon="📈", use_container_width=True)

with p3:
    st.markdown(
        """
        <div class="portal-card">
            <div class="portal-icon">🔔</div>
            <div class="portal-title">Disruption Feed</div>
            <div class="portal-desc">Monitor live GDELT geopolitical news, NOAA climate alerts, USGS earthquakes, and SEC filings.</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.page_link("pages/3_risk_events.py", label="Inspect Disruption Feed", icon="🔔", use_container_width=True)

p4, p5 = st.columns(2)

with p4:
    st.markdown(
        """
        <div class="portal-card">
            <div class="portal-icon">🤝</div>
            <div class="portal-title">Human Approval Gate</div>
            <div class="portal-desc">Review LangGraph-halted state checkpoints and sign off on volume shifts or backup suppliers.</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.page_link("pages/4_contingency_plans.py", label="Review Contingency Plans", icon="🤝", use_container_width=True)

with p5:
    st.markdown(
        """
        <div class="portal-card">
            <div class="portal-icon">💾</div>
            <div class="portal-title">Reports & Export</div>
            <div class="portal-desc">Download consolidated risk matrices and approved mitigation plans in structured CSV and JSON.</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.page_link("pages/5_reports.py", label="Generate Operations Reports", icon="💾", use_container_width=True)

st.markdown("---")

# Interactive Multi-Agent Architecture Explorer
st.markdown("### 🤖 Interactive Multi-Agent System Architecture")
st.markdown("Select a module below to inspect how the autonomous agent nodes gather signals, ground insights, and manage human review gates:")

t_geo, t_wx, t_fin, t_rag, t_gate = st.tabs([
    "🌍 Geopolitical Agent", 
    "⛈️ Weather & Seismic Agent", 
    "🏦 SEC Financial Agent", 
    "🧠 ChromaDB RAG Engine", 
    "🛑 LangGraph Human Gate"
])

with t_geo:
    st.markdown(
        """
        #### 🌍 Geopolitical Risk Collector
        - **Source Integration**: Ingests real-time events via **GDELT** and **ReliefWeb** APIs within supplier territories.
        - **Evaluation**: Identifies strikes, port blockades, export restrictions, and regional conflicts.
        - **Allowlist Enforcement**: Checks domain credentials against strict domain allowlists in `guardrails/source_allowlist.yaml`.
        """
    )

with t_wx:
    st.markdown(
        """
        #### ⛈️ Weather & USGS Seismic Monitor
        - **Climate Hazards**: Connects to **NOAA Climate API** for seasonal severe weather warnings.
        - **Earthquake Alerts**: Queries **USGS API** for seismic events occurring within **300km** of vendor coordinates.
        - **Scoring Logic**: Converts magnitude and proximity into transparent severity scores using rules in `risk_scoring_rules.yaml`.
        """
    )

with t_fin:
    st.markdown(
        """
        #### 🏦 SEC Financial & Credit Health Monitor
        - **Liquidity Checkers**: Scrapes SEC EDGAR 10-Q / 10-K filings and credit rating alerts for supplier corporate entities.
        - **Bankruptcy Warnings**: Flags restructuring risks that could jeopardize lead times or cause unexpected factory shutdowns.
        """
    )

with t_rag:
    st.markdown(
        """
        #### 🧠 Vector Intelligence (ChromaDB RAG)
        - **Playbook Grounding**: Queries ChromaDB vector store seeded with historical supply chain mitigation playbooks.
        - **Embedding Precision**: Uses HuggingFace sentence transformer models to match active disruption signals with contextual remediation strategies.
        """
    )

with t_gate:
    st.markdown(
        """
        #### 🛑 LangGraph Stateful Checkpointer & Human Gate
        - **Interrupt Protocol**: Automatically pauses execution when overall risk scores cross the **High/Critical threshold (>= 0.65)**.
        - **Human Oversight**: Holds the graph state in SQLite checkpointers until an operations manager approves, rejects, or requests rework.
        """
    )
