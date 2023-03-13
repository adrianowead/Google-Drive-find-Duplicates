from __future__ import print_function

import os.path
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly','https://www.googleapis.com/auth/drive']

def get_path_from_id(file_id):
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
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('drive', 'v3', credentials=creds)

    # Get the file's metadata
    try:
        file = service.files().get(fileId=file_id, fields='parents,name').execute()
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None

    # Recursively build the path from the file's parents
    path = [file['name']]
    while 'parents' in file:
        parent_id = file['parents'][0]
        try:
            parent = service.files().get(fileId=parent_id, fields='parents,name').execute()
        except HttpError as error:
            print(f'An error occurred: {error}')
            return None
        path.insert(0, parent['name'])
        file = parent

    # Return the path as a string
    return '/'.join(path)

def main():
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
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
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('drive', 'v3', credentials=creds)

    counter = 0
    page_token = None
    dups_dict = {}

    try:
        while True:
            counter = counter + 1

            response = service.files().list(
                spaces='drive',
                pageSize=10,
                fields='nextPageToken, files(id, name, md5Checksum, parents, size)',
                pageToken=page_token
            ).execute()
            
            for f in response.get('files', []):
                # Process change

                if f.get('md5Checksum') is not None:
                    if f.get('md5Checksum') in dups_dict:
                        dups_dict[f.get('md5Checksum')]['files'].append(f)
                    else:
                        dups_dict[f.get('md5Checksum')] = {'files': [f]}

            page_token = response.get('nextPageToken', None)

            #remove this IF if you want to scan through everything
            if counter >= 10:
                break

            if page_token is None:
                print("this many:" + str(counter))
                break

        out = {}
        for i in dups_dict:
            if len(dups_dict[i]['files']) > 1:
                out[i] = dups_dict[i]

        del dups_dict

        with open("duplicated.csv","w",encoding='utf-8') as f:
            f.write(f"md5;size;name;path\n")

            for i in out:
                for k in out[i]['files']:
                    md5 = k ['md5Checksum']
                    name = k['name']
                    size = k['size']
                    path = get_path_from_id(k['id'])

                    f.write(f"{md5};{size};{name};{path}\n")

    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f'An error occurred: {error}')


if __name__ == '__main__':
    main()