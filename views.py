#coding: utf-8

import re
import sys
from datetime import datetime
from api_gmail import GmailService
from api_google_drive import DriveService
from api_portal import PortalService
from api_trello import TrelloBoard
import api_firebase as afb


#import botsucesso
import settings as st

if sys.platform == 'linux':
    gmail_service = GmailService(
        '/tmp/gmail_token.pickle', '/tmp/gmail_credentials.json')
    drive_service = DriveService('/tmp/gdrive_token.json')
else:
    gmail_service = GmailService(
        'gmail_token.pickle', 'gmail_credentials.json')
    drive_service = DriveService('gdrive_token.json')

origins = st.origins

config_portal = st.portal_config
portal_service = PortalService(config_portal)

config_trello = st.trello_boards_lists_key_data
trello_service = TrelloBoard("Operação", config_trello)


import utils

from utils import upload_gdrive, upload_sicaq_file, calcula_restr_cad

import sicaq
import pesq_cadmut as cadmut
import pesq_ciweb as ciweb
import pesq_receita as receita


afb_collection = st.afb_collection

def include_historic(data):
    r = portal_service.verifica_e_loga()
    print(r)
    r_data = portal_service.inclui_historico(data)
    return r_data

def create_proposal(data):
    return_data = {}
    r_sicaq = {}
    
    doc_name = datetime.now().strftime('%y%m%d_%H%M%S') +"_"+ str(data['cpf1'])
    afb.save_info_firestore(afb_collection,doc_name,data)

    # background tasks:
    # portal, receita, ciweb, cadmut

    #store_dir = '/files/{}'.format(item.msg_id)
    #os.mkdir(store_dir)
    print(data['msg_id'])
    
    r_sicaq['status'] = 'iniciando'
    # list com cpf1 e depois append cpf2 e cpf3 , se houver
    cpfs = [data['cpf1']]
    qtd_cpf = 1
    if data['cpf2'] != "":
        cpfs.append(data['cpf2'])
        qtd_cpf = 2
    if data['cpf3'] != "":
        cpfs.append(data['cpf3'])
        qtd_cpf = 3

    # Sicaq
    if data['sicaq'] in ['S', 'N']:
        # realizar em qq caso, por causa da data de aniversario e nome, para nome do arquivo das pesquisas
        login_sicaq = st.sicaq_config475['login']
        password_sicaq = st.sicaq_config475['password']
        covenant = st.sicaq_config475['convenio']
        has_to_verify_cert = st.sicaq_config475['has_to_verify_certificate']
        r_sicaq = sicaq.search_sicaq(cpfs, login_sicaq, password_sicaq, covenant, has_to_verify_cert)
        print(r_sicaq)
        
        # ATUALIZA NOME PELO SICAQ E CALCULA RESTRICAO CADASTRAL
        data['nome1'] = r_sicaq['data']['cpf1']['cliente']['cliente']['nome'].title()
        if data['card_id'] != '':
            add_trello(data['card_id'], 'ciweb: {}'.format(data['nome1']))
        data['nasc1'] = r_sicaq['data']['cpf1']['nasc']
        restr_cad = calcula_restr_cad(r_sicaq['data']['cpf1'])
        
        if qtd_cpf > 1:
            data['nome2'] = r_sicaq['data']['cpf2']['cliente']['cliente']['nome'].title()
            data['nasc2'] = r_sicaq['data']['cpf2']['nasc']
            restr_cad2 = calcula_restr_cad(r_sicaq['data']['cpf2'])
            # Se cpf1 ou cpf2 tiver restricao, tem restricao
            if restr_cad == 'Sim' or restr_cad2 == 'Sim':
                restr_cad = 'Sim'
        
        if qtd_cpf > 2:
            data['nome3'] = r_sicaq['data']['cpf3']['cliente']['cliente']['nome'].title()
            data['nasc3'] = r_sicaq['data']['cpf3']['nasc']
            restr_cad2 = calcula_restr_cad(r_sicaq['data']['cpf3'])
            if restr_cad == 'Sim' or restr_cad2 == 'Sim':
                restr_cad = 'Sim'

        data['restr_cad'] = restr_cad
        
        return_data.update({'r_sicaq': r_sicaq})

    if data['nome1'] == "":
        folder_name = data['cpf1']
    else:
        folder_name = data['nome1']
    
    parents_list = st.shared_drive_2S21
    data['folder_id'] = drive_service.create_folder(folder_name, parents_list)
    
    r_sicaq['folder_id'] = data['folder_id']
    r_sicaq['qtd_cpf'] = qtd_cpf
    r_sicaq['restr_cad'] = restr_cad

    file_data = str(data)
    r = upload_gdrive('resumo.txt', file_data,[data['folder_id']], 
                        mime_type='text/plain', file_write_type='w')
    
    data['url_folder'] = st.url_gdrive_folders.format(data['folder_id'])

    return data, r_sicaq


def run_sicaq_pesq_cadastral(r_sicaq):
    try:
        file_id = upload_sicaq_file(r_sicaq, 1)

        if r_sicaq['qtd_cpf'] > 1:
            # segundo cpf
            file_id = upload_sicaq_file(r_sicaq, 2)

        if r_sicaq['qtd_cpf'] > 2:
            #terceiro cpf
            file_id = upload_sicaq_file(r_sicaq, 3)

        if r_sicaq['card_id'] != '':
            restr_cad = r_sicaq.get('restr_cad','na')
            add_trello(r_sicaq['card_id'], 'pesq cadastral: {}'.format(restr_cad))

        print('end run_sicaq')
        return 1
    except Exception as e:
        print('except sicaq: {}'.format(e))
        doc_name = 'except'+ str(r_sicaq['data']['cpf1']['cliente']['cliente']['cpf'])
        afb.save_info_firestore(afb_collection, doc_name, 'except run_sicaq: {}'.format(e))
        return 0


def run_download_files(data):
    try:
        parents_list = [data['folder_id']]
        #return_data = {}

        # busca anexos pelo msg_id e salva arquivos no google_drive
        print('download files msg_id: {}.'.format(data['msg_id']))
        if data['msg_id'] != '':
            r_gmail = gmail_service.get_attachments_to_save_google_drive(
                data['msg_id'], data['cpf1'],drive_service, parents_list)

            comment = 'download files: {}.'.format(data['msg_id'])
            #return_data.update({'status':'ok','r_gmail_drive': r_gmail})
        else:
            comment = 'download files: sem msg_id.'
            #return_data.update({'status':'sem msg_id'})

        if data['card_id'] != '':
            add_trello(data['card_id'], comment)

        print('end run_download_files')
        return 1
    except Exception as e:
        print('except download: {}'.format(e))
        doc_name = 'except' + str(data['cpf1'])
        afb.save_info_firestore(
            afb_collection, doc_name, 'except download: {}'.format(e))
        return 0


    
def run_portal(data):
    try:
        folder_id = data['folder_id']

        # Portal
        if data['portal'] == 'S':
            print('portal')
            data['url_folder'] = "["+st.url_gdrive_folders.format(folder_id)+"]"
            nro_contrato, contrato = portal_service.cadastro_cliente(data)
            #r_data = portal_service.inclui_historico(data)
            comment = 'portal contrato: {}; {}'.format(nro_contrato, contrato)
        else:
            comment = 'portal desligado.'

        if data['card_id'] != '':
            add_trello(data['card_id'], comment)

        print('end run_portal')
        return 1
    except Exception as e:
        doc_name = 'except' + str(data['cpf1'])
        afb.save_info_firestore(
            afb_collection, doc_name, 'except portal: {}'.format(e))
        return 0


def run_receita(data):
    try:
        # Receita
        folder_id = data['folder_id']

        r_receita1 = 'rec1'
        r_receita2 = 'rec2'
        r_receita3 = 'rec3'

        print(data)
        if data['receita'] == 'S':
            if data['nasc1'] is None:
                r_receita1 = 'receita: erro na data de nascimento1'

            elif "/" in data['nasc1'] and len(data['nasc1']) == 10:
                # salva no drive dentro da funcao receita
                r_receita1 = receita.main_receita(data['nome1'],
                                                 data['cpf1'],
                                                 data['nasc1'],
                                                 '/tmp',
                                                 folder_id,
                                                 drive_service)

                #return_data.update({'status':'ok','receita': r_receita})
                #print('receita: {}'.format(r_receita))

            if data['cpf2'] != "":
                if data['nasc2'] is None:
                    r_receita2 = 'receita: erro na data de nascimento 2'

                elif "/" in data['nasc2'] and len(data['nasc2']) == 10:
                # salva no drive dentro da funcao receita
                    r_receita2 = receita.main_receita(data['nome2'],
                                                 data['cpf2'],
                                                 data['nasc2'],
                                                 '/tmp',
                                                 folder_id,
                                                 drive_service)

            if data['cpf3'] != "":
                if data['nasc3'] is None:
                    r_receita3 = 'receita: erro na data de nascimento 3'

                elif "/" in data['nasc3'] and len(data['nasc3']) == 10:
                # salva no drive dentro da funcao receita
                    r_receita3 = receita.main_receita(data['nome3'],
                                                 data['cpf3'],
                                                 data['nasc3'],
                                                 '/tmp',
                                                 folder_id,
                                                 drive_service)

        if data['card_id'] != '':
            add_trello(data['card_id'], 'receita: {};{};{}'.format(r_receita1,r_receita2,r_receita3))

        print('end run_receita:{}'.format(r_receita1))
        return 1

    except Exception as e:
        print('except receita: {}'.format(e))
        doc_name = 'except' + str(data['cpf1'])
        afb.save_info_firestore(
            afb_collection, doc_name, 'except receita: {}'.format(e))
        return 0



def run_cadmut(data):
    try:
        folder_id = data['folder_id']
        
        if data['cadmut'] == 'S':
            # monta dict com nome e cpf dos clientes    
            cpfs_nomes = create_cpfs_nomes(data)

            # salva no drive dentro da funcao cadmut
            r_cadmut = cadmut.search_cadmut(cpfs_nomes, folder_id)
            #print(r_cadmut)
            comment = 'cadmut: {}'.format(r_cadmut[0]['meta_data']['message'])
        else:
            comment = 'cadmut: nao pesquisado'

        if data['card_id'] != '':
            add_trello(data['card_id'], 'cadmut: {}'.format(comment))

        print('end run_cadmut:{}'.format(comment))
        
        doc_name = 'cadmut' + str(data['cpf1'])
        afb.save_info_firestore(afb_collection, doc_name, 'cadmut: {}'.format(comment))
        return 1
    except Exception as e:
        print('except cadmut: {}'.format(e))
        doc_name = 'except' + str(data['cpf1'])
        afb.save_info_firestore(
            afb_collection, doc_name, 'except cadmut: {}'.format(e))
        return 0



def run_ciweb(data):
    try:
        folder_id = data['folder_id']

        day_of_week = datetime.today().strftime('%A')
        # dia da semana comeca com 0 para segunda. sabado eh 6 e domingo 7
        if day_of_week in ['Saturday','Sunday']:
            comment = 'fim de semana, ciweb: nao pesquisado'
        elif datetime.now().hour in [0,1,2,3,4,5,6,7,23]:
            comment = 'fora do horario, ciweb: nao pesquisado'
        elif data['ciweb'] == 'S':
            print('ciweb')
            cpfs_nomes = create_cpfs_nomes(data)
            r_list = ciweb.search_ciweb(cpfs_nomes, folder_id)
            comment = 'ciweb: {}'.format(r_list[0]['message'])
        else:
            comment = 'ciweb: nao pesquisado'

        if data['card_id'] != '':
            add_trello(data['card_id'], 'ciweb: {}'.format(comment))

        print('run_ciweb: {}'.format(comment))
        doc_name = 'ciweb' + str(data['cpf1'])
        afb.save_info_firestore(afb_collection, doc_name, 'ciweb: {}'.format(comment))

        return 1
    except Exception as e:
        print('except ciweb: {}'.format(e))
        doc_name = 'except' + str(data['cpf1'])
        afb.save_info_firestore(
            afb_collection, doc_name, 'except ciweb: {}'.format(e))
        return 0



def create_cpfs_nomes(data):
    cpfs_nomes = [{'cpf': data['cpf1'], 'nome':data['nome1']}]
    if data['cpf2'] != "":
        cpfs_nomes.append({'cpf': data['cpf2'], 'nome': data['nome2']})

    if data['cpf3'] != "":
        cpfs_nomes.append({'cpf': data['cpf3'], 'nome':data['nome3'] })
    
    return cpfs_nomes

def add_trello(card_id,text):
    if len(card_id) > 3:
        trello_service.add_comment(card_id,text)



def bot_sucesso(bot_dict):
    print('TODO bot sucesso')
    #r = botsucesso.main(rjson)
    return 'ok'
