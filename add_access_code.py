with open('app.py', 'r') as f:
    content = f.read()

# 1. Add is_unlocked to session state
content = content.replace(
    "    st.session_state.is_demo = False",
    "    st.session_state.is_demo = False\n    st.session_state.is_unlocked = False"
)

# 2. Add access code input in sidebar (after the "---" after Load Your Data section, before the scan button)
# Find the line with "Run Full Scan" button and add access code before it
# Actually, add it right before the scan button section. Let me find a good spot.
# Add it after the sidebar file uploaders, before the main content area.

# Find the line "st.sidebar.markdown("---")" that comes after the file uploaders
# Let's add it right before the "# === MAIN CONTENT ===" section

access_code_block = '''
# === ACCESS CODE (Unlock Full Access) ===
ACCESS_CODE = "REVAI-F4F49AD4"

if not st.session_state.get("is_demo", False):
    with st.sidebar:
        st.markdown("---")
        st.markdown("### Unlock Full Access")
        unlock_input = st.text_input("Enter Access Code", type="password", placeholder="Got a code? Enter it here")
        if unlock_input:
            if unlock_input.strip().upper() == ACCESS_CODE:
                st.session_state.is_unlocked = True
                st.sidebar.success("Access unlocked! Full findings enabled.")
            else:
                st.sidebar.error("Invalid code. Contact +234 704 929 4373")

'''

# Insert before "# === MAIN CONTENT ==="
content = content.replace("# === MAIN CONTENT ===", access_code_block + "# === MAIN CONTENT ===")

# 3. Now update all freemium checks to also check is_unlocked
# The pattern is: st.session_state.get("is_demo", False)
# We need: st.session_state.get("is_demo", False) or st.session_state.get("is_unlocked", False)

# For the PDF button condition
content = content.replace(
    'if st.session_state.get("is_demo", False) and st.button("Download PDF Report", type="primary", use_container_width=True):',
    'if (st.session_state.get("is_demo", False) or st.session_state.get("is_unlocked", False)) and st.button("Download PDF Report", type="primary", use_container_width=True):'
)

# For the PDF locked card
content = content.replace(
    'if not st.session_state.get("is_demo", False):\n                st.markdown("""\n                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 24px; text-align: center;">\n                    <p style="font-size: 16px; font-weight: 700; color: #0F172A; margin: 0 0 8px 0;">📄 PDF Report Locked</p>',
    'if not (st.session_state.get("is_demo", False) or st.session_state.get("is_unlocked", False)):\n                st.markdown("""\n                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 24px; text-align: center;">\n                    <p style="font-size: 16px; font-weight: 700; color: #0F172A; margin: 0 0 8px 0;">📄 PDF Report Locked</p>'
)

# For the Excel button condition
content = content.replace(
    'if st.session_state.get("is_demo", False) and st.button("Download Excel (All Findings)", type="primary", use_container_width=True):',
    'if (st.session_state.get("is_demo", False) or st.session_state.get("is_unlocked", False)) and st.button("Download Excel (All Findings)", type="primary", use_container_width=True):'
)

# For the Excel locked card
content = content.replace(
    'if not st.session_state.get("is_demo", False):\n                st.markdown("""\n                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 24px; text-align: center;">\n                    <p style="font-size: 16px; font-weight: 700; color: #0F172A; margin: 0 0 8px 0;">📊 Excel Export Locked</p>',
    'if not (st.session_state.get("is_demo", False) or st.session_state.get("is_unlocked", False)):\n                st.markdown("""\n                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 24px; text-align: center;">\n                    <p style="font-size: 16px; font-weight: 700; color: #0F172A; margin: 0 0 8px 0;">📊 Excel Export Locked</p>'
)

# For the free preview notice
content = content.replace(
    'if not st.session_state.get("is_demo", False):',
    'if not (st.session_state.get("is_demo", False) or st.session_state.get("is_unlocked", False)):'
)

# For ghost vendors table limit
content = content.replace(
    "if not st.session_state.get('is_demo', False) and len(vendor_df) > 3:",
    "if not (st.session_state.get('is_demo', False) or st.session_state.get('is_unlocked', False)) and len(vendor_df) > 3:"
)

# For ghost employees table limit
content = content.replace(
    "if not st.session_state.get('is_demo', False) and len(emp_df) > 3:",
    "if not (st.session_state.get('is_demo', False) or st.session_state.get('is_unlocked', False)) and len(emp_df) > 3:"
)

# For regular DataFrames limit
content = content.replace(
    "if not st.session_state.get('is_demo', False) and len(data) > 3:",
    "if not (st.session_state.get('is_demo', False) or st.session_state.get('is_unlocked', False)) and len(data) > 3:"
)

# 4. Add is_unlocked = False to the Load New Data reset
content = content.replace(
    "            st.session_state.is_demo = False\n            st.session_state.total_leakage = 0",
    "            st.session_state.is_demo = False\n            st.session_state.is_unlocked = False\n            st.session_state.total_leakage = 0"
)

with open('app.py', 'w') as f:
    f.write(content)

print("Access code added successfully")
