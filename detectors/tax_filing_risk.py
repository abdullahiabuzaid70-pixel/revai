"""
Detection 5: Late Tax Filing / Penalty Risk
Finds missed tax filing deadlines and upcoming deadlines at risk
"""
import pandas as pd
from datetime import datetime, timedelta
from utils.nigerian_tax_rules import FILING_DEADLINES, calculate_late_penalty


def detect_tax_filing_risk(df_tax=None, df_payroll=None, df_ap=None):
    """
    Detect late or at-risk tax filings.
    
    Returns DataFrame with columns:
    - tax_type, period, due_date, status, estimated_penalty, risk_level, details
    """
    results = []
    now = pd.Timestamp.now()
    
    # Determine which months we have data for
    all_months = set()
    
    if df_ap is not None and not df_ap.empty:
        date_col = 'payment_date' if 'payment_date' in df_ap.columns else 'transaction_date'
        if date_col in df_ap.columns:
            dates = pd.to_datetime(df_ap[date_col], errors='coerce').dropna()
            all_months.update(dates.dt.to_period('M').unique())
    
    if df_payroll is not None and not df_payroll.empty:
        if 'month' in df_payroll.columns:
            months = pd.to_datetime(df_payroll['month'], errors='coerce').dropna()
            all_months.update(months.dt.to_period('M').unique())
    
    if df_tax is not None and not df_tax.empty:
        if 'remittance_date' in df_tax.columns:
            dates = pd.to_datetime(df_tax['remittance_date'], errors='coerce').dropna()
            all_months.update(dates.dt.to_period('M').unique())
    
    # Track which tax periods have been remitted
    remitted_periods = set()
    if df_tax is not None and not df_tax.empty:
        if 'tax_type' in df_tax.columns and 'period_covered' in df_tax.columns:
            for _, row in df_tax.iterrows():
                tax_type = str(row.get('tax_type', '')).upper().strip()
                period = str(row.get('period_covered', '')).strip()
                if tax_type and period and period != 'nan':
                    remitted_periods.add((tax_type, period))
    
    # Check each tax type for each month we have data
    for period in sorted(all_months):
        period_str = str(period)  # e.g., "2026-03"
        year, month = period.year, period.month
        
        # Due date is in the FOLLOWING month
        if month == 12:
            due_month = 1
            due_year = year + 1
        else:
            due_month = month + 1
            due_year = year
        
        tax_types_to_check = []
        if df_ap is not None and not df_ap.empty:
            tax_types_to_check.extend(['VAT', 'WHT'])
        if df_payroll is not None and not df_payroll.empty:
            tax_types_to_check.append('PAYE')
        
        for tax_type in tax_types_to_check:
            deadline_day = FILING_DEADLINES.get(tax_type)
            if not deadline_day:
                continue
            
            due_date = pd.Timestamp(year=due_year, month=due_month, day=deadline_day)
            
            # Check if remitted
            was_remitted = (tax_type, period_str) in remitted_periods
            
            if was_remitted:
                continue  # Already remitted, no issue
            
            days_overdue = (now - due_date).days
            
            if days_overdue > 0:
                # Missed deadline
                penalty = calculate_late_penalty(tax_type, days_overdue)
                results.append({
                    'tax_type': tax_type,
                    'period': period_str,
                    'due_date': due_date.strftime('%Y-%m-%d'),
                    'status': 'Missed',
                    'days_overdue': days_overdue,
                    'estimated_penalty': penalty,
                    'risk_level': 'High' if days_overdue > 90 else 'Medium' if days_overdue > 30 else 'Low',
                    'details': f"{tax_type} for {period_str} was due on {due_date.strftime('%Y-%m-%d')} and is now {days_overdue} days overdue. Estimated penalty: ₦{penalty:,.2f}"
                })
            elif days_overdue > -7 and days_overdue <= 0:
                # At risk — due within 7 days
                results.append({
                    'tax_type': tax_type,
                    'period': period_str,
                    'due_date': due_date.strftime('%Y-%m-%d'),
                    'status': 'At Risk',
                    'days_overdue': 0,
                    'estimated_penalty': 0,
                    'risk_level': 'Medium',
                    'details': f"{tax_type} for {period_str} is due on {due_date.strftime('%Y-%m-%d')} — {abs(days_overdue)} days remaining. File now to avoid penalties."
                })
    
    if not results:
        return pd.DataFrame()
    
    result_df = pd.DataFrame(results)
    result_df = result_df.sort_values(['status', 'estimated_penalty'], ascending=[True, False])
    return result_df


def get_summary(results_df):
    """Return summary stats for tax filing risk detection."""
    if results_df.empty:
        return {
            'total_flagged': 0,
            'total_amount': 0,
            'count': 0,
            'missed_count': 0,
            'at_risk_count': 0,
            'top_penalty': 0,
            'detail': 'No tax filing risks detected. All filings are on time.'
        }
    
    missed_count = len(results_df[results_df['status'] == 'Missed']) if 'status' in results_df.columns else 0
    at_risk_count = len(results_df[results_df['status'] == 'At Risk']) if 'status' in results_df.columns else 0
    top_penalty = results_df['estimated_penalty'].max() if len(results_df) > 0 else 0
    return {
        'total_flagged': len(results_df),
        'total_amount': results_df['estimated_penalty'].sum(),
        'count': len(results_df),
        'missed_count': missed_count,
        'at_risk_count': at_risk_count,
        'top_penalty': top_penalty,
        'detail': f'{len(results_df)} tax filing risks. Missed: {missed_count}, At risk: {at_risk_count}'
    }
