"""
Detection 3: Overstated Expenses
Finds expense entries abnormally high compared to historical patterns or industry benchmarks
"""
import pandas as pd
import numpy as np


def detect_overstated_expenses(df):
    """
    Detect overstated/abnormal expenses in AP data.
    
    Returns DataFrame with columns:
    - category, transaction_amount, baseline_average, deviation_pct, date, risk_level, details
    """
    if df.empty or 'amount' not in df.columns:
        return pd.DataFrame()
    
    results = []
    df = df.copy()
    
    # Parse dates
    date_col = 'payment_date' if 'payment_date' in df.columns else 'transaction_date'
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    else:
        return pd.DataFrame()
    
    # Determine expense category column
    cat_col = 'expense_category' if 'expense_category' in df.columns else None
    if not cat_col:
        # Try to infer from other columns
        for col in ['category', 'description', 'narration', 'particulars', 'gl_account']:
            if col in df.columns:
                cat_col = col
                break
    
    if not cat_col:
        # If no category column, treat all as one category
        df['expense_category'] = 'General'
        cat_col = 'expense_category'
    
    # Clean category names
    df[cat_col] = df[cat_col].fillna('Uncategorized').astype(str).str.strip().str.lower()
    
    # Calculate monthly spend per category
    df['month'] = df[date_col].dt.to_period('M')
    
    monthly_spend = df.groupby([cat_col, 'month'])['amount'].agg(['sum', 'count', 'mean', 'std']).reset_index()
    monthly_spend.columns = [cat_col, 'month', 'monthly_total', 'txn_count', 'txn_mean', 'txn_std']
    
    # Flag 1: Monthly spend exceeding 2x the 3-month rolling average
    for category in monthly_spend[cat_col].unique():
        cat_data = monthly_spend[monthly_spend[cat_col] == category].sort_values('month')
        
        for i in range(3, len(cat_data)):
            current = cat_data.iloc[i]
            rolling_avg = cat_data.iloc[i-3:i]['monthly_total'].mean()
            
            if rolling_avg > 0 and current['monthly_total'] > 2 * rolling_avg:
                deviation = ((current['monthly_total'] - rolling_avg) / rolling_avg * 100)
                results.append({
                    'category': category,
                    'transaction_amount': current['monthly_total'],
                    'baseline_average': rolling_avg,
                    'deviation_pct': deviation,
                    'date': str(current['month']),
                    'risk_level': 'High' if current['monthly_total'] >= 1000000 else 'Medium',
                    'details': f"Monthly spend in '{category}' (NGN {current['monthly_total']:,.2f}) is {deviation:.0f}% above the 3-month average (NGN {rolling_avg:,.2f})"
                })
    
    # Flag 2: Individual transactions > 3 standard deviations above category mean
    for category in df[cat_col].unique():
        cat_txns = df[df[cat_col] == category]
        if len(cat_txns) < 5:
            continue
        
        mean_amount = cat_txns['amount'].mean()
        std_amount = cat_txns['amount'].std()
        
        if std_amount == 0 or pd.isna(std_amount):
            continue
        
        threshold = mean_amount + 3 * std_amount
        
        outliers = cat_txns[cat_txns['amount'] > threshold]
        for _, row in outliers.iterrows():
            if pd.isna(row.get(date_col)):
                continue
            std_devs = abs(float(row['amount']) - mean_amount) / std_amount
            results.append({
                'category': category,
                'transaction_amount': float(row['amount']),
                'baseline_average': mean_amount,
                'deviation_pct': ((float(row['amount']) - mean_amount) / mean_amount * 100) if mean_amount > 0 else 0,
                'date': row[date_col].strftime('%Y-%m-%d'),
                'risk_level': 'High' if float(row['amount']) >= 1000000 else 'Medium',
                'details': f"Transaction of NGN {float(row['amount']):,.2f} in '{category}' is {std_devs:.1f} standard deviations above normal"
            })
    
    # Flag 3: Round-number transactions (common fraud indicator)
    for _, row in df.iterrows():
        amount = float(row['amount'])
        if amount == 0:
            continue
        
        # Check if amount is a "suspiciously round" number
        if amount >= 100000 and amount % 100000 == 0:
            cat = str(row.get(cat_col, 'Unknown'))
            date_str = row[date_col].strftime('%Y-%m-%d') if not pd.isna(row.get(date_col)) else 'N/A'
            results.append({
                'category': cat,
                'transaction_amount': amount,
                'baseline_average': df[df[cat_col] == cat]['amount'].mean() if cat in df[cat_col].values else 0,
                'deviation_pct': 0,
                'date': date_str,
                'risk_level': 'Medium',
                'details': f"Round-number payment of NGN {amount:,.2f} in '{cat}' — common fraud pattern (exact multiple of NGN 100,000)"
            })
    
    # Remove duplicates by sorting and keeping highest amounts
    if not results:
        return pd.DataFrame()
    
    result_df = pd.DataFrame(results)
    result_df = result_df.drop_duplicates(subset=['category', 'transaction_amount', 'date'])
    result_df = result_df.sort_values('transaction_amount', ascending=False)
    return result_df


def get_summary(results_df):
    """Return summary stats for overstated expenses detection."""
    if results_df.empty:
        return {
            'total_flagged': 0,
            'total_amount': 0,
            'count': 0,
            'top_category': 'N/A',
            'top_amount': 0,
                    'detail': 'No overstated expenses detected.'
        }
    
    top_category = results_df.iloc[0]['category'] if len(results_df) > 0 else 'N/A'
    top_amount = results_df.iloc[0]['transaction_amount'] if len(results_df) > 0 else 0
    return {
        'total_flagged': len(results_df),
        'total_amount': results_df['transaction_amount'].sum(),
        'count': len(results_df),
        'top_category': top_category,
        'top_amount': top_amount,
        'detail': f'{len(results_df)} overstated expense categories. Top: {top_category} (NGN {top_amount:,.2f})'
    }
