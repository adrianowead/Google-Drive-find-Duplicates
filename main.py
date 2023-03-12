from __future__ import print_function

import os.path
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import collections

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']


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
    list_of_tuples = []
    dups_dict = collections.defaultdict(list) 

    try:
        while True:
            counter = counter + 1

            response = service.files().list(
                spaces='drive',
                pageSize=500,
                fields='nextPageToken, files(id, name, md5Checksum, parents)',
                pageToken=page_token
            ).execute()
            
            for f in response.get('files', []):
                # Process change

                list_of_tuples.append((f.get('md5Checksum'), f.get('name')))
                #dups_dict[f.get('md5Checksum')] += 1
                
                # print ('Found file: %s (%s) %s' % (f.get('name'), f.get('id'), f.get('md5Checksum')))
            page_token = response.get('nextPageToken', None)
            
            
            #remove this IF if you want to scan through everything
            if counter >= 10:
                break
            
            if page_token is None:
                print("this many:" + str(counter))
                break

        with open("duplicated.txt","w",encoding='utf-8') as f:
            for k,v in list_of_tuples:
                dups_dict[k].append(v)
                f.write(f"{v}\n")

        print("\r\n\r\n")
        print("here are the duplicates")

        for key in dups_dict:
            if len(dups_dict[key]) > 1 and "-checkpoint" not in str(dups_dict[key]):
                print(dups_dict[key])
    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f'An error occurred: {error}')


if __name__ == '__main__':
    main()