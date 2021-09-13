# https://github.com/sarumont/py-trello/blob/master/trello/card.py
#https://www.datacamp.com/community/tutorials/property-getters-setters?utm_source=adwords_ppc&utm_campaignid=1455363063&utm_adgroupid=65083631748&utm_device=c&utm_keyword=&utm_matchtype=b&utm_network=g&utm_adpostion=&utm_creative=332602034358&utm_targetid=aud-299261629574:dsa-429603003980&utm_loc_interest_ms=&utm_loc_physical_ms=1001655&gclid=Cj0KCQjwyJn5BRDrARIsADZ9ykHt9y6oO85cOmEcov01k-EeUhvTPMP-AgHySfHWGUx_elgGCyUhniQaAjMWEALw_wcB
import time
from datetime import datetime, timedelta, date
import pprint
import sys
import requests
import json

headers = {"Accept": "application/json"}

TIMEOUT = 30

#from trello.label import Label


class TrelloBoard:
    """Trello_Board class atitude Interface
    Inicializa board com as listas existentes
    time.sleep(0.15) para respeitar o intervalo entre requisicoes do trello
    """

    def __init__(self, boardName, config):
        self.apikey = config['apikey']
        self.token = config['token']
        self.headers = {"Accept": "application/json"}
        self.querystring = {"key": self.apikey, "token": self.token}
        self.memberid = self.get_member_id()
        self.boardName = boardName
        time.sleep(0.15)
        self.boardid = self.get_boardid_by_name()
        time.sleep(0.15)
        self.listsDict = self.get_board_listsDict()
        time.sleep(0.15)
        self.cardsDict = []
        self.labelsDict = self.get_boards_labels()

    #@property
    def boardid(self):
        boardid = self.get_boardid_by_name()
        return boardid

    #@property
    def boardName(self):
        return self.boardName

    # MEMBER
    def get_member_id(self):
        url = "https://api.trello.com/1/tokens/" + self.token + "/member"
        response = requests.request(
            "GET", url, params=self.querystring, headers=self.headers)
        rjson = json.loads(response.text)
        if 'id' not in rjson:
            raise Exception("key 'id' is not in rjson")
        return rjson['id']

    def get_member_info(self):
        url = "https://api.trello.com/1/tokens/" + self.token + "/member"
        response = requests.request(
            "GET", url, params=self.querystring, headers=self.headers)
        # print(response.text)
        #print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
        return json.loads(response.text)

    def get_member_actions(self, memberid, actionsfilter=''):
        url = "https://api.trello.com/1/members/"+str(memberid)+"/actions"
        query = self.querystring
        if actionsfilter != '':
            query.update({'filter': actionsfilter})
        r = requests.request("GET", url, headers=self.headers, params=query)
        if r.status_code == 200:
            rjson = json.loads(r.text)
        else:
            rjson = r.text
        return r.status_code, rjson

    def add_member_to_card(self, cardid, memberid):
        url = "https://api.trello.com/1/cards/{}/idMembers".format(cardid)
        query = self.querystring
        query.update({'value': memberid})
        r = requests.request("GET", url, headers=self.headers, params=query)
        return r.status_code, r.text

    ### BOARD ###

    def get_boards(self):
        url = "https://api.trello.com/1/members/" + self.memberid + "/boards"
        r = requests.request(
            "GET", url, params=self.querystring, headers=self.headers)
        # print(json.dumps(json.loads(r.text), sort_keys=True, indent=4, separators=(",", ": ")))
        list_boards = []
        if r.status_code == 200:
            rjson = json.loads(r.text)
            for item in rjson:
                list_boards.append({item['name']: item['id']})
        return list_boards

    def get_board_members(self):
        url = "https://api.trello.com/1/boards/" + self.boardid + "/members"
        r = requests.request("GET", url, params=self.querystring)
        # pprint(response_json)
        board_members = []
        if r.status_code == 200:
            r_json = json.loads(r.text)
            for item in r_json:
                #print(item)
                board_members.append({'name': item['fullName'],
                                      'id': item['id'],
                                      'username': item['username']
                                      })
        return board_members

    def get_boardid_by_name(self):
        boards = self.get_boards()
        boardid = 'na'
        #print(boards)
        print(self.boardName)
        for board in boards:
            if board.get(self.boardName, 'na') != 'na':
                boardid = board.get(self.boardName, 'na')
                break
        return boardid

    ### LIST ###
    def get_board_listsDict(self):
        url = "https://api.trello.com/1/boards/" + self.boardid + "/lists"
        r = requests.request("GET", url, params=self.querystring)
        list_listsid = []
        #print(r.text)
        if r.status_code == 200:
            rjson = json.loads(r.text)
            for item in rjson:
                list_listsid.append({'name': item['name'],
                                     'id': item['id'],
                                     'closed': item['closed']})
        return list_listsid

    def get_listid_by_name(self, listName):
        listid = 'na'
        if len(self.listsDict) == 0:
            self.listsDict = self.get_board_listsDict()
        for eachlist in self.listsDict:
            #print(eachlist)
            if eachlist.get('name') == listName:
                listid = eachlist.get('id')
                break
        #print('---- LIST ID :' + str(listid))
        return listid

    def archive_all_cards_in_list(self, listid):
        print('--- archive all cards ---')
        url = "https://api.trello.com/1/lists/"+str(listid)+"/archiveAllCards"
        try:
            response = requests.request(
                "POST", url, params=self.querystring, timeout=TIMEOUT)
            response_text = response.text
        except requests.Timeout as err:
            #logger.error({"message": err.message})
            response_text = str(err)
        except Exception as e:
            response_text = str(e)
        return response_text

    def get_cards_in_list(self, listid):
        url = "https://api.trello.com/1/lists/" + listid + "/cards"
        r = requests.request(
            "GET", url, params=self.querystring, headers=self.headers)
        # print(response.text)
        if r.status_code == 200:
             rjson = json.loads(r.text)
        else:
            rjson = r.text
        return r.status_code, rjson

    def get_qty_cards_in_list(self, listid):
        url = "https://api.trello.com/1/lists/" + listid + "/cards"
        response = requests.request(
            "GET", url, params=self.querystring, headers=self.headers)
        # print(response.text)
        qty = 0
        if response.status_code == 200:
            response_json = json.loads(response.text)
            qty = len(response_json)
        return qty

    ### CARD ###
    def add_card_list_name(self, name, descr, listName, duedate='', pos='bottom', labels=''):
        #listdict = get_lists_dict_by_boardid(self.boardid)
        #for item in listdict:
        #    if listName == item['name']:
        #        listid = item['id']
        #        break
        try:
            listid = self.get_listid_by_name(listName)
            #print('list ID:' + listid)
            cardid, rstatuscode = self.add_card(
                name, descr, listid, duedate, pos, labels)
        except Exception as e:
            cardid = str(e)
            rstatuscode = '500'
        return cardid, rstatuscode

    def add_card(self, name, desc, listid, duedate='', pos='bottom', labels=''):
        # CREATE CARD
        url = "https://api.trello.com/1/cards"
        try:
            if pos == 'top':
                pos = get_card_position(listid)
        except Exception as e:
            print(e)
        try:
            duedateformat = dueData(duedate)
        except Exception as e:
            print('Except duedateformat ' + str(e))
            duedateformat = ''
        print(duedateformat)
        if labels == '':  # SEM LABEL
            querystring = {"name": name, "desc": desc, "idList": listid, "keepFromSource": "all",
                           "pos": pos, "key": self.apikey, "token": self.token, 'due': duedateformat}
        else:  # COM LABEL
            labelsIds = self.deParaNomeIdLabels(labels)
            querystring = {"name": name, "desc": desc, "idLabels": labelsIds, "idList": listid, "keepFromSource": "all",
                           "pos": pos, "key": self.apikey, "token": self.token, 'due': duedateformat}
        r = requests.request("POST", url, params=querystring)
        cardid = 'na'
        # CHECA CRIACAO
        print(r.status_code)
        try:
            if r.status_code == 200:
                # print(r.text)
                rjson = json.loads(r.text)
                # print(rjson)
                cardid = rjson.get('id', 'na')
            else:
                print(r.text)
                time.sleep(1)
                cardid = r.text
        except Exception as e:
            print('EXCEPT reading r.status_code create card: ' + str(e))
            cardid = str(e)
        return cardid, r.status_code

    def update_card(self, cardid, updateField, updateValue):
        url = "https://api.trello.com/1/cards/{}".format(cardid)
        querystring = self.querystring
        querystring.update({updateField: updateValue})
        r = requests.request("PUT", url, params=querystring)
        return r.status_code, r.text

    def add_comment(self, cardid, comment):
        url = "https://api.trello.com/1/cards/" + cardid + "/actions/comments"
        querystring = self.querystring
        querystring.update({'text': comment})
        r = requests.request("POST", url, params=querystring)
        return r.status_code

    def get_cardid_open_card_by_name(self, cardName):
        search = cardName + " is:open"
        listcardsids = self.search_board_cards(search)
        cardid = listcardsids[0].get('id')

        return cardid

    def get_card_by_id(self, cardid):
        url = "https://api.trello.com/1/cards/{}".format(cardid)
        # print(url)
        querystring = self.querystring
        querystring.update({"attachments": "false"})
        r = requests.request(
            "GET", url, headers=self.headers, params=querystring)
        if r.status_code == 200:
            rjson = json.loads(r.text)
            # print(rjson)
            return rjson
        else:
            return {'id': 'na', 'name': 'not found', 'desc': str(r.status_code)}

    def get_card_actions(self, cardid, action):
        """:returns
            Args:
                cardid: id do cartao
                action: nome ou nomes separados por virgulas das acoes ex: "updateCard,createCard,addAttachmentToCard"
        """
        time.sleep(0.011)
        #print(cardid)
        url = "https://api.trello.com/1/cards/" + cardid + "/actions"
        querystring = {"limit": 500, "filter": action,
                       "key": self.apikey, "token": self.token}
        response = requests.request("GET", url, params=querystring)
        if response.status_code == 200:
            response_json = json.loads(response.text)
        else:
            response_json = {'data': {'type': 'noAction',
                                      'card': {'name': response.text, 'id': 'na'}}}
        return response.status_code, response_json

    def get_card_actions_moves_creation(self, cardid):
        time.sleep(0.011)
        #print(cardid)
        url = "https://api.trello.com/1/cards/" + cardid + "/actions"
        querystring = {"limit": 500, "filter": "updateCard,createCard",
                       "key": self.apikey, "token": self.token}
        response = requests.request("GET", url, params=querystring)
        if response.status_code == 200:
            response_json = json.loads(response.text)
            # pprint(response_json)
        else:
            response_json = {
                'data': {'card': {'name': response.text, 'id': 'na'}}}
        return response.status_code, response_json

    def get_card_actions_moves(self, cardid, filter):
        '''
        Arg: cardid
        filter: "updateCard,createCard"
        :returns
            json com a resposta
        '''
        time.sleep(0.011)
        #print(cardid)
        url = "https://api.trello.com/1/cards/" + cardid + "/actions"
        querystring = {"limit": 500, "filter": filter,
                       "key": self.apikey, "token": self.token}
        response = requests.request("GET", url, params=querystring)
        if response.status_code == 200:
            response_json = json.loads(response.text)
            # pprint(response_json)
        else:
            response_json = {
                'data': {'card': {'name': response.text, 'id': 'na'}}}
        return response.status_code, response_json

    def get_card_checklists(self, cardid):
        url = "https://api.trello.com/1/cards/{}/checklists".format(cardid)
        querystring = {"key": self.apikey, "token": self.token}
        response = requests.request("GET", url, params=querystring)
        if response.status_code == 200:
            response_json = json.loads(response.text)
            # pprint(response_json)
        else:
            # {'data': {'card': {'name': response.text, 'id': 'na'}}}
            response_json = {'id': 'na'}
        return response.status_code, response_json

    def extract_card_listMoves_from_actions_json(self, response_json):
        '''
        get acoes no trello para o cardid
        :param response_json: json com a resposta das actions extraidas do trello
        :return:lista com acoes e lista com colunas (para fazer um dataframe
        '''
        listActions = []
        for action in response_json:
            nomeCard = action['data']['card'].get('name')
            cardid = action['data']['card'].get('id')
            idListCard = action['data']['card'].get('idList')
            shortLink = "https://trello.com/c/" + \
                str(action['data']['card'].get('shortLink'))
            try:
                listAfter = action['data']['listAfter']['name']
                listBefore = action['data']['listBefore']['name']
            except:
                listAfter = "no list"
                listBefore = "no list"
            dataAction = action['date']
            criador = action['memberCreator']['fullName']
            idCriador = action['memberCreator']['id']
            dia = action['date'][:10]
            hora = action['date'][11:19]
            acao = action['type']
            actionid = action['id']
            if acao == 'createCard':
              listAfter = 'Emails'
              listBefore = 'Criacao'
            row = [actionid, cardid, nomeCard, idListCard, shortLink, listBefore, listAfter, dataAction, criador,
                   idCriador, dia, hora, acao]
            if listAfter == "no list":
                pass
                #print("nao salvar", end="\r")
            else:
                listActions.append(row)
        columns = ['actionid', 'cardid', 'nomeCard', 'idListCard', 'shortLink', 'listBefore', 'listAfter', 'dataAction', 'criador', 'idCriador',
                   'dia', 'hora', 'acao']
        return listActions, columns

    def archive_card(self, cardid):
        url = "https://api.trello.com/1/cards/"+str(cardid)
        querystring = self.querystring
        querystring.update({'closed': 'true'})
        response = requests.request(
            "PUT", url, headers=self.headers, params=querystring)
        print(json.dumps(json.loads(response.text),
                         sort_keys=True, indent=4, separators=(",", ": ")))
        return response.status_code, response.text

    def move_card_bottom(self, cardid):
        try:
            url = "https://api.trello.com/1/cards/"+str(cardid)
            querystring = self.querystring
            querystring.update({'pos': 'bottom'})
            response = requests.request(
                "PUT", url, headers=self.headers, params=querystring)
            #print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
            return response.status_code, response.text
        except Exception as e:
            return 555, str(e)

    # WEBHOOK
    def add_webhook(self, callbackurl, idModel):
        url = "https://api.trello.com/1/webhooks/"
        querystring = self.querystring
        querystring.update({'callbackURL': callbackurl,
                            'idModel': idModel})
        response = requests.request(
            "POST", url, headers=self.headers, params=querystring)
        #print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
        return response.text

    ### LABELS ###
    def add_label(self, cardid, labelName):
        try:
            url = "https://api.trello.com/1/cards/"+str(cardid)+"/idLabels"
            querystring = self.querystring
            labelid = self.get_label_id_by_name(labelName)
            querystring.update({'value': labelid})
            r = requests.request("POST", url, params=querystring)
            return r.status_code, r.text
        except Exception as e:
            return 500, str(e)

    def remove_label(self, cardid, labelName):
        try:
            idLabel = self.get_label_id_by_name(labelName)
            url = "https://api.trello.com/1/cards/" + \
                str(cardid)+"/idLabels/"+str(idLabel)
            querystring = self.querystring
            r = requests.request("DELETE", url, params=querystring)
            return r.status_code, r.text
        except Exception as e:
            return 500, str(e)

    def deParaNomeIdLabels(self, labels):
        if "," in labels:  # mais de um label separado por virgula
            labels = labels.split(",")
            labelid = ''
            for l in labels:
                if labelid == '':
                    labelid = self.get_label_id_by_name(l)
                else:
                    labelid = labelid + "," + self.get_label_id_by_name(l)
        else:  # so tem um label
            labelid = self.get_label_id_by_name(labels)
        return labelid

    def get_boards_labels(self):
        data_list = []
        url = "https://api.trello.com/1/boards/" + self.boardid + "/labels"
        querystring = {"fields": "all", "limit": "100",
                       "key": self.apikey, "token": self.token}
        response = requests.request("GET", url, params=querystring)
        response_json = json.loads(response.text)
        # pprint(response_json)
        for item in response_json:
            itemid = item['id']
            nome = item['name']
            row = [itemid, nome]
            data_list.append(row)
        return data_list

    def get_label_id_by_name(self, labelname):
        if len(self.labelsDict) == 0:
            self.labelsDict = self.get_boards_labels()
        label_id = ''
        for item in self.labelsDict:
            if labelname == item[1]:
                label_id = item[0]
        return label_id

    ### SEARCHS ###
    def search_cards_by_label_name(self, label):
        ''':arg
        :returns r.status_code,cardid
        '''
        url = "https://api.trello.com/1/search"
        search = 'label:' + label
        querystring = {
            "idBoards": self.boardid,
            "query": search,
            "key": self.apikey, "token": self.token,
            "modelTypes": "cards",
            "card_fields": "id,name,idList,shortUrl",
            "cards_limit": "500",
            "partial": "true",
        }
        r = requests.request("GET", url, params=querystring)
        listcardsids = []
        if r.status_code == 200:
            cards = json.loads(r.text).get('cards')
            for card in cards:
                cardid = card.get('id')
                listcardsids.append(cardid)
        return r.status_code, listcardsids

    def search_board_cards(self, search):
        """
        :search texto que sera procurado
        :boardName nome do quadro
        retorna json com cartoes encontrados
        """
        # 'is:visible and -list:"Finalizados" ' +
        try:
            boardid = self.boardid  # get_boardid_by_name(boardName)
            if boardid == 'na':
                boardid = "mine"
            url = "https://api.trello.com/1/search"
            querystring = {
                "idBoards": boardid,
                "query": search,
                "key": self.apikey, "token": self.token,
                "modelTypes": "cards",
                "card_fields": "name,desc,idList,dateLastActivity",
                "cards_limit": "500",
                "partial": "true"
            }
            r = requests.request(
                "GET", url, headers=self.headers, params=querystring)
            # print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
            if r.status_code == 200:
                rjson = json.loads(r.text)
                rjsoncards = rjson['cards']
                listaCartoes = []
                for card in rjsoncards:
                    listaCartoes.append(
                        {'id': card['id'], 'name': card['name'], 'desc': card['desc']})
                    #'filter:createCard since:"2021-06-01T10:00" before:"2021-06-02T10:00"'
                    #listaCartoes.append(card)
                return listaCartoes
            else:
                return [{'id': 'na', 'name': 'not found', 'desc': str(r.status_code), 'detail': r.text}]
        except Exception as e:
            print(e)
            return [{'id': 'na', 'name': 'erro', 'desc': str(e)}]

    def search_board_actions(self, action, since, before):
        """
        :action ação
        :since data inicio
        :before data fim
        retorna json com objetos encontrados
        """
        # 'is:visible and -list:"Finalizados" ' +
        try:
            boardid = self.boardid  # get_boardid_by_name(boardName)
            if boardid == 'na':
                boardid = "mine"
            url = "https://api.trello.com/1/boards/{}/actions?since={}&before={}&filter={}&actions_limit=1000".format(
                boardid, since, before, action)
            querystring = self.querystring
            r = requests.request(
                "GET", url, headers=self.headers, params=querystring)
            # print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
            if r.status_code == 200:
                rjson = json.loads(r.text)
                lista = []
                for item in rjson:
                    lista.append(item)
                return lista
            else:
                return [{'id': 'na', 'name': 'not found', 'desc': str(r.status_code), 'detail': r.text}]
        except Exception as e:
            print(e)
            return [{'id': 'na', 'name': 'erro', 'desc': str(e)}]

    ### CHECKLISTS ###
    def add_checklist_by_id(self, cardid, checklistid):
        # ADD CHECKLIST
        url = "https://api.trello.com/1/cards/" + cardid + "/checklists"
        querystring = {'idChecklistSource': checklistid,
                       "key": self.apikey, "token": self.token, }
        r = requests.request("POST", url, params=querystring)
        if r.status_code == 200:
            rjson = json.loads(r.text)
            return rjson
        else:
            return[{'id': 'na'}]

    def add_item_to_checklist(self, checklistid, itemname):
        url = "https://api.trello.com/1/checklists/{}/checkItems".format(
            checklistid)
        querystring = {'name': itemname,
                       "key": self.apikey, "token": self.token, }
        response = requests.request("POST", url, params=querystring)
        return response.text

    def get_checklists(self):
        # GET CHECKLISTS FROM BOARD
        url = "https://api.trello.com/1/boards/" + self.boardid + "/checklists"
        querystring = {"key": self.apikey, "token": self.token, }
        response = requests.request("GET", url, params=querystring)
        return response.text

    def delete_checklist_from_card(self, checklistid, cardid):
        url = "https://api.trello.com/1/cards/{}/checklists/{}".format(
            cardid, checklistid)
        r = requests.request(
            "DELETE", url, headers=self.headers, params=self.querystring)
        return r.status_code, r.text

    # next steps
    #@boardid.setter
    #def boardid(self, value):
    #    self._boardid = value


ApiKey = ''
Token = ''
BOARDID = ''


def get_card_position(listid):
    url = "https://api.trello.com/1/lists/" + listid + "/cards"
    querystring = {"key": ApiKey, "token": Token}
    response = requests.request("GET", url, params=querystring)
    # print(response.text)
    if response.status_code == 200:
        response_json = json.loads(response.text)
        lastpos = 0
        cardsTotal = 0
        priorityCardsTotal = 0
        for card in response_json:
            #print(card['pos'])
            #print(card['desc'])
            #print(card["labels"])
            # pprint(card)
            labels = card["labels"]
            for label in labels:
                if label['name'] == 'Prioridade':
                    lastpos = card['pos']
                    priorityCardsTotal += 1
            cardsTotal += 1
        #print(priorityCardsTotal)
        #print(cardsTotal)
        pos = float(lastpos) + 1
        #print(pos)
        return pos


def get_lists_dict_by_boardid(boardid):
    url = "https://api.trello.com/1/boards/" + boardid + "/lists"
    querystring = {"key": ApiKey, "token": Token}
    r = requests.request("GET", url, params=querystring)
    list_listsid = []
    if r.status_code == 200:
        #print(r.text)
        rjson = json.loads(r.text)
        for item in rjson:
            list_listsid.append({'name': item['name'],
                                 'id': item['id']})
    return list_listsid


def get_card_idnamedesc_by_name(cardName, boardName):
    r = get_cards_id_name_desc(boardName)
    for item in r:
        if item.get('id') == 'na':
            return item
        else:
            if item.get('name') == cardName:
                return item
    return {'id': 'na', 'name': 'erro', 'desc': 'not found'}


def get_cards_id_name_desc(boardName):
    """:arg
    boardName: nome do quadro
    return: array of dict with cardid, name, desc
    """
    try:
        url = "https://api.trello.com/1/search"
        search = 'is:visible and -list:"Finalizados" and board:' + boardName
        querystring = {"query": search, "idBoards": "mine", "modelTypes": "all", "board_fields": "name,idOrganization",
                       "boards_limit": "100", "card_fields": "all", "cards_limit": "1000", "cards_page": "0",
                       "card_board": "false", "card_list": "true", "card_members": "false", "card_stickers": "false",
                       "card_attachments": "false", "organization_fields": "name,displayName",
                       "organizations_limit": "10", "member_fields": "fullName,initials,username,confirmed",
                       "members_limit": "10", "partial": "false", "key": ApiKey, "token": Token}

        print(querystring)
        r = requests.request("GET", url, params=querystring)
        rjson = json.loads(r.text)
        listaCartoes = []
        print(r.text)
        print(r.status_code)
        for cartao in rjson['cards']:
            listaCartoes.append({'id': cartao['id'],
                                 'name': cartao['name'],
                                 'desc': cartao['desc']})
        return listaCartoes
    except Exception as e:
        print(e)
        return [{'id': 'na', 'name': 'erro', 'desc': str(e)}]


##########################################################
def dueData(prazoHoras):
    try:
        if sys.platform == 'linux':
            #xlsx = pd.ExcelFile("dueDate.xlsx")
            fuso = 4
        else:
            #xlsx = pd.ExcelFile("O:/Operação/Att/dueDate.xlsx")
            fuso = 2
        #df = pd.read_excel(xlsx, 'df', dtype={'tempo_entrega_gmail': int})

        ENTREGA = int(prazoHoras)*60  # df['tempo_entrega_gmail'][0]
        ENTREGA = int(ENTREGA)
        print("Tempo de entrega é de: " + str(ENTREGA) + " minutos")
    except Exception as e:
        print(e)
        print("NÃO LEU O TEMPO DE ENTREGA")
        ENTREGA = 2 * 60
        fuso = 2
    hoje = date.today()
    hoje = str(hoje).split("-")
    hoje = str(hoje[2] + "/" + hoje[1] + "/" + hoje[0])
    limite = "20:00:00"
    limite23 = "23:59:59"
    dayAfter = timedelta(days=1)
    limite08 = "08:59:59"
    diahora = hoje + " " + limite
    diahora23 = hoje + " " + limite23
    diahora08 = hoje + " " + limite08
    diahoraLimite = datetime.strptime(diahora, "%d/%m/%Y %H:%M:%S")
    diahoraLimite23 = datetime.strptime(diahora23, "%d/%m/%Y %H:%M:%S")
    diahoraLimite08 = datetime.strptime(diahora08, "%d/%m/%Y %H:%M:%S")
    ENTREGA = int(ENTREGA)
    entrega = timedelta(minutes=ENTREGA)
    inicio = datetime.now()
    corrige1 = timedelta(hours=fuso)
    #corrige2 = timedelta(minutes=5)
    #corrige1 = corrige1 + corrige2
    horaAtualTrello = inicio - corrige1
    dueFinal = horaAtualTrello + entrega
    if inicio >= diahoraLimite and inicio <= diahoraLimite23:
        entrega = hoje + " " + "11:00:00"
        entrega = datetime.strptime(entrega, "%d/%m/%Y %H:%M:%S")
        entrega = entrega + dayAfter
        dueFinal = entrega - corrige1
    elif inicio <= diahoraLimite08:
        entrega = hoje + " " + "11:00:00"
        entrega = datetime.strptime(entrega, "%d/%m/%Y %H:%M:%S")
        dueFinal = entrega - corrige1
    return dueFinal


def get_actions_change_card_name(qo, cardid):
    rstatus, actions = qo.get_card_actions(cardid, 'updateCard')
    print(cardid)
    listactions = []
    listactions.append(['cardid', 'newname', 'oldname',
                        'actioncreator', 'date', 'shortLink'])
    for action in actions:
        # print(action)
        actionold = action['data']['old']
        print(actionold)
        if 'name' in actionold.keys():
            oldname = actionold['name']
            newname = action['data']['card']['name']
            actioncreator = action['memberCreator']['fullName']
            date = action['date']
            shortLink = 'https://trello.com/c/' + \
                str(action['data']['card']['shortLink'])
            print(oldname)
            listactions.append(
                [cardid, newname, oldname, actioncreator, date, shortLink])
    return listactions
