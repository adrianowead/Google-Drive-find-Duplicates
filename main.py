import os
import csv
import sys
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

def get_all_files(service, folder_id, files, limit: int = 0, path='') -> None:
    """Recursively get all files in a folder and its subfolders."""
    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(q=query, fields="nextPageToken, files(id, md5Checksum, name, size, parents, mimeType)").execute()
    items = results.get('files', [])
    for item in items:
        # Skip folders
        if item.get('mimeType') in ['application/vnd.google-apps.folder']:
            get_all_files(
                service=service,
                folder_id=item['id'],
                files=files,
                limit=limit,
                path=path + '/' + item['name']
            )
        # skip shortcuts
        elif item.get('mimeType') not in ['application/vnd.google-apps.shortcut']:
            item['path'] = path + '/' + item['name']
            files.append(item)

        if limit > 0 and len(files) >= limit:
            break

def save_duplicates_to_csv(duplicates: list, csv_file_name: str) -> None:
    """Save a list of duplicate files to a CSV file."""
    with open(csv_file_name, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(['Checksum', 'Nome', 'Tamanho (bytes)', 'Caminho Completo', 'ID'])
        for d in duplicates:
            writer.writerow(
                [
                    d['copy_1']['md5Checksum'], d['copy_1']['name'], d['copy_1']['size'], d['copy_1']['path'], d['copy_1']['id']
                ]
            )
            writer.writerow(
                [
                    d['copy_2']['md5Checksum'], d['copy_2']['name'], d['copy_2']['size'], d['copy_2']['path'], d['copy_2']['id']
                ]
            )

def check_for_duplicates(files: list) -> list:
    """Find all duplicate files in a list of files."""
    duplicates = []
    seen_checksums = {}
    for f in files:
        if 'md5Checksum' in f:
            if f['md5Checksum'] not in seen_checksums:
                seen_checksums[f['md5Checksum']] = f
            else:
                # Check if files have the same path
                if seen_checksums[f['md5Checksum']]['path'] == f['path']:
                    continue
                # Check if files have the same size
                if seen_checksums[f['md5Checksum']]['size'] != f['size']:
                    continue
                duplicates.append({
                    'copy_1': f,
                    'copy_2': seen_checksums[f['md5Checksum']],
                })
    return duplicates

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly','https://www.googleapis.com/auth/drive']

# Authenticate and build the Drive API client
creds = Credentials.from_authorized_user_file('token.json', SCOPES)

# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.json', 'w', encoding='utf-8') as token:
        token.write(creds.to_json())

service = build('drive', 'v3', credentials=creds)

# Get all files in the root folder
files = []
get_all_files(
    service=service, 
    folder_id='root',
    files=files,
    limit=0,
    path=''
)

print(f'count {len(files)} arquivos\n')

# Compare files by checksum and group duplicates
duplicates = check_for_duplicates(files)

print(f'count {len(duplicates)} duplicados\n')

# Save list of duplicate files to CSV
save_duplicates_to_csv(duplicates,'duplicated.csv')
