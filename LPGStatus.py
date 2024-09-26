import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from twilio.rest import Client
import json

# Google Sheets API connection using Streamlit secrets
def connect_to_google_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Use Streamlit secrets to retrieve the credentials
    credentials_dict = {
        "type": st.secrets["gcp_service_account"]["type"],
        "project_id": st.secrets["gcp_service_account"]["project_id"],
        "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
        "private_key": st.secrets["gcp_service_account"]["private_key"].replace("\\n", "\n"),
        "client_email": st.secrets["gcp_service_account"]["client_email"],
        "client_id": st.secrets["gcp_service_account"]["client_id"],
        "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
        "token_uri": st.secrets["gcp_service_account"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"]
    }
    
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open("LPG_Container_Status").sheet1  # Open the Google Sheet by name
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# Twilio SMS alert function (no changes here)
def send_sms_alert(lpg_container_id, balance_percentage, supplier_phone_number, customer_name, customer_phone):
    account_sid = st.secrets["twilio"]["ACe55faccc9332af6d453f7d000995da61"]
    auth_token = st.secrets["twilio"]["faf00e1095e3df297aec655a4846a7af"]
    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body=f"LPG Container {lpg_container_id} for customer {customer_name} is at {balance_percentage}% balance. "
             f"Please prepare for delivery. Contact customer at {customer_phone}.",
        from_=st.secrets["twilio"]["15136665539"],
        to=supplier_phone_number
    )

    return message.sid

# Calculate LPG percentage and alert logic (no changes here)
def check_lpg_balance(df):
    for index, row in df.iterrows():
        initial_weight = row['Initial Weight (kg)']
        current_weight = row['Current Weight (kg)']
        percentage_balance = (current_weight / initial_weight) * 100
        df.at[index, 'Balance (%)'] = percentage_balance

        customer_name = row['Customer Name']
        customer_phone = row['Customer Phone']
        supplier_phone = row['Supplier Phone']
        
        if percentage_balance <= 30:
            st.warning(f"Container {row['Container ID']} for {customer_name} is at {percentage_balance:.2f}% balance.")
        if percentage_balance <= 20:
            st.error(f"Container {row['Container ID']} for {customer_name} is at {percentage_balance:.2f}% balance.")
        if percentage_balance <= 10:
            st.error(f"Container {row['Container ID']} for {customer_name} is critically low at {percentage_balance:.2f}% balance.")
            send_sms_alert(row['Container ID'], percentage_balance, supplier_phone, customer_name, customer_phone)

# Main app interface (no changes here)
def main():
    st.title("LPG Container Monitoring Dashboard")

    # Fetch data from Google Sheets
    df = connect_to_google_sheet()

    # Display LPG container status
    st.subheader("LPG Container Status")
    st.dataframe(df)

    # Calculate balance and trigger alerts
    check_lpg_balance(df)

if __name__ == "__main__":
    main()
