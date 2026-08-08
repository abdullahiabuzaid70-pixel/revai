with open('app.py', 'r') as f:
    lines = f.readlines()

new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # 1. Add is_demo to session state init (after leakages line)
    if "    st.session_state.leakages = {}" in line and "is_demo" not in line:
        new_lines.append(line)
        new_lines.append("    st.session_state.is_demo = False\n")
        i += 1
        continue
    
    # 2. Set is_demo = True when demo button clicked
    if "        st.session_state.data_loaded = True" in line and i + 1 < len(lines) and 'if not company_name:' in lines[i+1]:
        new_lines.append(line)
        new_lines.append("        st.session_state.is_demo = True\n")
        i += 1
        continue
    
    # 3. Set is_demo = False when real files uploaded
    if "            st.session_state.data_loaded = True" in line and i + 1 < len(lines) and 'st.session_state.company_name = company_name or' in lines[i+1]:
        new_lines.append(line)
        new_lines.append("            st.session_state.is_demo = False\n")
        i += 1
        continue
    
    # 4. PDF button - add demo check
    if 'if st.button("Download PDF Report", type="primary", use_container_width=True):' in line and 'is_demo' not in line:
        new_lines.append(line.replace(
            'if st.button("Download PDF Report", type="primary", use_container_width=True):',
            'if st.session_state.get("is_demo", False) and st.button("Download PDF Report", type="primary", use_container_width=True):'
        ))
        i += 1
        continue
    
    # 5. After PDF handler, before "with col2:", add locked card for non-demo
    if line.strip() == "        with col2:" and i > 0:
        # Check if previous non-empty line is the end of PDF download_button
        prev_idx = len(new_lines) - 1
        while prev_idx >= 0 and new_lines[prev_idx].strip() == "":
            prev_idx -= 1
        if prev_idx >= 0 and 'use_container_width=True' in new_lines[prev_idx] and 'Download PDF' not in new_lines[prev_idx]:
            # Insert locked card before "with col2:"
            new_lines.append("\n")
            new_lines.append("            if not st.session_state.get(\"is_demo\", False):\n")
            new_lines.append('                st.markdown("""\n')
            new_lines.append('                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 24px; text-align: center;">\n')
            new_lines.append('                    <p style="font-size: 16px; font-weight: 700; color: #0F172A; margin: 0 0 8px 0;">📄 PDF Report Locked</p>\n')
            new_lines.append('                    <p style="color: #64748B; font-size: 13px; margin: 0 0 12px 0;">Get a full branded PDF report with all findings, vendor names, and recommended actions.</p>\n')
            new_lines.append('                    <p style="color: #0F172A; font-size: 13px; font-weight: 600; margin: 0;">WhatsApp: +234 704 929 4373</p>\n')
            new_lines.append('                    <p style="color: #64748B; font-size: 12px; margin: 4px 0 0 0;">abuzaidabdullahi531@gmail.com</p>\n')
            new_lines.append('                </div>\n')
            new_lines.append('                """, unsafe_allow_html=True)\n')
            new_lines.append("\n")
    
    # 6. Excel button - add demo check  
    if 'if st.button("Download Excel (All Findings)", type="primary", use_container_width=True):' in line and 'is_demo' not in line:
        new_lines.append(line.replace(
            'if st.button("Download Excel (All Findings)", type="primary", use_container_width=True):',
            'if st.session_state.get("is_demo", False) and st.button("Download Excel (All Findings)", type="primary", use_container_width=True):'
        ))
        i += 1
        continue
    
    # 7. After Excel handler, before "=== DETAILED FINDINGS TABS ===", add locked card
    if "=== DETAILED FINDINGS TABS ===" in line:
        new_lines.append("\n")
        new_lines.append("            if not st.session_state.get(\"is_demo\", False):\n")
        new_lines.append('                st.markdown("""\n')
        new_lines.append('                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 24px; text-align: center;">\n')
        new_lines.append('                    <p style="font-size: 16px; font-weight: 700; color: #0F172A; margin: 0 0 8px 0;">📊 Excel Export Locked</p>\n')
        new_lines.append('                    <p style="color: #64748B; font-size: 13px; margin: 0 0 12px 0;">Get all findings in Excel with vendor names, amounts, dates, and risk levels.</p>\n')
        new_lines.append('                    <p style="color: #0F172A; font-size: 13px; font-weight: 600; margin: 0;">WhatsApp: +234 704 929 4373</p>\n')
        new_lines.append('                    <p style="color: #64748B; font-size: 12px; margin: 4px 0 0 0;">abuzaidabdullahi531@gmail.com</p>\n')
        new_lines.append('                </div>\n')
        new_lines.append('                """, unsafe_allow_html=True)\n')
        new_lines.append("\n")
    
    # 8. Limit ghost vendors table to 3 rows for non-demo
    if 'st.dataframe(data[\'vendors\'][display_cols], use_container_width=True, hide_index=True)' in line:
        indent = line[:len(line) - len(line.lstrip())]
        new_lines.append(indent + "vendor_df = data['vendors'][display_cols]\n")
        new_lines.append(indent + "if not st.session_state.get('is_demo', False) and len(vendor_df) > 3:\n")
        new_lines.append(indent + "    st.dataframe(vendor_df.head(3), use_container_width=True, hide_index=True)\n")
        new_lines.append(indent + "    st.markdown(f'<p style=\"color: #64748B; font-size: 12px; padding: 8px 0;\">Showing 3 of {len(vendor_df)} ghost vendors. <strong>Contact +234 704 929 4373 to unlock all findings.</strong></p>', unsafe_allow_html=True)\n")
        new_lines.append(indent + "else:\n")
        new_lines.append(indent + "    st.dataframe(vendor_df, use_container_width=True, hide_index=True)\n")
        i += 1
        continue
    
    # 9. Limit ghost employees table to 3 rows for non-demo
    if 'st.dataframe(data[\'employees\'][display_cols], use_container_width=True, hide_index=True)' in line:
        indent = line[:len(line) - len(line.lstrip())]
        new_lines.append(indent + "emp_df = data['employees'][display_cols]\n")
        new_lines.append(indent + "if not st.session_state.get('is_demo', False) and len(emp_df) > 3:\n")
        new_lines.append(indent + "    st.dataframe(emp_df.head(3), use_container_width=True, hide_index=True)\n")
        new_lines.append(indent + "    st.markdown(f'<p style=\"color: #64748B; font-size: 12px; padding: 8px 0;\">Showing 3 of {len(emp_df)} ghost employees. <strong>Contact +234 704 929 4373 to unlock all findings.</strong></p>', unsafe_allow_html=True)\n")
        new_lines.append(indent + "else:\n")
        new_lines.append(indent + "    st.dataframe(emp_df, use_container_width=True, hide_index=True)\n")
        i += 1
        continue
    
    # 10. Limit regular DataFrames to 3 rows for non-demo
    if 'st.dataframe(data, use_container_width=True, hide_index=True)' in line:
        indent = line[:len(line) - len(line.lstrip())]
        new_lines.append(indent + "if not st.session_state.get('is_demo', False) and len(data) > 3:\n")
        new_lines.append(indent + "    st.dataframe(data.head(3), use_container_width=True, hide_index=True)\n")
        new_lines.append(indent + "    st.markdown(f'<p style=\"color: #64748B; font-size: 12px; padding: 8px 0;\">Showing 3 of {len(data)} flagged items. <strong>Contact +234 704 929 4373 to unlock all {len(data)} findings.</strong></p>', unsafe_allow_html=True)\n")
        new_lines.append(indent + "else:\n")
        new_lines.append(indent + "    st.dataframe(data, use_container_width=True, hide_index=True)\n")
        i += 1
        continue
    
    new_lines.append(line)
    i += 1

with open('app.py', 'w') as f:
    f.writelines(new_lines)

print("Done")
