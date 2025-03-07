import streamlit as st
import pandas as pd
import io
import os
import uuid

# Secure Password Option (set password in Render environment variables)
PASSWORD = os.getenv("APP_PASSWORD", "defaultpassword")

# Session state to track login status
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Login form
if not st.session_state.logged_in:
    st.title("Login Required")
    user_password = st.text_input("Enter Password:", type="password")
    if st.button("Login"):
        if user_password == PASSWORD:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Incorrect password. Please try again.")

# Show app only if logged in
if st.session_state.logged_in:
    st.title("PID Processing Tool")

    # File Upload
    st.subheader("Upload Master Data File (CSV)")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

    st.subheader("Enter PIDs")
    pids_input = st.text_area("Enter PIDs (comma-separated)", placeholder="91825-3304,98122-3105,...")

    if st.button("Process File"):
        if uploaded_file and pids_input:
            # Read uploaded CSV file
            df = pd.read_csv(uploaded_file, delimiter=";", low_memory=False)
            df_filtered = df[['PID', 'MPL_PRODUCT_ID', 'COLOR_ID']]

            # Convert input PIDs from string to list
            user_pids = [pid.strip() for pid in pids_input.split(",")]

            # Filter dataset for provided PIDs
            df_selected = df_filtered[df_filtered['PID'].isin(user_pids)]

            # Find COLOR_IDs linked to those PIDs
            color_ids = df_selected['COLOR_ID'].dropna().unique()

            # Get all PIDs that share the same COLOR_ID
            df_final = df_filtered[df_filtered['COLOR_ID'].isin(color_ids)].copy()

            # Add required columns
            df_final['CATALOG_VERSION'] = "SBCColombiaProductCatalog"
            df_final['APPROVAL_STATUS'] = "approved"

            # Rename columns for output
            df_final.rename(columns={'PID': 'SKU', 'MPL_PRODUCT_ID': 'Base Product ID'}, inplace=True)
            df_final = df_final[['SKU', 'Base Product ID', 'CATALOG_VERSION', 'APPROVAL_STATUS']]

            # Generate output file
            output = io.StringIO()
            df_final.to_csv(output, sep="|", index=False)
            output_content = output.getvalue()

            # Provide download link
            st.download_button(
                label="Download Processed File",
                data=output_content,
                file_name="Processed_PIDs.txt",
                mime="text/plain"
            )
        else:
            st.error("Please upload a file and enter PIDs.")
