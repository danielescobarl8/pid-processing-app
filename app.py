import streamlit as st
import pandas as pd
import io
import random
from datetime import datetime

# 🔐 Set the password
PASSWORD = "specialized1974"

# Initialize session state flags
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "approval_file_content" not in st.session_state:
    st.session_state.approval_file_content = None

if "approval_file_name" not in st.session_state:
    st.session_state.approval_file_name = None

# -------------------------
# 🔑 LOGIN SCREEN
# -------------------------
if not st.session_state.logged_in:
    st.title("🔒 Secure Access")
    user_password = st.text_input("Enter Password:", type="password")
    if st.button("Login"):
        if user_password == PASSWORD:
            st.session_state.logged_in = True
            st.rerun()  # Refresh the app after login
        else:
            st.error("❌ Incorrect password. Please try again.")

# -------------------------
# 📦 MAIN APP (AFTER LOGIN)
# -------------------------
if st.session_state.logged_in:

    # Motivational messages
    motivational_phrases = [
        "🚀 Great things are coming! Hang tight...",
        "🔥 You're making big moves! Just a moment...",
        "💡 Smart choice! Approving your products...",
        "⏳ Almost there! Preparing your approval file...",
        "✨ Good things take time... but not too long!",
        "✅ Making sure your products are ready to shine!",
        "🌎 One step closer to a better catalog. Hold on!"
    ]

    # Streamlit UI
    st.title("Product Approval")

    # Description text
    st.markdown(
        "This tool will help you turn on the SKUs you input here on s.com. "
        "It will not only approve those specific SKUs but the full run of SKUs under the same Color ID to ensure consistency in the catalog. "
        "(For example, if you want to turn on a bike size 52, the other sizes will turn on as well)."
    )

    # -------------------------
    # 🌍 COUNTRY SELECTION
    # -------------------------
    st.subheader("Select Country")
    country_options = [
        "Brazil",
        "Chile",
        "Mexico",
        "Colombia",
        "Argentina",
        "United States",
        "Canada",
    ]
    selected_country = st.selectbox("Choose a country:", country_options)

    # Mapping: Country → Catalog Version
    catalog_map = {
        "Brazil": "SBCBrazilProductCatalog",
        "Chile": "SBCChileProductCatalog",
        "Mexico": "SBCMexicoProductCatalog",
        "Colombia": "SBCColombiaProductCatalog",
        "Argentina": "SBCArgentinaProductCatalog",
        "United States": "SBCUnitedSProductCatalog",
        "Canada": "SBCCanadaProductCatalog",
    }

    # -------------------------
    # 📂 FILE UPLOAD
    # -------------------------
    st.subheader("Upload your country datafeed")
    uploaded_file = st.file_uploader("Choose a CSV or TXT file", type=["csv", "txt"])

    # -------------------------
    # 🔢 SKUs INPUT
    # -------------------------
    st.subheader("Enter the SKUs you want to activate (comma-separated OR line-separated)")
    pids_input = st.text_area(
        "Paste SKUs here",
        placeholder="91825-3304\n98122-3105\n95223-7104"
    )

    # -------------------------
    # 🔧 HELPER FUNCTIONS
    # -------------------------
    def process_pids(pids_text: str):
        """Process comma/line separated SKUs into a clean list."""
        if pids_text:
            # Replace line breaks with commas, split, strip whitespace, remove empties
            return [pid.strip() for pid in pids_text.replace("\n", ",").split(",") if pid.strip()]
        return []

    def load_data(file):
        """Read either CSV (;) or TXT (|) file into a DataFrame."""
        if file.name.endswith(".csv"):
            return pd.read_csv(file, delimiter=";", low_memory=False)
        elif file.name.endswith(".txt"):
            return pd.read_csv(file, delimiter="|", low_memory=False)
        else:
            return None

    # -------------------------
    # ▶️ PROCESS BUTTON
    # -------------------------
    if st.button("Process File"):
        # Basic validations
        if not uploaded_file:
            st.error("Please upload a datafeed file before processing.")
        elif not pids_input.strip():
            st.error("Please paste at least one SKU before processing.")
        else:
            # Load the file based on format
            df = load_data(uploaded_file)

            if df is None:
                st.error("Invalid file format. Please upload a CSV or TXT file.")
            else:
                # Ensure required columns exist
                required_cols = {'PID', 'MPL_PRODUCT_ID', 'COLOR_ID'}
                if not required_cols.issubset(df.columns):
                    st.error("File is missing required columns (PID, MPL_PRODUCT_ID, COLOR_ID).")
                else:
                    # Work only with needed columns
                    df_filtered = df[['PID', 'MPL_PRODUCT_ID', 'COLOR_ID']].copy()

                    # Make sure PIDs are treated as strings
                    df_filtered['PID'] = df_filtered['PID'].astype(str)

                    # Convert input SKUs into a list
                    user_pids = process_pids(pids_input)

                    if not user_pids:
                        st.error("No valid SKUs were detected in your input. Please check and try again.")
                    else:
                        # Display a random motivational message while processing
                        st.info(random.choice(motivational_phrases))

                        # Filter dataset for provided SKUs
                        df_selected = df_filtered[df_filtered['PID'].isin(user_pids)]

                        if df_selected.empty:
                            st.error("None of the provided SKUs were found in the datafeed.")
                        else:
                            # Find COLOR_IDs linked to those SKUs
                            color_ids = df_selected['COLOR_ID'].dropna().unique()

                            if len(color_ids) == 0:
                                st.error("No COLOR_IDs were found for the provided SKUs.")
                            else:
                                # Get all SKUs that share the same COLOR_ID
                                df_final = df_filtered[df_filtered['COLOR_ID'].isin(color_ids)].copy()

                                if df_final.empty:
                                    st.error("No SKUs were found for the matching COLOR_IDs.")
                                else:
                                    # Add required columns
                                    df_final['CATALOG_VERSION'] = catalog_map[selected_country]
                                    df_final['APPROVAL_STATUS'] = "approved"

                                    # Rename and reorder columns for output
                                    df_final.rename(
                                        columns={
                                            'PID': 'SKU',
                                            'MPL_PRODUCT_ID': 'Base Product ID'
                                        },
                                        inplace=True
                                    )
                                    df_final = df_final[['SKU', 'Base Product ID', 'CATALOG_VERSION', 'APPROVAL_STATUS']]

                                    # Generate output file content
                                    output = io.StringIO()
                                    df_final.to_csv(output, sep="|", index=False)
                                    st.session_state.approval_file_content = output.getvalue()

                                    # Generate timestamp for filename
                                    timestamp = datetime.now().strftime("%d%m%Y%H%M")
                                    st.session_state.approval_file_name = f"SBC_HYBRIS_SIZEVARIANT_APPROVAL_{timestamp}.txt"

                                    # Success message
                                    st.success("✅ File successfully generated! Download it below.")

    # -------------------------
    # 💾 DOWNLOAD BUTTON
    # -------------------------
    if st.session_state.approval_file_content and st.session_state.approval_file_name:
        st.download_button(
            label="Download Processed File",
            data=st.session_state.approval_file_content,
            file_name=st.session_state.approval_file_name,
            mime="text/plain"
        )
            data=st.session_state.approval_file_content,
            file_name=st.session_state.approval_file_name,
            mime="text/plain"
        )
