"""
Sample Data Generator — creates realistic Nigerian company financial data
with known fraud patterns for demos and testing
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

random.seed(42)
np.random.seed(42)


def generate_sample_ap(n_transactions=500, months=6):
    """Generate realistic AP data with embedded fraud patterns."""
    start_date = datetime(2026, 1, 1)
    end_date = start_date + timedelta(days=30 * months)
    
    vendors = [
        "Dangote Industries Ltd", "Dangote Ind.", "DANGOTE INDUSTRIES LIMITED",
        " Julius Berger Nig Ltd", "Julius Berger PLC",
        "MTN Nigeria", "MTN Nig Ltd",
        "TotalEnergies Marketing", "Total Energies MKTG Nig",
        "BUA Cement PLC",
        "NNPC Retail Ltd",
        "Flutterwave Technologies",
        "Paystack Services Ltd",
        "Jumia Nigeria",
        "Konga Online",
        "Mr Price Logistics",
        "Glovo Nigeria",
        "First Bank of Nigeria",
        "Zenith Bank PLC",
        "Access Bank",
        "Airtel Networks",
        "Glo Mobile",
        "Lagos State Water Corp",
        "IKEDC Electricity",
        "Eko Electricity",
        # Ghost vendors (3)
        "Skyline Procurement Ltd",      # Ghost — not in master
        "Horizon Consulting Nig",         # Ghost — shares bank acct
        "Pinnacle Advisory Co",           # Ghost — single large payment
    ]
    
    categories = [
        "Fuel", "Office Supplies", "Consultancy", "Rent", "Marketing",
        "Transport", "Maintenance", "Equipment", "Software", "Security",
        "Cleaning", "Catering", "Professional Fees", "Contract", "Supplies"
    ]
    
    banks = [
        "0123456789", "9876543210", "1122334455", "9988776655",
        "4433221100", "5566778899", "1100998877", "2233445566"
    ]
    
    data = []
    
    # Normal transactions
    for i in range(n_transactions - 15):  # Reserve 15 for fraud patterns
        vendor = random.choice(vendors[:26])  # Exclude ghost vendors
        date = start_date + timedelta(days=random.randint(0, 30 * months - 1))
        amount = round(random.uniform(50000, 2000000), 2)
        vat = round(amount * 0.075, 2) if random.random() > 0.2 else 0
        wht = round(amount * 0.05, 2) if random.random() > 0.3 else 0
        
        data.append({
            'transaction_date': date,
            'vendor_name': vendor,
            'invoice_number': f"INV-2026-{random.randint(1000, 9999)}",
            'amount': amount,
            'payment_method': random.choice(['Bank Transfer', 'Cheque', 'Online']),
            'payment_date': date + timedelta(days=random.randint(1, 5)),
            'vat_amount': vat,
            'wht_amount': wht,
            'expense_category': random.choice(categories),
            'bank_account': random.choice(banks)
        })
    
    # === FRAUD PATTERN 1: 15 Duplicate Payments ===
    for _ in range(15):
        vendor = random.choice(vendors[:20])
        date1 = start_date + timedelta(days=random.randint(0, 30 * months - 1))
        date2 = date1 + timedelta(days=random.randint(1, 14))
        amount = round(random.uniform(100000, 800000), 2)
        inv = f"INV-2026-{random.randint(1000, 9999)}"
        
        for date in [date1, date2]:
            data.append({
                'transaction_date': date,
                'vendor_name': vendor,
                'invoice_number': inv,  # Same invoice number = duplicate
                'amount': amount,  # Same amount
                'payment_method': 'Bank Transfer',
                'payment_date': date,
                'vat_amount': round(amount * 0.075, 2),
                'wht_amount': 0,
                'expense_category': random.choice(categories),
                'bank_account': random.choice(banks)
            })
    
    # === FRAUD PATTERN 2: 10 Missing VAT Remittances ===
    for _ in range(10):
        vendor = random.choice(vendors[:20])
        date = start_date + timedelta(days=random.randint(0, 30 * months - 1))
        amount = round(random.uniform(200000, 1000000), 2)
        
        data.append({
            'transaction_date': date,
            'vendor_name': vendor,
            'invoice_number': f"INV-2026-{random.randint(1000, 9999)}",
            'amount': amount,
            'payment_method': 'Bank Transfer',
            'payment_date': date,
            'vat_amount': round(amount * 0.075, 2),  # VAT deducted but never remitted
            'wht_amount': 0,
            'expense_category': random.choice(categories),
            'bank_account': random.choice(banks)
        })
    
    # === FRAUD PATTERN 3: 8 Overstated Expenses ===
    for _ in range(8):
        vendor = random.choice(vendors[:20])
        date = start_date + timedelta(days=random.randint(0, 30 * months - 1))
        amount = round(random.uniform(5000000, 15000000), 2)  # Abnormally high
        
        data.append({
            'transaction_date': date,
            'vendor_name': vendor,
            'invoice_number': f"INV-2026-{random.randint(1000, 9999)}",
            'amount': amount,
            'payment_method': 'Bank Transfer',
            'payment_date': date,
            'vat_amount': 0,
            'wht_amount': 0,
            'expense_category': random.choice(['Consultancy', 'Marketing', 'Maintenance']),
            'bank_account': random.choice(banks)
        })
    
    # Add 3 round-number suspicious payments
    for _ in range(3):
        date = start_date + timedelta(days=random.randint(0, 30 * months - 1))
        amount = random.choice([500000, 1000000, 2000000])
        data.append({
            'transaction_date': date,
            'vendor_name': random.choice(vendors[:10]),
            'invoice_number': f"INV-2026-{random.randint(1000, 9999)}",
            'amount': float(amount),
            'payment_method': 'Bank Transfer',
            'payment_date': date,
            'vat_amount': 0,
            'wht_amount': 0,
            'expense_category': 'Supplies',
            'bank_account': random.choice(banks)
        })
    
    # === FRAUD PATTERN 4: Ghost Vendors ===
    # Skyline Procurement — not in master, multiple payments
    for _ in range(5):
        date = start_date + timedelta(days=random.randint(0, 30 * months - 1))
        amount = round(random.uniform(300000, 700000), 2)
        data.append({
            'transaction_date': date,
            'vendor_name': "Skyline Procurement Ltd",
            'invoice_number': f"INV-2026-{random.randint(1000, 9999)}",
            'amount': amount,
            'payment_method': 'Bank Transfer',
            'payment_date': date,
            'vat_amount': 0,
            'wht_amount': 0,
            'expense_category': 'Consultancy',
            'bank_account': '6666555544'  # Unique account
        })
    
    # Horizon Consulting & Pinnacle Advisory — same bank account
    for vendor in ["Horizon Consulting Nig", "Pinnacle Advisory Co"]:
        date = start_date + timedelta(days=random.randint(0, 30 * months - 1))
        amount = round(random.uniform(400000, 800000), 2)
        data.append({
            'transaction_date': date,
            'vendor_name': vendor,
            'invoice_number': f"INV-2026-{random.randint(1000, 9999)}",
            'amount': amount,
            'payment_method': 'Bank Transfer',
            'payment_date': date,
            'vat_amount': 0,
            'wht_amount': 0,
            'expense_category': 'Professional Fees',
            'bank_account': '7777888899'  # Shared account
        })
    
    df = pd.DataFrame(data)
    df = df.sort_values('transaction_date').reset_index(drop=True)
    return df


def generate_sample_payroll(n_employees=50, months=6):
    """Generate payroll data with ghost employees."""
    start_date = datetime(2026, 1, 1)
    
    real_names = [
        "Adeyemi Johnson", "Fatima Bello", "Chinedu Okafor", "Aisha Mohammed",
        "Emeka Nwosu", "Zainab Yusuf", "Tunde Bakare", "Hauwa Ibrahim",
        "Obinna Eze", "Maryam Sani", "Kunle Adeyemi", "Halima Abubakar",
        "David Oluwole", "Rukayat Aliyu", "Samuel Okonkwo", "Ngozi Eze",
        "Yakubu Idris", "Blessing Okeke", "Ibrahim Musa", "Stella Okafor",
        "Ahmed Tijani", "Rita Eze", "Oluwaseun Adewale", "Bilkisu Bello",
        "Chukwuemeka Obi", "Jummai Loko", "Dauda Adamu", "Comfort Bassey",
        "Nasir Usman", "Patience Okoro", "Bashir Shehu", "Grace Okon",
        "Musa Garba", "Adaeze Nwankwo", "Aliyu Baba", "Joy Ani",
        "Sadiq Bello", "Ogochukwu Eze", "Kabiru Salisu", "Amaka Obiora",
        "Umar Ali", "Titilayo Adewumi", "Mustapha Maude", "Bola Tinubu-Ojo",
        "Garba Sani", "Ifeoma Obi", "Mohammed Danjuma", "Funke Ojo",
        "Ibrahim Bello", "Catherine Okonkwo"
    ]
    
    # 3 ghost employees
    ghost_names = ["Ghost Employee A", "Test Staff X", "Unknown Worker Z"]
    ghost_banks = ["5555444433", "5555444433", "6666677777"]  # Two share same bank
    
    data = []
    
    for month_num in range(months):
        month = start_date + timedelta(days=30 * month_num)
        
        for name in real_names:
            gross = round(random.uniform(150000, 800000), 2)
            paye = round(gross * 0.10, 2)  # Simplified PAYE
            pension = round(gross * 0.08, 2)
            bank = f"BA{random.randint(10000000, 99999999)}"
            
            data.append({
                'month': month.strftime('%Y-%m-%d'),
                'employee_name': name,
                'gross_salary': gross,
                'paye_amount': paye,
                'pension_amount': pension,
                'bank_account': bank,
                'department': random.choice(['Finance', 'Operations', 'Sales', 'IT', 'Admin'])
            })
        
        # Ghost employees
        for i, name in enumerate(ghost_names):
            gross = round(random.uniform(300000, 600000), 2)
            data.append({
                'month': month.strftime('%Y-%m-%d'),
                'employee_name': name,
                'gross_salary': gross,
                'paye_amount': 0,  # No PAYE — ghost
                'pension_amount': 0,  # No pension — ghost
                'bank_account': ghost_banks[i],
                'department': 'Operations'
            })
    
    df = pd.DataFrame(data)
    return df


def generate_sample_tax_remittances():
    """Generate partial tax remittances (some months missing)."""
    data = [
        {'remittance_date': '2026-02-18', 'tax_type': 'VAT', 'period_covered': '2026-01', 'amount': 450000, 'revenue_agency': 'FIRS'},
        {'remittance_date': '2026-03-19', 'tax_type': 'VAT', 'period_covered': '2026-02', 'amount': 520000, 'revenue_agency': 'FIRS'},
        {'remittance_date': '2026-02-08', 'tax_type': 'PAYE', 'period_covered': '2026-01', 'amount': 280000, 'revenue_agency': 'FIRS'},
        {'remittance_date': '2026-03-08', 'tax_type': 'PAYE', 'period_covered': '2026-02', 'amount': 295000, 'revenue_agency': 'FIRS'},
        {'remittance_date': '2026-02-20', 'tax_type': 'WHT', 'period_covered': '2026-01', 'amount': 120000, 'revenue_agency': 'FIRS'},
    ]
    return pd.DataFrame(data)


def generate_sample_vendor_master():
    """Generate vendor master list (excludes ghost vendors)."""
    real_vendors = [
        "Dangote Industries Ltd", "Julius Berger Nig Ltd", "MTN Nigeria",
        "TotalEnergies Marketing", "BUA Cement PLC", "NNPC Retail Ltd",
        "Flutterwave Technologies", "Paystack Services Ltd", "Jumia Nigeria",
        "Konga Online", "Mr Price Logistics", "Glovo Nigeria",
        "First Bank of Nigeria", "Zenith Bank PLC", "Access Bank",
        "Airtel Networks", "Glo Mobile", "Lagos State Water Corp",
        "IKEDC Electricity", "Eko Electricity"
    ]
    
    data = []
    for v in real_vendors:
        data.append({
            'vendor_name': v,
            'vendor_id': f"V{random.randint(1000, 9999)}",
            'bank_account': f"BA{random.randint(10000000, 99999999)}",
            'address': f"{random.randint(1, 100)} Example Street, Lagos",
            'date_added': datetime(2025, random.randint(1, 12), random.randint(1, 28)).strftime('%Y-%m-%d')
        })
    
    return pd.DataFrame(data)


def generate_sample_employee_master():
    """Generate employee master list (excludes ghost employees)."""
    real_names = [
        "Adeyemi Johnson", "Fatima Bello", "Chinedu Okafor", "Aisha Mohammed",
        "Emeka Nwosu", "Zainab Yusuf", "Tunde Bakare", "Hauwa Ibrahim",
        "Obinna Eze", "Maryam Sani", "Kunle Adeyemi", "Halima Abubakar",
        "David Oluwole", "Rukayat Aliyu", "Samuel Okonkwo", "Ngozi Eze",
        "Yakubu Idris", "Blessing Okeke", "Ibrahim Musa", "Stella Okafor",
        "Ahmed Tijani", "Rita Eze", "Oluwaseun Adewale", "Bilkisu Bello",
        "Chukwuemeka Obi", "Jummai Loko", "Dauda Adamu", "Comfort Bassey",
        "Nasir Usman", "Patience Okoro", "Bashir Shehu", "Grace Okon",
        "Musa Garba", "Adaeze Nwankwo", "Aliyu Baba", "Joy Ani",
        "Sadiq Bello", "Ogochukwu Eze", "Kabiru Salisu", "Amaka Obiora",
        "Umar Ali", "Titilayo Adewumi", "Mustapha Maude", "Bola Tinubu-Ojo",
        "Garba Sani", "Ifeoma Obi", "Mohammed Danjuma", "Funke Ojo",
        "Ibrahim Bello", "Catherine Okonkwo"
    ]
    
    data = []
    for name in real_names:
        data.append({
            'employee_name': name,
            'employee_id': f"E{random.randint(1000, 9999)}",
            'bank_account': f"BA{random.randint(10000000, 99999999)}",
            'date_joined': datetime(2020 + random.randint(0, 5), random.randint(1, 12), random.randint(1, 28)).strftime('%Y-%m-%d'),
            'status': 'Active'
        })
    
    return pd.DataFrame(data)


def generate_all_sample_data():
    """Generate all sample datasets and return as dict of DataFrames."""
    return {
        'ap': generate_sample_ap(),
        'payroll': generate_sample_payroll(),
        'tax_remittance': generate_sample_tax_remittances(),
        'vendor_master': generate_sample_vendor_master(),
        'employee_master': generate_sample_employee_master()
    }
