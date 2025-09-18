import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import numpy as np
from database import DatabaseManager
from ai_models import AIForecasting, SmartReordering, ExpiryPredictor
from drug_interactions import DrugInteractionChecker
from utils import format_currency, format_dual_currency, calculate_days_until_expiry, generate_alerts
from receipt_scanner import render_receipt_scanner_page
from ai_chatbot import render_ai_chatbot_page
import os

# Page configuration
st.set_page_config(
    page_title="PharmaGPT",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

# Apply Plotly theme (light only)
px.defaults.template = "plotly_white"
import plotly.io as pio
pio.templates["plotly_white"].layout.colorscale.sequential = ["#3b82f6", "#ec4899", "#10b981", "#f59e0b", "#8b5cf6", "#06b6d4"]

# One-time injection for external animation libraries (safe within Streamlit component sandbox)
components.html(
    """
    <link rel=\"preconnect\" href=\"https://unpkg.com\" />
    <script src="https://unpkg.com/@lottiefiles/lottie-player@latest/dist/lottie-player.js"></script>
    """,
    height=0,
)

st.markdown("""
<style>
/* Custom CSS for better UX (light theme only) */
    /* Dark mode welcome message */
    
    
    .main-header {
        background: #667eea;
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        animation: fadeIn 0.6s ease both;
    }
    .metric-card {
        position: relative;
        background: #667eea;
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        min-height: 120px;
        box-sizing: border-box;
        transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease;
        animation: fadeInUp 0.4s ease both;
    }
    .metric-card h3 { margin: 0.25rem 0 0.5rem 0; font-weight: 600; line-height: 1.2; white-space: nowrap; }
    .metric-card h2 { margin: 0; line-height: 1; }
    .metric-card:hover { transform: translateY(-3px) scale(1.01); box-shadow: 0 10px 16px rgba(0,0,0,0.15); filter: saturate(1.1); }
    .alert-card {
        background: #fee2e2;
        padding: 1rem;
        border-radius: 12px;
        border-left: 4px solid #dc2626;
        border: 2px solid #dc2626;
        margin: 0.5rem 0;
        animation: fadeInUp 0.4s ease both;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
        box-shadow: var(--shadow-sm);
        color: #991b1b;
    }
    .alert-card:hover { 
        transform: translateY(-2px); 
        box-shadow: var(--shadow-md);
        background: #fecaca;
        border-color: #b91c1c;
    }
    .success-card {
        background: var(--card);
        padding: 1rem;
        border-radius: 12px;
        border-left: 4px solid #28a745;
        margin: 0.5rem 0;
        animation: fadeInUp 0.4s ease both;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: var(--shadow-sm);
    }
    .success-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
    .warning-card {
        background: var(--card);
        padding: 1rem;
        border-radius: 12px;
        border-left: 4px solid #ffc107;
        margin: 0.5rem 0;
        animation: fadeInUp 0.4s ease both;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: var(--shadow-sm);
    }
    .warning-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
    .error-card {
        background: #fee2e2;
        padding: 1rem;
        border-radius: 12px;
        border-left: 4px solid #dc2626;
        border: 2px solid #dc2626;
        margin: 0.5rem 0;
        animation: fadeInUp 0.4s ease both;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
        box-shadow: var(--shadow-sm);
        color: #991b1b;
    }
    .error-card:hover { 
        transform: translateY(-2px); 
        box-shadow: var(--shadow-md);
        background: #fecaca;
        border-color: #b91c1c;
    }
    .sidebar .sidebar-content {
        background: #f8f9fa;
    }
    
    .sidebar .stMarkdown h3 {
        color: #212529 !important;
        font-weight: 600 !important;
        margin-top: 1.5rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Force sidebar markdown text visibility */
    .sidebar .stMarkdown {
        color: #212529 !important;
    }
    
    .sidebar .stMarkdown p {
        color: #212529 !important;
    }
    
    .sidebar .stMarkdown strong {
        color: #212529 !important;
    }
    
    .sidebar .stMarkdown em {
        color: #212529 !important;
    }
    
    /* Target all text elements in sidebar */
    .sidebar * {
        color: #212529 !important;
    }
    
    /* Override any inherited colors */
    .sidebar .stMarkdown h1,
    .sidebar .stMarkdown h2,
    .sidebar .stMarkdown h3,
    .sidebar .stMarkdown h4,
    .sidebar .stMarkdown h5,
    .sidebar .stMarkdown h6 {
        color: #000000 !important;
    }
    
    /* Force ALL sidebar text to be black */
    .sidebar * {
        color: #000000 !important;
    }
    
    .sidebar div[data-testid="stMarkdownContainer"] {
        color: #000000 !important;
    }
    
    .sidebar div[data-testid="stMarkdownContainer"] * {
        color: #000000 !important;
    }
    
    .sidebar .stSelectbox label,
    .sidebar .stSelectbox label p {
        color: #000000 !important;
    }
    
    /* Force AI Assistant page sidebar text to be black */
    .sidebar .stMarkdown h3 {
        color: #000000 !important;
    }
    
    .sidebar .stButton button {
        color: #000000 !important;
    }
    
    .sidebar .stButton button span {
        color: #000000 !important;
    }
    
    /* Sidebar/navigation animations */
    [data-testid="stSidebar"] { animation: fadeIn 0.5s ease both; }
    /* Animate the Navigation Menu selectbox */
    [data-testid="stSidebar"] [data-testid="stSelectbox"] label p {
        display: inline-flex; align-items: center; gap: 6px;
        animation: fadeInUp 0.35s ease both;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] {
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
        border-radius: 10px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        animation: fadeInUp 0.35s ease both;
    }
    [data-testid="stSidebar"] [data-baseweb="select"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 14px rgba(0,0,0,0.12);
    }
    [data-testid="stSidebar"] [data-baseweb="select"]:focus-within {
        box-shadow: none !important; /* remove focus outline */
        animation: none !important;
    }
    /* Also ensure internal control shows no white outline/border */
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        box-shadow: none !important;
        border-color: transparent !important;
    }
    /* Hide blinking caret in the sidebar Navigation select input without affecting text */
    [data-testid="stSidebar"] [data-baseweb="select"] input { caret-color: transparent !important; }
    [data-testid="stSidebar"] [data-baseweb="select"] input::selection { background: transparent; }
    /* Dropdown menu (portal) - scoped to sidebar Navigation select */
    [data-testid="stSidebar"] [data-baseweb="menu"] { animation: fadeIn 0.25s ease both; }
    [data-testid="stSidebar"] [data-baseweb="menu"] [role="option"] {
        transition: background-color 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
        border-radius: 10px;
        transform-origin: left center;
    }
    [data-testid="stSidebar"] [data-baseweb="menu"] [role="option"]:hover {
        transform: translateX(8px) scale(1.06);
        background-color: rgba(102,126,234,0.16);
        box-shadow: 0 10px 20px rgba(0,0,0,0.12), inset 0 0 0 2px rgba(118,75,162,0.35);
        filter: saturate(1.08);
    }
    [data-testid="stSidebar"] [data-baseweb="menu"] [role="option"][aria-selected="true"] {
        transform: translateX(6px) scale(1.04);
        background-color: rgba(118,75,162,0.18);
        box-shadow: 0 6px 14px rgba(0,0,0,0.1), inset 0 0 0 2px rgba(102,126,234,0.32);
    }
    /* Pop effect on the closed select when hovering */
    [data-testid="stSidebar"] [data-baseweb="select"]:hover {
        transform: translateY(-3px) scale(1.02);
    }

    @keyframes pulseGlow {
        0% { box-shadow: 0 0 0 3px rgba(102,126,234,0.20), 0 6px 10px rgba(0,0,0,0.06); }
        50% { box-shadow: 0 0 0 4px rgba(118,75,162,0.30), 0 12px 18px rgba(0,0,0,0.12); }
        100% { box-shadow: 0 0 0 3px rgba(102,126,234,0.20), 0 6px 10px rgba(0,0,0,0.06); }
    }
    /* Glassmorphism accents */
    .glass { 
        backdrop-filter: blur(8px); 
        -webkit-backdrop-filter: blur(8px); 
        background: var(--glass-bg); 
        border: 1px solid var(--glass-brd); 
    }
    .glass-border { 
        position: relative; 
    }
    .glass-border::before {
        content: ""; 
        position: absolute; 
        inset: 0; 
        border-radius: 12px;
        padding: 1px; 
        background: rgba(102,126,234,0.35);
        -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        -webkit-mask-composite: xor; 
        mask-composite: exclude;
        pointer-events: none;
    }

    /* Primary/secondary button upgrades */
    .stButton > button {
        font-weight: 600;
        background: var(--primary-start);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
        box-shadow: var(--shadow-md);
        position: relative;
        overflow: hidden;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
        filter: brightness(1.05);
    }
    .stButton > button:active { 
        animation: btnRipple 0.5s ease; 
        transform: translateY(0);
    }
    
    /* Button variants */
    .stButton.primary > button { 
        background: linear-gradient(90deg, var(--primary-start), var(--primary-end)) !important; 
    }
    .stButton.secondary > button { 
        background: var(--text) !important; 
        color: var(--card) !important;
    }
    

    .chart-container {
        background: var(--card);
        padding: 1rem;
        border-radius: 12px;
        box-shadow: var(--shadow-md), inset 0 0 0 1px rgba(255,255,255,0.08);
        margin: 1rem 0;
        animation: fadeIn 0.4s ease both;
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
        border: 1px solid rgba(255,255,255,0.1);
    }
    .chart-container:hover { 
        transform: translateY(-2px); 
        box-shadow: var(--shadow-lg); 
        border-color: rgba(102,126,234,0.3);
    }
    /* Respect users who prefer reduced motion */
    @media (prefers-reduced-motion: reduce) {
        .metric-card,
        .alert-card,
        .success-card,
        .warning-card,
        .error-card,
        .chart-container,
        .main-header { animation: none !important; transition: none !important; }
    }

    /* Minimal, consistent transitions across the app */
    button, [role="button"], .stButton > button,
    input, textarea, select,
    [data-baseweb="input"], [data-baseweb="select"], [data-baseweb="textarea"],
    [data-testid="stDataFrame"], [data-testid="stTable"],
    [data-testid="stExpander"], [data-testid="stMetric"],
    .alert-card, .success-card, .warning-card, .error-card,
    .chart-container {
        transition: background-color 120ms ease, color 120ms ease, box-shadow 120ms ease, transform 120ms ease, border-color 120ms ease;
    }

    /* Headings and text reveal animations (lightweight) */
    h1, h2, h3, h4, h5, h6 { animation: fadeInUp 0.3s ease both; }
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMarkdownContainer"] h4,
    [data-testid="stMarkdownContainer"] h5,
    [data-testid="stMarkdownContainer"] h6,
    [data-testid="stMarkdownContainer"] p { animation: fadeIn 0.35s ease both; }
    /* Center page titles */
    [data-testid="stMarkdownContainer"] h1 { text-align: center; width: 100%; }
    
    /* Soft glow behind titles on white/light backgrounds (non-dashboard) */
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3 {
        text-shadow: 0 1px 0 rgba(0,0,0,0.04), 0 6px 16px rgba(102,126,234,0.16);
    }
    /* Gentle hover emphasis on headings */
    h1:hover, h2:hover, h3:hover, h4:hover, h5:hover, h6:hover { transform: translateY(-1px); }

    /* Eye-catchy but classy title effects */
    /* Dashboard keeps white title inside gradient header */
    .main-header h1 { color: #ffffff !important; text-shadow: 0 1px 0 rgba(0,0,0,0.15), 0 4px 12px rgba(102,126,234,0.20); }
    /* All other pages: dark titles for better readability */
    [data-testid="stMarkdownContainer"] h1 { color: #111827 !important; text-shadow: none; }




    /* Gentle hover cues */
    .stButton > button:hover { transform: translateY(-1px); }
    [data-baseweb="select"]:hover, [data-baseweb="input"]:hover, [data-baseweb="textarea"]:hover { transform: translateY(-1px); }
    [data-testid="stExpander"]:hover { transform: translateY(-1px); }
    [data-testid="stDataFrame"] table tbody tr:hover { background-color: rgba(0,0,0,0.03); }

    /* Subtle focus outline for accessibility */
    .stButton > button:focus-visible,
    input:focus-visible, textarea:focus-visible, select:focus-visible,
    [data-baseweb="select"]:focus-within, [data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within {
        box-shadow: 0 0 0 3px rgba(102,126,234,0.28) !important;
        outline: none;
    }
    @keyframes fadeInUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }


    @keyframes btnRipple { 0% { box-shadow: 0 0 0 0 rgba(118,75,162,0.4); } 100% { box-shadow: 0 0 0 18px rgba(118,75,162,0); } }



    /* Global page fade-in */
    body { animation: fadeIn 0.5s ease both; }
    
    /* Ensure dark mode applies to root */
    html.dark { background-color: var(--bg); }
    html.dark body { background-color: var(--bg); }

    /* Tabs: entrance + hover underline with proper spacing */
    [data-testid="stTabs"] [role="tablist"] { 
        gap: 1rem; 
        padding: 0 0.5rem;
    }
    [data-testid="stTabs"] [role="tab"] {
        position: relative;
        transition: color 0.2s ease, transform 0.2s ease;
        animation: fadeInUp 0.35s ease both;
        margin: 0 0.5rem;
        padding: 0.75rem 1.5rem;
        border-radius: 8px 8px 0 0;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        font-weight: 500;
        letter-spacing: 0.3px;
    }
    [data-testid="stTabs"] [role="tab"]:hover { 
        transform: translateY(-2px); 
        background: rgba(102, 126, 234, 0.1);
        border-color: rgba(102, 126, 234, 0.3);
    }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        background: #667eea;
        color: white;
        border-color: #667eea;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    [data-testid="stTabs"] [role="tab"]::after {
        content: "";
        position: absolute;
        left: 10%; right: 10%; bottom: -6px;
        height: 3px; border-radius: 2px;
        background: #667eea;
        transform: scaleX(0);
        transform-origin: left;
        transition: transform 0.25s ease;
    }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"]::after { transform: scaleX(1); }
    
    /* Dark theme removed */

    /* Expanders: soft pop */
    [data-testid="stExpander"] { animation: fadeInUp 0.35s ease both; }
    [data-testid="stExpander"] [data-testid="stExpanderToggle"] {
        transition: transform 0.2s ease;
    }
    [data-testid="stExpander"]:hover { transform: translateY(-2px); }

    /* Dataframes and tables */
    [data-testid="stDataFrame"] { animation: fadeIn 0.4s ease both; }
    [data-testid="stTable"] { animation: fadeIn 0.4s ease both; }

    /* Metrics */
    [data-testid="stMetric"] { animation: fadeInUp 0.35s ease both; }

    /* Form controls: focus glow */
    input[type="text"], input[type="number"], textarea, select, .stSelectbox, .stTextInput, .stNumberInput, .stDateInput {
        transition: box-shadow 0.2s ease, transform 0.2s ease;
    }
    input[type="text"]:focus, input[type="number"]:focus, textarea:focus, select:focus {
        box-shadow: 0 0 0 3px rgba(102,126,234,0.35) !important;
        transform: translateY(-1px);
    }
    @media (max-width: 768px) { .metric-card { min-height: 100px; } .metric-card h3 { font-size: 0.95rem; } .metric-card h2 { font-size: 1.3rem; } }
</style>
""", unsafe_allow_html=True)

# Dark mode removed - using light theme only

# Initialize database and AI models
@st.cache_resource
def init_database():
    return DatabaseManager()

@st.cache_resource
def init_ai_models():
    forecasting = AIForecasting()
    reordering = SmartReordering()
    expiry_predictor = ExpiryPredictor()
    interaction_checker = DrugInteractionChecker()
    return forecasting, reordering, expiry_predictor, interaction_checker

# Add progress indicators and loading states
def show_loading_spinner():
    """Show a loading spinner with custom styling"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <div style="display: inline-block; width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite;"></div>
        <p style="margin-top: 1rem; color: #666;">Loading...</p>
    </div>
    <style>
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
    """, unsafe_allow_html=True)

def show_success_message(message):
    """Show a success message with animation"""
    st.markdown(f"""
    <div style="background: #d4edda; color: #155724; padding: 1rem; border-radius: 8px; border-left: 4px solid #28a745; margin: 1rem 0; animation: slideIn 0.5s ease;">
        <strong>✅ Success!</strong> {message}
    </div>
    <style>
        @keyframes slideIn {{
            from {{ transform: translateX(-100%); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
    </style>
    """, unsafe_allow_html=True)

# Sidebar navigation with enhanced styling
st.sidebar.markdown("""
<div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 2rem; display: flex; align-items: center; justify-content: center; gap: 10px;">
    <div style="width: 40px; height: 40px; background: #F8F9FA; border-radius: 20px; display: flex; align-items: center; justify-content: center;">
        <div style="width: 24px; height: 16px; background: linear-gradient(90deg, #FF6B9D 0%, #FF8E53 100%); border-radius: 8px; position: relative; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="position: absolute; top: 2px; left: 2px; width: 20px; height: 12px; background: linear-gradient(90deg, #FF6B9D 0%, #FF8E53 100%); border-radius: 6px; opacity: 0.8;"></div>
            <div style="position: absolute; top: 1px; left: 1px; width: 22px; height: 14px; background: linear-gradient(90deg, #FF6B9D 0%, #FF8E53 100%); border-radius: 7px; opacity: 0.6;"></div>
        </div>
    </div>
    <div>
        <h2 style="color: white; margin: 0; font-size: 1.2rem;">PharmaGPT</h2>
        <p style="color: white; margin: 0; font-size: 0.8rem;">Smart Inventory Management</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Add a welcome message
st.sidebar.markdown("""
<div class="welcome-message" style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border: 1px solid #e9ecef;">
    <p style="margin: 0; font-size: 0.9rem; color: #495057; font-weight: 500;">👋 Welcome to your AI-powered pharmaceutical inventory management system!</p>
</div>
""", unsafe_allow_html=True)

# Dark mode removed - using light theme only

# Initialize components
db = init_database()
# Add sample data for smart reordering to work properly
try:
    if hasattr(db, 'add_sample_data') and callable(getattr(db, 'add_sample_data')):
        db.add_sample_data()
except Exception:
    pass
forecasting, reordering, expiry_predictor, interaction_checker = init_ai_models()

page = st.sidebar.selectbox(
    "📋 Navigation Menu",
    ["Dashboard", "Inventory Management", "Receipt Scanner", "AI Assistant", "AI Forecasting", "Smart Reordering", 
     "Expiry Management", "Drug Interactions", "Analytics", "Settings"]
)


def dashboard_page():
    # Enhanced header
    st.markdown("""
    <div class="main-header">
        <h1>📊 Dashboard</h1>
        <p>Real-time insights and smart analytics for your pharmacy</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Add a quick stats row
    st.markdown("### 📈 Quick Overview")
    
    # Key metrics with enhanced styling
    col1, col2, col3, col4 = st.columns(4)
    
    total_items = db.get_total_inventory_count()
    low_stock_items = db.get_low_stock_count()
    expiring_soon = db.get_expiring_soon_count()
    total_value = db.get_total_inventory_value()
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>📦 Total Items</h3>
            <h2>{total_items}</h2>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>⚠️ Low Stock Items</h3>
            <h2>{low_stock_items}</h2>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>⏰ Expiring Soon</h3>
            <h2>{expiring_soon}</h2>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>💰 Total Value</h3>
            <h2>{format_dual_currency(total_value)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Enhanced alerts section
    st.markdown("### 🚨 Smart Alerts & Notifications")
    alerts = generate_alerts(db)
    if alerts:
        for alert in alerts:
            if alert['type'] == 'critical':
                st.markdown(f"""
                <div class="error-card">
                    <strong>🚨 Critical Alert:</strong> {alert['message']}
                </div>
                """, unsafe_allow_html=True)
            elif alert['type'] == 'warning':
                st.markdown(f"""
                <div class="warning-card">
                    <strong>⚠️ Warning:</strong> {alert['message']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="alert-card">
                    <strong>ℹ️ Info:</strong> {alert['message']}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="success-card">
            <strong>✅ All Good!</strong> No alerts at this time. Your inventory is well-managed.
        </div>
        """, unsafe_allow_html=True)
    
    # Enhanced charts section
    st.markdown("### 📊 Analytics & Insights")
    

    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.subheader("📈 Inventory by Category")
        category_data = db.get_inventory_by_category()
        if not category_data.empty:
            fig = px.pie(category_data, values='quantity', names='category', 
                        title="Inventory Distribution", 
                        color_discrete_sequence=px.colors.qualitative.Set3)
            fig.update_layout(height=400)
            st.plotly_chart(fig, width='stretch')
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.subheader("📉 Stock Levels")
        stock_data = db.get_stock_levels()
        if not stock_data.empty:
            fig = px.bar(stock_data, x='drug_name', y='current_stock', 
                        title="Current Stock Levels", color='current_stock',
                        color_continuous_scale='RdYlGn')
            fig.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig, width='stretch')
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Recent transactions with enhanced styling
    st.markdown("### 📋 Recent Transactions")
    

    
    recent_transactions = db.get_recent_transactions()
    if not recent_transactions.empty:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.dataframe(recent_transactions, width='stretch')
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="alert-card">
            <strong>ℹ️ No recent transactions found.</strong>
        </div>
        """, unsafe_allow_html=True)
    
    # Add helpful footer
    st.markdown("""
    <div style="text-align: center; padding: 1rem; background: var(--card); border-radius: 12px; margin-top: 2rem; backdrop-filter: blur(4px); border: 1px solid rgba(255,255,255,0.1);">
        <p style="margin: 0; color: var(--text); font-size: 0.9rem;">
            💡 <strong>Tip:</strong> Use the sidebar to navigate between different features. Each section provides specialized tools for managing your pharmaceutical inventory.
        </p>
    </div>
    """, unsafe_allow_html=True)

def inventory_management_page():
    st.markdown("""
    <div class="main-header">
        <h1>📦 Inventory Management</h1>
        <p>Comprehensive tools for managing your pharmaceutical inventory</p>
    </div>
    """, unsafe_allow_html=True)
    

    
    tab1, tab2, tab3 = st.tabs(["View Inventory", "Add New Item", "Update Stock"])
    
    with tab1:
        st.subheader("Current Inventory")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            category_filter = st.selectbox("Filter by Category", ["All"] + db.get_categories())
        with col2:
            stock_filter = st.selectbox("Stock Status", ["All", "Low Stock", "Out of Stock", "Normal"])
        with col3:
            search_term = st.text_input("Search Drug Name")
        
        # Get filtered inventory
        inventory_data = db.get_filtered_inventory(category_filter, stock_filter, search_term)
        
        if not inventory_data.empty:
            # Add color coding for stock levels
            def color_stock_level(val):
                if val <= 10:
                    return 'background-color: #ffcccc'  # Red for low stock
                elif val <= 50:
                    return 'background-color: #fff3cd'  # Yellow for medium stock
                else:
                    return 'background-color: #d4edda'  # Green for good stock
            
            styled_df = inventory_data.style.applymap(color_stock_level, subset=['current_stock'])
            st.dataframe(styled_df, width='stretch')
            
            # Export functionality
            csv = inventory_data.to_csv(index=False)
            st.download_button(
                label="📥 Export to CSV",
                data=csv,
                file_name=f"inventory_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

            # Import functionality (CSV, XLSX, JSON)
            st.markdown("---")
            st.markdown("### Import Data")
            uploaded_file = st.file_uploader("Choose a file", type=['csv', 'xlsx', 'json'], key="inventory_import")
            if uploaded_file is not None:
                if st.button("Import Inventory Data"):
                    try:
                        if uploaded_file.name.lower().endswith('.csv'):
                            df = pd.read_csv(uploaded_file)
                        elif uploaded_file.name.lower().endswith('.xlsx'):
                            df = pd.read_excel(uploaded_file)
                        elif uploaded_file.name.lower().endswith('.json'):
                            df = pd.read_json(uploaded_file)
                        else:
                            st.error("Unsupported file type.")
                            df = None

                        if df is not None:
                            success = db.import_data(df, "Inventory Items")
                            if success:
                                st.success("Data imported successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to import data. Please check the format.")
                    except Exception as e:
                        st.error(f"Error importing data: {str(e)}")
        else:
            st.info("No inventory items found matching your criteria.")
    
    with tab2:
        st.subheader("Add New Pharmaceutical Item")
        
        st.markdown('<div class="glass-border">', unsafe_allow_html=True)
        with st.form("add_item_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                drug_name = st.text_input("Drug Name*")
                category = st.selectbox("Category", 
                    ["Antibiotics", "Analgesics", "Cardiovascular", "Diabetes", "Respiratory", "Other"])
                manufacturer = st.text_input("Manufacturer")
                batch_number = st.text_input("Batch Number*")
                
            with col2:
                current_stock = st.number_input("Current Stock", min_value=0, value=0)
                minimum_stock = st.number_input("Minimum Stock Level", min_value=0, value=10)
                unit_price = st.number_input("Unit Price (₹)", min_value=0.0, value=0.0, step=0.01)
                expiry_date = st.date_input("Expiry Date")
            
            supplier_name = st.text_input("Supplier Name")
            description = st.text_area("Description")
            
            submitted = st.form_submit_button("Add Item")
            
            if submitted:
                if drug_name and batch_number:
                    success = db.add_inventory_item(
                        drug_name, category, manufacturer, batch_number,
                        current_stock, minimum_stock, unit_price, expiry_date,
                        supplier_name, description
                    )
                    if success:
                        st.success("Item added successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to add item. Please check if batch number already exists.")
                else:
                    st.error("Please fill in all required fields (marked with *).")
    
    with tab3:
        st.subheader("Update Stock Levels")
        
        # Select item to update
        items = db.get_all_items_for_dropdown()
        if items:
            selected_item = st.selectbox("Select Item to Update", items)
            
            if selected_item:
                item_id = selected_item.split(" - ")[0]
                current_item = db.get_item_details(item_id)
                
                if current_item:
                    st.write(f"**Current Stock:** {current_item['current_stock']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        transaction_type = st.selectbox("Transaction Type", ["Add Stock", "Remove Stock"])
                        quantity = st.number_input("Quantity", min_value=1, value=1)
                    
                    with col2:
                        reason = st.text_input("Reason/Notes")
                    
                    if st.button("Update Stock"):
                        if transaction_type == "Add Stock":
                            new_stock = current_item['current_stock'] + quantity
                        else:
                            new_stock = max(0, current_item['current_stock'] - quantity)
                        
                        success = db.update_stock_level(item_id, new_stock, transaction_type, quantity, reason)
                        if success:
                            st.success(f"Stock updated successfully! New stock level: {new_stock}")
                            st.rerun()
                        else:
                            st.error("Failed to update stock.")
        else:
            st.info("No items available for update.")

def ai_forecasting_page():
    st.markdown("""
    <div class="main-header">
        <h1>🔮 AI Demand Forecasting</h1>
        <p>Predict future demand using advanced time series analysis and machine learning</p>
    </div>
    """, unsafe_allow_html=True)
    

    
    st.write("Predict future demand using advanced time series analysis and machine learning.")
    
    # Select drug for forecasting
    drugs = db.get_drugs_for_forecasting()
    if drugs:
        selected_drug = st.selectbox("Select Drug for Forecasting", drugs)
        
        col1, col2 = st.columns([2, 1])
        
        with col2:
            forecast_days = st.slider("Forecast Period (Days)", 7, 90, 30)
            model_type = st.selectbox("Forecasting Model", ["Linear Regression", "Random Forest", "ARIMA"])
        
        if st.button("Generate Forecast"):
            with st.spinner("Generating forecast..."):
                # Get historical data
                historical_data = db.get_historical_consumption(selected_drug)
                
                if len(historical_data) > 7:  # Need minimum data for forecasting
                    # Generate forecast
                    forecast_result = forecasting.generate_forecast(
                        historical_data, forecast_days, model_type
                    )
                    
                    with col1:
                        # Plot historical and forecasted data
                        fig = go.Figure()
                        
                        # Historical data
                        fig.add_trace(go.Scatter(
                            x=historical_data['date'],
                            y=historical_data['consumption'],
                            mode='lines+markers',
                            name='Historical Consumption',
                            line=dict(color='blue')
                        ))
                        
                        # Forecasted data
                        forecast_dates = pd.date_range(
                            start=historical_data['date'].max() + timedelta(days=1),
                            periods=forecast_days,
                            freq='D'
                        )
                        
                        fig.add_trace(go.Scatter(
                            x=forecast_dates,
                            y=forecast_result['forecast'],
                            mode='lines+markers',
                            name='Forecasted Consumption',
                            line=dict(color='red', dash='dash')
                        ))
                        
                        # Add confidence intervals if available
                        if 'confidence_upper' in forecast_result:
                            fig.add_trace(go.Scatter(
                                x=forecast_dates,
                                y=forecast_result['confidence_upper'],
                                fill=None,
                                mode='lines',
                                line_color='rgba(0,0,0,0)',
                                name='Upper Confidence'
                            ))
                            
                            fig.add_trace(go.Scatter(
                                x=forecast_dates,
                                y=forecast_result['confidence_lower'],
                                fill='tonexty',
                                mode='lines',
                                line_color='rgba(0,0,0,0)',
                                name='Confidence Interval',
                                fillcolor='rgba(255,0,0,0.2)'
                            ))
                        
                        fig.update_layout(
                            title=f"Demand Forecast for {selected_drug}",
                            xaxis_title="Date",
                            yaxis_title="Consumption",
                            hovermode='x unified'
                        )
                        
                        st.plotly_chart(fig, width='stretch')
                    
                    # Display forecast insights
                    st.subheader("📊 Forecast Insights")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        avg_daily_demand = np.mean(forecast_result['forecast'])
                        st.metric("Avg Daily Demand", f"{avg_daily_demand:.1f}")
                    
                    with col2:
                        total_demand = np.sum(forecast_result['forecast'])
                        st.metric("Total Forecasted Demand", f"{total_demand:.0f}")
                    
                    with col3:
                        accuracy = forecast_result.get('accuracy', 0)
                        st.metric("Model Accuracy", f"{accuracy:.1%}")
                    
                    # Recommendations
                    st.subheader("💡 AI Recommendations")
                    recommendations = forecasting.generate_recommendations(
                        selected_drug, forecast_result, db.get_current_stock(selected_drug)
                    )
                    
                    for rec in recommendations:
                        if rec['priority'] == 'high':
                            st.error(f"🔴 {rec['message']}")
                        elif rec['priority'] == 'medium':
                            st.warning(f"🟡 {rec['message']}")
                        else:
                            st.info(f"🔵 {rec['message']}")
                
                else:
                    st.warning("Insufficient historical data for forecasting. Need at least 7 data points.")
    else:
        st.info("No drugs available for forecasting. Please add some inventory items first.")

def smart_reordering_page():
    st.markdown("""
    <div class="main-header">
        <h1>🤖 Smart Reordering System</h1>
        <p>AI-powered automatic reordering suggestions based on consumption patterns and forecasts</p>
    </div>
    """, unsafe_allow_html=True)
    

    
    st.write("AI-powered automatic reordering suggestions based on consumption patterns and forecasts.")
    
    # Auto-reorder recommendations
    st.subheader("📋 Reorder Recommendations")
    
    reorder_suggestions = reordering.get_reorder_suggestions(db)
    
    if reorder_suggestions:
        for suggestion in reorder_suggestions:
            st.markdown('<div class="glass-border">', unsafe_allow_html=True)
            with st.expander(f"🔄 {suggestion['drug_name']} - Priority: {suggestion['priority'].upper()}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Current Stock:** {suggestion['current_stock']}")
                    st.write(f"**Minimum Level:** {suggestion['minimum_stock']}")
                    st.write(f"**Suggested Order:** {suggestion['suggested_quantity']}")
                
                with col2:
                    st.write(f"**Days Until Stockout:** {suggestion['days_until_stockout']}")
                    st.write(f"**Average Daily Usage:** {suggestion['avg_daily_usage']:.1f}")
                    st.write(f"**Supplier:** {suggestion['supplier']}")
                
                with col3:
                    st.write(f"**Estimated Cost:** {format_dual_currency(suggestion['estimated_cost'])}")
                    st.write(f"**Lead Time:** {suggestion['lead_time']} days")
                
                st.write(f"**Reason:** {suggestion['reason']}")
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"✅ Approve Order", key=f"approve_{suggestion['id']}"):
                        success = db.create_purchase_order(suggestion)
                        if success:
                            st.success("Purchase order created!")
                        else:
                            st.error("Failed to create purchase order.")
                
                with col2:
                    if st.button(f"⏰ Snooze (1 day)", key=f"snooze_{suggestion['id']}"):
                        db.snooze_reorder_suggestion(suggestion['id'], 1)
                        st.info("Suggestion snoozed for 1 day.")
                
                with col3:
                    if st.button(f"❌ Dismiss", key=f"dismiss_{suggestion['id']}"):
                        db.dismiss_reorder_suggestion(suggestion['id'])
                        st.info("Suggestion dismissed.")
    else:
        st.success("No reorder recommendations at this time!")
    
    # Supplier optimization
    st.subheader("🏪 Supplier Optimization")
    
    supplier_analysis = reordering.analyze_suppliers(db)
    if supplier_analysis:
        suppliers_df = pd.DataFrame(supplier_analysis)
        
        fig = px.scatter(suppliers_df, x='avg_delivery_time', y='avg_unit_cost',
                        size='reliability_score', color='supplier_name',
                        title="Supplier Performance Analysis",
                        hover_data=['total_orders'])
        fig.update_layout(
            xaxis_title="Average Delivery Time (days)",
                            yaxis_title="Average Cost per Unit (₹)"
        )
        st.plotly_chart(fig, width='stretch')
    
    # Manual reorder
    st.subheader("📝 Manual Reorder")
    
    st.markdown('<div class="glass-border">', unsafe_allow_html=True)
    with st.form("manual_reorder"):
        col1, col2 = st.columns(2)
        
        with col1:
            drugs = db.get_all_drugs()
            selected_drug = st.selectbox("Select Drug", drugs)
            quantity = st.number_input("Quantity to Order", min_value=1, value=1)
        
        with col2:
            suppliers = db.get_suppliers()
            selected_supplier = st.selectbox("Select Supplier", suppliers)
            notes = st.text_area("Notes")
        
        if st.form_submit_button("Create Manual Order"):
            order_data = {
                'drug_name': selected_drug,
                'quantity': quantity,
                'supplier': selected_supplier,
                'notes': notes,
                'manual': True
            }
            
            success = db.create_purchase_order(order_data)
            if success:
                st.success("Manual purchase order created successfully!")
            else:
                st.error("Failed to create purchase order.")

def expiry_management_page():
    st.title("⏰ Expiry & Wastage Management")
    
    st.write("AI-powered expiry monitoring and wastage prevention system.")
    
    # Expiry alerts
    st.subheader("🚨 Expiry Alerts")
    
    tab1, tab2, tab3 = st.tabs(["Expiring Soon", "Expiry Predictions", "Wastage Analysis"])
    
    with tab1:
        expiring_items = db.get_expiring_items()
        
        if not expiring_items.empty:
            # Color code by urgency
            def get_urgency_color(days):
                if days <= 7:
                    return "🔴"
                elif days <= 30:
                    return "🟡"
                else:
                    return "🟢"
            
            expiring_items['urgency'] = expiring_items['days_until_expiry'].apply(get_urgency_color)
            
            st.dataframe(expiring_items, width='stretch')
            
            # Bulk actions
            st.subheader("Bulk Actions")
            selected_items = st.multiselect(
                "Select items for bulk action:",
                options=expiring_items['drug_name'].tolist()
            )
            
            if selected_items:
                action = st.selectbox("Action", ["Mark as Used", "Return to Supplier", "Dispose"])
                
                if st.button(f"Apply {action}"):
                    for item in selected_items:
                        db.apply_expiry_action(item, action)
                    st.success(f"{action} applied to selected items!")
                    st.rerun()
        else:
            st.success("No items expiring soon!")
    
    with tab2:
        st.subheader("AI Expiry Predictions")
        
        # Get drugs with consumption data
        drugs_with_data = db.get_drugs_with_consumption_data()
        
        if drugs_with_data:
            selected_drug = st.selectbox("Select Drug for Expiry Prediction", drugs_with_data)
            
            if st.button("Generate Expiry Prediction"):
                with st.spinner("Analyzing consumption patterns..."):
                    prediction = expiry_predictor.predict_expiry_risk(selected_drug, db)
                    
                    if prediction:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric("Expiry Risk Score", f"{prediction['risk_score']:.2f}")
                            st.metric("Predicted Wastage", f"{prediction['predicted_wastage']:.0f} units")
                            st.metric("Days to Use Current Stock", f"{prediction['days_to_use']:.0f}")
                        
                        with col2:
                            risk_level = prediction['risk_level']
                            if risk_level == 'high':
                                st.error("🔴 High Risk of Wastage")
                            elif risk_level == 'medium':
                                st.warning("🟡 Medium Risk of Wastage")
                            else:
                                st.success("🟢 Low Risk of Wastage")
                        
                        # Recommendations
                        st.subheader("AI Recommendations")
                        for rec in prediction['recommendations']:
                            st.info(f"💡 {rec}")
                        
                        # Visualization
                        fig = go.Figure()
                        
                        # Consumption trend
                        fig.add_trace(go.Scatter(
                            x=prediction['trend_data']['dates'],
                            y=prediction['trend_data']['consumption'],
                            mode='lines+markers',
                            name='Historical Consumption',
                            line=dict(color='blue')
                        ))
                        
                        # Predicted consumption
                        fig.add_trace(go.Scatter(
                            x=prediction['trend_data']['future_dates'],
                            y=prediction['trend_data']['predicted_consumption'],
                            mode='lines',
                            name='Predicted Consumption',
                            line=dict(color='red', dash='dash')
                        ))
                        
                        fig.update_layout(
                            title=f"Consumption Trend Analysis - {selected_drug}",
                            xaxis_title="Date",
                            yaxis_title="Daily Consumption"
                        )
                        
                        st.plotly_chart(fig, width='stretch')
        else:
            st.info("No consumption data available for expiry prediction.")
    
    with tab3:
        st.subheader("Wastage Analysis")
        
        # Time period selection
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=90))
        with col2:
            end_date = st.date_input("End Date", datetime.now())
        
        wastage_data = db.get_wastage_analysis(start_date, end_date)
        
        if not wastage_data.empty:
            # Wastage by category
            fig1 = px.bar(wastage_data, x='category', y='wasted_value',
                         title="Wastage by Category", color='category')
            st.plotly_chart(fig1, width='stretch')
            
            # Top wasted drugs
            fig2 = px.pie(wastage_data.head(10), values='wasted_quantity', names='drug_name',
                         title="Top 10 Wasted Drugs by Quantity")
            st.plotly_chart(fig2, width='stretch')
            
            # Wastage trends
            wastage_trends = db.get_wastage_trends(start_date, end_date)
            if not wastage_trends.empty:
                fig3 = px.line(wastage_trends, x='date', y='daily_wastage',
                              title="Daily Wastage Trend")
                st.plotly_chart(fig3, width='stretch')
            
            # Summary metrics
            total_wastage = wastage_data['wasted_value'].sum()
            total_quantity = wastage_data['wasted_quantity'].sum()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Wastage Value", format_currency(total_wastage))
            with col2:
                st.metric("Total Wastage Quantity", f"{total_quantity:.0f} units")
            with col3:
                avg_daily_wastage = total_wastage / ((end_date - start_date).days + 1)
                st.metric("Avg Daily Wastage", format_currency(avg_daily_wastage))
        else:
            st.info("No wastage data found for the selected period.")

def drug_interactions_page():
    st.title("⚠️ Drug Interaction Checker")
    
    st.write("AI-powered drug interaction detection and safety alerts.")
    
    tab1, tab2 = st.tabs(["Check Interactions", "Interaction Database"])
    
    with tab1:
        st.subheader("Drug Interaction Analysis")
        
        # Multi-drug selection
        available_drugs = db.get_all_drugs()
        selected_drugs = st.multiselect(
            "Select drugs to check for interactions:",
            available_drugs,
            help="Select 2 or more drugs to check for potential interactions"
        )
        
        if len(selected_drugs) >= 2:
            if st.button("Check Interactions"):
                with st.spinner("Analyzing drug interactions..."):
                    interactions = interaction_checker.check_interactions(selected_drugs)
                    
                    if interactions:
                        st.subheader("⚠️ Potential Interactions Found")
                        
                        for interaction in interactions:
                            severity = interaction['severity'].lower()
                            
                            if severity == 'severe':
                                st.error(f"🔴 **SEVERE**: {interaction['drug1']} + {interaction['drug2']}")
                            elif severity == 'moderate':
                                st.warning(f"🟡 **MODERATE**: {interaction['drug1']} + {interaction['drug2']}")
                            else:
                                st.info(f"🔵 **MILD**: {interaction['drug1']} + {interaction['drug2']}")
                            
                            with st.expander(f"Details: {interaction['drug1']} + {interaction['drug2']}"):
                                st.write(f"**Severity:** {interaction['severity']}")
                                st.write(f"**Description:** {interaction['description']}")
                                st.write(f"**Clinical Effect:** {interaction['clinical_effect']}")
                                st.write(f"**Management:** {interaction['management']}")
                                
                                if interaction.get('alternatives'):
                                    st.write("**Suggested Alternatives:**")
                                    for alt in interaction['alternatives']:
                                        st.write(f"- {alt}")
                    else:
                        st.success("✅ No significant interactions found between selected drugs!")
                        
                        # Show safe combinations
                        st.subheader("✅ Safe Drug Combinations")
                        safe_combinations = interaction_checker.get_safe_combinations(selected_drugs)
                        for combo in safe_combinations:
                            st.success(f"✓ {combo['drug1']} + {combo['drug2']} - {combo['note']}")
        
        elif len(selected_drugs) == 1:
            st.info("Please select at least 2 drugs to check for interactions.")
        
        # Drug substitution finder
        st.subheader("🔄 Drug Substitution Finder")
        
        col1, col2 = st.columns(2)
        with col1:
            drug_to_substitute = st.selectbox("Drug to find substitutes for:", available_drugs)
        with col2:
            reason = st.selectbox("Reason for substitution:", 
                                ["Out of stock", "Drug interaction", "Patient allergy", "Cost optimization"])
        
        if st.button("Find Substitutes"):
            substitutes = interaction_checker.find_substitutes(drug_to_substitute, reason)
            
            if substitutes:
                st.subheader(f"🔄 Substitutes for {drug_to_substitute}")
                
                for substitute in substitutes:
                    with st.expander(f"{substitute['name']} - Similarity: {substitute['similarity']:.1%}"):
                        st.write(f"**Generic Name:** {substitute['generic_name']}")
                        st.write(f"**Strength:** {substitute['strength']}")
                        st.write(f"**Dosage Form:** {substitute['dosage_form']}")
                        st.write(f"**Manufacturer:** {substitute['manufacturer']}")
                        st.write(f"**Notes:** {substitute['notes']}")
                        
                        # Check availability
                        availability = db.check_drug_availability(substitute['name'])
                        if availability['in_stock']:
                            st.success(f"✅ In stock: {availability['quantity']} units")
                        else:
                            st.warning("⚠️ Not in stock")
            else:
                st.warning("No suitable substitutes found.")
    
    with tab2:
        st.subheader("Interaction Database Management")
        
        # Display known interactions
        known_interactions = db.get_known_interactions()
        
        if not known_interactions.empty:
            st.dataframe(known_interactions, width='stretch')
        
        # Add new interaction
        with st.expander("Add New Interaction"):
            with st.form("add_interaction"):
                col1, col2 = st.columns(2)
                
                with col1:
                    drug1 = st.selectbox("Drug 1", available_drugs, key="drug1_interaction")
                    drug2 = st.selectbox("Drug 2", available_drugs, key="drug2_interaction")
                    severity = st.selectbox("Severity", ["Mild", "Moderate", "Severe"])
                
                with col2:
                    clinical_effect = st.text_input("Clinical Effect")
                    management = st.text_area("Management Recommendation")
                
                description = st.text_area("Interaction Description")
                
                if st.form_submit_button("Add Interaction"):
                    if drug1 != drug2:
                        success = db.add_drug_interaction(
                            drug1, drug2, severity, description, clinical_effect, management
                        )
                        if success:
                            st.success("Interaction added successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to add interaction.")
                    else:
                        st.error("Please select different drugs.")

def analytics_page():
    st.title("📈 Analytics & Reports")
    
    st.write("Comprehensive analytics and insights for pharmaceutical inventory management.")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Consumption Analytics", "Financial Reports", "Supplier Performance", "Predictive Analytics"])
    
    with tab1:
        st.subheader("📊 Consumption Analytics")
        
        # Time period selection
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30), key="consumption_start")
        with col2:
            end_date = st.date_input("End Date", datetime.now(), key="consumption_end")
        
        consumption_data = db.get_consumption_analytics(start_date, end_date)
        
        if not consumption_data.empty:
            # Top consumed drugs
            fig1 = px.bar(consumption_data.head(15), x='drug_name', y='total_consumed',
                         title="Top 15 Consumed Drugs", color='total_consumed',
                         color_continuous_scale='Blues')
            fig1.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig1, width='stretch')
            
            # Consumption by category
            category_consumption = consumption_data.groupby('category')['total_consumed'].sum().reset_index()
            fig2 = px.pie(category_consumption, values='total_consumed', names='category',
                         title="Consumption by Drug Category")
            st.plotly_chart(fig2, width='stretch')
            
            # Daily consumption trends
            daily_trends = db.get_daily_consumption_trends(start_date, end_date)
            if not daily_trends.empty:
                fig3 = px.line(daily_trends, x='date', y='daily_consumption',
                              title="Daily Consumption Trends")
                st.plotly_chart(fig3, width='stretch')
            
            # Department-wise consumption (if department data available)
            dept_consumption = db.get_department_consumption(start_date, end_date)
            if not dept_consumption.empty:
                fig4 = px.treemap(dept_consumption, path=['department'], values='consumption',
                                 title="Consumption by Department")
                st.plotly_chart(fig4, width='stretch')
        else:
            st.info("No consumption data available for the selected period.")
    
    with tab2:
        st.subheader("💰 Financial Reports")
        
        # Financial overview
        financial_data = db.get_financial_overview()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Inventory Value", format_dual_currency(financial_data['total_value']))
        with col2:
            st.metric("Monthly Spend", format_dual_currency(financial_data['monthly_spend']))
        with col3:
            st.metric("Cost Savings", format_dual_currency(financial_data['cost_savings']))
        with col4:
            st.metric("ROI", f"{financial_data['roi']:.1%}")
        
        # Cost analysis
        cost_data = db.get_cost_analysis()
        if not cost_data.empty:
            # Cost by category
            fig1 = px.bar(cost_data, x='category', y='total_cost',
                         title="Cost by Drug Category", color='total_cost',
                         color_continuous_scale='Reds')
            st.plotly_chart(fig1, width='stretch')
            
            # Cost trends
            cost_trends = db.get_cost_trends()
            if not cost_trends.empty:
                fig2 = px.line(cost_trends, x='month', y='monthly_cost',
                              title="Monthly Cost Trends")
                st.plotly_chart(fig2, width='stretch')
        
        # Budget vs actual
        budget_data = db.get_budget_analysis()
        if budget_data:
            fig3 = go.Figure()
            
            categories = list(budget_data.keys())
            budgeted = [budget_data[cat]['budgeted'] for cat in categories]
            actual = [budget_data[cat]['actual'] for cat in categories]
            
            fig3.add_trace(go.Bar(name='Budgeted', x=categories, y=budgeted))
            fig3.add_trace(go.Bar(name='Actual', x=categories, y=actual))
            
            fig3.update_layout(
                title="Budget vs Actual Spending",
                barmode='group',
                yaxis_title="Amount (₹)"
            )
            st.plotly_chart(fig3, width='stretch')
    
    with tab3:
        st.subheader("🏪 Supplier Performance Analysis")
        
        supplier_metrics = db.get_supplier_metrics()
        
        if not supplier_metrics.empty:
            # Supplier scorecard
            fig1 = px.scatter(supplier_metrics, x='avg_delivery_time', y='quality_score',
                             size='total_orders', color='cost_rating',
                             hover_name='supplier_name',
                             title="Supplier Performance Matrix",
                             labels={'avg_delivery_time': 'Average Delivery Time (days)',
                                    'quality_score': 'Quality Score (/10)'})
            st.plotly_chart(fig1, width='stretch')
            
            # Delivery performance
            fig2 = px.bar(supplier_metrics, x='supplier_name', y='on_time_delivery_rate',
                         title="On-Time Delivery Rate by Supplier",
                         color='on_time_delivery_rate',
                         color_continuous_scale='RdYlGn')
            fig2.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig2, width='stretch')
            
            # Cost comparison
            fig3 = px.box(supplier_metrics, y='avg_unit_cost', x='supplier_name',
                         title="Cost Distribution by Supplier")
            fig3.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig3, width='stretch')
            
            # Supplier recommendations
            st.subheader("🎯 Supplier Recommendations")
            recommendations = db.get_supplier_recommendations()
            for rec in recommendations:
                if rec['type'] == 'best_performer':
                    st.success(f"⭐ **Best Performer**: {rec['supplier']} - {rec['reason']}")
                elif rec['type'] == 'needs_improvement':
                    st.warning(f"⚠️ **Needs Improvement**: {rec['supplier']} - {rec['reason']}")
                elif rec['type'] == 'cost_optimization':
                    st.info(f"💰 **Cost Optimization**: {rec['message']}")
        else:
            st.info("No supplier performance data available.")
    
    with tab4:
        st.subheader("🔮 Predictive Analytics")
        
        # Anomaly detection
        st.write("**Anomaly Detection Results**")
        anomalies = db.detect_anomalies()
        
        if anomalies:
            for anomaly in anomalies:
                severity = anomaly['severity'].lower()
                if severity == 'high':
                    st.error(f"🔴 **High Priority**: {anomaly['description']}")
                elif severity == 'medium':
                    st.warning(f"🟡 **Medium Priority**: {anomaly['description']}")
                else:
                    st.info(f"🔵 **Low Priority**: {anomaly['description']}")
        else:
            st.success("✅ No anomalies detected in recent data.")
        
        # Predictive insights
        st.write("**Predictive Insights**")
        insights = db.get_predictive_insights()
        
        for insight in insights:
            with st.expander(f"📊 {insight['title']}"):
                st.write(insight['description'])
                
                if insight.get('chart_data') is not None and not insight['chart_data'].empty:
                    # Create chart based on insight type
                    if insight['chart_type'] == 'line':
                        fig = px.line(insight['chart_data'], x='x', y='y', title=insight['title'])
                        st.plotly_chart(fig, width='stretch')
                    elif insight['chart_type'] == 'bar':
                        fig = px.bar(insight['chart_data'], x='x', y='y', title=insight['title'])
                        st.plotly_chart(fig, width='stretch')
                
                if insight.get('recommendations'):
                    st.write("**Recommendations:**")
                    for rec in insight['recommendations']:
                        st.write(f"• {rec}")

def settings_page():
    st.title("⚙️ Settings & Configuration")
    
    tab1, tab2, tab3, tab4 = st.tabs(["General Settings", "Alert Configuration", "Data Management", "AI Model Settings"])
    
    with tab1:
        st.subheader("General Settings")
        
        with st.form("general_settings"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Inventory Settings**")
                default_min_stock = st.number_input("Default Minimum Stock Level", min_value=0, value=10)
                low_stock_threshold = st.number_input("Low Stock Alert Threshold", min_value=0, value=20)
                auto_reorder = st.checkbox("Enable Auto-Reordering", value=True)
                
            with col2:
                st.write("**System Settings**")
                currency = st.selectbox("Currency", ["INR"])
                date_format = st.selectbox("Date Format", ["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"])
                timezone = st.selectbox("Timezone", ["UTC", "EST", "PST", "GMT"])
                
                # Currency converter removed - INR only
            
            if st.form_submit_button("Save General Settings"):
                settings = {
                    'default_min_stock': default_min_stock,
                    'low_stock_threshold': low_stock_threshold,
                    'auto_reorder': auto_reorder,
                    'currency': currency,
                    'date_format': date_format,
                    'timezone': timezone
                }
                db.update_settings(settings)
                st.success("Settings saved successfully!")
    
    with tab2:
        st.subheader("Alert Configuration")
        
        with st.form("alert_settings"):
            st.write("**Expiry Alerts**")
            expiry_warning_days = st.slider("Days before expiry to alert", 1, 90, 30)
            expiry_critical_days = st.slider("Days before expiry for critical alert", 1, 30, 7)
            
            st.write("**Stock Alerts**")
            stock_alert_threshold = st.slider("Stock level percentage for alerts", 1, 50, 20)
            
            st.write("**Financial Alerts**")
            budget_alert_threshold = st.slider("Budget usage percentage for alerts", 50, 100, 80)
            
            st.write("**Notification Preferences**")
            email_alerts = st.checkbox("Enable Email Alerts", value=True)
            sms_alerts = st.checkbox("Enable SMS Alerts", value=False)
            dashboard_alerts = st.checkbox("Enable Dashboard Alerts", value=True)
            
            if st.form_submit_button("Save Alert Settings"):
                alert_settings = {
                    'expiry_warning_days': expiry_warning_days,
                    'expiry_critical_days': expiry_critical_days,
                    'stock_alert_threshold': stock_alert_threshold,
                    'budget_alert_threshold': budget_alert_threshold,
                    'email_alerts': email_alerts,
                    'sms_alerts': sms_alerts,
                    'dashboard_alerts': dashboard_alerts
                }
                db.update_alert_settings(alert_settings)
                st.success("Alert settings saved successfully!")
    
    with tab3:
        st.subheader("Data Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Export Data**")
            export_format = st.selectbox("Export Format", ["CSV", "Excel", "JSON"])
            export_data_type = st.selectbox("Data Type", ["All Data", "Inventory Only", "Transactions Only", "Reports Only"])
            
            if st.button("Export Data"):
                if export_data_type == "All Data":
                    data = db.export_all_data()
                elif export_data_type == "Inventory Only":
                    data = db.export_inventory_data()
                elif export_data_type == "Transactions Only":
                    data = db.export_transaction_data()
                else:
                    data = db.export_report_data()
                
                if export_format == "CSV":
                    st.download_button(
                        label="📥 Download CSV",
                        data=data.to_csv(index=False),
                        file_name=f"pharma_data_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                elif export_format == "JSON":
                    st.download_button(
                        label="📥 Download JSON",
                        data=data.to_json(orient='records'),
                        file_name=f"pharma_data_{datetime.now().strftime('%Y%m%d')}.json",
                        mime="application/json"
                    )
        
        with col2:
            # Import functionality moved to Inventory Management → View Inventory
            pass
        
        # Database maintenance (stacked vertically for cleaner look)
        st.write("**Database Maintenance**")
        if st.button("🧹 Clean Old Data"):
            cleaned_records = db.clean_old_data()
            st.success(f"Cleaned {cleaned_records} old records!")
        
        st.markdown("")
        if st.button("📊 Optimize Database"):
            db.optimize_database()
            st.success("Database optimized!")
        
        st.markdown("")
        if st.button("💾 Backup Database"):
            backup_file = db.backup_database()
            st.success(f"Database backed up to: {backup_file}")
    
    with tab4:
        st.subheader("AI Model Settings")
        
        with st.form("ai_settings"):
            st.write("**Forecasting Models**")
            default_forecast_model = st.selectbox("Default Forecasting Model", 
                                                 ["Linear Regression", "Random Forest", "ARIMA"])
            forecast_accuracy_threshold = st.slider("Minimum Accuracy Threshold", 0.1, 1.0, 0.7)
            
            st.write("**Reordering AI**")
            reorder_safety_factor = st.slider("Safety Stock Factor", 1.0, 3.0, 1.5)
            lead_time_variance = st.slider("Lead Time Variance Factor", 0.1, 1.0, 0.2)
            
            st.write("**Anomaly Detection**")
            anomaly_sensitivity = st.slider("Anomaly Detection Sensitivity", 0.1, 1.0, 0.5)
            
            if st.form_submit_button("Save AI Settings"):
                ai_settings = {
                    'default_forecast_model': default_forecast_model,
                    'forecast_accuracy_threshold': forecast_accuracy_threshold,
                    'reorder_safety_factor': reorder_safety_factor,
                    'lead_time_variance': lead_time_variance,
                    'anomaly_sensitivity': anomaly_sensitivity
                }
                db.update_ai_settings(ai_settings)
                st.success("AI settings saved successfully!")
        
        # Model performance monitoring
        st.subheader("Model Performance Monitoring")
        
        model_performance = db.get_model_performance()
        if model_performance:
            performance_df = pd.DataFrame(model_performance)
            
            fig = px.bar(performance_df, x='model_name', y='accuracy',
                        title="AI Model Performance", color='accuracy',
                        color_continuous_scale='RdYlGn')
            st.plotly_chart(fig, width='stretch')
            
            # Model recommendations
            st.write("**Model Recommendations:**")
            for model in model_performance:
                if model['accuracy'] < 0.7:
                    st.warning(f"⚠️ {model['model_name']} accuracy is below threshold. Consider retraining.")
                else:
                    st.success(f"✅ {model['model_name']} is performing well.")

# Main app logic
if page == "Dashboard":
    dashboard_page()
elif page == "Inventory Management":
    inventory_management_page()
elif page == "Receipt Scanner":
    render_receipt_scanner_page(db)
elif page == "AI Assistant":
    render_ai_chatbot_page(db)
elif page == "AI Forecasting":
    ai_forecasting_page()
elif page == "Smart Reordering":
    smart_reordering_page()
elif page == "Expiry Management":
    expiry_management_page()
elif page == "Drug Interactions":
    drug_interactions_page()
elif page == "Analytics":
    analytics_page()
elif page == "Settings":
    settings_page()

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**PharmaGPT**")
st.sidebar.markdown("Version 1.0.0")
st.sidebar.markdown("© 2025 PharmaGPT")
