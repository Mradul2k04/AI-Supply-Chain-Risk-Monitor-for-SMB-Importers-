import os
import streamlit as st
import pandas as pd
from src.services.database import SessionLocal, DBSupplierRiskAssessment, DBContingencyPlan
from src.services.supplier_service import list_suppliers
from src.services.reporting_service import export_risk_report
from src.services.ui_helper import inject_premium_theme

st.set_page_config(page_title="Risk Reports - Export", page_icon="💾", layout="wide")
inject_premium_theme()

st.markdown('<h1 class="gradient-title">💾 Reports & Exports</h1>', unsafe_allow_html=True)
st.markdown("Compile, review, and export active supply-chain risk assessments and mitigation playbooks.")

db = SessionLocal()
suppliers = list_suppliers(db)
assessments = db.query(DBSupplierRiskAssessment).all()
plans = db.query(DBContingencyPlan).all()

# Compile general reports list
report_rows = []
for s in suppliers:
    assess = next((a for a in assessments if a.supplier_id == s.supplier_id), None)
    supplier_plans = [p for p in plans if p.supplier_id == s.supplier_id]
    
    plan_actions = "; ".join([p.recommended_action for p in supplier_plans]) or "None"
    alts = ", ".join([p.alternate_supplier_id for p in supplier_plans if p.alternate_supplier_id]) or "None"
    
    report_rows.append({
        "supplier_id": s.supplier_id,
        "supplier_name": s.name,
        "country": s.country,
        "primary_port": s.primary_port or "N/A",
        "dependency_percent": s.dependency_percent or 0.0,
        "risk_score": assess.overall_risk_score if assess else 0.0,
        "risk_level": assess.risk_level if assess else "CLEAR",
        "operational_impact": assess.operational_impact if assess else "Clear operations.",
        "mitigation_actions": plan_actions,
        "alternate_options": alts
    })

if not report_rows:
    st.info("No supplier risk assessment reports available to export.")
else:
    st.markdown("### 📊 Consolidated Risk Summary Preview")
    df_report = pd.DataFrame(report_rows)
    st.dataframe(df_report)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📥 Export Formats")
        format_type = st.radio("Select Export File Format", ["json", "csv"])
        
        if st.button("Generate and Save Export File"):
            try:
                file_path = export_risk_report(report_rows, format_type)
                st.success(f"Report exported successfully! Saved to: `{file_path}`")
            except Exception as e:
                st.error(f"Failed to export report: {e}")
                
    with col2:
        st.markdown("### 💾 Available Exports Folder")
        # List files in exports directory
        export_dir = os.getenv("EXPORT_DIR", "data/exports")
        if os.path.exists(export_dir):
            files = [f for f in os.listdir(export_dir) if f.startswith("risk_report_")]
            if files:
                for file_name in files:
                    file_path = os.path.join(export_dir, file_name)
                    with open(file_path, "rb") as f:
                        btn = st.download_button(
                            label=f"📥 Download {file_name}",
                            data=f,
                            file_name=file_name,
                            mime="text/csv" if file_name.endswith(".csv") else "application/json"
                        )
            else:
                st.info("No export files generated in data/exports/ yet.")
        else:
            st.info("No exports folder exists. Click 'Generate and Save Export File' to create it.")

db.close()
