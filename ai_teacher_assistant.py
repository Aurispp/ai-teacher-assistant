import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SERVICE_ACCOUNT_FILE = 'top-design-431016-q2-827579d0dee6.json'
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Replace this with the ID of the folder you shared
SHARED_FOLDER_ID = '1-23N2YmayxZ2uHfYtw3_7COC4sUTXxkF'

def get_drive_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    print(f"Using service account: {creds.service_account_email}")
    return build('drive', 'v3', credentials=creds)

def list_files_in_folder(service, folder_id):
    try:
        results = service.files().list(
            pageSize=100,
            fields="nextPageToken, files(id, name, mimeType)",
            q=f"'{folder_id}' in parents and trashed=false"
        ).execute()
        items = results.get('files', [])

        if not items:
            print('No files found in the shared folder.')
            return
        print('Files in the shared folder:')
        for item in items:
            print(f"{item['name']} ({item['id']}) - {item['mimeType']}")
    except HttpError as error:
        print(f'An error occurred: {error}')

def main():
    try:
        service = get_drive_service()
        print(f"Listing files from the shared folder (ID: {SHARED_FOLDER_ID}):")
        list_files_in_folder(service, SHARED_FOLDER_ID)
    except Exception as error:
        print(f'An error occurred: {error}')

if __name__ == '__main__':
    main()