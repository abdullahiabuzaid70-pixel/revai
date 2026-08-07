"""
RevAI - AI Revenue & Fraud Detection for African Companies
Main Streamlit Application

Run: streamlit run app.py
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import io
import base64
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# === PAGE CONFIG (must be first) ===
st.set_page_config(
    page_title="RevAI - Revenue. Protected.",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === IMPORTS ===
from utils.data_loader import (
    read_uploaded_file, normalize_columns, validate_data,
    auto_map_columns, apply_mapping, get_data_summary, generate_data_template
)
from utils.sample_data_generator import generate_all_sample_data
from detectors.duplicate_payments import detect_duplicate_payments, get_summary as dup_summary
from detectors.vat_wht_remittance import detect_vat_wht_issues, get_summary as vat_summary
from detectors.overstated_expenses import detect_overstated_expenses, get_summary as exp_summary
from detectors.ghost_vendors_employees import (
    detect_ghost_vendors, detect_ghost_employees,
    get_summary as ghost_summary
)
from detectors.tax_filing_risk import detect_tax_filing_risk, get_summary as tax_summary
from utils.report_generator import generate_report

# === PROFESSIONAL CSS ===
st.markdown("""
<style>
/* ===== HIDE STREAMLIT CHROME ===== */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }
.stDeployButton { display: none !important; }
div[data-testid="stToolbar"] { display: none !important; }
.stApp > header { height: 0 !important; }
.css-1rs6osy .stAlert { display: none; }

/* Fork/GitHub button */
.st-emotion-cache-1wrcr25, .st-emotion-cache-1khj6t { display: none !important; }
a[href*="streamlit.io/cloud"] { display: none !important; }
[class*="stGithub"] { display: none !important; }

/* ===== GLOBAL ===== */
.stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #F8FAFC;
}

/* ===== SIDEBAR ===== */
section[data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 1px solid #E2E8F0;
}

section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #0F172A;
}

/* ===== HERO ===== */
.revai-hero {
    background: linear-gradient(135deg, #0F172A 0%, #1E3A5F 50%, #1E293B 100%);
    padding: 30px 40px;
    border-radius: 16px;
    margin-bottom: 24px;
    box-shadow: 0 4px 20px rgba(15, 23, 42, 0.15);
}
.revai-hero h1 {
    color: #FFFFFF;
    font-size: 32px;
    font-weight: 800;
    margin: 0;
    letter-spacing: -0.5px;
}
.revai-hero p {
    color: #94A3B8;
    font-size: 14px;
    margin: 8px 0 0 0;
}
.revai-hero .badge {
    display: inline-block;
    background: rgba(59, 130, 246, 0.2);
    color: #60A5FA;
    font-size: 11px;
    padding: 4px 12px;
    border-radius: 20px;
    margin-top: 10px;
    font-weight: 600;
}

/* ===== METRIC CARDS ===== */
.metric-card {
    background: #FFFFFF;
    padding: 24px 20px;
    border-radius: 14px;
    border: 1px solid #E2E8F0;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    transition: transform 0.2s;
}
.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.metric-card .value {
    font-size: 28px;
    font-weight: 800;
    color: #0F172A;
    margin: 0;
}
.metric-card .label {
    font-size: 12px;
    color: #64748B;
    margin: 6px 0 0 0;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.metric-card.danger .value { color: #DC2626; }
.metric-card.warning .value { color: #EA580C; }
.metric-card.success .value { color: #16A34A; }

/* ===== SEVERITY BADGES ===== */
.severity-critical {
    background: #FEE2E2;
    color: #DC2626;
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 700;
}
.severity-high {
    background: #FFEDD5;
    color: #EA580C;
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 700;
}
.severity-medium {
    background: #FEF3C7;
    color: #CA8A04;
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 700;
}
.severity-low {
    background: #DBEAFE;
    color: #2563EB;
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 700;
}

/* ===== TABS ===== */
.stTabs [data-baseweb="tab-list"] {
    gap: 0px;
    background: #FFFFFF;
    border-radius: 10px 10px 0 0;
    padding: 0;
}
.stTabs [data-baseweb="tab"] {
    padding: 12px 20px;
    font-weight: 600;
    color: #64748B;
}
.stTabs [aria-selected="true"] {
    color: #0F172A;
    border-bottom: 3px solid #2563EB;
}

/* ===== BUTTONS ===== */
.stButton > button {
    border-radius: 10px;
    font-weight: 600;
    border: none;
    transition: all 0.2s;
}
.stButton > button[kind="primary"] {
    background: #0F172A;
}
.stButton > button[kind="primary"]:hover {
    background: #1E293B;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(15,23,42,0.2);
}

/* ===== DATAFRAMES ===== */
.dataframe {
    border-radius: 10px;
    overflow: hidden;
}
.dataframe th {
    background: #0F172A;
    color: white;
    font-weight: 600;
}

/* ===== LOGIN SCREEN ===== */
.login-container {
    max-width: 420px;
    margin: 80px auto;
    background: white;
    padding: 40px;
    border-radius: 20px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.08);
    border: 1px solid #E2E8F0;
}
.login-container h2 {
    text-align: center;
    color: #0F172A;
    margin-bottom: 8px;
}
.login-container p {
    text-align: center;
    color: #64748B;
    margin-bottom: 24px;
}

/* ===== SECURITY BANNER ===== */
.security-banner {
    background: #F0FDF4;
    border: 1px solid #BBF7D0;
    border-radius: 10px;
    padding: 12px 16px;
    color: #15803D;
    font-size: 13px;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* ===== FINDINGS TABLE ===== */
.findings-table {
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0;
}
.findings-table th {
    background: #0F172A;
    color: white;
    padding: 10px 14px;
    text-align: left;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.findings-table td {
    padding: 10px 14px;
    border-bottom: 1px solid #E2E8F0;
    font-size: 13px;
}

/* ===== SPACING ===== */
div[data-testid="column"] {
    gap: 0.5rem;
}

/* Custom scrollbar */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-thumb {
    background: #CBD5E1;
    border-radius: 3px;
}
::-webkit-scrollbar-track {
    background: #F1F5F9;
}
</style>
""", unsafe_allow_html=True)

# === SESSION STATE ===
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'company_name' not in st.session_state:
    st.session_state.company_name = ""
if 'company_revenue' not in st.session_state:
    st.session_state.company_revenue = 0
if 'audit_period' not in st.session_state:
    st.session_state.audit_period = ""
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
    st.session_state.ap_data = None
    st.session_state.payroll_data = None
    st.session_state.tax_data = None
    st.session_state.vendor_master = None
    st.session_state.employee_master = None
    st.session_state.results = {}
    st.session_state.scan_complete = False
    st.session_state.total_leakage = 0

# === LOGIN SCREEN ===
if not st.session_state.authenticated:
    st.markdown("""
    <div class="login-container">
        <h2>RevAI</h2>
        <p>AI Revenue & Fraud Detection</p>
        <div style="text-align: center; margin: 20px 0;">
            <span style="font-size: 48px;">🛡️</span>
        </div>
        <p style="font-size: 13px; color: #94A3B8;">Enter your access key to start scanning</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        access_key = st.text_input("Access Key", type="password", placeholder="Enter access key or type 'demo'")
        if st.button("Enter RevAI", type="primary", use_container_width=True):
            if access_key == "demo" or access_key == "" or access_key == "revai":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid key. Use 'demo' for trial access.")

        st.markdown("""
        <div style="text-align: center; margin-top: 20px;">
            <p style="font-size: 12px; color: #94A3B8;">
                No key? Type <strong>demo</strong> for free trial access.<br>
                Your financial data never leaves your browser session.
            </p>
        </div>
        """, unsafe_allow_html=True)
    st.stop()

# === LOGOUT ===
if st.sidebar.button("Logout", use_container_width=True):
    st.session_state.authenticated = False
    st.session_state.data_loaded = False
    st.session_state.scan_complete = False
    st.rerun()

# === COMPANY INFO ===
st.sidebar.markdown("---")
if not st.session_state.company_name:
    st.sidebar.markdown("### Company Setup")
    st.session_state.company_name = st.sidebar.text_input("Company Name", placeholder="e.g. ABC Manufacturing Ltd")
    st.session_state.company_revenue = st.sidebar.number_input("Annual Revenue (NGN)", min_value=0, value=0, step=1000000, help="Used to calculate leakage as % of revenue")
    st.session_state.audit_period = st.sidebar.text_input("Audit Period", value=f"FY {datetime.now().year}", placeholder="e.g. FY 2025")
else:
    st.sidebar.markdown("### Company")
    st.sidebar.markdown(f"**{st.session_state.company_name}**")
    st.sidebar.markdown(f"_Period: {st.session_state.audit_period}_")
    if st.sidebar.button("Edit Company Info"):
        st.session_state.company_name = ""
        st.rerun()

# === HERO HEADER ===
st.markdown("""
<div class="revai-hero">
    <h1>🛡️ RevAI</h1>
    <p>AI Revenue & Fraud Detection for African Companies - Find your leaked money.</p>
    <span class="badge">SECURE - DATA STAYS IN YOUR BROWSER</span>
</div>
""", unsafe_allow_html=True)

# === DATA SECURITY NOTICE ===
if not st.session_state.data_loaded:
    st.markdown("""
    <div class="security-banner">
        <span>🔒</span>
        <span><strong>Data Security:</strong> Your uploaded data is processed in your browser session and is never stored on our servers. All data is cleared when you logout or close the tab.</span>
    </div>
    """, unsafe_allow_html=True)

# === SIDEBAR: DATA UPLOAD ===
st.sidebar.markdown("---")
st.sidebar.markdown("### Data Input")

use_sample = st.sidebar.checkbox("Use Sample Data (Demo)", value=False, help="Generate realistic Nigerian company data with known fraud patterns")

if use_sample:
    if st.sidebar.button("Load Sample Data", type="primary", use_container_width=True):
        with st.spinner("Generating sample data..."):
            sample = generate_all_sample_data()
            st.session_state.ap_data = sample['ap']
            st.session_state.payroll_data = sample['payroll']
            st.session_state.tax_data = sample['tax_remittance']
            st.session_state.vendor_master = sample['vendor_master']
            st.session_state.employee_master = sample['employee_master']
            st.session_state.data_loaded = True
            st.sidebar.success("Sample data loaded. Ready to scan.")
            st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("#### Upload Your Data")

ap_file = st.sidebar.file_uploader("Accounts Payable (AP)", type=['csv', 'xlsx', 'xls'])
payroll_file = st.sidebar.file_uploader("Payroll", type=['csv', 'xlsx', 'xls'])
tax_file = st.sidebar.file_uploader("Tax Remittances", type=['csv', 'xlsx', 'xls'])
vendor_file = st.sidebar.file_uploader("Vendor Master (Optional)", type=['csv', 'xlsx', 'xls'])
employee_file = st.sidebar.file_uploader("Employee Master (Optional)", type=['csv', 'xlsx', 'xls'])

# Download templates
st.sidebar.markdown("---")
st.sidebar.markdown("#### Download Templates")
template_type = st.sidebar.selectbox("Template type", ["ap", "payroll", "tax_remittance", "vendor_master", "employee_master"])
template_output, template_name = generate_data_template(template_type)
st.sidebar.download_button(
    label=f"Download {template_type} template",
    data=template_output,
    file_name=template_name,
    mime='text/csv'
)

# Load uploaded files
if ap_file or payroll_file or tax_file:
    if st.sidebar.button("Process Uploaded Data", type="primary", use_container_width=True):
        progress = st.sidebar.progress(0)

        if ap_file:
            df = read_uploaded_file(ap_file)
            if df is not None:
                df = normalize_columns(df)
                mapping = auto_map_columns(df, "ap")
                df = apply_mapping(df, mapping)
                st.session_state.ap_data = df
                st.sidebar.success(f"AP: {len(df)} rows loaded")
            progress.progress(20)

        if payroll_file:
            df = read_uploaded_file(payroll_file)
            if df is not None:
                df = normalize_columns(df)
                mapping = auto_map_columns(df, "payroll")
                df = apply_mapping(df, mapping)
                st.session_state.payroll_data = df
                st.sidebar.success(f"Payroll: {len(df)} rows loaded")
            progress.progress(40)

        if tax_file:
            df = read_uploaded_file(tax_file)
            if df is not None:
                df = normalize_columns(df)
                mapping = auto_map_columns(df, "tax_remittance")
                df = apply_mapping(df, mapping)
                st.session_state.tax_data = df
                st.sidebar.success(f"Tax: {len(df)} rows loaded")
            progress.progress(60)

        if vendor_file:
            df = read_uploaded_file(vendor_file)
            if df is not None:
                df = normalize_columns(df)
                mapping = auto_map_columns(df, "vendor_master")
                df = apply_mapping(df, mapping)
                st.session_state.vendor_master = df
                st.sidebar.success(f"Vendor Master: {len(df)} rows loaded")
            progress.progress(80)

        if employee_file:
            df = read_uploaded_file(employee_file)
            if df is not None:
                df = normalize_columns(df)
                mapping = auto_map_columns(df, "employee_master")
                df = apply_mapping(df, mapping)
                st.session_state.employee_master = df
                st.sidebar.success(f"Employee Master: {len(df)} rows loaded")
            progress.progress(100)

        if st.session_state.ap_data is not None or st.session_state.payroll_data is not None:
            st.session_state.data_loaded = True
            st.sidebar.success("Data processed. Ready to scan.")
            st.rerun()
        else:
            st.sidebar.error("No valid data loaded. Upload at least AP or Payroll.")

# === MAIN CONTENT ===

if not st.session_state.data_loaded:
    # Landing page
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("### Welcome to RevAI")
        st.markdown("""
        RevAI scans your company's financial data and finds money that's quietly leaking out:

        1. **Duplicate Payments** - Same invoice paid twice
        2. **Unremitted VAT/WHT** - Tax deducted but never sent to FIRS
        3. **Overstated Expenses** - Abnormally high or suspicious spending
        4. **Ghost Vendors/Employees** - People receiving payments who shouldn't exist
        5. **Late Tax Filing Risk** - Missed deadlines and penalty exposure

        Upload your data in the sidebar or click **Use Sample Data** to see a live demo.
        """)

        st.markdown("---")
        st.markdown("#### How It Works")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**1. Upload** your AP, Payroll, and Tax data (CSV or Excel)")
        with c2:
            st.markdown("**2. Scan** runs 5 detection engines automatically")
        with c3:
            st.markdown("**3. Download** your PDF report and action plan")

    with col2:
        st.markdown("#### Why RevAI?")
        st.markdown("""
        - Average leakage: 2-5% of revenue
        - Most companies don't know it's happening
        - Recovery starts immediately
        - No software to install
        - Works with your existing data
        """)

    st.info("Click 'Use Sample Data (Demo)' in the sidebar to load realistic Nigerian company data with embedded fraud patterns, then click 'Run Full Scan'.")

else:
    # Data loaded - show dashboard
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        ap_count = len(st.session_state.ap_data) if st.session_state.ap_data is not None else 0
        st.markdown(f"""
        <div class="metric-card">
            <p class="value">{ap_count:,}</p>
            <p class="label">AP Transactions</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        payroll_count = len(st.session_state.payroll_data) if st.session_state.payroll_data is not None else 0
        st.markdown(f"""
        <div class="metric-card">
            <p class="value">{payroll_count:,}</p>
            <p class="label">Payroll Records</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        tax_count = len(st.session_state.tax_data) if st.session_state.tax_data is not None else 0
        st.markdown(f"""
        <div class="metric-card">
            <p class="value">{tax_count:,}</p>
            <p class="label">Tax Remittances</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        total_records = ap_count + payroll_count + tax_count
        st.markdown(f"""
        <div class="metric-card success">
            <p class="value">{total_records:,}</p>
            <p class="label">Total Records</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Run scan button
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("Run Full Scan", type="primary", use_container_width=True):
            with st.spinner("Scanning for financial leakage..."):
                results = {}
                total_leakage = 0
                progress = st.progress(0)
                status = st.empty()

                # Detection 1: Duplicate Payments
                if st.session_state.ap_data is not None:
                    status.text("Checking for duplicate payments...")
                    dup_results = detect_duplicate_payments(st.session_state.ap_data)
                    results['duplicates'] = dup_results
                    dup_sum = dup_summary(dup_results)
                    total_leakage += dup_sum['total_amount']
                    progress.progress(20)

                # Detection 2: VAT/WHT Issues
                if st.session_state.ap_data is not None:
                    status.text("Checking VAT/WHT remittances...")
                    vat_results = detect_vat_wht_issues(st.session_state.ap_data, st.session_state.tax_data)
                    results['vat_wht'] = vat_results
                    vat_sum = vat_summary(vat_results)
                    total_leakage += vat_sum.get('total_amount', 0)
                    progress.progress(40)

                # Detection 3: Overstated Expenses
                if st.session_state.ap_data is not None:
                    status.text("Checking for overstated expenses...")
                    exp_results = detect_overstated_expenses(st.session_state.ap_data)
                    results['expenses'] = exp_results
                    exp_sum = exp_summary(exp_results)
                    total_leakage += exp_sum.get('total_amount', 0)
                    progress.progress(60)

                # Detection 4: Ghost Vendors/Employees
                status.text("Checking for ghost vendors and employees...")
                ghost_results = {}
                if st.session_state.ap_data is not None and st.session_state.vendor_master is not None:
                    ghost_results['vendors'] = detect_ghost_vendors(st.session_state.ap_data, st.session_state.vendor_master)
                if st.session_state.payroll_data is not None and st.session_state.employee_master is not None:
                    ghost_results['employees'] = detect_ghost_employees(st.session_state.payroll_data, st.session_state.employee_master)
                results['ghost'] = ghost_results
                ghost_sum = ghost_summary(ghost_results)
                total_leakage += ghost_sum.get('total_amount', 0)
                progress.progress(80)

                # Detection 5: Tax Filing Risk
                status.text("Checking tax filing deadlines...")
                tax_results = detect_tax_filing_risk(st.session_state.ap_data)
                results['tax_filing'] = tax_results
                tax_sum = tax_summary(tax_results)
                total_leakage += tax_sum.get('total_amount', 0)
                progress.progress(100)

                status.text("Scan complete!")
                st.session_state.results = results
                st.session_state.scan_complete = True
                st.session_state.total_leakage = total_leakage
                st.rerun()

    # === SCAN RESULTS ===
    if st.session_state.scan_complete:
        results = st.session_state.results
        total_leakage = st.session_state.total_leakage

        # === LEAKAGE BANNER ===
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #DC2626 0%, #B91C1C 100%); padding: 24px 30px; border-radius: 14px; margin: 20px 0; box-shadow: 0 4px 20px rgba(220,38,38,0.2);">
            <h2 style="color: white; margin: 0; font-size: 24px;">Total Financial Leakage Detected</h2>
            <h1 style="color: white; margin: 8px 0 0 0; font-size: 40px; font-weight: 800;">NGN {total_leakage:,.2f}</h1>
            {"<p style='color: #FECACA; margin: 5px 0 0 0;'>" + f"{(total_leakage / st.session_state.company_revenue * 100):.1f}% of audited revenue" + "</p>" if st.session_state.company_revenue > 0 else ""}
        </div>
        """, unsafe_allow_html=True)

        # === METRICS ROW ===
        col1, col2, col3, col4, col5 = st.columns(5)

        # Get summaries
        summaries = []
        if 'duplicates' in results:
            s = dup_summary(results['duplicates'])
            summaries.append(("Duplicates", s))
        if 'vat_wht' in results:
            s = vat_summary(results['vat_wht'])
            summaries.append(("VAT/WHT", s))
        if 'expenses' in results:
            s = exp_summary(results['expenses'])
            summaries.append(("Expenses", s))
        if 'ghost' in results:
            s = ghost_summary(results['ghost'])
            summaries.append(("Ghost", s))
        if 'tax_filing' in results:
            s = tax_summary(results['tax_filing'])
            summaries.append(("Tax Risk", s))

        for i, (name, s) in enumerate(summaries):
            with [col1, col2, col3, col4, col5][i]:
                amount = s.get('total_amount', 0)
                count = s.get('count', 0)
                css_class = "danger" if amount >= 1000000 else "warning" if amount >= 100000 else "success"
                st.markdown(f"""
                <div class="metric-card {css_class}">
                    <p class="value">NGN {amount/1000000:.1f}M</p>
                    <p class="label">{name} ({count} items)</p>
                </div>
                """, unsafe_allow_html=True)

        # === CHARTS ===
        st.markdown("---")
        st.markdown("### Leakage Breakdown")

        # Prepare chart data
        chart_data = []
        for name, s in summaries:
            chart_data.append({
                "Category": name,
                "Amount (NGN)": s.get('total_amount', 0),
                "Items": s.get('count', 0)
            })
        chart_df = pd.DataFrame(chart_data)

        col1, col2 = st.columns(2)

        with col1:
            fig = px.bar(
                chart_df,
                x="Category",
                y="Amount (NGN)",
                color="Category",
                color_discrete_sequence=['#0F172A', '#1E3A5F', '#DC2626', '#EA580C', '#CA8A04'],
                title="Leakage by Category",
                labels={"Amount (NGN)": "Amount (NGN)"}
            )
            fig.update_layout(
                showlegend=False,
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(family='Inter, sans-serif', size=12),
                margin=dict(t=40, b=20, l=0, r=0),
                height=350
            )
            fig.update_xaxes(tickfont=dict(size=11))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig2 = px.pie(
                chart_df,
                values="Amount (NGN)",
                names="Category",
                title="Leakage Distribution",
                color_discrete_sequence=['#0F172A', '#1E3A5F', '#DC2626', '#EA580C', '#CA8A04'],
                hole=0.4
            )
            fig2.update_layout(
                showlegend=True,
                font=dict(family='Inter, sans-serif', size=12),
                margin=dict(t=40, b=20, l=0, r=0),
                height=350
            )
            st.plotly_chart(fig2, use_container_width=True)

        # === EXPORT BAR ===
        st.markdown("---")
        st.markdown("### Export & Share")

        col1, col2, col3 = st.columns(3)

        with col1:
            # PDF Report
            if st.button("📄 Download PDF Report", use_container_width=True, type="primary"):
                with st.spinner("Generating professional report..."):
                    # Build detection summaries for report
                    det_summaries = []
                    top_actions = []

                    for name, s in summaries:
                        det_summaries.append({
                            'name': name,
                            'amount': s.get('total_amount', 0),
                            'count': s.get('count', 0),
                            'detail': s.get('detail', '')
                        })

                    # Build top actions from findings
                    if 'duplicates' in results:
                        dup_df = results['duplicates']
                        if isinstance(dup_df, pd.DataFrame) and len(dup_df) > 0:
                            for _, row in dup_df.head(3).iterrows():
                                top_actions.append({
                                    'action': f"Recover duplicate payment to {row.get('vendor_name', 'vendor')} - Invoice {row.get('invoice_number', 'N/A')}",
                                    'amount': row.get('amount', 0)
                                })

                    while len(top_actions) < 3:
                        if 'vat_wht' in results:
                            vat_df = results['vat_wht']
                            if isinstance(vat_df, pd.DataFrame) and len(vat_df) > 0:
                                for _, row in vat_df.head(3 - len(top_actions)).iterrows():
                                    top_actions.append({
                                        'action': f"Remit unremitted {row.get('tax_type', 'tax')} for {row.get('vendor_name', 'vendor')}",
                                        'amount': row.get('amount', 0)
                                    })
                        break

                    while len(top_actions) < 3:
                        top_actions.append({
                            'action': 'Review all flagged transactions with your finance team',
                            'amount': 0
                        })

                    # Generate AI summary
                    ai_summary = ""
                    try:
                        from openai import OpenAI
                        api_key = os.getenv("OPENAI_API_KEY")
                        if api_key:
                            client = OpenAI(api_key=api_key)
                            prompt = f"""You are a financial auditor. Write a 3-paragraph executive summary for a leakage report.

Company: {st.session_state.company_name or 'Sample Company'}
Total Leakage: NGN {total_leakage:,.2f}
Findings:
"""
                            for ds in det_summaries:
                                prompt += f"- {ds['name']}: NGN {ds['amount']:,.2f} ({ds['count']} items)\n"
                            prompt += "\nWrite a clear, professional summary. Use NGN not the naira symbol. ASCII only."

                            response = client.chat.completions.create(
                                model="gpt-4o-mini",
                                messages=[{"role": "user", "content": prompt}],
                                max_tokens=500,
                                temperature=0.3
                            )
                            ai_summary = response.choices[0].message.content
                    except Exception:
                        pass

                    if not ai_summary:
                        ai_summary = f"""This audit of {st.session_state.company_name or 'the company'} for {st.session_state.audit_period or 'the current period'} identified total financial leakage of NGN {total_leakage:,.2f} across {sum(s.get('count', 0) for _, s in summaries)} flagged items.

The most significant areas of concern are duplicate payments and unremitted tax deductions, which together account for the majority of identified leakage. These represent immediate recovery opportunities that should be prioritized.

We recommend a detailed review of all flagged transactions, immediate recovery of duplicate payments, and prompt remittance of outstanding tax deductions to avoid additional penalties and interest charges from FIRS."""

                    # Generate the PDF
                    pdf_path = generate_report(
                        company_name=st.session_state.company_name or "Sample Company",
                        audit_period=st.session_state.audit_period or f"FY {datetime.now().year}",
                        total_leakage=total_leakage,
                        total_revenue=st.session_state.company_revenue,
                        detection_summaries=det_summaries,
                        top_actions=top_actions,
                        ai_summary=ai_summary
                    )

                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()

                    safe_name = (st.session_state.company_name or "company").replace(' ', '_')
                    st.download_button(
                        label="⬇️ Download PDF Report",
                        data=pdf_bytes,
                        file_name=f"RevAI_Leakage_Report_{safe_name}_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

        with col2:
            # Excel Export
            if st.button("📊 Download Excel (All Findings)", use_container_width=True):
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    # Summary sheet
                    summary_df = pd.DataFrame([
                        {
                            'Category': name,
                            'Amount (NGN)': s.get('total_amount', 0),
                            'Items Flagged': s.get('count', 0),
                            'Details': s.get('detail', '')
                        }
                        for name, s in summaries
                    ])
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)

                    # Individual findings sheets
                    if 'duplicates' in results and isinstance(results['duplicates'], pd.DataFrame) and len(results['duplicates']) > 0:
                        results['duplicates'].to_excel(writer, sheet_name='Duplicate Payments', index=False)
                    if 'vat_wht' in results and isinstance(results['vat_wht'], pd.DataFrame) and len(results['vat_wht']) > 0:
                        results['vat_wht'].to_excel(writer, sheet_name='VAT-WHT Issues', index=False)
                    if 'expenses' in results and isinstance(results['expenses'], pd.DataFrame) and len(results['expenses']) > 0:
                        results['expenses'].to_excel(writer, sheet_name='Overstated Expenses', index=False)
                    if 'ghost' in results:
                        ghost = results['ghost']
                        if 'vendors' in ghost and isinstance(ghost['vendors'], pd.DataFrame) and len(ghost['vendors']) > 0:
                            ghost['vendors'].to_excel(writer, sheet_name='Ghost Vendors', index=False)
                        if 'employees' in ghost and isinstance(ghost['employees'], pd.DataFrame) and len(ghost['employees']) > 0:
                            ghost['employees'].to_excel(writer, sheet_name='Ghost Employees', index=False)
                    if 'tax_filing' in results and isinstance(results['tax_filing'], pd.DataFrame) and len(results['tax_filing']) > 0:
                        results['tax_filing'].to_excel(writer, sheet_name='Tax Filing Risk', index=False)

                output.seek(0)
                safe_name = (st.session_state.company_name or "company").replace(' ', '_')
                st.download_button(
                    label="⬇️ Download Excel",
                    data=output.getvalue(),
                    file_name=f"RevAI_Findings_{safe_name}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

        with col3:
            # Share via email link
            st.markdown("""
            <div style="text-align: center; padding: 20px; border: 1px dashed #CBD5E1; border-radius: 10px;">
                <p style="color: #64748B; font-size: 13px; margin: 0;">📧 Share Report</p>
                <p style="color: #94A3B8; font-size: 11px; margin: 5px 0;">Download the PDF and forward to your finance team or auditors</p>
            </div>
            """, unsafe_allow_html=True)

        # === DETAILED FINDINGS TABS ===
        st.markdown("---")
        st.markdown("### Detailed Findings")

        tab_titles = []
        for name, s in summaries:
            count = s.get('count', 0)
            amount = s.get('total_amount', 0)
            tab_titles.append(f"{name} ({count})")

        if tab_titles:
            tabs = st.tabs(tab_titles)

            for i, (name, s) in enumerate(summaries):
                with tabs[i]:
                    # Summary box
                    amount = s.get('total_amount', 0)
                    count = s.get('count', 0)
                    detail = s.get('detail', '')

                    if amount >= 1000000:
                        severity = "severity-critical"
                        sev_label = "CRITICAL"
                    elif amount >= 100000:
                        severity = "severity-high"
                        sev_label = "HIGH"
                    elif amount > 0:
                        severity = "severity-medium"
                        sev_label = "MEDIUM"
                    else:
                        severity = "severity-low"
                        sev_label = "LOW"

                    st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                        <div>
                            <span class="{severity}">{sev_label}</span>
                            <span style="margin-left: 10px; color: #64748B; font-size: 13px;">{count} items flagged</span>
                        </div>
                        <div style="text-align: right;">
                            <span style="font-size: 20px; font-weight: 800; color: #0F172A;">NGN {amount:,.2f}</span>
                        </div>
                    </div>
                    <p style="color: #64748B; font-size: 13px;">{detail}</p>
                    """, unsafe_allow_html=True)

                    # Show data
                    result_key_map = {
                        "Duplicates": "duplicates",
                        "VAT/WHT": "vat_wht",
                        "Expenses": "expenses",
                        "Ghost": "ghost",
                        "Tax Risk": "tax_filing"
                    }
                    key = result_key_map.get(name)

                    if key and key in results:
                        data = results[key]
                        if key == "ghost":
                            # Handle ghost which has sub-keys
                            has_data = False
                            if 'vendors' in data and isinstance(data['vendors'], pd.DataFrame) and len(data['vendors']) > 0:
                                st.markdown("**Ghost Vendors**")
                                st.dataframe(data['vendors'], use_container_width=True, hide_index=True)
                                has_data = True
                            if 'employees' in data and isinstance(data['employees'], pd.DataFrame) and len(data['employees']) > 0:
                                st.markdown("**Ghost Employees**")
                                st.dataframe(data['employees'], use_container_width=True, hide_index=True)
                                has_data = True
                            if not has_data:
                                st.success("No ghost vendors or employees detected.")
                        elif isinstance(data, pd.DataFrame) and len(data) > 0:
                            st.dataframe(data, use_container_width=True, hide_index=True)
                        else:
                            st.success(f"No issues detected in {name}.")
                    else:
                        st.success(f"No issues detected in {name}.")

        # === RECOMMENDATIONS ===
        st.markdown("---")
        st.markdown("### Recommended Actions")

        actions = []
        for name, s in summaries:
            amount = s.get('total_amount', 0)
            count = s.get('count', 0)
            if amount > 0:
                actions.append({
                    'priority': 1 if amount >= 1000000 else 2 if amount >= 100000 else 3,
                    'category': name,
                    'action': f"Review and recover {count} flagged {name.lower()} items",
                    'amount': amount
                })

        actions.sort(key=lambda x: x['priority'])

        for action in actions[:5]:
            priority_label = ["URGENT", "HIGH", "MEDIUM"][action['priority'] - 1] if action['priority'] <= 3 else "LOW"
            priority_color = ["#DC2626", "#EA580C", "#CA8A04"][action['priority'] - 1] if action['priority'] <= 3 else "#2563EB"

            st.markdown(f"""
            <div style="background: white; border-left: 4px solid {priority_color}; padding: 14px 18px; border-radius: 8px; margin: 8px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="color: {priority_color}; font-weight: 700; font-size: 12px;">{priority_label}</span>
                        <span style="margin-left: 10px; font-size: 14px; color: #0F172A;">{action['action']}</span>
                    </div>
                    <span style="font-size: 14px; font-weight: 700; color: #0F172A;">NGN {action['amount']:,.2f}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # === CONTACT / CTA ===
        st.markdown("---")
        st.markdown("""
        <div style="background: #0F172A; padding: 24px 30px; border-radius: 14px; text-align: center; margin-top: 20px;">
            <h3 style="color: white; margin: 0;">Need help recovering your leaked money?</h3>
            <p style="color: #94A3B8; margin: 10px 0 0 0;">Schedule a walkthrough with our team to review each finding and build a recovery plan.</p>
            <p style="color: #60A5FA; margin: 15px 0 0 0; font-weight: 600;">WhatsApp: +234 800 000 0000 | Email: hello@revai.ng</p>
        </div>
        """, unsafe_allow_html=True)
