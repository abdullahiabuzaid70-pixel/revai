"""
Data Loader — handles CSV/XLS parsing, validation, and column mapping
"""
import pandas as pd
import streamlit as st
from io import BytesIO


# Expected columns for each data type
EXPECTED_COLUMNS = {
    "ap": {
        "required": ["transaction_date", "vendor_name", "amount"],
        "optional": ["invoice_number", "payment_method", "payment_date", "vat_amount", "wht_amount", "expense_category", "bank_account"],
        "label": "Accounts Payable (AP)"
    },
    "payroll": {
        "required": ["month", "employee_name", "gross_salary"],
        "optional": ["paye_amount", "pension_amount", "bank_account", "department"],
        "label": "Payroll"
    },
    "tax_remittance": {
        "required": ["remittance_date", "tax_type", "amount"],
        "optional": ["period_covered", "revenue_agency"],
        "label": "Tax Remittances"
    },
    "vendor_master": {
        "required": ["vendor_name"],
        "optional": ["vendor_id", "bank_account", "address", "date_added"],
        "label": "Vendor Master List"
    },
    "employee_master": {
        "required": ["employee_name"],
        "optional": ["employee_id", "bank_account", "date_joined", "status"],
        "label": "Employee Master List"
    }
}


def read_uploaded_file(uploaded_file):
    """Read an uploaded CSV or Excel file into a DataFrame."""
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith('.xlsx') or uploaded_file.name.endswith('.xls'):
            df = pd.read_excel(uploaded_file)
        else:
            st.error(f"Unsupported file format: {uploaded_file.name}. Please upload CSV or Excel.")
            return None
        return df
    except Exception as e:
        st.error(f"Error reading {uploaded_file.name}: {str(e)}")
        return None


def normalize_columns(df):
    """Normalize column names — lowercase, strip, replace spaces with underscores."""
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('-', '_')
    return df


def validate_data(df, data_type):
    """
    Validate a DataFrame against expected columns.
    Returns: (is_valid, missing_required, available_optional, all_columns)
    """
    spec = EXPECTED_COLUMNS.get(data_type, {})
    if not spec:
        return False, [], [], list(df.columns)
    
    df_cols = set(df.columns)
    required = spec["required"]
    optional = spec["optional"]
    
    missing_required = [c for c in required if c not in df_cols]
    available_optional = [c for c in optional if c in df_cols]
    
    is_valid = len(missing_required) == 0
    
    return is_valid, missing_required, available_optional, list(df.columns)


def auto_map_columns(df, data_type):
    """
    Attempt to auto-map common column name variations to RevAI's expected names.
    e.g., 'Vendor' -> 'vendor_name', 'Amount (NGN)' -> 'amount'
    """
    mapping_suggestions = {
        "vendor_name": ["vendor", "supplier", "payee", "vendor_name", "name", "beneficiary", "supplier_name"],
        "amount": ["amount", "amount_ngn", "amount_naira", "value", "payment_amount", "total", "sum", "cost", "price"],
        "transaction_date": ["transaction_date", "date", "txn_date", "payment_date", "post_date", "entry_date", "doc_date"],
        "payment_date": ["payment_date", "paid_date", "settlement_date", "disbursement_date"],
        "invoice_number": ["invoice", "invoice_no", "invoice_number", "inv", "ref", "reference", "doc_number", "document_number", "txn_ref"],
        "vat_amount": ["vat", "vat_amount", "value_added_tax", "tax_amount"],
        "wht_amount": ["wht", "wht_amount", "withholding_tax", "withholding"],
        "expense_category": ["category", "expense_category", "gl_account", "account", "description", "narration", "particulars", "expense_type", "cost_center"],
        "bank_account": ["bank_account", "account_number", "bank_acct", "account_no", "account"],
        "employee_name": ["employee", "employee_name", "staff_name", "name", "worker", "personnel"],
        "gross_salary": ["gross_salary", "gross", "gross_pay", "salary", "monthly_salary", "pay", "wage", "emolument"],
        "paye_amount": ["paye", "paye_amount", "tax", "income_tax", "paye_deduction"],
        "pension_amount": ["pension", "pension_amount", "cpf", "pension_contribution"],
        "month": ["month", "period", "pay_period", "salary_month", "pay_month"],
        "department": ["department", "dept", "unit", "division", "cost_center"],
        "remittance_date": ["remittance_date", "date", "payment_date", "remittance"],
        "tax_type": ["tax_type", "type", "tax", "tax_category"],
        "revenue_agency": ["revenue_agency", "agency", "collector", "paid_to"],
        "period_covered": ["period_covered", "period", "tax_period", "month"],
        "vendor_id": ["vendor_id", "id", "vendor_code", "supplier_id", "code"],
        "address": ["address", "location", "addr", "street"],
        "date_added": ["date_added", "created_date", "onboarded", "registration_date", "start_date"],
        "employee_id": ["employee_id", "id", "staff_id", "employee_code", "staff_no"],
        "date_joined": ["date_joined", "hire_date", "start_date", "employment_date"],
        "status": ["status", "active", "employment_status"],
        "payment_method": ["payment_method", "method", "channel", "payment_type", "mode_of_payment"],
    }
    
    spec = EXPECTED_COLUMNS.get(data_type, {})
    all_expected = spec.get("required", []) + spec.get("optional", [])
    
    mapping = {}
    df_cols_lower = {c.lower(): c for c in df.columns}
    
    for expected_col in all_expected:
        suggestions = mapping_suggestions.get(expected_col, [expected_col])
        for suggestion in suggestions:
            if suggestion in df_cols_lower:
                mapping[df_cols_lower[suggestion]] = expected_col
                break
    
    return mapping


def apply_mapping(df, mapping):
    """Apply column mapping to rename DataFrame columns."""
    return df.rename(columns=mapping)


def get_data_summary(df, data_type):
    """Return a summary of the loaded data."""
    summary = {
        "rows": len(df),
        "columns": list(df.columns),
        "date_range": None,
        "total_amount": None,
    }
    
    # Date range
    date_cols = [c for c in df.columns if 'date' in c.lower()]
    for col in date_cols:
        try:
            dates = pd.to_datetime(df[col], errors='coerce').dropna()
            if len(dates) > 0:
                summary["date_range"] = (dates.min().strftime('%Y-%m-%d'), dates.max().strftime('%Y-%m-%d'))
                break
        except:
            pass
    
    # Total amount
    if 'amount' in df.columns:
        summary["total_amount"] = f"₦{df['amount'].sum():,.2f}"
    elif 'gross_salary' in df.columns:
        summary["total_amount"] = f"₦{df['gross_salary'].sum():,.2f}"
    
    return summary


def generate_data_template(data_type):
    """Generate a downloadable template CSV for the specified data type."""
    spec = EXPECTED_COLUMNS.get(data_type, {})
    columns = spec.get("required", []) + spec.get("optional", [])
    df = pd.DataFrame(columns=columns)
    
    output = BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return output, f"revai_{data_type}_template.csv"
