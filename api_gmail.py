# coding: utf-8
# https://developers.google.com/gmail/api/quickstart/python
# pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib

from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseUpload
from apiclient import errors
from pprint import pprint
#from apiclient.discovery import build
#from httplib2 import Http
#from oauth2client import file, client, tools
import time
from datetime import datetime
import json
import base64
import logging
import os
from pprint import pprint
import io
import pathlib
import sys

SCOPES = ['https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/gmail.readonly']

class GmailService:
    def __init__(self, token_file, credentials_file):
        creds = None
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token: #token.pickle
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
        self.service = build('gmail', 'v1', credentials=creds, cache_discovery=False)


    def get_msgid_by_text(self, reference_text):
        inbox = self.service.users().messages().list(
            userId='me', labelIds=['INBOX'],q=reference_text).execute()

        list_msg = []
        listIds = inbox.get('messages', [])
        for msg_id in listIds:
            msg = self.service.users().messages().get(userId='me', id=msg_id).execute()
            list_msg.append(msg)

        return list_msg

    def get_msgid_first_message_from_inbox(self, message_order=0):
        '''
        param: 
            message_order: default 0 (first inbox message)
        return msg_id
        '''
        try:
            inbox = self.service.users().messages().list(userId='me', labelIds=['INBOX']).execute()
            listIds = inbox.get('messages', [])
            msg_id = listIds[message_order]['id']
            return msg_id
        except Exception as e:
            return 'except:'+str(e)


    def get_msgid_n_first_messages_from_inbox(self, messages=1):
            '''
            param:
                message_order: default 0 (first inbox message)
            return msg_id list
            '''
            try:
                inbox = self.service.users().messages().list(
                    userId='me', labelIds=['INBOX']).execute()
                listIds = inbox.get('messages', [])
                msg_ids = []
                for i in range(0,messages):
                    msg_ids.append(listIds[i]['id'])
                return msg_ids
            except Exception as e:
                return 'except:'+str(e)


    def get_msgid_threadid_first_message_from_inbox(self):
        try:
            inbox = self.service.users().messages().list(userId='me', labelIds=['INBOX']).execute()
            listIds = inbox.get('messages', [])
            msg_id = listIds[0]['id']
            thread_id = listIds[0]['threadId']
            return msg_id, thread_id
        except Exception as e:
            return 'except:' + str(e)

    def get_listof_msgid_threadid_from_inbox(self):
        try:
            inbox = self.service.users().messages().list(userId='me', labelIds=['INBOX']).execute()
            listIds = inbox.get('messages', [])
            #msg_id = listIds[0]['id']
            #thread_id = listIds[0]['threadId']
            return listIds
        except Exception as e:
            return 'except:' + str(e)


    def get_thread_messages_by_threadid(self, thread_id):
        threads = self.service.users().threads().get(userId='me', id=thread_id).execute()
        threadmessages = threads['messages']
        return threadmessages
        #except Exception as e:
        #    return 'except:' + str(e)


    def get_message_by_msgid(self, msg_id):
        try:
            msg = self.service.users().messages().get(userId='me', id=msg_id).execute()
            return msg
        except Exception as e:
            return 'except:' + str(e)

    def get_headers_info_from_msg(self, msg_by_id):
        try:
            subject, remetente, messageId, content, dataEnvio = '','','','',''
            headers = msg_by_id['payload']['headers']
            for x in headers:
                if x["name"] == "Subject":
                    subject = x['value']
                if x["name"] == "From":
                    remetente = x["value"]
                if x["name"] == "Message-ID":
                    messageId = x["value"]
                if x['name'] == "Content-Type":
                    content = x["value"]
                if x["name"] == "Date":
                    dataenvio = x["value"]
                    tamFinal = len(dataenvio) - 5
                    dataEnvio = dataenvio[0:tamFinal]
            return subject, remetente, messageId, content, dataEnvio
        except Exception as e:
            return 'except:', str(e), '', '',''

    def count_msg_atachments(self, message):
        count = 0
        try:
            for part in message['payload']['parts']:
              if part['filename']:
                  count +=1
        except Exception as e:
            print(e)
        return count


    def get_body_msg(self, msg):
        # https://stackoverflow.com/questions/50630130/how-to-retrieve-the-whole-message-body-using-gmail-api-python
        if msg.get("payload").get("body").get("data"):
            return base64.urlsafe_b64decode(msg.get("payload").get("body").get("data").encode("ASCII")).decode("utf-8")
        return msg.get("snippet")


    def get_textplain_body_msg(self, msg):
        payload = msg['payload']
        parts = payload['parts']
        corpo = ''
        fullbody = ''
        for part in parts:
            mimetype = part.get("mimeType", "NA")
            bodypart = part.get("body", "nobody")
            if mimetype == 'text/plain':
                #print("entrou no if")
                headers = part['headers']
                for header in headers:
                    if header['name'] == "Contant-Type":
                        contenttypevalue = header['value']
                        listcontenttype = contenttypevalue.split(";")
                        contenttype = listcontenttype[0]
                        charset = listcontenttype[1]
                        print("contenttype: {}; charset: {};".format(contenttype, charset))
                bodymessage = part.get('body').get('data')
                corpo = base64.urlsafe_b64decode(bodymessage.encode('ASCII'))
                corpo = corpo.decode('utf-8')
                fullbody = fullbody + corpo
                #print(corpo[:200])
            elif mimetype == "multipart/alternative":
                print("entrou no elif")
                print("existe subpart")
                for subpart in part['parts']:
                    # print(subpart)
                    mimetype = subpart.get('mimeType', "")
                    #print(mimetype)
                    if mimetype == 'text/plain':
                        #print("mimetype: {} =============".format(mimetype))
                        msg_html_text = subpart.get('body').get('data')
                        corpo = base64.urlsafe_b64decode(msg_html_text.encode('ASCII'))
                        corpo = corpo.decode('utf-8')
                        fullbody = fullbody + corpo
        #print("========================+++++++====================")
        return fullbody


    def remove_inbox_unread_labels(self, msgid):
        #modificaLabel = {'addLabelIds': ['STARRED'], 'removeLabelIds': ['INBOX','UNREAD']}
        modificaLabel = {'addLabelIds': ['STARRED'], 'removeLabelIds': ['INBOX', 'UNREAD']}
        try:
            modifica = self.service.users().messages().modify(userId='me', id=msgid, body=modificaLabel).execute()
            print(modifica)
            return "ok"
        except Exception as e:
            return 'except:'+str(e)


    def add_label(self, msgid, label):
        #modificaLabel = {'addLabelIds': ['STARRED'], 'removeLabelIds': ['INBOX','UNREAD']}
        modificaLabel = {'addLabelIds': [label], 'removeLabelIds': []}
        try:
            modifica = self.service.users().messages().modify(userId='me', id=msgid, body=modificaLabel).execute()
            return "ok"
        except Exception as e:
            return 'except:' + str(e)


    def get_previous_msg_id_by_threadid(self, msgid):
        try:
            thread = self.service.users().threads().get(userId='me', id=msgid).execute()
            messages = thread['messages']
            if len(messages) > 1:
                previous_msg_id = messages[-2]['id']
            else:
                previous_msg_id = 'na'
            return previous_msg_id
        except Exception as e:
            return 'except:'+str(e)

    def get_attachments_save_local(self, msg_id, store_dir):
      """Get and store attachment from Message with given id.
      Args:
        service: Authorized Gmail API service instance.
        user_id: User's email address. The special value "me"
        can be used to indicate the authenticated user.
        msg_id: ID of Message containing attachment.
        store_dir: The directory used to store attachments.
      """
      try:
        message = self.service.users().messages().get(userId='me', id=msg_id).execute()
        count = 0
        for part in message['payload']['parts']:
          if part['filename']:
            file_data = base64.urlsafe_b64decode(part['body']['data'].encode('UTF-8'))
            path = ''.join([store_dir, part['filename']])
            f = open(path, 'w')
            f.write(file_data)
            f.close()
            count += 1
        return count
      except errors.HttpError as error:
        print('An error occurred: %s' % error)
        return 0

    # https://stackoverflow.com/questions/25832631/download-attachments-from-gmail-using-gmail-api
    def get_attachments_memory_save_google_drive(self, msg_id,cpf1, folder_name, gdrive_service, parents_list=[]):
        print('get_attachments')
        
        if folder_name == '':
            folder_name = msg_id
        #client_folder_id = gdrive_service.create_folder(folder_name,parents_list)
        parents_list=[]#[client_folder_id]
        
        message = self.service.users().messages().get(userId='me', id=msg_id).execute()
        #pprint(message)
        print('++++++++++++++++++++++++++++++++++++++++++++++++++++')
        
        count = 0
        parts = message['payload']
        #while parts:
        for part in message['payload']['parts']:
            #part = parts.pop()
            #if part.get('parts'):
            #    parts.extend(part['parts'])
            if part.get('filename'):
                if 'data' in part['body']:
                    file_data = base64.urlsafe_b64decode(part['body']['data'].encode('UTF-8'))
                    #self.stdout.write('FileData for %s, %s found! size: %s' % (message['id'], part['filename'], part['size']))
                elif 'attachmentId' in part['body']:
                    attachment = self.service.users().messages().attachments().get(userId='me', messageId=message['id'], id=part['body']['attachmentId']).execute()
                    file_data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))
                    #self.stdout.write('FileData for %s, %s found! size: %s' % (message['id'], part['filename'], attachment['size']))
                else:
                    file_data = None
                if file_data:
                    file_name = part['filename']
                    print(file_name)
                    fh_data = io.BytesIO(base64.b64encode(file_data))
                    gdrive_service.upload_file_from_memory(fh_data, file_name, parents_list)
                    count += 1
        return count    

    def get_attachments_to_save_google_drive(self, msg_id, cpf1, gdrive_service, parents_list):
        """Get and store attachment from Message with given id.

        :param service: Authorized Gmail API service instance.
        :param user_id: User's email address. The special value "me" can be used to indicate the authenticated user.
        :param msg_id: ID of Message containing attachment.
        """
        try:
            pass
        except:
            pass
        if True:
            message = self.service.users().messages().get(userId='me', id=msg_id).execute()
            count = 0
                        
            print(msg_id)
            
            for part in message['payload']['parts']:
                if part.get('filename'):
                    mime_type = part.get('mimeType')
                    if part.get('body'):
                        if 'data' in part['body']:
                            data = part['body']['data']
                        else:
                            att_id = part['body']['attachmentId']
                            att = self.service.users().messages().attachments().get(userId='me', messageId=msg_id, id=att_id).execute()
                            data = att['data']
                        
                        cpf1 = cpf1.replace(".","")
                        
                        # salva arquivo temporario com cpf para evitar problema com dois arquivos com mesmo nome
                        # de clientes diferentes
                        file_name = str(cpf1)+part['filename']
                        
                        # decode and save file locally
                        file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))

                        if sys.platform == 'linux':
                            folder_name = "/tmp/"
                        else:
                            folder_name = os.path.join(pathlib.Path(__file__).parent.absolute(), "files")
                        
                        print(folder_name)
                        local_file_name = os.path.join(folder_name, file_name)
                        
                        f = open(local_file_name, 'wb')
                        f.write(file_data)
                        f.close()

                        # upload file to google drive
                        gdrive_service.upload_file(local_file_name, part['filename'], parents_list)
                        
                        # remove local file
                        if os.path.exists(local_file_name):
                            os.remove(local_file_name)
                        
                        count +=1
            r = {
                'attachment_number': count
            }
            return r
        try:
            pass
        except Exception as e:
            print(str(e))
            return str(e)

    def GetMessage(self, msg_id):
      try:
        message = self.service.users().messages().get(userId='me', id=msg_id).execute()
        print('Message snippet: %s' % message['snippet'])
        return message
      except errors.HttpError as error:
        print( 'An error occurred: %s' % error)


    def GetMimeMessage(self, msg_id):
      try:
        message = self.service.users().messages().get(userId='me', id=msg_id, format='raw').execute()
        print('Message snippet: %s' % message['snippet'])
        msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))
        #mime_msg = email.message_from_string(msg_str)
        return msg_str
      except errors.HttpError as error:
        print('An error occurred: %s' % error)


    def get_body_msg_excepts(self, msg_by_id):
        try:
            # pprint(msg_by_id['payload'])
            body = msg_by_id['payload']['parts'][0]
            tri1 = "Foi pelo try1"
            print("Foi pelo try1")
        except:
            body = msg_by_id['payload']
            tri1 = "Foi pelo except1"
            print("Foi pelo except1")
        try:
            corpo = body['body']['data']
            tri2 = "Foi pelo try2"
            print("Foi pelo try2")
        except:
            try:
                corpo = body['parts'][0]['body']['data']
                tri2 = "Except 2 try 1"
                print("Except 2 try 1")
            except:
                corpo = body['parts'][0]['parts'][0]['body']['data']
                tri2 = "Except 2 except 1"
                print("Except 2 except 1")
        corpo = base64.urlsafe_b64decode(corpo.encode('ASCII'))
        corpo = corpo.decode('utf-8')
        corpo = str(corpo)
        return corpo
