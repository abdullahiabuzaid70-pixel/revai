# RevAI - AI Revenue & Fraud Detection for African Companies

> Upload your financial data. We find your leaked money. You pay us 10% of what we recover.

## What It Does

RevAI scans company financial data (AP, Payroll, Tax) and finds money quietly leaking out through 5 automated detections:

1. **Duplicate Payments** - Same invoice paid twice, or near-duplicate amounts to same vendor within 30 days
2. **Unremitted VAT/WHT** - VAT/Withholding Tax deducted but never remitted to FIRS
3. **Overstated Expenses** - Abnormally high spending, round-number fraud patterns, statistical outliers
4. **Ghost Vendors/Employees** - Payments to entities not in master lists, shared bank accounts, missing PAYE/pension
5. **Late Tax Filing Risk** - Missed filing deadlines with estimated penalty exposure

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Add your OpenAI API key
cp .env.example .env
# Edit .env and add your key

# Run the app
streamlit run app.py
```

Then click "Use Sample Data (Demo)" in the sidebar to instantly load realistic Nigerian company data with known fraud patterns.

## Tech Stack

- **Frontend:** Streamlit (Python web app framework)
- **Data Processing:** Pandas, NumPy
- **Vendor Matching:** FuzzyWuzzy (fuzzy string matching)
- **AI Summary:** OpenAI GPT-4o-mini (optional - falls back to template if no API key)
- **PDF Generation:** fpdf2
- **Tax Rules:** Hardcoded Nigerian tax rates (VAT 7.5%, WHT by category, PAYE brackets, penalties)

## File Structure

```
revai/
  app.py                         # Main Streamlit application
  requirements.txt               # Python dependencies
  .env.example                   # Environment variable template
  detectors/
    duplicate_payments.py        # Detection 1: Duplicate payments
    vat_wht_remittance.py        # Detection 2: VAT/WHT issues
    overstated_expenses.py       # Detection 3: Overstated expenses
    ghost_vendors_employees.py   # Detection 4: Ghost vendors/employees
    tax_filing_risk.py           # Detection 5: Tax filing risk
  utils/
    data_loader.py              # CSV/XLS parsing, validation, column mapping
    fuzzy_matcher.py             # Vendor name normalization & fuzzy matching
    nigerian_tax_rules.py        # Nigerian tax rates, penalties, brackets
    sample_data_generator.py    # Generates realistic demo data with known fraud
    report_generator.py         # 1-page PDF Leakage Report
```

## Data Input Format

RevAI accepts CSV or Excel files. Download templates from the app sidebar.

**Required (minimum):** Accounts Payable (transaction_date, vendor_name, amount)
**Optional but improves accuracy:** Payroll, Tax Remittances, Vendor Master, Employee Master

## Deployment

### Option 1: Streamlit Community Cloud (FREE)
1. Push to GitHub
2. Go to share.streamlit.io
3. Connect repo, set main file as app.py
4. Add OPENAI_API_KEY as secret

### Option 2: Railway ($5/mo)
1. Push to GitHub
2. Create new project on Railway
3. Connect repo
4. Add env var: OPENAI_API_KEY
5. Deploy command: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`

### Option 3: Local
```bash
streamlit run app.py
```

## Business Model

- **Free audit:** Upload data, get the Leakage Report, no cost
- **If we find nothing:** You owe nothing
- **If we find money:** $500/month for ongoing monitoring OR 10% of first-year savings
- **Accounting firm partnership:** They run RevAI on client data, keep 80% of what they charge, RevAI takes 20%

## Roadmap

**v1 (MVP - now):**
- 5 detection rules
- CSV/XLS upload
- Dashboard + PDF report
- Sample data generator
- No database, no auth

**v2:**
- User accounts & auth
- PostgreSQL database
- Saved reports & history
- Scheduled recurring scans
- Email alerts for new findings

**v3:**
- API for accounting firms (white-label)
- Bank integration (Open Banking)
- Custom ML models for pattern detection
- Multi-company dashboard

**v4:**
- Direct FIRS/IRS integration
- Automated tax filing
- Government B2B contracts

## License

Proprietary - All rights reserved.
