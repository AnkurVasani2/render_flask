from flask import Flask, request, jsonify
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
# Google Sheets Configuration
SPREADSHEET_ID = '1c1EdwOSD_IKSW71xKXCiz-vdlm18OYzcwLhPS2cxhU4'
SHEET_NAME = 'Sheet2'  # Change this to the name of your sheet
CREDENTIALS_FILE = 'C:\\Users\\Ankur Vasani\\Desktop\\trinity_backup\\trinity-registrations-1f920e0fbad0.json'

# Function to append data to Google Sheets
def append_to_sheet(data):
    try:
        # Load credentials
        credentials = Credentials.from_service_account_file(
            CREDENTIALS_FILE, scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        
        # Build the Sheets API client
        service = build('sheets', 'v4', credentials=credentials)
        sheet = service.spreadsheets()

        # Prepare data to append
        values = [
            [
                data['email'],
                data['title'],
                data['firstName'],
                data['surname'],
                data['institute'],
                data['graduationYear'],
                data['contactNumber'],
                data['event']
            ]
        ]

        body = {'values': values}

        # Append data to the spreadsheet
        result = sheet.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A1",
            valueInputOption="RAW",
            body=body
        ).execute()

        return result
    except Exception as e:
        print(f"Error: {e}")
        return None

# Route to handle registration
@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json

        # Validate required fields
        required_fields = ['email','title', 'firstName', 'surname', 'institute', 'graduationYear', 'contactNumber', 'event']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'message': f'Missing or empty field: {field}'}), 400

        # Append to Google Sheet
        result = append_to_sheet(data)
        if result:
            return jsonify({'message': 'Registration successful!'}), 200
        else:
            return jsonify({'message': 'Failed to register. Please try again later.'}), 500

    except Exception as e:
        print(f"Error during registration: {e}")
        return jsonify({'message': 'An error occurred during registration.'}), 500

if __name__ == '__main__':
    app.run(debug=True)
