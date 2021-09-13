from typing import Optional
from pydantic import BaseModel


class Item(BaseModel):
    name: str
    price: float
    is_offer: Optional[bool] = None


class GoogleDriveItem(BaseModel):
    local_file_name: str
    drive_file_name: str


class HistoricData(BaseModel):
    contrato: str
    cpf1: str
    nome1: str
    nasc1: Optional[str] = ""
    imobiliaria: Optional[str] = ""
    gerente: Optional[str] = ""
    empreendimento: Optional[str] = ""
    codempreendimento: Optional[str] = ""
    codGerente: Optional[str] = ""
    codImob: Optional[str] = ""
    observacao: Optional[str] = "-"


class ProposalData(BaseModel):
    nome1: Optional[str] = ""
    nome2: Optional[str] = ""
    nome3: Optional[str] = ""
    cpf1: str
    cpf2: Optional[str] = ""
    cpf3: Optional[str] = ""
    nasc1: Optional[str] = ""
    nasc2: Optional[str] = ""
    nasc3: Optional[str] = ""
    sexo1: Optional[str] = ""
    sexo2: Optional[str] = ""
    sexo3: Optional[str] = ""
    
    imobiliaria: Optional[str] = ""
    gerente: Optional[str] = ""
    empreendimento: Optional[str] = ""
    codempreendimento: Optional[str] = ""
    codGerente: Optional[str] = ""
    codImob: Optional[str] = ""

    usersicaqname: Optional[str] = ""

    msg_id: Optional[str] = ""
    card_id: Optional[str] = ""
    
    sicaq: Optional[str] = "N"
    cadmut: Optional[str] = "N"
    ciweb: Optional[str] = "N"
    receita: Optional[str] = "N"
    portal: Optional[str] = "N"
    pastas: Optional[str] = "N"
    
    googledrive: Optional[str] = ""
    
    propid: Optional[str] = ""
    user_id: Optional[str] = ""
    token: Optional[str] = ""
    
    tipoPesquisa: Optional[str] = ""
    preenchimento_manual: Optional[str] = "S"


class GoogleChatMsg(BaseModel):
    contentName: str
    resourceName: str
    attachmentDataRef: str
    downloadUri: str
    thumbnailUri:str


class GoogleChatSpaces(BaseModel):
    spaces: str
    displayName: Optional[str] = ""
    name: Optional[str] = ""
