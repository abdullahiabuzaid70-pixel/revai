import re

with open('app.py', 'r') as f:
    content = f.read()

# 1. Add is_demo to session state init
content = content.replace(
    "    st.session_state.leakages = {}",
    "    st.session_state.leakages = {}\n    st.session_state.is_demo = False"
)

# 2. Set is_demo = True when demo button clicked
content = content.replace(
    "        st.session_state.data_loaded = True\n        if not company_name:\n            st.session_state.company_name = \"Demo Company Ltd\"",
    "        st.session_state.data_loaded = True\n        st.session_state.is_demo = True\n        if not company_name:\n            st.session_state.company_name = \"Demo Company Ltd\""
)

# 3. Set is_demo = False when real files uploaded
content = content.replace(
    "            st.session_state.data_loaded = True\n            st.session_state.company_name = company_name or \"Uploaded Company\"",
    "            st.session_state.data_loaded = True\n            st.session_state.is_demo = False\n            st.session_state.company_name = company_name or \"Uploaded Company\""
)

# 4. In detailed findings, limit to 3 rows for non-demo users
# For ghost vendors
content = content.replace(
    '                            st.markdown("**Ghost Vendors**")\n                            display_cols = [c for c in [\'name\', \'red_flag_reason\', \'total_paid\', \'risk_level\', \'bank_account\'] if c in data[\'vendors\'].columns]\n                            st.dataframe(data[\'vendors\'][display_cols], use_container_width=True, hide_index=True)',
    '                            st.markdown("**Ghost Vendors**")\n                            display_cols = [c for c in [\'name\', \'red_flag_reason\', \'total_paid\', \'risk_level\', \'bank_account\'] if c in data[\'vendors\'].columns]\n                            vendor_df = data[\'vendors\'][display_cols]\n                            if not st.session_state.get(\'is_demo\', False):\n                                vendor_df = vendor_df.head(3)\n                                st.dataframe(vendor_df, use_container_width=True, hide_index=True)\n                                if len(data[\'vendors\']) > 3:\n                                    st.markdown(f\'<p style="color: #64748B; font-size: 12px; padding: 8px 0;">Showing 3 of {len(data["vendors"])} ghost vendors. <strong>Contact +234 704 929 4373 to unlock full findings.</strong></p>\', unsafe_allow_html=True)\n                            else:\n                                st.dataframe(vendor_df, use_container_width=True, hide_index=True)'
)

# For ghost employees
content = content.replace(
    '                            st.markdown("**Ghost Employees**")\n                            display_cols = [c for c in [\'name\', \'red_flag_reason\', \'total_paid\', \'risk_level\', \'bank_account\'] if c in data[\'employees\'].columns]\n                            st.dataframe(data[\'employees\'][display_cols], use_container_width=True, hide_index=True)',
    '                            st.markdown("**Ghost Employees**")\n                            display_cols = [c for c in [\'name\', \'red_flag_reason\', \'total_paid\', \'risk_level\', \'bank_account\'] if c in data[\'employees\'].columns]\n                            emp_df = data[\'employees\'][display_cols]\n                            if not st.session_state.get(\'is_demo\', False):\n                                emp_df = emp_df.head(3)\n                                st.dataframe(emp_df, use_container_width=True, hide_index=True)\n                                if len(data[\'employees\']) > 3:\n                                    st.markdown(f\'<p style="color: #64748B; font-size: 12px; padding: 8px 0;">Showing 3 of {len(data["employees"])} ghost employees. <strong>Contact +234 704 929 4373 to unlock full findings.</strong></p>\', unsafe_allow_html=True)\n                            else:\n                                st.dataframe(emp_df, use_container_width=True, hide_index=True)'
)

# For regular DataFrames (duplicates, VAT/WHT, expenses, tax)
content = content.replace(
    '                    elif isinstance(data, pd.DataFrame) and len(data) > 0:\n                        st.dataframe(data, use_container_width=True, hide_index=True)',
    '                    elif isinstance(data, pd.DataFrame) and len(data) > 0:\n                        if not st.session_state.get(\'is_demo\', False) and len(data) > 3:\n                            st.dataframe(data.head(3), use_container_width=True, hide_index=True)\n                            st.markdown(f\'<p style="color: #64748B; font-size: 12px; padding: 8px 0;">Showing 3 of {len(data)} flagged items. <strong>Contact +234 704 929 4373 to unlock all {len(data)} findings.</strong></p>\', unsafe_allow_html=True)\n                        else:\n                            st.dataframe(data, use_container_width=True, hide_index=True)'
)

# 5. Lock PDF export for non-demo users
content = content.replace(
    '        if st.button("Download PDF Report", type="primary", use_container_width=True):',
    '        if st.session_state.get("is_demo", False):\n            if st.button("Download PDF Report", type="primary", use_container_width=True):'
)

# Find the end of the PDF button block and add else clause
# The PDF button block ends with the download_button for PDF
content = content.replace(
    "                        use_container_width=True\n                    )\n\n        with col2:",
    "                        use_container_width=True\n                    )\n        else:\n            st.markdown(\"\"\"\n            <div style=\"background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 24px; text-align: center;\">\n                <p style=\"font-size: 16px; font-weight: 700; color: #0F172A; margin: 0 0 8px 0;\">PDF Report Locked</p>\n                <p style=\"color: #64748B; font-size: 13px; margin: 0 0 12px 0;\">Get a full branded PDF report with all findings, vendor names, amounts, and recommended actions.</p>\n                <p style=\"color: #0F172A; font-size: 13px; font-weight: 600; margin: 0;\">WhatsApp: +234 704 929 4373</p>\n                <p style=\"color: #64748B; font-size: 12px; margin: 4px 0 0 0;\">abuzaidabdullahi531@gmail.com</p>\n            </div>\n            \"\"\", unsafe_allow_html=True)\n\n        with col2:"
)

# 6. Lock Excel export for non-demo users
content = content.replace(
    '            if st.button("Download Excel (All Findings)", type="primary", use_container_width=True):',
    '            if st.session_state.get("is_demo", False):\n            if st.button("Download Excel (All Findings)", type="primary", use_container_width=True):'
)

# Find the Excel download button end and add else
content = content.replace(
    "                    st.download_button(\n                        label=\"Download Excel\",\n                        data=output.getvalue(),\n                        file_name=f\"RevAI_Findings_{safe_name}_{datetime.now().strftime('%Y%m%d')}.xlsx\",\n                        mime=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\",\n                        use_container_width=True\n                    )\n\n        # === RECOMMENDED ACTIONS ===",
    "                    st.download_button(\n                        label=\"Download Excel\",\n                        data=output.getvalue(),\n                        file_name=f\"RevAI_Findings_{safe_name}_{datetime.now().strftime('%Y%m%d')}.xlsx\",\n                        mime=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\",\n                        use_container_width=True\n                    )\n            else:\n                st.markdown(\"\"\"\n                <div style=\"background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 24px; text-align: center;\">\n                    <p style=\"font-size: 16px; font-weight: 700; color: #0F172A; margin: 0 0 8px 0;\">Excel Export Locked</p>\n                    <p style=\"color: #64748B; font-size: 13px; margin: 0 0 12px 0;\">Get all findings in Excel format with vendor names, amounts, dates, and risk levels for your team.</p>\n                    <p style=\"color: #0F172A; font-size: 13px; font-weight: 600; margin: 0;\">WhatsApp: +234 704 929 4373</p>\n                    <p style=\"color: #64748B; font-size: 12px; margin: 4px 0 0 0;\">abuzaidabdullahi531@gmail.com</p>\n                </div>\n                \"\"\", unsafe_allow_html=True)\n\n        # === RECOMMENDED ACTIONS ==="
)

with open('app.py', 'w') as f:
    f.write(content)

print("Patch applied successfully")
