# coding: utf-8
# https://developers.google.com/drive/api/v3/quickstart/python
# https://developers.google.com/drive/api/v3/reference/files#methods
# pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib

from __future__ import print_function
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload

import io
import uuid

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive']#.metadata.readonly']

class DriveService:
	def __init__(self, token_file):
		if os.path.exists(token_file):
			creds = Credentials.from_authorized_user_file(token_file, SCOPES)
			self.service = build('drive', 'v3', credentials=creds)
		else:
			raise ValueError("File not found")


	def upload_file(self, local_file_name, drive_file_name, parents_list, mime_type=None):
		'''
		upload file to google drive

		:param service:
		:param local_file_name: local file full name
		:param drive_file_name: file name in google drive
		:param parents_list: list with id of parent folders
		:param mime_type: 'image/jpeg' , 'application/pdf'
		:return: created file_id
		https://developer.mozilla.org/pt-BR/docs/Web/HTTP/Basics_of_HTTP/MIME_types
		'''
		if not mime_type:
			file_type = local_file_name.split(".")[-1]
			if file_type == '.pdf':
				mime_type = 'application/pdf'
			elif file_type == '.pdf':
				mime_type = 'image/jpeg'
				
		# [''] da erro: file not found
		if parents_list == ['']:
			parents_list = []

		file_metadata = {'name': drive_file_name, 'parents': parents_list}
		media = MediaFileUpload(local_file_name, mimetype=mime_type)
		
		file = self.service.files().create(body=file_metadata,
	                              	media_body=media,
                                  	supportsAllDrives=True,
	                              	fields='id').execute()
		# print('File ID: %s' % file.get('id'))
		#print(file)
		return file.get('id')

	def upload_file_from_memory(self, fileInMemory, file_name, parents_list,mime_type=None):
		file_metadata = {'name': file_name, 'parents': parents_list}
		if not mime_type:
			file_type = file_name.split(".")[-1]
			if file_type == '.pdf':
				mime_type = 'application/pdf'
			elif file_type == '.pdf':
				mime_type = 'image/jpeg'
		print(mime_type)
		print(file_metadata)
		print(fileInMemory)
		#fh = io.BytesIO()
		
		media = MediaIoBaseUpload(fileInMemory, mimetype=mime_type, chunksize=1024*1024, resumable=True)
		print('xxxxx')
		file = self.service.files().create(body=file_metadata,media_body=media,fields='id,name').execute()
		print(file)
		return file.get('id')


	def create_folder(self, folder_name, parents_list=[]):
		'''
		Create folder in goolge drive

		:param folder_name folder name to be created
		:param parents_list list with id of parents folder, if none, should be []
		:returns folder_id
		'''
		mime_type = 'application/vnd.google-apps.folder'
		file_metadata = {'name': folder_name, 'mimeType': mime_type, 'parents': parents_list}

		file = self.service.files().create(supportsAllDrives=True,body=file_metadata, fields='id').execute()
		return file.get('id')


	def list_files(self):
		# Call the Drive v3 API
		results = self.service.files().list(pageSize=200,
		                               # fields="nextPageToken, files(id, name)",
		                               includeItemsFromAllDrives=True,
                                       q="trashed = false",
		                               supportsAllDrives=True).execute()
		items = results.get('files', [])

		return items
	
	def list_drives(self):
		results = self.service.drives().list(pageSize=10).execute()
		items = results.get('drives', [])
		return items #results
	
	def create_shared_drive(self, drive_name):
		drive_metadata = {'name': drive_name}
		request_id = str(uuid.uuid4())
		drive = self.service.drives().create(body=drive_metadata,
                                      requestId=request_id,
                                      fields='id').execute()
		#print 'Drive ID: %s' % drive.get('id')
		return drive.get('id')

'''
		if not items:
			print('No files found.')
		else:
			print('Files:')
			for item in items:
				print(u'{0} ({1})'.format(item['name'], item['id']))
				print(item)

			return items


def create_service():
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('gdrive_token.json'):
        creds = Credentials.from_authorized_user_file('gdrive_token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_gdrive.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('gdrive_token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('drive', 'v3', credentials=creds)
    return service


drive_service = create_service()
# https://drive.google.com/file/d/1i_lz4dn26XV6pP4oxbv7gud4NQgYLGHM/view?usp=sharing

# 'mimeType': 'application/vnd.google-apps.folder' 'mimeType': 'image/jpeg'
# {'kind': 'drive#file', 'id': '1EUx69rGKv62-TSkoZs5ts5BSgv4oMHGH', 'name': 'Files_create.pdf',
# 'mimeType': 'application/pdf', 'teamDriveId': '0ADvcUlbItjC6Uk9PVA', 'driveId': '0ADvcUlbItjC6Uk9PVA'}
if __name__ == '__main__':
    list_files(drive_service)
    local_file_name = 'mercados.jpg' #'a_users_click_06232021_06292021.xlsx'
    drive_file_name = 'emails_mercados.jpg'
    parents_list = ['133hvg77Bc2D-Y3hsPnC_DIwaNNCzeXkY']#['0ADvcUlbItjC6Uk9PVA']
    #upload_file(drive_service, local_file_name, drive_file_name,parents_list)
    folder_name = 'pasta_teste1'
    create_folder(drive_service, folder_name)
'''
