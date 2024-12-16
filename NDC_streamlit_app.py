import streamlit as st
import pandas as pd
import numpy as np

# Load the datasets
@st.cache_data
def load_data():
    file_path = 'Final_Updated_Classifications.csv'
    return pd.read_csv(file_path).drop_duplicates()

@st.cache_data
def load_reclassified_data():
    file_path = 'Updated_Reclassified_DrugDatabase.csv'
    return pd.read_csv(file_path).drop_duplicates()

# Load the data
df = load_data()
reclassified_df = load_reclassified_data()

# Ensure the NDC and Drug Name columns are strings for comparison and strip whitespace
df['NDC'] = df['NDC'].astype(str).str.strip()
df['Drug Name'] = df['Drug Name'].astype(str).str.strip()
df['class'] = df['class'].astype(str).str.strip()
reclassified_df['ndc'] = reclassified_df['ndc'].astype(str).str.strip()
reclassified_df['drug_name'] = reclassified_df['drug_name'].astype(str).str.strip()

# Ensure Date column is parsed as datetime for sorting
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

# Calculate Net Profit dynamically
df['Net Profit'] = ((df['Pat Pay'] + df['Ins Pay']) - df['ACQ']).round(2)

# Insurance mapping (short to full name)
insurance_mapping = {
    'AL': 'Aetna (AL)',
    'BW': 'aetna (BW)',
    'AD': 'Aetna Medicare (AD)',
    'AF': 'Anthem BCBS (AF)',
    'DS': 'Blue Cross Blue Shield (DS)',
    'CA': 'blue shield medicare (CA)',
    'FQ': 'Capital Rx (FQ)',
    'BF': 'Caremark (BF)',
    'ED': 'CatalystRx (ED)',
    'AM': 'Cigna (AM)',
    'BO': 'Default Claim Format (BO)',
    'AP': 'Envision Rx Options (AP)',
    'CG': 'Express Scripts (CG)',
    'BI': 'Horizon (BI)',
    'AJ': 'Humana Medicare (AJ)',
    'BP': 'informedRx (BP)',
    'AO': 'MEDCO HEALTH (AO)',
    'AC': 'MEDCO MEDICARE PART D (AC)',
    'AQ': 'MEDGR (AQ)',
    'CC': 'MY HEALTH LA (CC)',
    'AG': 'Navitus Health Solutions (AG)',
    'AH': 'OptumRx (AH)',
    'AS': 'PACIFICARE LIFE AND H (AS)',
    'FJ': 'Paramount Rx (FJ)',
    'X ': 'PF - DEFAULT (X )',
    'EA': 'Pharmacy Data Management (EA)',
    'DW': 'phcs (DW)',
    'AX': 'PINNACLE (AX)',
    'BN': 'Prescription Solutions (BN)',
    'AA': 'Tri-Care Express Scripts (AA)',
    'AI': 'United Healthcare (AI)'
}

df['Ins Full Name'] = df['Ins'].map(insurance_mapping).fillna(df['Ins'])

# Display logo and title
logo_path = 'img.png'  # Replace with the actual path to your logo
col1, col2 = st.columns([1, 4])
with col1:
    st.image(logo_path, use_container_width=True)
with col2:
    st.title("Enhanced Medication Guiding Tool 💊")

st.markdown("### Input your search criteria below:")

# Input Fields
drug_name_input = st.selectbox("Search for a Drug Name:", options=[""] + list(df['Drug Name'].unique()), format_func=lambda x: x if x else "Type to search...")

if drug_name_input:
    insurances_for_drug = df[df['Drug Name'] == drug_name_input][['Ins Full Name', 'Ins']].dropna().drop_duplicates(subset=['Ins Full Name'])['Ins Full Name'].unique()
    insurance_input = st.selectbox("Select Insurance:", options=[opt for opt in [""] + list(insurances_for_drug) if opt.strip()], format_func=lambda x: x if x else "Type to search...")
    ndcs_for_drug = df[df['Drug Name'] == drug_name_input]['NDC'].unique()
    ndc_input = st.selectbox("Select an NDC:", options=ndcs_for_drug, format_func=lambda x: x if x else "Type to search...")
else:
    insurance_input = None
    ndc_input = None

# Map insurance input back to short code
insurance_code = df[df['Ins Full Name'] == insurance_input]['Ins'].iloc[0] if insurance_input and not df[df['Ins Full Name'] == insurance_input].empty else None

# Filter data based on inputs
filtered_df = df
if drug_name_input:
    filtered_df = filtered_df[filtered_df['Drug Name'] == drug_name_input]
if ndc_input:
    filtered_df = filtered_df[filtered_df['NDC'] == ndc_input]
if insurance_input:
    filtered_df = filtered_df[filtered_df['Ins Full Name'] == insurance_input]

# Sort filtered data by latest date
filtered_df = filtered_df.sort_values(by='Date', ascending=False)

if drug_name_input and ndc_input and filtered_df.empty:
    st.markdown(f"<p style='color: red; font-weight: bold;'>No insurance data available for {drug_name_input} with NDC {ndc_input}</p>", unsafe_allow_html=True)

    # Fetch details from reclassified database
    formatted_ndc = f"{ndc_input[:5]}-{ndc_input[5:9]}-{ndc_input[9:]}"
    reclassified_details = reclassified_df[reclassified_df['ndc'] == formatted_ndc]
    if not reclassified_details.empty:
        st.markdown(f"### Drug Name: *{drug_name_input}*")
        first_reclassified_result = reclassified_details.iloc[0]
        st.markdown(f"- *Manufacturer (MFG)*: {first_reclassified_result['mfg']}")
        st.markdown(f"- *Acquisition Cost (ACQ)*: {first_reclassified_result['acq']}")
        st.markdown(f"- *Average Wholesale Price (AWP)*: {first_reclassified_result['awp']}")
        st.markdown(f"- *RxCui*: {first_reclassified_result['rxcui']}")
        
        # Fetch alternatives based on the drug class
        drug_class = first_reclassified_result['drug_class']
        alternatives = reclassified_df[reclassified_df['drug_class'] == drug_class].drop_duplicates(subset=['drug_name'])
        st.subheader("Alternative Drugs in the Same Class")
        st.markdown(f"*Found {len(alternatives)} alternatives in the same class.*")

        # Sorting options
        sort_option = st.selectbox("Sort Alternatives By:", ["Highest Net Profit", "Lowest AWP"])
        if sort_option == "Highest Net Profit" and 'Net Profit' in alternatives.columns:
            alternatives = alternatives.sort_values(by="Net Profit", ascending=False)
        elif sort_option == "Lowest AWP":
            alternatives = alternatives.sort_values(by="awp", ascending=True)

        # Display alternatives
        for _, alt_row in alternatives.iterrows():
            st.markdown("---")
            st.markdown(f"### Alternative Drug Name: *{alt_row['drug_name']}*")
            st.markdown(f"- *Class*: {alt_row['drug_class']}")
            st.markdown(f"- *Manufacturer (MFG)*: {alt_row['mfg']}")
            st.markdown(f"- *Acquisition Cost (ACQ)*: {alt_row['acq']}")
            st.markdown(f"- *Average Wholesale Price (AWP)*: {alt_row['awp']}")
            st.markdown(f"- *NDC*: {alt_row['ndc']}")
    else:
        st.warning("No additional data found in the reclassified database.")

if drug_name_input and insurance_code and not filtered_df.empty:
    st.subheader(f"Latest Billing Details :")

    # Display selected drug details
    first_valid_result = filtered_df.iloc[0]
    net_profit_calculation = f"({first_valid_result['Pat Pay']} + {first_valid_result['Ins Pay']}) - {first_valid_result['ACQ']}"
    net_profit_value = first_valid_result['Net Profit']

    st.markdown(f"### Drug Name: *{first_valid_result['Drug Name']}*")
    st.markdown(f"- *NDC*: {first_valid_result['NDC']}")
    st.markdown(f"- *Insurance*: {insurance_mapping.get(first_valid_result['Ins'], first_valid_result['Ins'])}")
    st.markdown(f"- *Quantity*: {first_valid_result['Qty']}")
    st.markdown(f"- *Net Profit*: {net_profit_value:.2f} (Calculation: {net_profit_calculation})")
    st.markdown(f"- *Copay*: {first_valid_result['Pat Pay']}")
    st.markdown(f"- *Insurance Pay*: {first_valid_result['Ins Pay']}")
    st.markdown(f"- *Acquisition Cost*: {first_valid_result['ACQ']}")
    st.markdown(f"- *Class*: {first_valid_result['class']}")
    st.markdown(f"- *Script*: {first_valid_result['Script']}")
    st.markdown(f"- *Date*: {first_valid_result['Date'].strftime('%m/%d/%Y') if pd.notnull(first_valid_result['Date']) else 'Not Available'}")
    st.markdown("---")

    # Find alternatives by class
    drug_class = first_valid_result['class']
    if drug_class.lower() != 'other':
        # Get the latest entry for each alternative drug name
        alternatives = (df[(df['class'] == drug_class) & (df['Drug Name'] != first_valid_result['Drug Name'])]
                        .sort_values(by='Date', ascending=False)
                        .drop_duplicates(subset=['Drug Name']))

        st.subheader("Alternative Drugs in the Same Class")
        st.markdown(f"*Found {len(alternatives)} alternatives in the same class.*")

        # Sorting options
        sort_option = st.selectbox("Sort Alternatives By:", ["Highest Net Profit", "Lowest Copay"])
        if sort_option == "Highest Net Profit":
            if 'Net Profit' in alternatives.columns:
                alternatives = alternatives.sort_values(by="Net Profit", ascending=False)
        elif sort_option == "Lowest Copay":
            if 'Pat Pay' in alternatives.columns:
                alternatives = alternatives.sort_values(by="Pat Pay", ascending=True)

        # Display alternatives
        for _, alt_row in alternatives.iterrows():
            ndc_formatted = alt_row.get('ndc', '').replace('-', '') if 'ndc' in alt_row else alt_row.get('NDC', '')
            st.markdown("---")
            st.markdown(f"### Alternative Drug Name: *{alt_row.get('Drug Name', alt_row.get('drug_name'))}*")
            st.markdown(f"- *Class*: {alt_row.get('class', alt_row.get('drug_class'))}")
            st.markdown(f"- *Copay*: {alt_row.get('Pat Pay', 'N/A')}")
            st.markdown(f"- *Insurance Pay*: {alt_row.get('Ins Pay', 'N/A')}")
            st.markdown(f"- *Acquisition Cost*: {alt_row.get('ACQ', alt_row.get('acq'))}")
            st.markdown(f"- *NDC*: {ndc_formatted}")
            st.markdown(f"- *Net Profit*: {alt_row.get('Net Profit', 'N/A'):.2f}" if 'Net Profit' in alt_row else "")
    else:
        st.info("No alternatives available for drugs in the 'Other' class.")
