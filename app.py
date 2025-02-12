import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
from werkzeug.utils import secure_filename
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)

# Initialize Supabase
SUPABASE_URL = "https://fkouotklvmnxjhwcppdw.supabase.co"
SUPABASE_KEY='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZrb3VvdGtsdm1ueGpod2NwcGR3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczOTM4NTM0NSwiZXhwIjoyMDU0OTYxMzQ1fQ.Tnb_soA7kuvmFiflp7-prSvf41HuDTnEcCqMYxq-nMg'
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

SPREADSHEET_ID = '1UQjNJOE4eeluGNmq0F3PY3Vut_Mhd-0jFQvP64pFlUI'
SHEET_NAME = 'Sheet2'
CREDENTIALS_FILE = '/etc/secrets/trinity-registrations-1f920e0fbad0.json'
BUCKET_NAME = "register"  # Replace with your bucket name

# Function to upload file to Supabase Storage
import time

def upload_to_supabase(file, filename):
    try:
        # Generate a unique filename by appending a timestamp
        unique_filename = f"{int(time.time())}_{filename}"

        # Read the file as bytes
        file_data = file.read()

        # Upload the file with the unique filename
        response = supabase.storage.from_(BUCKET_NAME).upload(unique_filename, file_data)
        print("Response: ", response)
        signed_url_response = supabase.storage.from_(BUCKET_NAME).create_signed_url(unique_filename,3600)
        print("URL: ",signed_url_response)
        # Return the signed URL if successful
        if signed_url_response.get("signedURL"):
            return signed_url_response["signedURL"]

        # Fallback to returning None if signed URL generation fails
        print(f"Failed to generate signed URL: {signed_url_response}")
        return None
    except Exception as e:
        print(f"Error uploading to Supabase: {e}")
        return None





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
                data['firstName'],
                data['surname'],
                data['institute'],
                data['contactNumber'],
                data['event'],
                data['teamName'],
                data['teamMembers'],
                data['nationalIdProof'],
                data['paymentScreenshot']
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
        # Parse FormData for text and files
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        surname = request.form.get('surname')
        contact_number = request.form.get('contactNumber')
        institute = request.form.get('institute')
        event = request.form.get('event')
        team_name = request.form.get('teamName')
        team_members = request.form.get('teamMembers')

        # Handle file uploads
        national_id_file = request.files.get('nationalIdProof')
        payment_screenshot_file = request.files.get('paymentScreenshot')

        national_id_url = None
        payment_screenshot_url = None

        if national_id_file:
            national_id_url = upload_to_supabase(
                national_id_file,
                secure_filename(national_id_file.filename),
            )

        if payment_screenshot_file:
            payment_screenshot_url = upload_to_supabase(
                payment_screenshot_file,
                secure_filename(payment_screenshot_file.filename),
            )

        # Validate required fields
        required_fields = [email, first_name, surname, contact_number, institute, event]
        if not all(required_fields):
            return jsonify({'message': 'Missing required fields'}), 400

        # Prepare data for Google Sheets
        data = {
            'email': email,
            'firstName': first_name,
            'surname': surname,
            'contactNumber': contact_number,
            'institute': institute,
            'event': event,
            'teamName': team_name or '',
            'teamMembers': team_members or '',
            'nationalIdProof': national_id_url or '',
            'paymentScreenshot': payment_screenshot_url or ''
        }

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
