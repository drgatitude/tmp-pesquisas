import json
import os
import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
import numpy as np

import settings as st
from utils import upload_html_pdf_files

#from decouple import config
#from apps.prior_research.models import ResearchExecution

URL_CADMUT_BASE = 'https://www.cadastromutuarios.caixa.gov.br{}'
URL_2CAPTCHA_BASE = 'http://2captcha.com/{}'

# timeout no post
CADMUT_TIME_OUT_EXCEPT = 'Read timed out'
CNX_ERROR = ['Max retries exceeded with url']

def search_cadmut(lead_proponents, folder_id):
    '''
    returns a list of dicts
    '''
    url_research = URL_CADMUT_BASE.format('/sicdm/CDM/WEB/009/consulta.do')
    url_research_action = URL_CADMUT_BASE.format('/sicdm/CDM/WEB/009/consulta.do?acao=report_retorno')

    with requests.Session() as session:
        processed, e = login_cadmut(session)
        response_dict = []
        json_data = {"status": "inicio", "meta_data": {
            "message": "nao pesquisado", "cod_proposta": ""}, "html_result": ""}

        if processed:
            for item in lead_proponents:
                try:
                    response = session.get(
                        url_research, verify=False, timeout=2)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    codes = soup.find_all('img')
                    code_complete = ''
                except Exception as e:
                    json_data = json.dumps({"status": "erro", "meta_data": {
                        "message": "Erro no CADMUT - {}".format(e), "cod_proposta": ""}, "html_result": ""})
                else:
                    for i in range(1, 5):
                        letter = codes[i].attrs.get("src")[-5:]
                        code_complete += letter[0]

                    payload = {'consulta': '0', 'IN_CD_CPF_PAG': item['cpf'], 'IN_CD_AG_FINANCEIRO_PAG': '', 'IN_NR_CONTRATO_PAG': '', 'IN_CD_GRAU_HIPOTECA_PAG': '',
                               'IN_NM_MUTUARIO_PAG': '', 'IN_NM_MUTUARIO2_PAG': '', 'IN_SG_UF': '0', 'IN_NM_END_IMOVEL': '', 'senha': code_complete, 'valcpf': '0', 'controle': '0'}
                    response = session.post(url_research_action,
                                            data=payload, verify=False, timeout=2)
                    tables = pd.read_html(response.text)

                    json_data = {"status": "erro", "meta_data": {
                        "message": "Erro no CADMUT - {}".format(e), "cod_proposta": ""}, "html_result": ""}

                    if tables[4].iloc[0][0] is np.NaN:
                        json_data = {"status": "ok", "meta_data": {
                            "message": "Nada consta", "cod_proposta": ""}, "html_result": response.text}

                    else:
                        json_data = {"status": "ok", "meta_data": {
                            "message": "Consta", "cod_proposta": ""}, "html_result": response.text}
                    
                    # SALVA NO DRIVE
                    file_name_html = str(item['nome'])+"_"+json_data['meta_data']['message']+"_CADMUT.html"
                    file_name_pdf = str(item['nome'])+"_"+json_data['meta_data']['message']+"_CADMUT.pdf"

                    cadmut_html = response.text
                    cadmut_html = cadmut_html.replace('/sicdm/images/logoCEF.gif','logoCEF.gif')

                    upload_html_pdf_files(
                        file_name_html, file_name_pdf, cadmut_html, folder_id)

                finally:
                    response_dict.append(json_data)
                    
            
            return response_dict
            
        else:
            # ERRO NO LOGIN
            response_dict.append({"status": "erro", "meta_data": {
                "message": "Erro CADMUT login_cadmut. Exception - {}".format(e), "cod_proposta": ""}, "html_result": ""})
            return response_dict

def login_cadmut(session, g_response=False):
    credential = st.cadmut['CADMUT_CREDENTIAL']  # config('CADMUT_CREDENTIAL')
    password = st.cadmut['CADMUT_PASSWORD']  # config('CADMUT_PASSWORD')
    url_validate = 'https://acessoseguro.caixa.gov.br/login-internet.do'
    url_login_manual = 'https://acessoseguro.caixa.gov.br/internet.do?segmento=CONVENIADO01&urlCallback=https://www.cadastromutuarios.caixa.gov.br/sicdm/ReceberParametros'
    url_login = URL_CADMUT_BASE.format('/sicdm/ReceberParametros')
    url_cadmut = URL_CADMUT_BASE.format('')
    #https://acessoseguro.caixa.gov.br/login-internet.do/sicdm/ReceberParametros
    # https://www.cadastromutuarios.caixa.gov.br//sicdm/ReceberParametros
    
    while g_response is False:
        try:
            response = session.get(url_cadmut, verify=False, timeout=10)
            print(url_cadmut)
            soup = BeautifulSoup(response.text, 'html.parser')
            site_key = soup.find("div", attrs={'class': 'g-recaptcha'})
            site_key = site_key.attrs.get("data-sitekey")
            print('login cadmut')
        except Exception as e:
            return False, e
        g_response = resolve_captcha(site_key)

    payload_captcha = {'segmento': 'CONVENIADO01', 'tipoAutenticacao': 'internet', 'template': '', 
                        'perfil': 'DEFAULT', 'urlCallback': URL_CADMUT_BASE.format('/sicdm/ReceberParametros'),
                       'pageName': 'login-internet', 'tipoCredencial': '0001', 
                       'codigoCredencial': credential, 'senha': password, 
                       'g-recaptcha-response': g_response, 'idBotao': 'ACESSAR'}
    print('post 1')
    try:
        response = session.post(
            url_validate, data=payload_captcha, verify=False, timeout=2)
        print(response.text)
    except Exception as e:
        print('url_validate: {}'.format(e))
        return False, e

    print('after validate')
    soup = BeautifulSoup(response.text, 'html.parser')
    ptype = soup.find('input', attrs={'id': 'pType'})
    try:
        ptype = ptype.attrs.get('value')
    except Exception as e:
        result = "verifique senha: ptype not found - " + str(e)
        return False, result
        
    enc = soup.find('input', attrs={'id': 'enc'})
    enc = enc.attrs.get('value')

    payload = {'pType': ptype, 'enc': enc}
    try:
        response = session.post(url_login, data=payload,
                                verify=False, timeout=10)
    except Exception as e:
        print('except confirma login')
        return False, 'except confirma login {}'.format(e)

    body = response.text
    isLogged = body.find('Consultar')
    if isLogged > -1:
        return True, 1
    else:
        return False, 'Page not match'


def resolve_captcha(googlekey):
    apikey = st.TWOCAPTCHAKEY #config('2CAPTCHAKEY')
    credits = get_balance(apikey)
    print('credit: {}'.format(credits))
    if credits >= 0.006:
        data = {'key': apikey, 'method': 'userrecaptcha',
                'googlekey': googlekey, 'pageurl': URL_CADMUT_BASE.format('')}
        try:
            r = requests.post(URL_2CAPTCHA_BASE.format(
                'in.php'), data=data, timeout=10)
        except Exception as e:
            json_data = json.dumps({"status": "2", "meta_data": {
                "message": "Erro no CADMUT função resolve_captcha- {}".format(e), "cod_proposta": ""}, "html_result": ""})
            return json_data
        reqid = r.text[r.text.find('|')+1:]
        url_ret = URL_2CAPTCHA_BASE.format(
            'res.php?key=' + apikey + '&action=get&id=' + reqid)
        
        time.sleep(15)
        
        r = requests.get(url_ret, timeout=15)
        print(r.text)

        while 'CAPCHA_NOT_READY' in r.text:
            r = requests.get(url_ret)
            time.sleep(5)
        resp = r.text[r.text.find('|') + 1:]
        print(resp)
        if 'ERROR_CAPTCHA_UNSOLVABLE' in r.text:
            return False
        else:
            return resp
    else:
        json_data = {"status": "2", "meta_data": {
            "message": "Acabou o crédito na conta do 2captcha.", "cod_proposta": ""}, "html_result": ""}
        return json_data


def get_balance(apikey):
    url = URL_2CAPTCHA_BASE.format(
        'res.php?key=' + apikey + '&action=getbalance')
    try:
        response = requests.get(url, timeout=5)
    except Exception as e:
        json_data = json.dumps({"status": "2", "meta_data": {
            "message": "Erro no CADMUT função get_balance- {}".format(e), "cod_proposta": ""}, "html_result": ""})
        return json_data
    return float(response.text)


def persist_cadmut_execution_result(system, lead_proponent, jsonify_result):
    """
    Persists cadmut execution result 
    """
    print('NA')
    '''
    research_execution = ResearchExecution(
        lead_proponent=lead_proponent,
        meta_data=jsonify_result.get('meta_data'),
        system=system,
        status=jsonify_result.get('status'),
        html_result=jsonify_result.get("html_result")
    )
    research_execution.save()
    '''
