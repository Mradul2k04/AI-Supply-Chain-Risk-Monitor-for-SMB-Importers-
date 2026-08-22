import streamlit as st
import pandas as pd
import logging
from src.services.database import SessionLocal
from src.services.supplier_service import upsert_supplier, list_suppliers, clear_all_suppliers
from src.agents.supplier_profile_agent import run_supplier_profile_agent
from src.services.ui_helper import inject_premium_theme

st.set_page_config(page_title="Upload Suppliers - Risk Monitor", page_icon="📤", layout="wide")
inject_premium_theme()

st.markdown('<h1 class="gradient-title">📤 Supplier Upload Interface</h1>', unsafe_allow_html=True)
st.markdown("Upload your supplier master CSV list or register a new vendor manually.")

db = SessionLocal()

# 1. Template Download Section
st.markdown("### 📥 Get Template")

DEFAULT_TEMPLATE_CSV = """supplier_id,name,country,city_or_region,primary_port,latitude,longitude,dependency_percent,lead_time_days,product_categories,approved_alternate_supplier_ids
SUP001,Aria Packaging Ltd,China,Shenzhen,Port of Shenzhen,22.5431,114.0579,35.0,14,"Electronics, Packaging",SUP002
SUP002,Oman Oils & Extracts,Oman,Muscat,Port Sultan Qaboos,23.5880,58.3829,25.0,21,"Essential Oils",SUP003
SUP003,Vietnam Ceramics Co,Vietnam,Da Nang,Da Nang Port,16.0544,108.2022,40.0,18,"Ceramics, Tableware",SUP001
"""

try:
    with open("data/sample_suppliers/supplier_template.csv", "r", encoding="utf-8") as f:
        csv_data = f.read()
except Exception:
    csv_data = DEFAULT_TEMPLATE_CSV

st.download_button(
    label="Download Supplier CSV Template",
    data=csv_data,
    file_name="supplier_template.csv",
    mime="text/csv"
)

st.markdown("---")

# 2. Database Management & Session Filter
col_a, col_b = st.columns([3, 2])

with col_a:
    st.markdown("### 🔑 Supplier Session Filter")
    query_target_id = st.query_params.get("target_supplier_id", "")
    target_id = st.text_input(
        "Filter by Supplier ID",
        value=query_target_id,
        help="Enter a specific Supplier ID to filter active database records."
    )
    if target_id != query_target_id:
        st.query_params["target_supplier_id"] = target_id
        st.rerun()

with col_b:
    st.markdown("### 🗑️ Reset Database")
    st.caption("Remove previous records before ingesting your CSV file.")
    if st.button("Clear All Suppliers from DB", type="secondary"):
        count = clear_all_suppliers(db)
        st.success(f"Cleared {count} supplier records. Ready for your new CSV upload!")
        st.rerun()



st.markdown("---")

st.markdown("### 📤 Upload CSV/XLSX List")
uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        st.write("Preview of Uploaded Data:")
        st.dataframe(df)
        
        if st.button("Process and Ingest Suppliers"):
            ingested = 0
            for idx, row in df.iterrows():
                # Flexible helper to retrieve key from row dynamically
                def get_val(keys):
                    for k in keys:
                        if k in row and pd.notna(row[k]):
                            return row[k]
                    return None

                # Extract values dynamically
                supplier_id = str(get_val(["supplier_id", "Supplier_ID"]) or target_id.strip() or f"SUP_{idx}")
                name = str(get_val(["name", "Name"]) or f"Supplier {supplier_id}")
                country = str(get_val(["country", "Country"]) or "Unknown")
                city_or_region = str(get_val(["city_or_region", "City/Region", "City", "Region"]) or "")
                if city_or_region == "None" or city_or_region == "nan": city_or_region = ""
                primary_port = str(get_val(["primary_port", "Primary Port", "Port"]) or "")
                if primary_port == "None" or primary_port == "nan": primary_port = ""
                
                latitude = get_val(["latitude", "Latitude", "Lat"])
                if latitude is not None: latitude = float(latitude)
                longitude = get_val(["longitude", "Longitude", "Lon", "Lng"])
                if longitude is not None: longitude = float(longitude)
                
                # Dependency Calculation
                dependency_percent = get_val(["dependency_percent", "Dependency %", "Dependency"])
                if dependency_percent is not None:
                    dependency_percent = float(dependency_percent)
                else:
                    # Fallback calculation if shipment demand/volume are present
                    volume = get_val(["Shipment_Volume_Tons"])
                    demand = get_val(["Monthly_Demand_Tons"])
                    if volume is not None and demand is not None and float(demand) > 0:
                        dependency_percent = round((float(volume) / float(demand)) * 100.0, 1)
                        
                # Lead Time days mapping
                lead_time_days = get_val(["lead_time_days", "Lead Time", "Transit_Time_Days"])
                if lead_time_days is not None:
                    lead_time_days = int(float(lead_time_days))
                    
                # Product Categories list extraction
                cats_raw = get_val(["product_categories", "Product Categories", "Product_Type", "Product Type"])
                cats = []
                if cats_raw:
                    cats = [c.strip() for c in str(cats_raw).split(",") if c.strip()]
                    
                # Alternate IDs list extraction
                alts_raw = get_val(["approved_alternate_supplier_ids", "approved_alternate_supplier_ids", "approved_alternate_suppliers"])
                alts = []
                if alts_raw:
                    alts = [a.strip() for a in str(alts_raw).split(",") if a.strip()]
                    
                raw_dict = {
                    "supplier_id": supplier_id,
                    "name": name,
                    "country": country,
                    "city_or_region": city_or_region if city_or_region else None,
                    "primary_port": primary_port if primary_port else None,
                    "latitude": latitude,
                    "longitude": longitude,
                    "dependency_percent": dependency_percent,
                    "lead_time_days": lead_time_days,
                    "product_categories": cats,
                    "approved_alternate_supplier_ids": alts
                }
                
                normalized_supplier = run_supplier_profile_agent(raw_dict)
                upsert_supplier(db, normalized_supplier)
                ingested += 1
                
            st.success(f"Successfully normalized and saved {ingested} supplier profiles!")
            from src.services.session_service import get_or_create_session_id, add_session_message
            sess_id = get_or_create_session_id()
            add_session_message(db, sess_id, f"Successfully ingested {ingested} supplier profiles", "success")
    except Exception as e:
        st.error(f"Failed to process CSV file: {e}")
        from src.services.session_service import get_or_create_session_id, add_session_message
        sess_id = get_or_create_session_id()
        add_session_message(db, sess_id, f"Failed to ingest CSV: {str(e)}", "error")

st.markdown("---")
st.markdown("### 📋 Active Suppliers Database")
suppliers = list_suppliers(db)
if target_id.strip():
    suppliers = [s for s in suppliers if s.supplier_id.strip().lower() == target_id.strip().lower()]
if suppliers:
    supp_list = []
    for s in suppliers:
        supp_list.append({
            "ID": s.supplier_id,
            "Name": s.name,
            "Country": s.country,
            "City/Region": s.city_or_region or "N/A",
            "Port": s.primary_port or "N/A",
            "Coordinates": f"{s.latitude:.2f}, {s.longitude:.2f}" if s.latitude else "N/A",
            "Categories": ", ".join(s.product_categories),
            "Dependency": f"{s.dependency_percent or 0}%",
            "Lead Time": f"{s.lead_time_days or 0} days",
            "Alternates": ", ".join(s.approved_alternate_supplier_ids)
        })
    st.dataframe(pd.DataFrame(supp_list))
else:
    st.info("No suppliers in the database yet. Please upload a CSV file above to ingest supplier profiles.")

db.close()
