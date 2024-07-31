import os
import re
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, time

SERVICE_ACCOUNT_FILE = 'top-design-431016-q2-827579d0dee6.json'
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
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
        return results.get('files', [])
    except HttpError as error:
        print(f'An error occurred: {error}')
        return []

def parse_filename(filename):
    parts = filename.lower().split('_')
    days = []
    time_str = ''
    for part in parts:
        if part in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
            days.append(part)
        elif re.match(r'\d{4}', part):
            time_str = part
    return days, time_str

def get_file_content(service, file_id):
    try:
        content = service.files().export(fileId=file_id, mimeType='text/plain').execute()
        return content.decode('utf-8')
    except HttpError as error:
        print(f'An error occurred: {error}')
        return ""

import re
from datetime import datetime

def get_latest_notes(service, files, day, time):
    print(f"Searching for files containing '{day.lower()}' in the name...")
    relevant_files = []
    for file in files:
        days, file_time = parse_filename(file['name'])
        if day.lower() in days:
            relevant_files.append((file, file_time))
    
    print(f"Found {len(relevant_files)} relevant files.")
    
    if not relevant_files:
        return "No relevant files found."
    
    # Sort files by time, closest to the input time
    input_time = datetime.strptime(time, "%H%M").time()
    relevant_files.sort(key=lambda x: abs((datetime.strptime(x[1], "%H%M").time().hour * 60 + datetime.strptime(x[1], "%H%M").time().minute) - (input_time.hour * 60 + input_time.minute)))
    
    latest_file = relevant_files[0][0]
    print(f"Using file: {latest_file['name']}")
    
    content = get_file_content(service, latest_file['id'])
    print(f"File content length: {len(content)} characters")

    lines = content.split('\n')
    
    date_pattern = r'^\s*(\d{1,2}/\d{1,2}/\d{4})\s*$'
    entries = []
    current_entry = []
    current_date = None

    for i, line in enumerate(lines):
        match = re.match(date_pattern, line.strip())
        if match:
            if current_date:
                entries.append((current_date, '\n'.join(current_entry).strip()))
            current_date = match.group(1)
            current_entry = []
        elif current_date:
            current_entry.append(line.strip())
        
        # If we're at the last line, add the current entry
        if i == len(lines) - 1 and current_date:
            entries.append((current_date, '\n'.join(current_entry).strip()))

    # Sort entries by date, most recent first
    entries.sort(key=lambda x: datetime.strptime(x[0], "%d/%m/%Y"), reverse=True)

    # Take only the 4 most recent entries
    entries = entries[:4]

    print(f"\nTotal dated entries found: {len(entries)}")
    print(f"Using the following dates: {[entry[0] for entry in entries]}")

    if not entries:
        return "No notes found for the last 4 classes."

    result = ""
    for date, content in entries:
        result += f"{date}\n\n{content}\n\n"

    return result.strip()

def main():
    service = get_drive_service()
    files = list_files_in_folder(service, SHARED_FOLDER_ID)
    print(f"Total files in folder: {len(files)}")
    
    day = input("Enter the day (e.g., Wednesday): ")
    time = input("Enter the time (e.g., 0800): ")
    
    latest_notes = get_latest_notes(service, files, day, time)
    print("\nNotes for the last 4 classes:")
    print(latest_notes)

if __name__ == '__main__':
    main()