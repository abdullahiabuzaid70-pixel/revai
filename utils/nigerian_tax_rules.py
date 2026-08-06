"""
Nigerian Tax Rules — hardcoded for RevAI v1
All rates and penalties based on FIRS and Nigerian tax law as of 2026
"""

# Tax rates
VAT_RATE = 0.075  # 7.5%

WHT_RATES = {
    "rent": 0.10,          # 10% for rent
    "consultancy": 0.10,   # 10% for professional services
    "management": 0.10,    # 10% for management services
    "contract": 0.05,      # 5% for contracts
    "interest": 0.10,      # 10% for interest
    "dividend": 0.10,      # 10% for dividends
    "royalty": 0.10,       # 10% for royalties
    "commission": 0.10,    # 10% for commissions
    "default": 0.05,      # 5% default
}

# Filing deadlines (day of month following the tax period)
FILING_DEADLINES = {
    "VAT": 21,      # 21st of following month
    "PAYE": 10,     # 10th of following month
    "WHT": 21,      # 21st of following month
    "CIT": None,    # Quarterly for large companies, annual for SMEs
}

# Penalties
VAT_LATE_PENALTY_FIRST_MONTH = 25000  # ₦25,000
VAT_LATE_PENALTY_DAILY = 200          # ₦2,000/day (CAMA)
PAYE_LATE_PENALTY_FIRST_MONTH = 25000
PAYE_LATE_PENALTY_DAILY = 2000       # ₦2,000/day
WHT_LATE_PENALTY = 25000            # ₦25,000 flat for non-remittance

# Interest on unremitted tax (CBN Monetary Policy Rate based)
INTEREST_RATE = 0.15  # 15% per annum (approximate)

# VAT exemption threshold — payments below this may not require VAT
VAT_THRESHOLD = 50000  # ₦50,000

# Expense categories that should always have VAT
VAT_APPLICABLE_CATEGORIES = [
    "rent", "consultancy", "management_fee", "contract", 
    "purchase", "supplies", "equipment", "software", "maintenance",
    "marketing", "advertising", "professional_fee", "cleaning",
    "security", "catering", "transport", "fuel"
]

# PAYE tax brackets (monthly, ₦)
PAYE_BRACKETS = [
    {"min": 0, "max": 300000, "rate": 0.07},       # First ₦300k — 7%
    {"min": 300000, "max": 600000, "rate": 0.11},   # Next ₦300k — 11%
    {"min": 600000, "max": 1100000, "rate": 0.15},  # Next ₦500k — 15%
    {"min": 1100000, "max": 1600000, "rate": 0.19}, # Next ₦500k — 19%
    {"min": 1600000, "max": 3200000, "rate": 0.21}, # Next ₦1.6M — 21%
    {"min": 3200000, "max": float('inf'), "rate": 0.24}, # Above ₦3.2M — 24%
]

# Pension contribution rate
PENSION_RATE = 0.10  # 10% of gross salary (employee + employer combined, minimum 8%)

# NHF (National Housing Fund)
NHF_RATE = 0.025  # 2.5% of gross salary

# Minimum wage (for reference)
MINIMUM_WAGE = 70000  # ₦70,000/month (2024 update)


def calculate_vat(amount):
    """Calculate VAT on a given amount."""
    return round(amount * VAT_RATE, 2)


def calculate_wht(amount, category="default"):
    """Calculate WHT based on payment category."""
    rate = WHT_RATES.get(category.lower(), WHT_RATES["default"])
    return round(amount * rate, 2)


def calculate_paye(annual_gross):
    """Calculate PAYE tax based on Nigerian tax brackets."""
    tax = 0
    remaining = annual_gross
    for bracket in PAYE_BRACKETS:
        if remaining <= 0:
            break
        taxable = min(remaining, bracket["max"] - bracket["min"])
        if annual_gross > bracket["min"]:
            tax += taxable * bracket["rate"]
            remaining -= taxable
    return round(tax, 2)


def calculate_late_penalty(tax_type, days_late):
    """Calculate penalty for late filing/remittance."""
    if tax_type == "VAT":
        if days_late <= 30:
            return VAT_LATE_PENALTY_FIRST_MONTH
        else:
            return VAT_LATE_PENALTY_FIRST_MONTH + (days_late - 30) * VAT_LATE_PENALTY_DAILY
    elif tax_type == "PAYE":
        if days_late <= 30:
            return PAYE_LATE_PENALTY_FIRST_MONTH
        else:
            return PAYE_LATE_PENALTY_FIRST_MONTH + (days_late - 30) * PAYE_LATE_PENALTY_DAILY
    elif tax_type == "WHT":
        return WHT_LATE_PENALTY
    else:
        return VAT_LATE_PENALTY_FIRST_MONTH


def should_have_vat(amount, category=""):
    """Check if a payment should have VAT applied."""
    if amount < VAT_THRESHOLD:
        return False
    if not category:
        return True  # Assume yes if no category info
    category_lower = category.lower()
    for cat in VAT_APPLICABLE_CATEGORIES:
        if cat in category_lower:
            return True
    return True  # Default: assume VAT applies
