import streamlit as st
import pandas as pd
import io

# Streamlit UI
st.title("PID Processing Tool")

# Dropdown for country selection
st.subheader("Select Country")
country_options = ["Brazil", "Chile", "Mexico", "Colombia", "Argentina"]
selected_country = st.selectbox("Choose a country:", country_options)

# File Upload
st.subheader("Upload Master Data File (CSV)")
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

# Text area for PIDs
st.subheader("Enter PIDs (comma-separated OR line-separated)")
pids_input = st.text_area("Paste PIDs here", placeholder="91825-3304\n98122-3105\n95223-7104")

# Process input to handle both comma-separated and line-separated formats
def process_pids(pids_text):
    if pids_text:
        return [pid.strip() for pid in pids_text.replace("\n", ",").split(",") if pid.strip()]
    return []

if st.button("Process File"):
    if uploaded_file and pids_input:
        # Read uploaded CSV file
        df = pd.read_csv(uploaded_file, delimiter=";", low_memory=False)
        df_filtered = df[['PID', 'MPL_PRODUCT_ID', 'COLOR_ID']]

        # Convert input PIDs into a list
        user_pids = process_pids(pids_input)

        # Filter dataset for provided PIDs
        df_selected = df_filtered[df_filtered['PID'].isin(user_pids)]

        # Find COLOR_IDs linked to those PIDs
        color_ids = df_selected['COLOR_ID'].dropna().unique()

        # Get all PIDs that share the same COLOR_ID
        df_final = df_filtered[df_filtered['COLOR_ID'].isin(color_ids)].copy()

        # Add required columns
        df_final['CATALOG_VERSION'] = f"SBC{selected_country}ProductCatalog"  # Dynamically replace COUNTRY
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
            file_name=f"Processed_PIDs_{selected_country}.txt",
            mime="text/plain"
        )
    else:
        st.error("Please upload a file and enter PIDs.")

