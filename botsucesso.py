# coding: utf-8
# https://console.cloud.google.com/apis/api/chat.googleapis.com/
# https://stackoverflow.com/questions/55279348/hangout-bot-how-to-mention-user-in-a-card-message/57278464#57278464
# https://developers.google.com/hangouts/chat/quickstart/gcf-bot?authuser=1
# https://developers.google.com/hangouts/chat/reference/rest

# 'users/115397794711172468233'
import json
from json import dumps, loads
from httplib2 import Http
import requests as req
import os
from datetime import datetime, timedelta
import api_google as apg
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build

from google_auth_oauthlib import flow
from google_auth_oauthlib.flow import InstalledAppFlow
from apiclient import errors
#import google.oauth2
from google.oauth2 import id_token
from google.auth.transport import requests
from google.oauth2 import service_account

import api_gsheets as ags

import settings as st

BLOB_PATH = 'botsucesso/'
SPACE_DEMANDAS_SUCESSO = st.SPACE_DEMANDAS_SUCESSO
SPACE_DANIEL = st.SPACE_DANIEL
SPACE_TEST_BOTS = st.SPACE_TEST_BOTS
SPACE_ERROS = st.SPACE_ERROS

SHEET_ID_BOT_SUCESSO = st.SHEET_ID_BOT_SUCESSO

urlerros = st.urlerros
urlsucesso = st.urlsucesso


# webhook header
message_headers = {'Content-Type': 'application/json; charset=UTF-8'}

# webhook
http_obj = Http()

CLIENT_SECRET_PATH = 'attadmin-chatbot9.json'
CLIENT_ID = st.BOT_SUCESSO_CLIENT_ID
CLIENT_SECRET = st.BOT_SUCESSO_CLIENT_SECRET


SCOPES = ['https://www.googleapis.com/auth/chat.bot']
scopes = 'https://www.googleapis.com/auth/chat.bot'

PROJETO = os.getenv('PROJETO')
if PROJETO == 'attadmin':
    creds = ServiceAccountCredentials.from_json_keyfile_name('attadmin-chatbot9.json', scopes)
else:
    print('botsucesso projeto else')
    creds = ServiceAccountCredentials.from_json_keyfile_name('atitudesf-53c7b-c52f7888061f.json', scopes)

http1 = creds.authorize(Http())
chat = build('chat', 'v1', http=creds.authorize(Http()))

#AMBIENTE = os.getenv('AMBIENTE')
SPACE = SPACE_TEST_BOTS if os.getenv('AMBIENTE') == 'PRODUCAO' else SPACE_DANIEL

def main(data):
    """
    recebe o json do request
    :returns
    """
    try:
        print(data)

        # pega space para enviar a mensagem
        space_data = apg.get_document_by_name_from_collection('chat_botsucesso', 'config')
        space = space_data.get('space')

        r = treat_message(data, space)
    except Exception as e:
        r = str(e)

    rjson = {"text":str(r)}
    print(rjson)
    rjson = dumps(rjson)
    return rjson


def send_webhook_message(message, uri=urlsucesso):
    bot_message = {'text': message}
    response = http_obj.request(uri=uri, method='POST', headers=message_headers, body=dumps(bot_message), )
    return response

def bot_get_spaces():
    # space eh a sala onde o dialogo ocorre
    resp = chat.spaces().list().execute()
    return resp

def get_space(name):
    # space eh a sala onde o dialogo ocorre
    # ex de nome: name = 'spaces/iT6JJQAAAAE'
    space = chat.spaces(name=name).get().execute()
    return space

def bot_get_space_by_name(name):
    spaceName = 'na'
    spaces = chat.spaces().list().execute()
    spacesList = spaces['spaces']
    for space in spacesList:
        if space['displayName'] == name:
            spaceName = space['name']
    return spaceName

def bot_send_message(parentspace, body):
    # body={'text': message}
    resp = chat.spaces().messages().create(parent=parentspace,body=body).execute()
    return resp

def bot_get_message(messageName):
    r = chat.spaces().messages().get(name=messageName).execute()
    return r

def bot_get_space_messages(space_name):
    r = chat.spaces(name=space_name).messages().get().execute()
    return r

def bot_get_attachments(attachmentName):
    # https://developers.google.com/hangouts/chat/reference/rest/v1/spaces.messages.attachments#Attachment
    attachment = chat.spaces().messages().attachments().get(name=attachmentName).execute()
    # print(attachment)
    contentName = attachment.get('contentName')
    # contentType = attachment.get('contentType')
    attachmentDataRef = attachment.get('attachmentDataRef')
    resourceName = attachmentDataRef.get('resourceName')
    thumbnailUri = attachment.get('thumbnailUri')
    downloadUri = attachment.get('downloadUri')
    return resourceName, contentName, thumbnailUri, downloadUri

def bot_download_media(resourceName, contentName):
    # download nao funciona por causa do alt=media
    r1 = chat.media().download(resourceName=resourceName, alt='media')
    # r = r1.execute()
    # troca do alt=json para alt=media.
    uri = r1.uri
    urimedia = uri.replace("alt=json", "alt=media")
    r1.uri = urimedia
    print(r1.uri)
    # faz o http com a mensagem apos troca do alt de json para media
    response = http1.request(uri=urimedia, method='GET', headers=r1.headers, )
    #print(response[0])
    file_data = response[1]

    #with open(contentName, 'wb') as f:
    #    f.write(file_data)
    return file_data

def get_attachment_name(attachmentName):
    url = "https://chat.googleapis.com/v1/" + attachmentName
    # token = get_oauth_service()    
    # token = get_token()
    token = '' # TODO: nao sei como gerar o token
    headers = {'Authorization': 'Bearer ' + token}
    r = req.get(url, headers=headers, allow_redirects=True)
    print(r.status_code)
    print(r.text)
    try:
        open('file.png', 'wb').write(r.content)
    except Exception as e:
        print(str(e))
    return r.text

def get_attachment(url):
    # url = "https://chat.googleapis.com/v1/media/" + dataRef + "?alt=media"
    token = creds._make_authorization_grant_assertion()
    token = token.decode("utf-8")
    headers = {'Authorization': 'Bearer ' + token} # accesstoken[0]}
    r = req.get(url, headers=headers)
    print(r.status_code)
    print(r.text)
    return r

def card_widget(text, displayName):
    #displayName = 'Meu Nome'
    cardHeader = {'title': 'Olá ' + displayName + '!', }
    rjson = {
        "cards": [
            {
                #"header": cardHeader,
                "sections": [
                    {
                        "widgets": [
                            {
                                "keyValue": {
                                    "content": "<pre>" + "Olá " + displayName + "!</pre>",
                                    "contentMultiline": "true",
                                    "icon": "CLOCK",
                                    "topLabel": "Mensagem enviada!"
                                }
                            }
                        ]
                    }
                ]
            }
        ],
        "text": text
        }
    #rjson = dumps(rjson)
    return rjson

def card_image(content, imageUrl, downloadUrl):
    rjson = {
        "cards": [
            {
                "sections": [
                    {
                        "widgets": [
                            {
                                "image": {
                                    "imageUrl": imageUrl,
                                    "onClick": {
                                        "openLink": {
                                            "url": downloadUrl
                                        }
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        ],
        "text": content,
    }

    #rjson = dumps(rjson)
    return rjson

def setTextMessage(message):
    messageDict = {'text': message}
    return messageDict

def treat_message(data, SPACE_DESTINY):
    # space
    print('treat message')
    space = data.get('space').get('name')
    message_name = data.get('message').get('name', 'na')
    name = data.get('message').get('sender').get('name')

    displayName = data.get('message').get('sender').get('displayName')
    # text
    text = data.get('message').get('argumentText', 'na')

    data_hora = data.get('eventTime','na')
    if data_hora != 'na':
        data_hora = data_hora[:19]

    # informação que vai para g sheet
    message_info = text

    if text == 'na':
        print('no text message sent')
    else:
        text = "*" + displayName + "*" + " mandou a mensagem: " + text
        body = setTextMessage(text)
        print(body)
        r = bot_send_message(SPACE_DESTINY, body)
        print(r)
        print('after send message')

    # attachment
    attachmentList = data.get('message').get('attachment', 'na')
    if attachmentList == 'na':
        print('no attachment sent')
    else:
        for attachment in attachmentList:
            attachmentName = attachment.get('name')
            contentName = attachment.get('contentName')
            contentType = attachment.get('contentType')
            resourceName = attachment.get('attachmentDataRef').get('resourceName')
            text = "*" + displayName + "*" + " enviou um arquivo: " + contentName
            thumbnailUri = attachment.get('thumbnailUri')
            downloadUri = attachment.get('downloadUri')

            filedata = bot_download_media(resourceName, contentName)
            folder = datetime.now().strftime('%y-%m-%d')
            target_key = BLOB_PATH + folder +"/"+ resourceName[:10] +"/"+ contentName
            fileurl = apg.upload_data_to_gcs(filedata, target_key)
            cardjson = card_image(text, fileurl, fileurl)
            bot_send_message(SPACE_DESTINY, cardjson)

            message_info = contentName

    response = "Mensagem enviada para a equipe de Sucesso do Cliente!"
    # salva na gsheet
    try:
        ags.append_sheet([[message_name, data_hora, displayName, message_info]], SHEET_ID_BOT_SUCESSO, "dados!A:D")
    except Exception as e:
        response = str(e)

    #message = setTextMessage("Mensagem enviada para a equipe de Sucesso do Cliente!")
    #bot_send_message(space, message)
    return response

import testdata
def teste():
    data = testdata.data
    treat_message(data, SPACE_TEST_BOTS)
    return 'get'

if __name__ == '__main__':
    data = testdata.data
    space_data = apg.get_document_by_name_from_collection('chat_botsucesso', 'config')
    space = space_data.get('space')
    print(space)
    treat_message(data, space)
    #r = bot_get_spaces()
    #print(r)

    r = bot_get_space_messages(SPACE_DEMANDAS_SUCESSO)
    print(r)





