# coding: utf-8
# uvicorn main:app --reload
import os
import uvicorn
from fastapi import FastAPI
from fastapi import BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from models import ProposalData, GoogleChatMsg, HistoricData

from views import create_proposal, include_historic
from views import run_receita, run_cadmut, run_portal, run_download_files, run_sicaq_pesq_cadastral
from views import run_ciweb
#from views import bot_sucesso


import settings as st
origins = st.origins

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def main():
    return {"message": "Main page"}


@app.get("/createproposal1")
def createproposalget():
    #return_data = {}
    print('get_create_proposal')
    return {"message": "dados recebidos"}


@app.post("/createproposal")
def createproposal(item: ProposalData, background_tasks: BackgroundTasks):
    data = {} #st.data
    data['cpf1'] = item.cpf1
    data['cpf2'] = item.cpf2
    data['cpf3'] = item.cpf3
    data['nome1'] = item.nome1
    data['nome2'] = item.nome2
    data['nome3'] = item.nome3
    data['nasc1'] = item.nasc1
    data['nasc2'] = item.nasc2
    data['nasc3'] = item.nasc3
    data['sexo1'] = item.sexo1
    data['sexo2'] = item.sexo2
    data['sexo3'] = item.sexo3

    data['imobiliaria'] = item.imobiliaria
    data['empreendimento'] = item.empreendimento
    data['codempreendimento'] = item.codempreendimento
    data['codGerente'] = item.codGerente,
    data['codImob'] = item.codImob,
    
    data['msg_id'] = item.msg_id
    data['card_id'] = item.card_id
    data['user_id'] = item.user_id
    
    data['sicaq'] = item.sicaq
    data['cadmut'] = item.cadmut
    data['ciweb'] = item.ciweb
    data['receita'] = item.receita
    data['portal'] = item.portal
    data['pastas'] = item.pastas

    data['prop_id'] = item.propid
    
    # views
    result = {}
    try:
        data, r_sicaq = create_proposal(data)
        result['status'] = r_sicaq['status']
        result['url_folder'] = data['url_folder']
    except Exception as e:
        result['status'] = 'except create_proposal: ' + str(e)
        result['url_folder'] = 'sem informação'
        
    if data['pastas'] == 'S':
        background_tasks.add_task(run_download_files, data)

    if data['portal'] == 'S':
        background_tasks.add_task(run_portal, data)

    if data['sicaq'] == 'S':
        r_sicaq['card_id'] = data['card_id']
        background_tasks.add_task(run_sicaq_pesq_cadastral, r_sicaq)

    if data['receita'] == 'S':
        background_tasks.add_task(run_receita, data)
    
    if data['cadmut'] == 'S':
        background_tasks.add_task(run_cadmut, data)
    
    if data['ciweb'] == 'S':
        background_tasks.add_task(run_ciweb, data)
    
    
    return result


@app.get('/endpoints')
def listendpoints():
    return {"endpoints": '/criachecklist , /botsucesso, /folgaspontomais, /criaproposta'}


@app.get("/testproposal")
def test_proposal(background_tasks: BackgroundTasks):
    item = {
        'portal': 'S'
    }
    return_data = {}
    if item['portal'] == 'S':
        print('portal')
        data_portal = {
            'cpf1': '12345678909',
            'name1': 'VANIA MARIA BOTELHO',
            'birth_date1': '05/05/2000',
            'gender1': 'F',
            'tipoPesquisa': "teste",
            'sicaq': 'N',
            'portal': 'S',
            'msg_id': '17ab20aa5c6d2ef3',
            'tipoPesquisa' : 'teste',
            'acao':'atendimento'
        }
        #background_tasks.add_task(treat_proposal, data_portal)
    return {'message':"dados recebidos"}


@app.post('/botsucesso')
def callbotsucesso(chat_json):
    '''space = item.space
    contentName = item.contentName
    resourceName = item.resourceName
    attachmentDataRef = item.attachmentDataRef
    downloadUri = item.downloadUri
    thumbnailUri= item.thumbnailUri
    print(thumbnailUri)
    
    bot_dict = {
        "rstatus_code":503,
        "contentName": contentName,
        "resourceName": resourceName,
        "attachmentDataRef": attachmentDataRef,
        "downloadUri": downloadUri,
        "thumbnailUri": thumbnailUri
    }
    
    
    '''
    print(chat_json)
    #r = bot_sucesso(bot_dict)
    return {"message":"ok"}

@app.post('/incluihistorico')
def incluihistorico(item: HistoricData):
    data = {}
    data['contrato'] = item.contrato
    data['cpf1'] = item.cpf1
    data['nome1']= item.nome1
    data['nasc1'] = item.nasc1
    data['imobiliaria'] = item.imobiliaria
    data['gerente']= item.gerente
    data['empreendimento']= item.empreendimento
    data['codempreendimento']= item.codempreendimento
    data['codGerente']= item.codGerente
    data['codImob'] = item.codImob
    data['observacao'] = item.observacao
    data['url_folder'] = item.observacao
    r = include_historic(data)
    return r


    

@app.get('/botsucesso')
def botsucessoget():
    #r = bot_sucesso.bot_get_spaces()
    r = ''
    return {"message":r}


@app.options('/botsucesso')
def botsucessooptions():
    return {"message": "options"}
    

if __name__=='__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
