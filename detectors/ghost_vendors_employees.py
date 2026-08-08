"""
Detection 4: Ghost Vendors / Ghost Employees
Finds vendors or employees receiving payments who shouldn't be
"""
import pandas as pd
from utils.fuzzy_matcher import normalize_vendor_name


def detect_ghost_vendors(df_ap, df_vendor_master=None):
    """
    Detect ghost vendors in AP data.
    
    Returns DataFrame with columns:
    - name, type, bank_account, red_flag_reason, total_paid, risk_level, details
    """
    if df_ap is None or df_ap.empty or 'vendor_name' not in df_ap.columns:
        return pd.DataFrame()
    
    results = []
    df = df_ap.copy()
    df['vendor_normalized'] = df['vendor_name'].apply(normalize_vendor_name)
    
    # Flag 1: Payments to vendors not in master list
    if df_vendor_master is not None and not df_vendor_master.empty and 'vendor_name' in df_vendor_master.columns:
        master_normalized = set(df_vendor_master['vendor_name'].apply(normalize_vendor_name))
        
        unknown_vendors = df[~df['vendor_normalized'].isin(master_normalized)]
        for vendor, group in unknown_vendors.groupby('vendor_normalized'):
            total_paid = group['amount'].sum()
            bank = group['bank_account'].iloc[0] if 'bank_account' in group.columns and len(group) > 0 else 'N/A'
            results.append({
                'name': group['vendor_name'].iloc[0],
                'type': 'Ghost Vendor',
                'bank_account': str(bank),
                'red_flag_reason': 'Not in vendor master list',
                'total_paid': total_paid,
                'risk_level': 'High' if total_paid >= 500000 else 'Medium',
                'details': f"Vendor '{group['vendor_name'].iloc[0]}' received NGN {total_paid:,.2f} but is not in the approved vendor master list"
            })
    
    # Flag 2: Multiple vendors sharing the same bank account
    if 'bank_account' in df.columns:
        bank_groups = df[df['bank_account'].notna() & (df['bank_account'] != '')].groupby('bank_account')
        
        for bank_acct, group in bank_groups:
            unique_vendors = group['vendor_normalized'].nunique()
            if unique_vendors > 1:
                vendor_list = group['vendor_name'].unique().tolist()
                total_paid = group['amount'].sum()
                results.append({
                    'name': ' / '.join(vendor_list[:3]),
                    'type': 'Ghost Vendor',
                    'bank_account': str(bank_acct),
                    'red_flag_reason': f'{unique_vendors} vendors sharing same bank account',
                    'total_paid': total_paid,
                    'risk_level': 'High' if total_paid >= 500000 else 'Medium',
                    'details': f"Multiple vendors ({', '.join(vendor_list[:3])}) all pay to bank account {bank_acct}. Total: NGN {total_paid:,.2f}"
                })
    
    # Flag 3: Vendor with only one payment ever (hit-and-run pattern)
    vendor_payment_counts = df.groupby('vendor_normalized').agg({
        'amount': ['sum', 'count'],
        'vendor_name': 'first'
    }).reset_index()
    vendor_payment_counts.columns = ['vendor_normalized', 'total_amount', 'payment_count', 'vendor_name']
    
    one_payment_vendors = vendor_payment_counts[
        (vendor_payment_counts['payment_count'] == 1) & 
        (vendor_payment_counts['total_amount'] >= 1000000)
    ]
    
    for _, row in one_payment_vendors.iterrows():
        vendor_data = df[df['vendor_normalized'] == row['vendor_normalized']]
        bank = vendor_data['bank_account'].iloc[0] if 'bank_account' in vendor_data.columns and len(vendor_data) > 0 else 'N/A'
        results.append({
            'name': row['vendor_name'],
            'type': 'Ghost Vendor',
            'bank_account': str(bank),
            'red_flag_reason': 'Single large payment (hit-and-run pattern)',
            'total_paid': row['total_amount'],
            'risk_level': 'Medium' if row['total_amount'] >= 5000000 else 'Low',
            'details': f"Vendor '{row['vendor_name']}' received only one payment of NGN {row['total_amount']:,.2f} — potential ghost vendor"
        })
    
    # Flag 4: Vendor created and paid within same week (if date_added available in master)
    if df_vendor_master is not None and not df_vendor_master.empty:
        if 'date_added' in df_vendor_master.columns and 'vendor_name' in df_vendor_master.columns:
            master = df_vendor_master.copy()
            master['date_added'] = pd.to_datetime(master['date_added'], errors='coerce')
            master['vendor_normalized'] = master['vendor_name'].apply(normalize_vendor_name)
            
            date_col = 'payment_date' if 'payment_date' in df.columns else 'transaction_date'
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                
                for _, m_row in master.iterrows():
                    if pd.isna(m_row['date_added']):
                        continue
                    vendor_payments = df[df['vendor_normalized'] == m_row['vendor_normalized']]
                    if vendor_payments.empty:
                        continue
                    first_payment = vendor_payments[date_col].min()
                    if pd.isna(first_payment):
                        continue
                    days_to_payment = (first_payment - m_row['date_added']).days
                    if 0 <= days_to_payment <= 7:
                        total_paid = vendor_payments['amount'].sum()
                        results.append({
                            'name': m_row['vendor_name'],
                            'type': 'Ghost Vendor',
                            'bank_account': str(m_row.get('bank_account', 'N/A')),
                            'red_flag_reason': 'Created and paid within same week',
                            'total_paid': total_paid,
                            'risk_level': 'Medium',
                            'details': f"Vendor '{m_row['vendor_name']}' was added to master list on {m_row['date_added'].strftime('%Y-%m-%d')} and received first payment within {days_to_payment} days"
                        })
    
    if not results:
        return pd.DataFrame()
    
    result_df = pd.DataFrame(results)
    result_df = result_df.drop_duplicates(subset=['name', 'red_flag_reason'])
    result_df = result_df.sort_values('total_paid', ascending=False)
    return result_df


def detect_ghost_employees(df_payroll, df_employee_master=None):
    """
    Detect ghost employees in payroll data.
    
    Returns DataFrame with columns:
    - name, type, bank_account, red_flag_reason, total_paid, risk_level, details
    """
    if df_payroll is None or df_payroll.empty or 'employee_name' not in df_payroll.columns:
        return pd.DataFrame()
    
    results = []
    df = df_payroll.copy()
    df['employee_normalized'] = df['employee_name'].apply(lambda x: normalize_vendor_name(str(x)))
    
    # Flag 1: Employees not in master list
    if df_employee_master is not None and not df_employee_master.empty and 'employee_name' in df_employee_master.columns:
        master_normalized = set(df_employee_master['employee_name'].apply(lambda x: normalize_vendor_name(str(x))))
        
        unknown_employees = df[~df['employee_normalized'].isin(master_normalized)]
        for emp, group in unknown_employees.groupby('employee_normalized'):
            total_paid = group['gross_salary'].sum()
            bank = group['bank_account'].iloc[0] if 'bank_account' in group.columns and len(group) > 0 else 'N/A'
            results.append({
                'name': group['employee_name'].iloc[0],
                'type': 'Ghost Employee',
                'bank_account': str(bank),
                'red_flag_reason': 'Not in employee master list',
                'total_paid': total_paid,
                'risk_level': 'High' if total_paid >= 1000000 else 'Medium',
                'details': f"Employee '{group['employee_name'].iloc[0]}' received NGN {total_paid:,.2f} in salary but is not in the HR/employee master list"
            })
    
    # Flag 2: Multiple employees sharing same bank account
    if 'bank_account' in df.columns:
        bank_groups = df[df['bank_account'].notna() & (df['bank_account'] != '')].groupby('bank_account')
        
        for bank_acct, group in bank_groups:
            unique_employees = group['employee_normalized'].nunique()
            if unique_employees > 1:
                emp_list = group['employee_name'].unique().tolist()
                total_paid = group['gross_salary'].sum()
                results.append({
                    'name': ' / '.join(emp_list[:3]),
                    'type': 'Ghost Employee',
                    'bank_account': str(bank_acct),
                    'red_flag_reason': f'{unique_employees} employees sharing same bank account',
                    'total_paid': total_paid,
                    'risk_level': 'High' if total_paid >= 1000000 else 'Medium',
                    'details': f"Multiple employees ({', '.join(emp_list[:3])}) all receive salary in bank account {bank_acct}. Total: NGN {total_paid:,.2f}"
                })
    
    # Flag 3: No PAYE deduction
    if 'paye_amount' in df.columns:
        no_paye = df[(df['paye_amount'] == 0) | (df['paye_amount'].isna())]
        for emp, group in no_paye.groupby('employee_normalized'):
            total_salary = group['gross_salary'].sum()
            if total_salary >= 600000:  # Above minimum wage threshold
                results.append({
                    'name': group['employee_name'].iloc[0],
                    'type': 'Ghost Employee',
                    'bank_account': str(group['bank_account'].iloc[0]) if 'bank_account' in group.columns and len(group) > 0 else 'N/A',
                    'red_flag_reason': 'No PAYE tax deduction',
                    'total_paid': total_salary,
                    'risk_level': 'Medium',
                    'details': f"Employee '{group['employee_name'].iloc[0]}' received NGN {total_salary:,.2f} salary with no PAYE tax deduction"
                })
    
    # Flag 4: No pension contribution
    if 'pension_amount' in df.columns:
        no_pension = df[(df['pension_amount'] == 0) | (df['pension_amount'].isna())]
        for emp, group in no_pension.groupby('employee_normalized'):
            total_salary = group['gross_salary'].sum()
            if total_salary >= 600000:  # Above threshold
                # Only flag if not already flagged for PAYE
                already_flagged = any(r['name'] == group['employee_name'].iloc[0] for r in results)
                if not already_flagged:
                    results.append({
                        'name': group['employee_name'].iloc[0],
                        'type': 'Ghost Employee',
                        'bank_account': str(group['bank_account'].iloc[0]) if 'bank_account' in group.columns and len(group) > 0 else 'N/A',
                        'red_flag_reason': 'No pension contribution',
                        'total_paid': total_salary,
                        'risk_level': 'Low',
                        'details': f"Employee '{group['employee_name'].iloc[0]}' received NGN {total_salary:,.2f} salary with no pension contribution"
                    })
    
    if not results:
        return pd.DataFrame()
    
    result_df = pd.DataFrame(results)
    result_df = result_df.drop_duplicates(subset=['name', 'red_flag_reason'])
    result_df = result_df.sort_values('total_paid', ascending=False)
    return result_df


def get_summary(results):
    """Return summary stats for ghost vendor/employee detection."""
    # Handle dict format with 'vendors' and 'employees' keys
    if isinstance(results, dict):
        all_dfs = []
        for key in ['vendors', 'employees']:
            df = results.get(key)
            if df is not None and isinstance(df, pd.DataFrame) and not df.empty:
                all_dfs.append(df)
        if not all_dfs:
            return {
                'total_flagged': 0,
                'total_amount': 0,
                'count': 0,
                'top_entity': 'N/A',
                'top_amount': 0,
                'detail': 'No ghost vendors or employees detected'
            }
        combined = pd.concat(all_dfs, ignore_index=True)
    elif results is None or (hasattr(results, 'empty') and results.empty):
        return {
            'total_flagged': 0,
            'total_amount': 0,
            'count': 0,
            'top_entity': 'N/A',
            'top_amount': 0,
            'detail': 'No ghost vendors or employees detected'
        }
    else:
        combined = results
    
    total_amount = combined['total_paid'].sum() if 'total_paid' in combined.columns and len(combined) > 0 else 0
    count = len(combined)
    top_name = combined.iloc[0]['name'] if len(combined) > 0 else 'N/A'
    top_amount = combined.iloc[0]['total_paid'] if len(combined) > 0 and 'total_paid' in combined.columns else 0
    
    return {
        'total_flagged': count,
        'total_amount': total_amount,
        'count': count,
        'top_entity': top_name,
        'top_amount': top_amount,
        'detail': f'{count} ghost entities detected. Top: {top_name} (NGN {top_amount:,.2f})'
    }
