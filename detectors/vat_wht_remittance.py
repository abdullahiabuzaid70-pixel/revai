"""
Detection 2: Missing VAT/WHT Remittances
Finds VAT or Withholding Tax that was deducted but never remitted to FIRS/State IRS
"""
import pandas as pd
from datetime import timedelta
from utils.nigerian_tax_rules import (
    VAT_RATE, WHT_RATES, calculate_vat, calculate_wht,
    should_have_vat, calculate_late_penalty
)


def detect_vat_wht_issues(df_ap, df_tax=None):
    """
    Detect VAT/WHT issues in AP data, cross-referencing with tax remittances.
    
    Returns DataFrame with columns:
    - issue_type, vendor_name, payment_amount, expected_tax, remittance_status,
      estimated_liability, period, risk_level, details
    """
    if df_ap.empty:
        return pd.DataFrame()
    
    results = []
    df = df_ap.copy()
    
    # Parse dates
    date_col = 'payment_date' if 'payment_date' in df.columns else 'transaction_date'
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    else:
        return pd.DataFrame()
    
    # Parse tax remittances
    tax_periods_remitted = set()
    if df_tax is not None and not df_tax.empty:
        if 'remittance_date' in df_tax.columns and 'tax_type' in df_tax.columns:
            df_tax_copy = df_tax.copy()
            df_tax_copy['remittance_date'] = pd.to_datetime(df_tax_copy['remittance_date'], errors='coerce')
            if 'period_covered' in df_tax.columns:
                for _, row in df_tax_copy.iterrows():
                    tax_type = str(row.get('tax_type', '')).upper().strip()
                    period = str(row.get('period_covered', '')).strip()
                    if tax_type and period and period != 'nan':
                        tax_periods_remitted.add((tax_type, period))
    
    # Check each AP transaction for VAT/WHT issues
    for idx, row in df.iterrows():
        if pd.isna(row.get(date_col)):
            continue
        
        amount = float(row.get('amount', 0))
        if amount <= 0:
            continue
        
        vendor = row.get('vendor_name', 'Unknown')
        category = str(row.get('expense_category', '')).lower() if 'expense_category' in df.columns else ''
        payment_period = row[date_col].strftime('%Y-%m')
        
        # --- Check VAT ---
        vat_amount = float(row.get('vat_amount', 0)) if 'vat_amount' in df.columns else 0
        
        if should_have_vat(amount, category):
            expected_vat = calculate_vat(amount)
            
            if vat_amount == 0:
                # No VAT deducted where it should have been
                results.append({
                    'issue_type': 'VAT Under-deducted',
                    'vendor_name': vendor,
                    'payment_amount': amount,
                    'expected_tax': expected_vat,
                    'remittance_status': 'Not deducted',
                    'estimated_liability': expected_vat,
                    'period': payment_period,
                    'risk_level': 'High' if expected_vat >= 500000 else 'Medium' if expected_vat >= 50000 else 'Low',
                    'details': f"VAT of ₦{expected_vat:,.2f} should have been deducted on payment of ₦{amount:,.2f} to {vendor}"
                })
            elif vat_amount > 0:
                # VAT was deducted — check if it was remitted
                vat_remitted = ('VAT', payment_period) in tax_periods_remitted
                if not vat_remitted:
                    # Estimate penalty
                    days_since = (pd.Timestamp.now() - row[date_col]).days
                    penalty = calculate_late_penalty('VAT', days_since) if days_since > 21 else 0
                    results.append({
                        'issue_type': 'VAT Unremitted',
                        'vendor_name': vendor,
                        'payment_amount': amount,
                        'expected_tax': vat_amount,
                        'remittance_status': 'Deducted but not remitted',
                        'estimated_liability': vat_amount + penalty,
                        'period': payment_period,
                        'risk_level': 'High' if (vat_amount + penalty) >= 500000 else 'Medium',
                        'details': f"VAT of ₦{vat_amount:,.2f} was deducted but not remitted to FIRS for period {payment_period}. Estimated penalty: ₦{penalty:,.2f}"
                    })
        
        # --- Check WHT ---
        wht_amount = float(row.get('wht_amount', 0)) if 'wht_amount' in df.columns else 0
        
        # Determine WHT category
        wht_category = 'default'
        for cat in WHT_RATES:
            if cat in category:
                wht_category = cat
                break
        
        expected_wht = calculate_wht(amount, wht_category)
        
        if expected_wht > 0 and wht_amount == 0:
            # No WHT deducted where it should have been
            results.append({
                'issue_type': 'WHT Under-deducted',
                'vendor_name': vendor,
                'payment_amount': amount,
                'expected_tax': expected_wht,
                'remittance_status': 'Not deducted',
                'estimated_liability': expected_wht,
                'period': payment_period,
                'risk_level': 'Medium' if expected_wht >= 50000 else 'Low',
                'details': f"WHT of ₦{expected_wht:,.2f} should have been deducted on payment of ₦{amount:,.2f} to {vendor} (category: {wht_category})"
            })
        elif wht_amount > 0:
            wht_remitted = ('WHT', payment_period) in tax_periods_remitted
            if not wht_remitted:
                penalty = calculate_late_penalty('WHT', 0)
                results.append({
                    'issue_type': 'WHT Unremitted',
                    'vendor_name': vendor,
                    'payment_amount': amount,
                    'expected_tax': wht_amount,
                    'remittance_status': 'Deducted but not remitted',
                    'estimated_liability': wht_amount + penalty,
                    'period': payment_period,
                    'risk_level': 'High' if (wht_amount + penalty) >= 500000 else 'Medium',
                    'details': f"WHT of ₦{wht_amount:,.2f} was deducted but not remitted to FIRS for period {payment_period}. Penalty: ₦{penalty:,.2f}"
                })
    
    if not results:
        return pd.DataFrame()
    
    result_df = pd.DataFrame(results)
    result_df = result_df.sort_values('estimated_liability', ascending=False)
    return result_df


def get_summary(results_df):
    """Return summary stats for VAT/WHT detection."""
    if results_df.empty:
        return {
            'total_flagged': 0,
            'total_amount': 0,
            'count': 0,
            'top_issue': 'N/A',
            'top_amount': 0,
                    'detail': 'No VAT/WHT issues detected.'
        }
    
    top_issue = results_df.iloc[0]['issue_type'] if len(results_df) > 0 else 'N/A'
    top_amount = results_df.iloc[0]['estimated_liability'] if len(results_df) > 0 else 0
    return {
        'total_flagged': len(results_df),
        'total_amount': results_df['estimated_liability'].sum(),
        'count': len(results_df),
        'top_issue': top_issue,
        'top_amount': top_amount,
        'detail': f'{len(results_df)} VAT/WHT issues found. Top issue: {top_issue} (NGN {top_amount:,.2f})'
    }
