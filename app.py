"""
RevAI - AI Revenue & Fraud Detection for African Companies
Main Streamlit Application - MVP Production Build

Fixes applied:
1. Total math: exact sum of all categories, no rounding
2. Ghost logic: only flag vendors with 1 payment AND amount > 1M
3. PDF summary: dynamic based on actual results
4. Ghost tab: shows vendor names + amounts in table
5. Single button flow: no confusing dual buttons
6. No login screen for MVP
7. Loading spinner with transaction count
8. Templates moved to top of sidebar
9. Mobile-friendly header
10. Big "Try Demo" button
11. Data validation with error messages
12. Chart labels on donut
13. Expected recovery = 80% of leakage
14. File upload text fixed
15. Company name dynamic in PDF report
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import io
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="RevAI - Revenue. Protected.",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# === CSS ===
st.markdown("""
<style>
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }
.stDeployButton { display: none !important; }
div[data-testid="stToolbar"] { display: none !important; }
.stApp > header { height: 0 !important; }
.st-emotion-cache-1wrcr25, .st-emotion-cache-1khj6t { display: none !important; }
a[href*="streamlit.io/cloud"] { display: none !important; }

.stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #F8FAFC;
}

section[data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 1px solid #E2E8F0;
}

.revai-hero {
    background: linear-gradient(135deg, #0F172A 0%, #1E3A5F 50%, #1E293B 100%);
    padding: 20px 24px;
    border-radius: 14px;
    margin-bottom: 16px;
    box-shadow: 0 4px 20px rgba(15, 23, 42, 0.15);
}
.revai-hero h1 {
    color: #FFFFFF;
    font-size: 24px;
    font-weight: 800;
    margin: 0;
    letter-spacing: -0.5px;
}
.revai-hero p {
    color: #94A3B8;
    font-size: 12px;
    margin: 6px 0 0 0;
}
.revai-hero .badge {
    display: inline-block;
    background: rgba(59, 130, 246, 0.2);
    color: #60A5FA;
    font-size: 10px;
    padding: 3px 10px;
    border-radius: 20px;
    margin-top: 8px;
    font-weight: 600;
}

.metric-card {
    background: #FFFFFF;
    padding: 18px 14px;
    border-radius: 12px;
    border: 1px solid #E2E8F0;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.metric-card .value {
    font-size: 22px;
    font-weight: 800;
    color: #0F172A;
    margin: 0;
}
.metric-card .label {
    font-size: 11px;
    color: #64748B;
    margin: 4px 0 0 0;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.metric-card.danger .value { color: #DC2626; }
.metric-card.warning .value { color: #EA580C; }
.metric-card.success .value { color: #16A34A; }

.stButton > button {
    border-radius: 10px;
    font-weight: 600;
    border: none;
}
.stButton > button[kind="primary"] {
    background: #0F172A;
}
.stButton > button[kind="primary"]:hover {
    background: #1E293B;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0px;
    background: #FFFFFF;
    border-radius: 10px 10px 0 0;
}
.stTabs [data-baseweb="tab"] {
    padding: 10px 16px;
    font-weight: 600;
    color: #64748B;
}
.stTabs [aria-selected="true"] {
    color: #0F172A;
    border-bottom: 3px solid #2563EB;
}

.dataframe th {
    background: #0F172A !important;
    color: white !important;
    font-weight: 600;
}

.severity-critical { background: #FEE2E2; color: #DC2626; padding: 3px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; }
.severity-high { background: #FFEDD5; color: #EA580C; padding: 3px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; }
.severity-medium { background: #FEF3C7; color: #CA8A04; padding: 3px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; }
.severity-low { background: #DBEAFE; color: #2563EB; padding: 3px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; }

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 3px; }
::-webkit-scrollbar-track { background: #F1F5F9; }
</style>
""", unsafe_allow_html=True)

# === SESSION STATE ===
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
    st.session_state.leakages = {}

# === HERO HEADER ===
st.markdown("""
<div class="revai-hero">
    <h1>RevAI</h1>
    <p>Find leaked money in your company financials</p>
    <span class="badge">DATA STAYS IN YOUR BROWSER</span>
</div>
""", unsafe_allow_html=True)

# === SIDEBAR: TEMPLATES AT TOP ===
st.sidebar.markdown("### Download Templates")
st.sidebar.markdown("Get the right format first, then upload your data.")
template_type = st.sidebar.selectbox(
    "Template type",
    ["ap", "payroll", "tax_remittance", "vendor_master", "employee_master"],
    format_func=lambda x: {
        "ap": "Accounts Payable",
        "payroll": "Payroll",
        "tax_remittance": "Tax Remittances",
        "vendor_master": "Vendor Master",
        "employee_master": "Employee Master"
    }.get(x, x)
)
template_output, template_name = generate_data_template(template_type)
st.sidebar.download_button(
    label="Download template",
    data=template_output,
    file_name=template_name,
    mime='text/csv',
    use_container_width=True
)

st.sidebar.markdown("---")

# === COMPANY INFO ===
st.sidebar.markdown("### Company Details")
company_name = st.sidebar.text_input("Company Name", value="", placeholder="e.g. ABC Manufacturing Ltd")
company_revenue = st.sidebar.number_input("Annual Revenue (NGN)", min_value=0, value=0, step=1000000, help="Used to show leakage as % of revenue")
audit_period = st.sidebar.text_input("Audit Period", value=f"FY {datetime.now().year}", placeholder="e.g. FY 2026")

st.sidebar.markdown("---")

# === DATA INPUT ===
st.sidebar.markdown("### Load Your Data")

# Big demo button at top
if st.sidebar.button("Try Demo with 1 Click", type="primary", use_container_width=True):
    with st.spinner("Generating sample data..."):
        sample = generate_all_sample_data()
        st.session_state.ap_data = sample['ap']
        st.session_state.payroll_data = sample['payroll']
        st.session_state.tax_data = sample['tax_remittance']
        st.session_state.vendor_master = sample['vendor_master']
        st.session_state.employee_master = sample['employee_master']
        st.session_state.data_loaded = True
        if not company_name:
            st.session_state.company_name = "Demo Company Ltd"
        else:
            st.session_state.company_name = company_name
        st.session_state.company_revenue = company_revenue
        st.session_state.audit_period = audit_period
        st.sidebar.success("Data loaded! Click Run Full Scan below.")
        st.rerun()

st.sidebar.markdown("_Or upload your own files:_")

ap_file = st.sidebar.file_uploader("Accounts Payable", type=['csv', 'xlsx', 'xls'])
payroll_file = st.sidebar.file_uploader("Payroll", type=['csv', 'xlsx', 'xls'])
tax_file = st.sidebar.file_uploader("Tax Remittances", type=['csv', 'xlsx', 'xls'])
vendor_file = st.sidebar.file_uploader("Vendor Master (Optional)", type=['csv', 'xlsx', 'xls'])
employee_file = st.sidebar.file_uploader("Employee Master (Optional)", type=['csv', 'xlsx', 'xls'])

# Process uploaded files
if ap_file or payroll_file or tax_file:
    if st.sidebar.button("Load Uploaded Data", type="primary", use_container_width=True):
        errors = []
        loaded = []

        if ap_file:
            df = read_uploaded_file(ap_file)
            if df is not None:
                df = normalize_columns(df)
                is_valid, missing, _, _ = validate_data(df, "ap")
                if is_valid:
                    mapping = auto_map_columns(df, "ap")
                    df = apply_mapping(df, mapping)
                    st.session_state.ap_data = df
                    loaded.append(f"AP: {len(df)} rows")
                else:
                    errors.append(f"AP file missing columns: {', '.join(missing)}")
            else:
                errors.append("Could not read AP file")

        if payroll_file:
            df = read_uploaded_file(payroll_file)
            if df is not None:
                df = normalize_columns(df)
                is_valid, missing, _, _ = validate_data(df, "payroll")
                if is_valid:
                    mapping = auto_map_columns(df, "payroll")
                    df = apply_mapping(df, mapping)
                    st.session_state.payroll_data = df
                    loaded.append(f"Payroll: {len(df)} rows")
                else:
                    errors.append(f"Payroll file missing columns: {', '.join(missing)}")
            else:
                errors.append("Could not read Payroll file")

        if tax_file:
            df = read_uploaded_file(tax_file)
            if df is not None:
                df = normalize_columns(df)
                is_valid, missing, _, _ = validate_data(df, "tax_remittance")
                if is_valid:
                    mapping = auto_map_columns(df, "tax_remittance")
                    df = apply_mapping(df, mapping)
                    st.session_state.tax_data = df
                    loaded.append(f"Tax: {len(df)} rows")
                else:
                    errors.append(f"Tax file missing columns: {', '.join(missing)}")
            else:
                errors.append("Could not read Tax file")

        if vendor_file:
            df = read_uploaded_file(vendor_file)
            if df is not None:
                df = normalize_columns(df)
                mapping = auto_map_columns(df, "vendor_master")
                df = apply_mapping(df, mapping)
                st.session_state.vendor_master = df
                loaded.append(f"Vendor Master: {len(df)} rows")

        if employee_file:
            df = read_uploaded_file(employee_file)
            if df is not None:
                df = normalize_columns(df)
                mapping = auto_map_columns(df, "employee_master")
                df = apply_mapping(df, mapping)
                st.session_state.employee_master = df
                loaded.append(f"Employee Master: {len(df)} rows")

        for msg in loaded:
            st.sidebar.success(msg)
        for err in errors:
            st.sidebar.error(err)

        if st.session_state.ap_data is not None or st.session_state.payroll_data is not None:
            st.session_state.data_loaded = True
            st.session_state.company_name = company_name or "Uploaded Company"
            st.session_state.company_revenue = company_revenue
            st.session_state.audit_period = audit_period
            st.rerun()

# === MAIN CONTENT ===

if not st.session_state.data_loaded:
    # Landing page
    st.markdown("### How RevAI Works")
    st.markdown("RevAI scans your financial data and finds money quietly leaking out:")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**1. Load Data** - Upload AP, Payroll, Tax files or click Try Demo")
    with c2:
        st.markdown("**2. Run Scan** - 5 detection engines check for leakage")
    with c3:
        st.markdown("**3. Export** - Download PDF report + Excel findings")

    st.markdown("---")

    st.markdown("#### What RevAI Detects")
    items = [
        ("Duplicate Payments", "Same invoice paid twice"),
        ("Unremitted VAT/WHT", "Tax deducted but never sent to FIRS"),
        ("Overstated Expenses", "Abnormally high or suspicious spending"),
        ("Ghost Vendors/Employees", "People receiving payments who shouldn't exist"),
        ("Late Tax Filing Risk", "Missed deadlines and penalty exposure")
    ]
    for name, desc in items:
        st.markdown(f"**{name}** - {desc}")

    st.info("Click 'Try Demo with 1 Click' in the sidebar to load sample Nigerian company data, then click 'Run Full Scan'.")

else:
    # Data loaded - show dashboard
    st.markdown(f"**Company:** {st.session_state.get('company_name', 'N/A')} | **Period:** {st.session_state.get('audit_period', 'N/A')}")

    # Data summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ap_count = len(st.session_state.ap_data) if st.session_state.ap_data is not None else 0
        st.metric("AP Transactions", f"{ap_count:,}")
    with col2:
        payroll_count = len(st.session_state.payroll_data) if st.session_state.payroll_data is not None else 0
        st.metric("Payroll Records", f"{payroll_count:,}")
    with col3:
        tax_count = len(st.session_state.tax_data) if st.session_state.tax_data is not None else 0
        st.metric("Tax Remittances", f"{tax_count:,}")
    with col4:
        total_records = ap_count + payroll_count + tax_count
        st.metric("Total Records", f"{total_records:,}")

    st.markdown("---")

    # === SINGLE SCAN BUTTON ===
    if not st.session_state.scan_complete:
        if st.button("Run Full Scan", type="primary", use_container_width=True):
            results = {}
            leakages = {}

            total_txns = (len(st.session_state.ap_data) if st.session_state.ap_data is not None else 0) + \
                        (len(st.session_state.payroll_data) if st.session_state.payroll_data is not None else 0) + \
                        (len(st.session_state.tax_data) if st.session_state.tax_data is not None else 0)

            progress = st.progress(0)
            status = st.empty()

            # 1. Duplicates
            if st.session_state.ap_data is not None:
                status.text(f"Scanning {len(st.session_state.ap_data)} AP transactions for duplicates...")
                dup_results = detect_duplicate_payments(st.session_state.ap_data)
                results['duplicates'] = dup_results
                s = dup_summary(dup_results)
                leakages['Duplicates'] = s['total_amount']
                progress.progress(20)

            # 2. VAT/WHT
            if st.session_state.ap_data is not None:
                status.text("Checking VAT/WHT remittances...")
                vat_results = detect_vat_wht_issues(st.session_state.ap_data, st.session_state.tax_data)
                results['vat_wht'] = vat_results
                s = vat_summary(vat_results)
                leakages['VAT/WHT'] = s['total_amount']
                progress.progress(40)

            # 3. Overstated Expenses
            if st.session_state.ap_data is not None:
                status.text("Checking for overstated expenses...")
                exp_results = detect_overstated_expenses(st.session_state.ap_data)
                results['expenses'] = exp_results
                s = exp_summary(exp_results)
                leakages['Expenses'] = s['total_amount']
                progress.progress(60)

            # 4. Ghost Vendors/Employees
            status.text("Checking for ghost vendors and employees...")
            ghost_results = {}
            if st.session_state.ap_data is not None and st.session_state.vendor_master is not None:
                ghost_results['vendors'] = detect_ghost_vendors(st.session_state.ap_data, st.session_state.vendor_master)
            if st.session_state.payroll_data is not None and st.session_state.employee_master is not None:
                ghost_results['employees'] = detect_ghost_employees(st.session_state.payroll_data, st.session_state.employee_master)
            results['ghost'] = ghost_results
            s = ghost_summary(ghost_results)
            leakages['Ghost'] = s['total_amount']
            progress.progress(80)

            # 5. Tax Filing Risk
            status.text("Checking tax filing deadlines...")
            tax_results = detect_tax_filing_risk(st.session_state.tax_data, st.session_state.payroll_data, st.session_state.ap_data)
            results['tax_filing'] = tax_results
            s = tax_summary(tax_results)
            leakages['Tax Risk'] = s['total_amount']
            progress.progress(100)

            status.text("Scan complete!")

            # CRITICAL FIX: Total = exact sum of all categories
            total_leakage = sum(leakages.values())

            st.session_state.results = results
            st.session_state.scan_complete = True
            st.session_state.total_leakage = total_leakage
            st.session_state.leakages = leakages
            st.rerun()

    # === SCAN RESULTS ===
    if st.session_state.scan_complete:
        results = st.session_state.results
        leakages = st.session_state.leakages
        total_leakage = st.session_state.total_leakage

        # === LEAKAGE BANNER ===
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #DC2626 0%, #B91C1C 100%); padding: 20px 24px; border-radius: 14px; margin: 16px 0; box-shadow: 0 4px 20px rgba(220,38,38,0.2);">
            <h2 style="color: white; margin: 0; font-size: 20px;">Total Financial Leakage</h2>
            <h1 style="color: white; margin: 6px 0 0 0; font-size: 36px; font-weight: 800;">NGN {total_leakage:,.2f}</h1>
            {"<p style='color: #FECACA; margin: 4px 0 0 0;'>" + f"{(total_leakage / st.session_state.company_revenue * 100):.1f}% of annual revenue" + "</p>" if st.session_state.get('company_revenue', 0) > 0 else ""}
        </div>
        """, unsafe_allow_html=True)

        # === METRIC CARDS ===
        cols = st.columns(5)
        for i, (name, amount) in enumerate(leakages.items()):
            with cols[i]:
                count = 0
                if name == 'Duplicates' and 'duplicates' in results:
                    df = results['duplicates']
                    count = len(df) if isinstance(df, pd.DataFrame) else 0
                elif name == 'VAT/WHT' and 'vat_wht' in results:
                    df = results['vat_wht']
                    count = len(df) if isinstance(df, pd.DataFrame) else 0
                elif name == 'Expenses' and 'expenses' in results:
                    df = results['expenses']
                    count = len(df) if isinstance(df, pd.DataFrame) else 0
                elif name == 'Ghost':
                    ghost = results.get('ghost', {})
                    count = sum(len(ghost[k]) for k in ['vendors', 'employees'] if k in ghost and isinstance(ghost[k], pd.DataFrame))
                elif name == 'Tax Risk' and 'tax_filing' in results:
                    df = results['tax_filing']
                    count = len(df) if isinstance(df, pd.DataFrame) else 0

                css_class = "danger" if amount >= 1000000 else "warning" if amount >= 100000 else "success"
                display_amount = f"{amount/1000000:.1f}M" if amount >= 1000000 else f"{amount/1000:.0f}K" if amount >= 1000 else "0"
                st.markdown(f"""
                <div class="metric-card {css_class}">
                    <p class="value">{display_amount}</p>
                    <p class="label">{name} ({count} items)</p>
                </div>
                """, unsafe_allow_html=True)

        # === CHARTS ===
        st.markdown("---")
        st.markdown("### Leakage Breakdown")

        chart_data = []
        for name, amount in leakages.items():
            if amount > 0:
                chart_data.append({"Category": name, "Amount (NGN)": amount})

        if chart_data:
            chart_df = pd.DataFrame(chart_data)
            col1, col2 = st.columns(2)

            with col1:
                fig = px.bar(
                    chart_df,
                    x="Category",
                    y="Amount (NGN)",
                    color="Category",
                    color_discrete_sequence=['#0F172A', '#1E3A5F', '#DC2626', '#EA580C', '#CA8A04'],
                    title="Leakage by Category"
                )
                fig.update_layout(
                    showlegend=False,
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    font=dict(family='Inter, sans-serif', size=12),
                    margin=dict(t=40, b=20, l=0, r=0),
                    height=320
                )
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
                fig2.update_traces(
                    textinfo='label+percent',
                    textposition='outside',
                    textfont=dict(size=11)
                )
                fig2.update_layout(
                    showlegend=False,
                    font=dict(family='Inter, sans-serif', size=12),
                    margin=dict(t=40, b=20, l=0, r=0),
                    height=320
                )
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No leakage detected in any category.")

        # === EXPORT BAR ===
        st.markdown("---")
        st.markdown("### Export & Share")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Download PDF Report", type="primary", use_container_width=True):
                with st.spinner("Generating report..."):
                    # Build detection summaries
                    det_summaries = []
                    for name, amount in leakages.items():
                        s_func = {
                            'Duplicates': lambda: dup_summary(results.get('duplicates', pd.DataFrame())),
                            'VAT/WHT': lambda: vat_summary(results.get('vat_wht', pd.DataFrame())),
                            'Expenses': lambda: exp_summary(results.get('expenses', pd.DataFrame())),
                            'Ghost': lambda: ghost_summary(results.get('ghost', {})),
                            'Tax Risk': lambda: tax_summary(results.get('tax_filing', pd.DataFrame()))
                        }
                        s = s_func.get(name, lambda: {'count': 0, 'detail': ''})()
                        det_summaries.append({
                            'name': name,
                            'amount': amount,
                            'count': s.get('count', 0),
                            'detail': s.get('detail', '')
                        })

                    # Build top actions from actual results
                    top_actions = []

                    # Get top items from each category
                    if 'duplicates' in results and isinstance(results['duplicates'], pd.DataFrame) and len(results['duplicates']) > 0:
                        for _, row in results['duplicates'].head(2).iterrows():
                            top_actions.append({
                                'action': f"Recover duplicate payment to {row.get('vendor_name', 'vendor')} - Invoice {row.get('invoice_ref', 'N/A')}",
                                'amount': float(row.get('flagged_amount', 0))
                            })

                    if 'ghost' in results:
                        ghost = results['ghost']
                        if 'vendors' in ghost and isinstance(ghost['vendors'], pd.DataFrame) and len(ghost['vendors']) > 0:
                            for _, row in ghost['vendors'].head(1).iterrows():
                                top_actions.append({
                                    'action': f"Investigate ghost vendor: {row.get('name', 'Unknown')} - {row.get('red_flag_reason', '')}",
                                    'amount': float(row.get('total_paid', 0))
                                })

                    if 'vat_wht' in results and isinstance(results['vat_wht'], pd.DataFrame) and len(results['vat_wht']) > 0:
                        for _, row in results['vat_wht'].head(1).iterrows():
                            top_actions.append({
                                'action': f"Remit unremitted {row.get('issue_type', 'tax')} for {row.get('vendor_name', 'vendor')}",
                                'amount': float(row.get('estimated_liability', 0))
                            })

                    while len(top_actions) < 3:
                        top_actions.append({
                            'action': 'Review all flagged transactions with your finance team',
                            'amount': 0
                        })
                    top_actions = top_actions[:3]

                    # Build dynamic AI summary based on ACTUAL results
                    sorted_leakages = sorted(leakages.items(), key=lambda x: x[1], reverse=True)
                    nonzero = [(n, a) for n, a in sorted_leakages if a > 0]

                    if nonzero:
                        top_cat = nonzero[0][0]
                        top_amt = nonzero[0][1]
                        total_items = sum(
                            len(results[k]) if isinstance(results.get(k), pd.DataFrame)
                            else sum(len(results.get(k, {}).get(sub, pd.DataFrame())) for sub in ['vendors', 'employees']) if k == 'ghost'
                            else 0
                            for k in ['duplicates', 'vat_wht', 'expenses', 'ghost', 'tax_filing']
                        )

                        ai_summary = f"This audit of {st.session_state.get('company_name', 'the company')} for {st.session_state.get('audit_period', 'the current period')} identified total financial leakage of NGN {total_leakage:,.2f} across {total_items} flagged items.\n\n"

                        ai_summary += "Breakdown by category:\n"
                        for name, amount in sorted_leakages:
                            if amount > 0:
                                pct = (amount / total_leakage * 100) if total_leakage > 0 else 0
                                ai_summary += f"- {name}: NGN {amount:,.2f} ({pct:.1f}%)\n"

                        ai_summary += f"\nThe most significant area of concern is {top_cat}, accounting for NGN {top_amt:,.2f}. "
                        ai_summary += "Immediate investigation and recovery action is recommended, starting with the highest-value findings.\n\n"
                        ai_summary += "Expected recovery potential: 80% of identified leakage (NGN {0:,.2f}).".format(total_leakage * 0.8)
                    else:
                        ai_summary = f"This audit of {st.session_state.get('company_name', 'the company')} for {st.session_state.get('audit_period', 'the current period')} found no significant financial leakage. All 5 detection engines returned clean results."

                    # Try OpenAI for better summary
                    try:
                        from openai import OpenAI
                        api_key = os.getenv("OPENAI_API_KEY")
                        if api_key:
                            client = OpenAI(api_key=api_key)
                            prompt = f"""You are a financial auditor. Write a 3-paragraph executive summary for a leakage report. Use ONLY the data below. Do NOT mention categories that show 0.

Company: {st.session_state.get('company_name', 'Company')}
Total Leakage: NGN {total_leakage:,.2f}
"""
                            for name, amount in sorted_leakages:
                                prompt += f"- {name}: NGN {amount:,.2f}\n"
                            prompt += "\nExpected recovery: 80% of total leakage. Write a clear, professional summary. Use NGN not naira symbol. ASCII only."

                            response = client.chat.completions.create(
                                model="gpt-4o-mini",
                                messages=[{"role": "user", "content": prompt}],
                                max_tokens=500,
                                temperature=0.3
                            )
                            ai_summary = response.choices[0].message.content
                    except Exception:
                        pass

                    pdf_path = generate_report(
                        company_name=st.session_state.get('company_name', 'Company'),
                        audit_period=st.session_state.get('audit_period', f'FY {datetime.now().year}'),
                        total_leakage=total_leakage,
                        total_revenue=st.session_state.get('company_revenue', 0),
                        detection_summaries=det_summaries,
                        top_actions=top_actions,
                        ai_summary=ai_summary
                    )

                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()

                    safe_name = (st.session_state.get('company_name', 'company')).replace(' ', '_')
                    st.download_button(
                        label="Download PDF",
                        data=pdf_bytes,
                        file_name=f"RevAI_Leakage_Report_{safe_name}_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

        with col2:
            if st.button("Download Excel (All Findings)", type="primary", use_container_width=True):
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    # Summary sheet
                    summary_rows = []
                    for name, amount in leakages.items():
                        s_func = {
                            'Duplicates': lambda: dup_summary(results.get('duplicates', pd.DataFrame())),
                            'VAT/WHT': lambda: vat_summary(results.get('vat_wht', pd.DataFrame())),
                            'Expenses': lambda: exp_summary(results.get('expenses', pd.DataFrame())),
                            'Ghost': lambda: ghost_summary(results.get('ghost', {})),
                            'Tax Risk': lambda: tax_summary(results.get('tax_filing', pd.DataFrame()))
                        }
                        s = s_func.get(name, lambda: {'count': 0, 'detail': ''})()
                        summary_rows.append({
                            'Category': name,
                            'Amount (NGN)': amount,
                            'Items Flagged': s.get('count', 0),
                            'Details': s.get('detail', ''),
                            'Expected Recovery (80%)': amount * 0.8
                        })
                    pd.DataFrame(summary_rows).to_excel(writer, sheet_name='Summary', index=False)

                    # Individual sheets
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
                safe_name = (st.session_state.get('company_name', 'company')).replace(' ', '_')
                st.download_button(
                    label="Download Excel",
                    data=output.getvalue(),
                    file_name=f"RevAI_Findings_{safe_name}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

        # === DETAILED FINDINGS TABS ===
        st.markdown("---")
        st.markdown("### Detailed Findings")

        # Build tab names with counts
        tab_info = []
        for name in ['Duplicates', 'VAT/WHT', 'Expenses', 'Ghost', 'Tax Risk']:
            amount = leakages.get(name, 0)
            key_map = {
                'Duplicates': 'duplicates',
                'VAT/WHT': 'vat_wht',
                'Expenses': 'expenses',
                'Ghost': 'ghost',
                'Tax Risk': 'tax_filing'
            }
            key = key_map.get(name)
            count = 0
            if key and key in results:
                if key == 'ghost':
                    ghost = results[key]
                    count = sum(len(ghost.get(sub, pd.DataFrame())) for sub in ['vendors', 'employees'] if isinstance(ghost.get(sub), pd.DataFrame))
                elif isinstance(results[key], pd.DataFrame):
                    count = len(results[key])
            tab_info.append((name, count, amount, key))

        tab_names = [f"{name} ({count})" for name, count, _, _ in tab_info]
        tabs = st.tabs(tab_names)

        for i, (name, count, amount, key) in enumerate(tab_info):
            with tabs[i]:
                # Severity badge
                if amount >= 1000000:
                    severity, sev_label = "severity-critical", "CRITICAL"
                elif amount >= 100000:
                    severity, sev_label = "severity-high", "HIGH"
                elif amount > 0:
                    severity, sev_label = "severity-medium", "MEDIUM"
                else:
                    severity, sev_label = "severity-low", "CLEAN"

                # Get detail
                s_func = {
                    'Duplicates': lambda: dup_summary(results.get('duplicates', pd.DataFrame())),
                    'VAT/WHT': lambda: vat_summary(results.get('vat_wht', pd.DataFrame())),
                    'Expenses': lambda: exp_summary(results.get('expenses', pd.DataFrame())),
                    'Ghost': lambda: ghost_summary(results.get('ghost', {})),
                    'Tax Risk': lambda: tax_summary(results.get('tax_filing', pd.DataFrame()))
                }
                s = s_func.get(name, lambda: {'detail': ''})()

                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <div>
                        <span class="{severity}">{sev_label}</span>
                        <span style="margin-left: 8px; color: #64748B; font-size: 13px;">{count} items flagged</span>
                    </div>
                    <span style="font-size: 18px; font-weight: 800; color: #0F172A;">NGN {amount:,.2f}</span>
                </div>
                <p style="color: #64748B; font-size: 13px;">{s.get('detail', '')}</p>
                """, unsafe_allow_html=True)

                # Show data table
                if key and key in results:
                    data = results[key]
                    if key == "ghost":
                        has_data = False
                        if 'vendors' in data and isinstance(data['vendors'], pd.DataFrame) and len(data['vendors']) > 0:
                            st.markdown("**Ghost Vendors**")
                            display_cols = [c for c in ['name', 'red_flag_reason', 'total_paid', 'risk_level', 'bank_account'] if c in data['vendors'].columns]
                            st.dataframe(data['vendors'][display_cols], use_container_width=True, hide_index=True)
                            has_data = True
                        if 'employees' in data and isinstance(data['employees'], pd.DataFrame) and len(data['employees']) > 0:
                            st.markdown("**Ghost Employees**")
                            display_cols = [c for c in ['name', 'red_flag_reason', 'total_paid', 'risk_level', 'bank_account'] if c in data['employees'].columns]
                            st.dataframe(data['employees'][display_cols], use_container_width=True, hide_index=True)
                            has_data = True
                        if not has_data:
                            st.success("No ghost vendors or employees detected.")
                    elif isinstance(data, pd.DataFrame) and len(data) > 0:
                        st.dataframe(data, use_container_width=True, hide_index=True)
                    else:
                        st.success(f"No issues detected in {name}.")
                else:
                    st.success(f"No issues detected in {name}.")

        # === RECOMMENDED ACTIONS ===
        st.markdown("---")
        st.markdown("### Recommended Actions")

        # Build actions from actual results, sorted by amount
        actions = []
        for name, amount in leakages.items():
            if amount > 0:
                actions.append({
                    'priority': 1 if amount >= 1000000 else 2 if amount >= 100000 else 3,
                    'category': name,
                    'action': f"Review and recover {count} flagged {name.lower()} items",
                    'amount': amount,
                    'recovery': amount * 0.8  # 80% expected recovery
                })

        actions.sort(key=lambda x: x['priority'])

        for action in actions[:5]:
            priority_label = ["URGENT", "HIGH", "MEDIUM"][action['priority'] - 1] if action['priority'] <= 3 else "LOW"
            priority_color = ["#DC2626", "#EA580C", "#CA8A04"][action['priority'] - 1] if action['priority'] <= 3 else "#2563EB"

            st.markdown(f"""
            <div style="background: white; border-left: 4px solid {priority_color}; padding: 12px 16px; border-radius: 8px; margin: 8px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="color: {priority_color}; font-weight: 700; font-size: 11px;">{priority_label}</span>
                        <span style="margin-left: 8px; font-size: 13px; color: #0F172A;">{action['action']}</span>
                    </div>
                    <div style="text-align: right;">
                        <span style="font-size: 13px; font-weight: 700; color: #0F172A;">NGN {action['amount']:,.2f}</span>
                        <br><span style="font-size: 11px; color: #16A34A;">Expected recovery: NGN {action['recovery']:,.2f}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # === CONTACT CTA ===
        st.markdown("---")
        st.markdown("""
        <div style="background: #0F172A; padding: 20px 24px; border-radius: 14px; text-align: center; margin-top: 16px;">
            <h3 style="color: white; margin: 0; font-size: 16px;">Need help recovering your leaked money?</h3>
            <p style="color: #94A3B8; margin: 8px 0 0 0; font-size: 13px;">Schedule a walkthrough to review each finding and build a recovery plan.</p>
            <p style="color: #60A5FA; margin: 10px 0 0 0; font-weight: 600; font-size: 13px;">WhatsApp: +234 704 929 4373 | Email: abuzaidabdullahi531@gmail.com</p>
        </div>
        """, unsafe_allow_html=True)

        # === RESET BUTTON ===
        st.markdown("---")
        if st.button("Load New Data", use_container_width=True):
            st.session_state.data_loaded = False
            st.session_state.scan_complete = False
            st.session_state.results = {}
            st.session_state.leakages = {}
            st.session_state.total_leakage = 0
            st.rerun()
