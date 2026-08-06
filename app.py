"""
RevAI — AI Revenue & Fraud Detection for African Companies
Main Streamlit Application

Run: streamlit run app.py
"""
import streamlit as st
import pandas as pd
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# === CONFIG ===
st.set_page_config(
    page_title="RevAI — Revenue. Protected.",
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

# === STYLING ===
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        padding: 20px 30px;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    .main-header h1 {
        color: white;
        font-size: 28px;
        margin: 0;
    }
    .main-header p {
        color: #94A3B8;
        font-size: 14px;
        margin: 5px 0 0 0;
    }
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #E5E7EB;
        text-align: center;
    }
    .metric-card h2 {
        font-size: 24px;
        margin: 0;
        color: #0F172A;
    }
    .metric-card p {
        font-size: 12px;
        color: #6B7280;
        margin: 5px 0 0 0;
    }
    .risk-high { color: #DC2626; font-weight: bold; }
    .risk-medium { color: #EA580C; font-weight: bold; }
    .risk-low { color: #CA8A04; font-weight: bold; }
    .risk-clean { color: #16A34A; font-weight: bold; }
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

# === HEADER ===
st.markdown("""
<div class="main-header">
    <h1>🛡️ RevAI</h1>
    <p>AI Revenue & Fraud Detection for African Companies — Find your leaked money.</p>
</div>
""", unsafe_allow_html=True)

# === SIDEBAR: DATA UPLOAD ===
st.sidebar.title("📊 Data Input")
st.sidebar.markdown("Upload your financial data or try with sample data.")

use_sample = st.sidebar.checkbox("Use Sample Data (Demo)", value=False, help="Generate realistic Nigerian company data with known fraud patterns")

if use_sample:
    if st.sidebar.button("Load Sample Data", type="primary"):
        with st.spinner("Generating sample data..."):
            sample = generate_all_sample_data()
            st.session_state.ap_data = sample['ap']
            st.session_state.payroll_data = sample['payroll']
            st.session_state.tax_data = sample['tax_remittance']
            st.session_state.vendor_master = sample['vendor_master']
            st.session_state.employee_master = sample['employee_master']
            st.session_state.data_loaded = True
            st.sidebar.success("✅ Sample data loaded! Ready to scan.")
            st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### Upload Your Data")

ap_file = st.sidebar.file_uploader("Accounts Payable (AP)", type=['csv', 'xlsx', 'xls'])
payroll_file = st.sidebar.file_uploader("Payroll", type=['csv', 'xlsx', 'xls'])
tax_file = st.sidebar.file_uploader("Tax Remittances", type=['csv', 'xlsx', 'xls'])
vendor_file = st.sidebar.file_uploader("Vendor Master (Optional)", type=['csv', 'xlsx', 'xls'])
employee_file = st.sidebar.file_uploader("Employee Master (Optional)", type=['csv', 'xlsx', 'xls'])

# Download templates
st.sidebar.markdown("---")
st.sidebar.markdown("### 📥 Download Templates")
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
    if st.sidebar.button("Process Uploaded Data", type="primary"):
        progress = st.sidebar.progress(0)
        
        if ap_file:
            df = read_uploaded_file(ap_file)
            if df is not None:
                df = normalize_columns(df)
                mapping = auto_map_columns(df, "ap")
                df = apply_mapping(df, mapping)
                st.session_state.ap_data = df
                st.sidebar.success(f"✅ AP: {len(df)} rows loaded")
            progress.progress(20)
        
        if payroll_file:
            df = read_uploaded_file(payroll_file)
            if df is not None:
                df = normalize_columns(df)
                mapping = auto_map_columns(df, "payroll")
                df = apply_mapping(df, mapping)
                st.session_state.payroll_data = df
                st.sidebar.success(f"✅ Payroll: {len(df)} rows loaded")
            progress.progress(40)
        
        if tax_file:
            df = read_uploaded_file(tax_file)
            if df is not None:
                df = normalize_columns(df)
                mapping = auto_map_columns(df, "tax_remittance")
                df = apply_mapping(df, mapping)
                st.session_state.tax_data = df
                st.sidebar.success(f"✅ Tax: {len(df)} rows loaded")
            progress.progress(60)
        
        if vendor_file:
            df = read_uploaded_file(vendor_file)
            if df is not None:
                df = normalize_columns(df)
                mapping = auto_map_columns(df, "vendor_master")
                df = apply_mapping(df, mapping)
                st.session_state.vendor_master = df
                st.sidebar.success(f"✅ Vendor Master: {len(df)} rows loaded")
            progress.progress(80)
        
        if employee_file:
            df = read_uploaded_file(employee_file)
            if df is not None:
                df = normalize_columns(df)
                mapping = auto_map_columns(df, "employee_master")
                df = apply_mapping(df, mapping)
                st.session_state.employee_master = df
                st.sidebar.success(f"✅ Employee Master: {len(df)} rows loaded")
            progress.progress(100)
        
        if st.session_state.ap_data is not None or st.session_state.payroll_data is not None:
            st.session_state.data_loaded = True
            st.sidebar.success("✅ Data processed! Ready to scan.")
            st.rerun()
        else:
            st.sidebar.error("No valid data loaded. Please upload at least AP or Payroll.")

# === MAIN CONTENT ===

if not st.session_state.data_loaded:
    # Landing page
    st.markdown("### Welcome to RevAI")
    st.markdown("""
    RevAI scans your company's financial data and finds money that's quietly leaking out:
    
    1. *Duplicate Payments* — Same invoice paid twice
    2. *Unremitted VAT/WHT* — Tax deducted but never sent to FIRS
    3. *Overstated Expenses* — Abnormally high or suspicious spending
    4. *Ghost Vendors/Employees* — People receiving payments who shouldn't exist
    5. *Late Tax Filing Risk* — Missed deadlines and penalty exposure
    
    Upload your data in the sidebar or click *Use Sample Data* to see a live demo.
    """)
    
    st.info("💡 Tip: Click 'Use Sample Data (Demo)' in the sidebar to instantly load realistic Nigerian company data with embedded fraud patterns, then click 'Run Full Scan'.")

else:
    # Data loaded — show summary and scan button
    col1, col2, col3 = st.columns(3)
    
    with col1:
        ap_count = len(st.session_state.ap_data) if st.session_state.ap_data is not None else 0
        st.metric("AP Transactions", f"{ap_count:,}")
    with col2:
        payroll_count = len(st.session_state.payroll_data) if st.session_state.payroll_data is not None else 0
        st.metric("Payroll Records", f"{payroll_count:,}")
    with col3:
        tax_count = len(st.session_state.tax_data) if st.session_state.tax_data is not None else 0
        st.metric("Tax Remittances", f"{tax_count:,}")
    
    st.markdown("---")
    
    # Run scan button
    if st.button("🔍 Run Full Scan", type="primary", use_container_width=True):
        with st.spinner("Scanning for financial leakage..."):
            results = {}
            total_leakage = 0
            
            # Progress bar
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
                total_leakage += vat_sum['total_amount']
                progress.progress(40)
            
            # Detection 3: Overstated Expenses
            if st.session_state.ap_data is not None:
                status.text("Checking for overstated expenses...")
                exp_results = detect_overstated_expenses(st.session_state.ap_data)
                results['expenses'] = exp_results
                exp_sum = exp_summary(exp_results)
                total_leakage += exp_sum['total_amount']
                progress.progress(60)
            
            # Detection 4: Ghost Vendors/Employees
            status.text("Checking for ghost vendors and employees...")
            ghost_results = pd.DataFrame()
            if st.session_state.ap_data is not None:
                ghost_vendor_results = detect_ghost_vendors(st.session_state.ap_data, st.session_state.vendor_master)
                if not ghost_vendor_results.empty:
                    ghost_results = pd.concat([ghost_results, ghost_vendor_results], ignore_index=True)
            
            if st.session_state.payroll_data is not None:
                ghost_emp_results = detect_ghost_employees(st.session_state.payroll_data, st.session_state.employee_master)
                if not ghost_emp_results.empty:
                    ghost_results = pd.concat([ghost_results, ghost_emp_results], ignore_index=True)
            
            results['ghosts'] = ghost_results
            ghost_sum = ghost_summary(ghost_results)
            total_leakage += ghost_sum['total_amount']
            progress.progress(80)
            
            # Detection 5: Tax Filing Risk
            status.text("Checking tax filing deadlines...")
            tax_results = detect_tax_filing_risk(
                st.session_state.tax_data,
                st.session_state.payroll_data,
                st.session_state.ap_data
            )
            results['tax_risk'] = tax_results
            tax_sum = tax_summary(tax_results)
            total_leakage += tax_sum['total_amount']
            progress.progress(100)
            
            status.text("Scan complete!")
            
            st.session_state.results = results
            st.session_state.total_leakage = total_leakage
            st.session_state.scan_complete = True
            st.rerun()
    
    # === RESULTS DISPLAY ===
    if st.session_state.scan_complete:
        st.markdown("---")
        
        # Total Leakage Banner
        total = st.session_state.total_leakage
        if total > 0:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%); 
                        padding: 30px; border-radius: 12px; text-align: center; margin-bottom: 20px;">
                <h1 style="color: white; font-size: 36px; margin: 0;">₦{total:,.2f}</h1>
                <p style="color: #94A3B8; font-size: 16px; margin: 10px 0 0 0;">TOTAL LEAKAGE IDENTIFIED</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #16A34A 0%, #15803D 100%); 
                        padding: 30px; border-radius: 12px; text-align: center; margin-bottom: 20px;">
                <h1 style="color: white; font-size: 36px; margin: 0;">✓ No Significant Leakage</h1>
                <p style="color: #D1FAE5; font-size: 16px; margin: 10px 0 0 0;">Your financial controls appear healthy.</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Detection Summary Cards
        results = st.session_state.results
        col1, col2, col3, col4, col5 = st.columns(5)
        
        summaries = {
            'duplicates': ("Duplicate Payments", dup_summary),
            'vat_wht': ("VAT/WHT Issues", vat_summary),
            'expenses': ("Overstated Expenses", exp_summary),
            'ghosts': ("Ghost Vendors/Employees", ghost_summary),
            'tax_risk': ("Tax Filing Risk", tax_summary)
        }
        
        cols = [col1, col2, col3, col4, col5]
        
        for i, (key, (label, summary_fn)) in enumerate(summaries.items()):
            with cols[i]:
                result_df = results.get(key, pd.DataFrame())
                sum_data = summary_fn(result_df)
                if sum_data['total_amount'] > 0:
                    st.markdown(f"""
                    <div class="metric-card">
                        <p>{label}</p>
                        <h2 class="risk-high">₦{sum_data['total_amount']:,.0f}</h2>
                        <p>{sum_data['count']} flagged</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="metric-card">
                        <p>{label}</p>
                        <h2 class="risk-clean">✓ Clean</h2>
                        <p>0 issues</p>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Detailed Results in Tabs
        st.markdown("### Detailed Findings")
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "1. Duplicate Payments", "2. VAT/WHT Issues", "3. Overstated Expenses",
            "4. Ghost Vendors/Employees", "5. Tax Filing Risk"
        ])
        
        with tab1:
            dup_df = results.get('duplicates', pd.DataFrame())
            if not dup_df.empty:
                st.dataframe(dup_df, use_container_width=True)
                csv = dup_df.to_csv(index=False)
                st.download_button("Download CSV", csv, "revai_duplicates.csv", "text/csv")
            else:
                st.success("✓ No duplicate payments found.")
        
        with tab2:
            vat_df = results.get('vat_wht', pd.DataFrame())
            if not vat_df.empty:
                st.dataframe(vat_df, use_container_width=True)
                csv = vat_df.to_csv(index=False)
                st.download_button("Download CSV", csv, "revai_vat_wht.csv", "text/csv")
            else:
                st.success("✓ No VAT/WHT issues found.")
        
        with tab3:
            exp_df = results.get('expenses', pd.DataFrame())
            if not exp_df.empty:
                st.dataframe(exp_df, use_container_width=True)
                csv = exp_df.to_csv(index=False)
                st.download_button("Download CSV", csv, "revai_expenses.csv", "text/csv")
            else:
                st.success("✓ No overstated expenses found.")
        
        with tab4:
            ghost_df = results.get('ghosts', pd.DataFrame())
            if not ghost_df.empty:
                st.dataframe(ghost_df, use_container_width=True)
                csv = ghost_df.to_csv(index=False)
                st.download_button("Download CSV", csv, "revai_ghosts.csv", "text/csv")
            else:
                st.success("✓ No ghost vendors or employees found.")
        
        with tab5:
            tax_df = results.get('tax_risk', pd.DataFrame())
            if not tax_df.empty:
                st.dataframe(tax_df, use_container_width=True)
                csv = tax_df.to_csv(index=False)
                st.download_button("Download CSV", csv, "revai_tax_risk.csv", "text/csv")
            else:
                st.success("✓ No tax filing risks found.")
        
        # === PDF REPORT GENERATION ===
        st.markdown("---")
        st.markdown("### 📄 Generate Leakage Report")
        
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            company_name = st.text_input("Company Name", value="Sample Company Ltd")
        with col_r2:
            total_revenue = st.number_input("Annual Revenue (₦)", value=500000000, step=10000000)
        
        # Build detection summaries for PDF
        detection_summaries = []
        for key, (label, summary_fn) in summaries.items():
            result_df = results.get(key, pd.DataFrame())
            sum_data = summary_fn(result_df)
            detail = sum_data.get('top_vendor', sum_data.get('top_issue', sum_data.get('top_category', sum_data.get('top_entity', 'N/A'))))
            if isinstance(detail, str) and detail != 'N/A':
                detail = f"Top: {detail} (₦{sum_data.get('top_amount', 0):,.2f})"
            else:
                detail = f"{sum_data['count']} items flagged" if sum_data['count'] > 0 else "No issues detected"
            
            detection_summaries.append({
                'name': label,
                'amount': sum_data['total_amount'],
                'count': sum_data['count'],
                'detail': detail
            })
        
        # Build top 3 actions
        all_findings = []
        for key in ['duplicates', 'vat_wht', 'expenses', 'ghosts']:
            df = results.get(key, pd.DataFrame())
            if df.empty:
                continue
            amount_col = 'flagged_amount' if 'flagged_amount' in df.columns else \
                        'estimated_liability' if 'estimated_liability' in df.columns else \
                        'transaction_amount' if 'transaction_amount' in df.columns else \
                        'total_paid' if 'total_paid' in df.columns else None
            if amount_col:
                for _, row in df.iterrows():
                    detail = row.get('details', row.get('detail', ''))
                    all_findings.append({
                        'action': detail if isinstance(detail, str) else str(detail),
                        'amount': float(row[amount_col])
                    })
        
        all_findings.sort(key=lambda x: x['amount'], reverse=True)
        top_actions = all_findings[:3]
        
        if not top_actions:
            top_actions = [
                {'action': 'No actionable findings — financial controls appear healthy', 'amount': 0}
            ]
        
        # AI Summary (try OpenAI, fall back to template)
        ai_summary = ""
        try:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key and api_key != "sk-your-key-here":
                client = OpenAI(api_key=api_key)
                prompt = f"""Summarize these financial audit findings in 2-3 sentences for a business owner who is not an accountant. 
                Tone: professional, direct, not alarmist. Include the total amount and the top issue.
                
                Total leakage: ₦{total:,.2f}
                Findings: {json.dumps([{'name': d['name'], 'amount': d['amount'], 'count': d['count']} for d in detection_summaries])}
                """
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=150
                )
                ai_summary = response.choices[0].message.content
            else:
                raise Exception("No API key")
        except:
            # Fallback summary
            if total > 0:
                top_det = max(detection_summaries, key=lambda x: x['amount'])
                ai_summary = f"Your company has an estimated ₦{total:,.2f} in financial leakage across {sum(d['count'] for d in detection_summaries)} flagged items. The most significant issue is {top_det['name']} at ₦{top_det['amount']:,.2f}. Addressing the top 3 items would recover approximately ₦{sum(a['amount'] for a in top_actions):,.2f} immediately."
            else:
                ai_summary = "No financial leakage was detected in the audited data. Your financial controls appear to be functioning effectively."
        
        # Audit period
        audit_period = "N/A"
        if st.session_state.ap_data is not None:
            date_col = 'payment_date' if 'payment_date' in st.session_state.ap_data.columns else 'transaction_date'
            if date_col in st.session_state.ap_data.columns:
                dates = pd.to_datetime(st.session_state.ap_data[date_col], errors='coerce').dropna()
                if len(dates) > 0:
                    audit_period = f"{dates.min().strftime('%b %Y')} — {dates.max().strftime('%b %Y')}"
        
        if st.button("Generate PDF Report", type="primary"):
            with st.spinner("Generating report..."):
                import tempfile
                import json
                pdf_path = generate_report(
                    company_name=company_name,
                    audit_period=audit_period,
                    total_leakage=total,
                    total_revenue=total_revenue,
                    detection_summaries=detection_summaries,
                    top_actions=top_actions,
                    ai_summary=ai_summary,
                )
                
                with open(pdf_path, 'rb') as f:
                    st.download_button(
                        label="⬇️ Download Leakage Report (PDF)",
                        data=f.read(),
                        file_name=f"RevAI_Leakage_Report_{company_name.replace(' ', '_')}.pdf",
                        mime="application/pdf"
                    )
                st.success("✅ Report generated! Click the download button above.")
        
        # Show AI summary preview
        st.markdown("### AI Executive Summary (Preview)")
        st.info(ai_summary)
