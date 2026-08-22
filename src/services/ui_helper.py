import streamlit as st

def inject_premium_theme():
    """
    Injects custom CSS to style the Streamlit interface with a premium dark-glassmorphism theme.
    """
    st.markdown(
        """
        <style>
        /* Import Google Font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            background-color: #0d1117;
            color: #c9d1d9;
        }

        /* Sidebar styling */
        section[data-testid="stSidebar"] {
            background-color: #161b22 !important;
            border-right: 1px solid #21262d;
        }
        
        /* Card Container (Glassmorphic) */
        .risk-card {
            background: rgba(22, 27, 34, 0.7);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
            border: 1px solid #30363d;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        .risk-card:hover {
            transform: translateY(-2px);
            border-color: #58a6ff;
        }

        /* Vibrant Risk Badges */
        .badge-critical {
            background-color: #da3633;
            color: white;
            padding: 4px 10px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 0.85rem;
        }
        .badge-high {
            background-color: #f77825;
            color: white;
            padding: 4px 10px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 0.85rem;
        }
        .badge-medium {
            background-color: #d29922;
            color: white;
            padding: 4px 10px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 0.85rem;
        }
        .badge-low {
            background-color: #238636;
            color: white;
            padding: 4px 10px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 0.85rem;
        }

        /* Headers with Gradient */
        .gradient-title {
            background: linear-gradient(135deg, #58a6ff 0%, #1f6feb 50%, #a371f7 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        
        .gradient-subtitle {
            background: linear-gradient(135deg, #ff7b72 0%, #da3633 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700;
            font-size: 1.6rem;
            margin-bottom: 10px;
        }

        /* Status Pill Badge */
        .status-pill {
            display: inline-flex;
            align-items: center;
            background: rgba(35, 134, 54, 0.15);
            border: 1px solid #238636;
            color: #3fb950;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            letter-spacing: 0.5px;
            margin-bottom: 15px;
        }

        /* Metric Box Glassmorphism */
        .kpi-card {
            background: linear-gradient(145deg, rgba(22, 27, 34, 0.9), rgba(13, 17, 23, 0.8));
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 16px 20px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.3);
            text-align: center;
            transition: all 0.3s ease;
        }
        .kpi-card:hover {
            border-color: #58a6ff;
            box-shadow: 0 8px 30px rgba(88, 166, 255, 0.2);
            transform: translateY(-2px);
        }
        .kpi-title {
            color: #8b949e;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-bottom: 6px;
        }
        .kpi-value {
            font-size: 2.2rem;
            font-weight: 800;
            color: #f0f6fc;
        }
        .kpi-sub {
            font-size: 0.78rem;
            color: #3fb950;
            margin-top: 4px;
            font-weight: 500;
        }
        
        /* Action Hub Cards */
        .portal-card {
            background: linear-gradient(135deg, rgba(22, 27, 34, 0.85) 0%, rgba(33, 38, 45, 0.6) 100%);
            border: 1px solid #30363d;
            border-radius: 14px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            height: 100%;
        }
        .portal-card:hover {
            border-color: #58a6ff;
            box-shadow: 0 10px 30px rgba(88, 166, 255, 0.15);
            transform: translateY(-3px);
        }
        .portal-icon {
            font-size: 2rem;
            margin-bottom: 10px;
        }
        .portal-title {
            font-size: 1.15rem;
            font-weight: 700;
            color: #f0f6fc;
            margin-bottom: 8px;
        }
        .portal-desc {
            font-size: 0.88rem;
            color: #8b949e;
            line-height: 1.45;
        }

        /* Pulse micro-animation for alerts */
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(218, 54, 51, 0.4); }
            70% { box-shadow: 0 0 0 10px rgba(218, 54, 51, 0); }
            100% { box-shadow: 0 0 0 0 rgba(218, 54, 51, 0); }
        }
        .alert-pulse {
            border: 1px solid #da3633;
            animation: pulse 2s infinite;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    render_session_sidebar()

def render_session_sidebar():
    """Renders the persistent session activity log in the Streamlit sidebar."""
    from src.services.session_service import get_or_create_session_id, get_session_messages, clear_session_messages
    from src.services.database import SessionLocal
    
    session_id = get_or_create_session_id()
    
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"### 💬 Session Activity Log (`{session_id[-6:]}`)")
        
        db = SessionLocal()
        try:
            messages = get_session_messages(db, session_id)
            if messages:
                for msg in messages:
                    t_str = msg["timestamp"].strftime("%H:%M:%S")
                    level = msg["level"].lower()
                    
                    if level == "error":
                        st.error(f"[{t_str}] {msg['message']}")
                    elif level == "warning":
                        st.warning(f"[{t_str}] {msg['message']}")
                    elif level == "success":
                        st.success(f"[{t_str}] {msg['message']}")
                    else:
                        st.info(f"[{t_str}] {msg['message']}")
                        
                if st.button("🗑️ Clear Log History"):
                    clear_session_messages(db, session_id)
                    st.rerun()
            else:
                st.caption("No activities recorded yet in this session.")
        finally:
            db.close()
