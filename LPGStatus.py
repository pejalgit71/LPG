import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from twilio.rest import Client

# Google Sheets API connection
def connect_to_google_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("xstreamkey-b8d0df4e924d.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("LPG_Container_Status").sheet1  # Open the Google Sheet by name
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# Twilio SMS alert function
def send_sms_alert(lpg_container_id, balance_percentage, supplier_phone_number):
    account_sid = "ACe55faccc9332af6d453f7d000995da61"
    auth_token = "a54d3f6c80d6e04b55c6bc87bdbef947"
    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body=f"LPG Container {lpg_container_id} is at {balance_percentage:.2f}% balance. Please prepare for delivery.",
        from_="+15136665539",
        to=supplier_phone_number
    )

    return message.sid

# Calculate LPG percentage and alert logic
def check_lpg_balance(df):
    for index, row in df.iterrows():
        initial_weight = row['Initial Weight (kg)']
        current_weight = row['Current Weight (kg)']
        percentage_balance = (current_weight / initial_weight) * 100
        df.at[index, 'Balance (%)'] = percentage_balance

        # Trigger alerts at 30%, 20%, and 10%
        if percentage_balance <= 30:
            st.warning(f"Container {row['Container ID']} is at {percentage_balance:.2f}% balance.")
        if percentage_balance <= 20:
            st.error(f"Container {row['Container ID']} is at {percentage_balance:.2f}% balance.")
        if percentage_balance <= 10:
            st.error(f"Container {row['Container ID']} is critically low at {percentage_balance:.2f}% balance.")
            send_sms_alert(row['Container ID'], percentage_balance, row['Supplier Phone'])

# Main app interface
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
