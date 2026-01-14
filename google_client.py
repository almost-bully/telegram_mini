# google_client.py

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from config import SERVICE_ACCOUNT_FILE

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_sheets_service():
    credentials = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )
    service = build("sheets", "v4", credentials=credentials)
    return service
