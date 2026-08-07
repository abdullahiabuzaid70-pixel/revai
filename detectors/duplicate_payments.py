"""
Detection 1: Duplicate Payments
Finds the same invoice paid twice or near-duplicate payments to the same vendor
"""
import pandas as pd
from datetime import timedelta
from utils.fuzzy_matcher import are_same_vendor, normalize_vendor_name


def detect_duplicate_payments(df):
    """
    Detect duplicate payments in AP data.
    
    Returns DataFrame with columns:
    - vendor_name, amount, date1, date2, invoice_ref, flagged_amount, risk_level, details
    """
    if df.empty or 'vendor_name' not in df.columns or 'amount' not in df.columns:
        return pd.DataFrame()
    
    results = []
    df = df.copy()
    
    # Parse dates
    date_col = 'payment_date' if 'payment_date' in df.columns else 'transaction_date'
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    else:
        return pd.DataFrame()
    
    # Normalize vendor names
    df['vendor_normalized'] = df['vendor_name'].apply(normalize_vendor_name)
    
    # Group by normalized vendor name
    for vendor_norm, group in df.groupby('vendor_normalized'):
        if len(group) < 2:
            continue
        
        group = group.sort_values(date_col)
        
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                row1 = group.iloc[i]
                row2 = group.iloc[j]
                
                # Skip if either date is NaT
                if pd.isna(row1[date_col]) or pd.isna(row2[date_col]):
                    continue
                
                # Check date proximity (within 30 days)
                date_diff = abs((row1[date_col] - row2[date_col]).days)
                if date_diff > 30:
                    continue
                
                # Check amount similarity (within 2%)
                amt1 = float(row1['amount'])
                amt2 = float(row2['amount'])
                
                if amt1 == 0 or amt2 == 0:
                    continue
                
                amount_diff_pct = abs(amt1 - amt2) / max(amt1, amt2)
                
                # Check invoice number
                inv1 = str(row1.get('invoice_number', '')).strip() if 'invoice_number' in df.columns else ''
                inv2 = str(row2.get('invoice_number', '')).strip() if 'invoice_number' in df.columns else ''
                
                is_duplicate = False
                match_reason = ""
                
                if inv1 and inv2 and inv1 == inv2 and inv1 != 'nan':
                    # Same invoice number — strong duplicate signal
                    is_duplicate = True
                    match_reason = f"Same invoice #{inv1} paid twice"
                elif amount_diff_pct < 0.02:
                    # Amounts within 2%
                    if date_diff <= 7:
                        is_duplicate = True
                        match_reason = f"Near-identical amounts (₦{amt1:,.2f} vs ₦{amt2:,.2f}) within {date_diff} days"
                    elif not inv1 and not inv2:
                        # No invoice numbers but same amount and close dates
                        is_duplicate = True
                        match_reason = f"Identical amounts (₦{amt1:,.2f}) within {date_diff} days, no invoice ref"
                
                if is_duplicate:
                    flagged_amount = min(amt1, amt2)  # The duplicate amount
                    risk_level = "High" if flagged_amount >= 1000000 else "Medium" if flagged_amount >= 100000 else "Low"
                    
                    results.append({
                        'vendor_name': row1['vendor_name'],
                        'amount_1': amt1,
                        'date_1': row1[date_col].strftime('%Y-%m-%d'),
                        'amount_2': amt2,
                        'date_2': row2[date_col].strftime('%Y-%m-%d'),
                        'invoice_ref': inv1 if inv1 != 'nan' else inv2 if inv2 != 'nan' else 'N/A',
                        'flagged_amount': flagged_amount,
                        'risk_level': risk_level,
                        'details': match_reason
                    })
    
    if not results:
        return pd.DataFrame()
    
    result_df = pd.DataFrame(results)
    result_df = result_df.sort_values('flagged_amount', ascending=False)
    return result_df


def get_summary(results_df):
    """Return summary stats for duplicate payments detection."""
    if results_df.empty:
        return {
            'total_flagged': 0,
            'total_amount': 0,
            'count': 0,
            'top_vendor': 'N/A',
            'top_amount': 0,
                    'detail': 'No duplicate payments detected.'
        }
    
    top_vendor = results_df.iloc[0]['vendor_name'] if len(results_df) > 0 else 'N/A'
    top_amount = results_df.iloc[0]['flagged_amount'] if len(results_df) > 0 else 0
    return {
        'total_flagged': len(results_df),
        'total_amount': results_df['flagged_amount'].sum(),
        'count': len(results_df),
        'top_vendor': top_vendor,
        'top_amount': top_amount,
        'detail': f'{len(results_df)} duplicate payments found. Top: {top_vendor} (NGN {top_amount:,.2f})'
    }
