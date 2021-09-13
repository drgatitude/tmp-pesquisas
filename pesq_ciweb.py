# coding: utf-8
import json
import requests
import json
import time
import sys
import os
import logging
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup
from decouple import config

from ciweb_encrypt import ciweb_encrypt
import settings as st
from utils import upload_html_pdf_files

import utils

# codigo de login por email e resolve captcha do cadmut
from api_gmail import GmailService
from pesq_cadmut import resolve_captcha

if sys.platform == 'linux':
    gmail_tecnologia_service = GmailService(
        '/tmp/gmail_token_tecnologia.pickle', '/tmp/gmail_credentials.json')
else:
    gmail_tecnologia_service = GmailService(
        'gmail_token_tecnologia.pickle', 'gmail_credentials.json')

BASE_URL_CIWEB = 'https://www.portaldeempreendimentos.caixa.gov.br/{}'

# from decouple import config
# from apps.prior_research.utils import get_credential

BASE_DIR = Path(__file__).resolve().parent.parent
TIMEOUT = 30
# Get an instance of a logger
logger = logging.getLogger("django")


def search_ciweb(lead_proponents, folder_id):
    base_url_ciweb = BASE_URL_CIWEB

    response_list = []
    strUser = st.ciweb["CIWEB_LOGIN"]
    with requests.Session() as session:
        processed, response = bypass_ciweb(session, strUser)  # bypass
        if processed:
            time.sleep(1)
            get_menu = session.get(
                base_url_ciweb.format('menu/'), verify=False, timeout=TIMEOUT)
            resp = get_menu.text

            find_bemvindo = resp.find('Seja bem-vindo')
            print('find bem vindo:{}'.format(find_bemvindo))

            time.sleep(1)

            for item in lead_proponents:
                try:
                    print('before make research')
                    status, obs, html = make_research(
                        session, base_url_ciweb, item['cpf'])

                    # jsonify_result = json.loads(json.dumps(result))
                    # persist_ciweb_execution_result('CIWEB', item, jsonify_result)
                    file_name_html = item['nome'] + obs + "CIWEB.html"
                    file_name_pdf = item['nome'] + obs + "CIWEB.pdf"

                    upload_html_pdf_files(
                        file_name_html, file_name_pdf, html, folder_id)

                    response_list.append({"cpf": item['cpf'],
                                      "message": obs,
                                      "status": status
                                      })
                except Exception as e:
                    response_list.append({"cpf": item['cpf'],
                                  "message": str(e),
                                  "status": "except"
                                  })
                time.sleep(1)

        else:
            logger.error("Processed Bypass returned 0")
            response_list.append({"cpf": "erro bypass",
                      "message": response,
                      "status": "erro"
                      })

        return response_list


def make_research(session, base_url_ciweb, cpf):
    research_url = base_url_ciweb.format("buscaSiger/BuscaSiger.asp?")

    payload_research = {
        "txtML": '',
        "txtNumeroContrato": '',
        "txtNome": '',
        "txtCpf": cpf,
        "txtPIS": '',
        "btnOk1": ''
    }

    post_research = session.post(
        research_url, data=payload_research, verify=False)

    post_research_body = convert_response_to_text_body(post_research)
    post_researh_status_code = convert_response_to_status_code(post_research)

    if post_researh_status_code != 200:
        status = "2"
        obs = f"Unexpected status code in POST research {post_researh_status_code}"
        return status, obs

    status, obs = verify_situation(post_research_body)

    return status, obs, post_research_body


def verify_situation(post_research_body):
    try:
        number_of_tables = len(pd.read_html(post_research_body))
    except ValueError:
        status = "2"
        obs = "An error has occurred in CIWEB POST return"
        return status, obs

    if "Não existe contrato" in post_research_body and number_of_tables == 1:
        status = "1"
        obs = "OK_NAO_existe"
        return status, obs

    elif "Seguradora" in post_research_body and number_of_tables == 2:
        status = "0"
        obs = "OK_EXISTE"
        return status, obs

    else:
        status = "2"
        obs = "An error has occurred in CIWEB POST return"
        return status, obs


def convert_response_to_status_code(response_obj):
    return response_obj.status_code


def verify_login_success(post_login_body):
    return (True if post_login_body.find('bem-vindo') > -1 else False)


def set_cookie(strUser):
    return config("COOKIE").format(get_ip(), strUser)


def get_ip():
    return requests.request("GET", "http://checkip.amazonaws.com/").text.strip()


def convert_response_to_text_body(response_obj):
    return response_obj.text


def get_params_from_login_page(get_login_soup):
    try:
        strPut = get_login_soup.find(
            'input', attrs={'id': 'strPut'}).get('value', 'na')
        strBid = get_login_soup.find(
            'input', attrs={'id': 'strBid'}).get('value', 'na')
        strPush = get_login_soup.find(
            'input', attrs={'id': 'strPush'}).get('value', 'na')
        idxBG = get_login_soup.find(
            'input', attrs={'id': 'idxBG'}).get('value', 'na')
    except Exception as e:
        strPut, strBid, strPush, idxBG = "na", "na", "na", "na"

    return strPut, strBid, strPush, idxBG


def bypass_ciweb(session, user):
    founded = False
    base_url_ciweb = 'https://www.portaldeempreendimentos.caixa.gov.br/{}'
    strPassword = st.ciweb['CIWEB_PASS']  # config("STRPASSWORD")
    obs = "An unknown error has occurred"
    url = base_url_ciweb.format("sso/")
    url_login = base_url_ciweb.format("sso/")

    # request 1: tela com usuario e google captcha
    get_login = session.get(url, verify=False)

    get_login_soup = BeautifulSoup(get_login.text, 'html.parser')

    site_key = get_login_soup.find("div", attrs={'class': 'g-recaptcha'})
    site_key = site_key.attrs.get("data-sitekey")

    # url_ip = "https://api.ipify.org/?format=json"
    # r_bid = session.get(url_ip)
    # var site portal
    # ssobid1 = r_bid.text

    # 1 eh strStatus da primeira tela de login
    cookie_usuid_value = '_' + user.upper() + '_' + "1"
    cookie_USUID = requests.cookies.create_cookie(
        name='USUID',
        value=cookie_usuid_value,
        path='/',
        domain='www.portaldeempreendimentos.caixa.gov.br',
        # expires=''
    )

    # Counter-intuitively, set_cookie _adds_ the cookie to your session object,
    #  keeping existing cookies in place
    session.cookies.set_cookie(cookie_USUID)
    print(session.cookies)

    g_response = False
    while g_response is False:
        g_response = resolve_captcha(site_key)

    print('after g captcha, g_response: {}'.format(g_response))

    strPut, strBid, strPush, idxBG = get_params_from_login_page(
        get_login_soup)

    payload_first = {
        "strUsuario": user,
        "strStatus": "1",
        "strBid": strBid,
        "strPut": strPut,
        "strPush": strPush,
        "idxBG": idxBG,
        "g-captcha-response": g_response
    }

    time.sleep(3)

    print('post com g captcha:')
    first_post = session.post(
        url, data=payload_first, verify=False, timeout=TIMEOUT)

    # print(first_post.text)
    print('============================================================================')
    print(payload_first)

    #    return 0, "apos post com resposta do captcha. {}".format(e)

    print('verificar codigo da matricula')
    time.sleep(5)

    # tela 2 apos primeiro post: codigo enviado por email
    if "Código de Verificação da matricula" in first_post.text or \
            "CÃ³digo de VerificaÃ§Ã£o da matricula" in first_post.text:
        second_post = send_post_email_code(first_post, session, user, url)
        print('if codigo verificacao')
        if second_post == 0:
            return 0, 'erro send post email code'
    elif "Digite sua senha" in first_post.text:
        # pulou a etapa do codigo por email e ja foi para asenha
        print('if digite sua senhas')
        second_post = first_post
    elif "Informe sua matr&iacute;cula de acesso" in first_post.text:
        # continuou na mesma tela, tentar novamente
        print("continuou na mesma tela, tentar novamente")
        second_post = first_post
        # return 0, "continuou na mesma tela, tentar novamente"
    else:
        # na duvida, tenta prosseguir
        print("foi pelo else")
        second_post = send_post_email_code(first_post, session, user, url)
        if second_post == 0:
            return 0, 'erro send post email code'

    time.sleep(2)
    print('apos etapa de codigo por email')
    # tela 3, apos segundo post e incluir senha
    get_login_body = convert_response_to_text_body(second_post)
    get_login_status_code = convert_response_to_status_code(second_post)

    if get_login_status_code != 200:
        is_logged = False
        obs = "Unexpected status code in GET login {}".format(
            get_login_status_code)
        return is_logged, obs + get_login_body

    get_login_soup = BeautifulSoup(get_login_body, 'html.parser')

    strPut, strBid, strPush, idxBG = get_params_from_login_page(get_login_soup)
    if "na" in [strPut, strBid, strPush, idxBG]:
        is_logged = False
        obs = "Can't find any of these parameters in GET login: strPut, strBid, strPush, idxBG"
        return is_logged, obs + get_login_body

    # funcao em javascript
    strPush = ciweb_encrypt.ciweb_hash(strPut, strPush, strPassword)

    payload_login = {
        "strUsuario": user,
        "strSenha": strPassword,
        "strStatus": "3",
        "strBid": strBid,
        "strPut": strPut,
        "strPush": strPush,
        "idxBG": idxBG,
    }

    try:
        cookie = ''  # set_cookie(user)
        print(cookie)
    except Exception as e:
        print('header update: {}'.format(e))

    print("***************************************")

    # ultimo post
    print('post com senha:')
    post_code_login = session.post(
        url_login, data=payload_login, verify=False, timeout=TIMEOUT)

    # verificar cod matricula
    if "CÃ³digo de VerificaÃ§Ã£o da matricula" in post_code_login.text:
        print('achou texto codigo verificacao')
        time.sleep(2)
        post_email_code = send_post_email_code(
            post_code_login, session, user, url)
        print('if codigo verificacao')
        if post_email_code == 0:
            print(post_email_code.text)
            return 0, 'erro send post email code'
    elif "Digite sua senha" in post_code_login.text:
        # ir direto para senha
        print('achou digite sua senha, nao precisa do codigo')
        post_email_code = post_code_login

    # post para enviar a senha
    get_login_soup = BeautifulSoup(post_email_code.text, 'html.parser')

    strPut, strBid, strPush, idxBG = get_params_from_login_page(get_login_soup)
    if "na" in [strPut, strBid, strPush, idxBG]:
        is_logged = False
        obs = "Can't find parameters in GET login: strPut, strBid, strPush, idxBG"
        return is_logged, obs + post_code_login.text

    # funcao em javascript
    strPush = ciweb_encrypt.ciweb_hash(strPut, strPush, strPassword)

    payload_login = {
        "strUsuario": user,
        "strSenha": strPassword,
        "strStatus": "3",
        "strBid": strBid,
        "strPut": strPut,
        "strPush": strPush,
        "idxBG": idxBG,
    }

    print('antes segundo post com senha (final):')
    print(url_login)
    post_login = session.post(
        url_login, data=payload_login, verify=False, timeout=TIMEOUT)

    # verifica se login ocorreu
    print('verifica se logou')
    if verify_login_success(post_login.text):
        print('succes')
        return 1, post_login.text
    else:
        if "Acesso ao sistema desabilitado neste per" in post_login.text and "7h" in post_login.text:
            print("sistema indisponivel")
            return 0, "sistema indisponivel, verifique dia e horario"
        else:
            print('======= get menu =====')
            get_menu = session.get(
                base_url_ciweb.format('menu/'), verify=False, timeout=TIMEOUT)
            if verify_login_success(get_menu.text):
                return 1, get_menu.text
            else:
                print(post_login.text)
                # save_file('ciweb_login_final.html', 'w', post_login.text)
                return 0, post_login.text


def send_post_email_code(first_post, session, user, url):
    '''
    return
        response from post with code sent by email
    '''
    # <span class="label-matricula">X687024</span>
    first_post_soup = BeautifulSoup(first_post.text, 'html.parser')
    nsenha = first_post_soup.findAll(attrs={'class': 'nsenha-info'})
    try:
        print(str(nsenha))
        email_reference_ = nsenha[1].text  # [31:]
        email_reference = normalize(email_reference_)
    except:
        email_reference = 'except email reference'

    strPut, strBid, strPush, idxBG = get_params_from_login_page(
        first_post_soup)

    tries = 0

    print('referencia de busca do código: {}'.format(email_reference))
    founded = False
    while founded is not True:
        print('checking founded')
        if tries <= 5 or founded == True:
            print('esperando o codigo')
            time.sleep(5)
            strcodigo = get_ciweb_email_code(email_reference)
            if strcodigo == '':
                founded = False
                tries + 1
            else:
                founded = True
                print('codigo: {}'.format(strcodigo))
        else:
            # save_file('ciweb_login.html', 'w',first_post.text)
            return 0

    payload_second = {
        "strUsuario": user,
        "strStatus": "2",
        "strCodigo": strcodigo,
        "strBid": strBid,
        "strPut": strPut,
        "strPush": strPush,
        "idxBG": idxBG,
    }

    # second_post
    print('post funcao post_send_email:{}'.format(url))
    second_post = session.post(
        url, data=payload_second, verify=False, timeout=TIMEOUT)

    return second_post


def get_ciweb_email_code(reference):
    # email_from = "SIACIWEB.SISEG@unisys.com.br"
    # reference no formato 02/09/2021 20:47:47
    print('reference:{}'.format(reference))

    # aguardar 10 segundos para esperar a mensagem chegar
    time.sleep(10)

    # verifica 5 primeiras mensagens
    i = 5
    msg_ids = gmail_tecnologia_service.get_msgid_n_first_messages_from_inbox(i)

    for j in range(0, i):
        str_code = ''
        msg = gmail_tecnologia_service.get_message_by_msgid(msg_ids[j])

        # o body da mensagem pode vir de duas formas diferentes
        # tento achar de uma, se der erro, tento a segunda
        try:
            msg_body = gmail_tecnologia_service.get_textplain_body_msg(msg)
        except:
            msg_body = gmail_tecnologia_service.get_body_msg(msg)

        if "Sua solicitacao para login no site" in msg_body:
            # pprint(msg)
            find_var = "Codigo: "
            size_code = 6
            position = msg_body.find(find_var)

            str_code = msg_body[position +
                                len(find_var):position + len(find_var) + size_code]
            print(str_code)
            # retorna o primeiro que achar
            return str_code

    return str_code


def get_ciweb_email_code_by_firebase(reference):
    # return projectAttadmin.get_documents_from_collection_isequal('codigo_ciweb', 'data_referencia', reference)
    return 'not implemented'


def normalize(string):
    """
        function to remove / and ' ' from string
    """

    s = string.replace('/', '')
    s = s.replace(':', '')
    s = s.replace(' ', '_')
    return s

