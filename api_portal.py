# coding: utf-8
import requests
from bs4 import BeautifulSoup
# import dados
import time
from datetime import datetime, timedelta
import json
from pprint import pprint

INCLUSAO = "payload_inclusao.json"
HISTORICO = "payload_portal.json"

class PortalService:
	"""Portal atitude Interface"""

	def __init__(self, config):
		self.login = config['login']
		self.password = config['password']
		self.session = requests.Session()
		self.payload = {} #self.load_payload(config['payload_file_name'])
		self.url_detalhe_contrato = "https://atitudesf.portalderepasse.com.br/v3/contrato_detalhe.asp?contrato={}"
		self.url_incluir = "https://atitudesf.portalderepasse.com.br/v3/contrato_incluir.asp"

	
	def load_payload(self, file_name):
		# Opening JSON file
		f = open(file_name,'r')
  
		# returns JSON object as a dictionary
		f_dict =  json.load(f)

		# Closing file
		f.close()

		self.payload = f_dict

		return 'ok load'

 
	def login_portal(self):
		payload = {"flg": "1", "acao": '',"txtUsuario": self.login, "txtSenha": self.password}
		url = "https://atitudesf.portalderepasse.com.br/v3/login.asp"
		url2 = "https://atitudesf.portalderepasse.com.br/v3/inicial.asp"
		with self.session as session:  # requests.Session() as session:
			r = session.get(url, data=payload)
			r = session.get(url2)
			body = r.text
			# print(body)
			resp = body.find("AGENDA")
			if resp > -1:
				print("LOGOU")
				status = 'LOGOU'
			else:
				print("NAO LOGOU")
				status = 'NAO LOGOU'
				print(r.text[:50])
		return status

	def verifica_login(self):
		url = "https://atitudesf.portalderepasse.com.br/v3/inicial.asp"
		with self.session as session:
			r = session.get(url)
			body = r.text
			resp = body.find("AGENDA")
			if resp > -1:
				status = 'LOGADO'
			else:
				status = 'NAO LOGADO'
		return status

	def verifica_e_loga(self):
		status = self.verifica_login()
		if status == 'NAO LOGADO':
			r = self.login_portal()
			if r == 'NAO LOGOU':
				resp = 'FALHA NO LOGIN'
			else:
				resp = 'LOGADO'
		else:
			resp = 'LOGADO'
		return resp

	def get_info_cpf(self, cpf):
		""":arg
		retorna 3 resultados: numero de contratos para o cpf, o numero do primeiro contrato e etapa do primeiro contrato
		"""
		# chave = "FFA1BB73-E32E-4E48-9F50-BB65199D4AD5"
		numContratos, primeiroContrato, etapa = '0', 'na', 'na'
		url = "https://atitudesf.portalderepasse.com.br/v3/contrato_result.asp"
		payload = {"pagina": "", "cpf": cpf,
		           "cod_pasta": "1122,1123,1124,1125,1126,1127,1265,1223,1364,1232,1365,1240,1366,1360",
		           "sit_cliente": "1130,1132,1133,1134,1135,1137,1140,1141,1142,1143,1145,1188,1190,1195,1200,1208,1329,1354,1330,1267,1296,1275,1230,1147,1259,1148,1149,1150,1189,1347,1191,1151,1155,1152,1153,1154,1328,1337,1248,1239,1156,1157,1158,1349,1350,1245,1244,1247,1159,1161,1160,1207,1194,1294,1162,1164,1163,1165,1299,1166,1323,1325,1324,1326,1327,1261,1168,1169,1171,1172,1173,1174,1175,1176,1177,1210,1178,1179,1180,1181,1206,1209,1300,1361,1331,1291,1292,1298,1332,1293,1339,1348,1224,1363,1225,1226,1227,1228,1258,1229,1231,1386,1362,1390,1367,1368,1369,1370,1371,1236,1237,1238,1235,1338,1372,1373,1374,1375,1376,1377,1378,1380,1379,1243,1241,1382,1381,1383,1384,1385,1387,1388,1389",
		           "chkCodPastaEstoque": "1", "chave_browser": "{1B43E604-C42B-4567-91A2-5E91EB699B68}"}
		with self.session as session:
			r = session.get(url, data=payload)
			body = r.text
			nenhumContratoEncontrado = body.find('Nenhum resultado foi encontrado')
			if 'Nenhum resultado foi encontrado' in body:
				return numContratos, 'nenhum contrato encontrado', etapa
			elif 'foram localizados contratos utilizando os filtros de' in body:
				return numContratos, 'contrato finalizado encontrado', 'finalizado'
			# else, prossegue:
			soup = BeautifulSoup(body, "html.parser")
			# resp1 = soup.find("Nenhum resultado foi encontrado")
			elnumcontratos = soup.find('div', attrs={"id": "contratos_selecionados"})
			numContratos = elnumcontratos.contents[0]
			elementPrimeiroContrato = soup.find('input', attrs={"id": "contrato_sel"})
			try:
				primeiroContrato = elementPrimeiroContrato['value']
			# exemplo: input_tag = soup.find_all(attrs={"name": "stainfo"}) ; output = input_tag[0]['value']
			except Exception as e:
				primeiroContrato = 'na'
			try:
				# pega o pai dos tds
				eltdNowRapParent = soup.find('div', attrs={'id': 'progresso1'}).parent
				elCidade = eltdNowRapParent.find_next('td')
				# cidade = elCidade.contents[0]
				elEmpreendimento = elCidade.find_next('td')
				elBlUnid = elEmpreendimento.find_next('td')
				elcpfNome = elBlUnid.find_next('td')
				elEtapa = elcpfNome.find_next('td')
				cpfNome = elcpfNome.contents[0]
				# print(cpfNome)
				etapa = elEtapa.contents[0]
			# print(etapa)
			except Exception as e:
				# empreendimento = 'na'
				# cpfNome = 'na'
				etapa = 'except'

		return numContratos, primeiroContrato, etapa

	def get_info_detalhe_contrato(self, contrato):
		"""
		Retorna o html para extrair a informação desejada
		Args:
			contrato (str): Contrato interno do Portal
		Return:
			soup: html do detalhe do contrato
		"""
		r = self.verificaELoga()
		if r != 'LOGADO':
			return 'erro'

		url = 'https://atitudesf.portalderepasse.com.br/v3/contrato_detalhe.asp?contrato={}'.format(
			contrato)
		# print(url)
		with self.session as session:
			r = session.get(url)
			body = r.text
			soup = BeautifulSoup(body, "html.parser")

			return soup

	def get_convenio_debito_fgts(self, contrato):
		soup = self.get_info_detalhe_contrato(contrato)
		# get details
		# a = soup.find('nmr_pis')
		# a = soup.find_all('select')

		el_convenio_fgts = soup.find('select', attrs={"id": "convenio_debito_fgts"})
		el_convenio_fgts_option = el_convenio_fgts.find_all('option', selected=True)

		convenio_debito_fgts = ''
		if el_convenio_fgts_option is not None:
			# print(str(el_convenio_fgts_option))
			try:
				convenio_fgts_option = el_convenio_fgts_option[0]
				convenio_debito_fgts = convenio_fgts_option.get_text()
			except:
				# campo esta em branco
				convenio_debito_fgts = ''

		return convenio_debito_fgts


	def inclui_historico(self, data):
		print('inclui historico')
				
		# carrega payload padrao
		self.load_payload(HISTORICO)
		
		# passa dados para o payload
		self.preenche_payload(data, 'historico')
		
		#urlcontrato = self.url_detalhe_contrato + self.payload['contrato']
		# respContrato = session.get(urlcontrato)
		# respContrato = respContrato.text

		print('apos preenche payload historico')
		# pprint(payloadFinal)
		r_dict = {}
		try:
			print("contrato: {}".format(data['contrato']))
			print(self.url_detalhe_contrato.format(data['contrato']))
			r = self.session.post(self.url_detalhe_contrato.format(data['contrato']), data=self.payload)
			print('inclui historico: {}'.format(r.status_code))
			r_dict.update({'incluihistorico': 'ok'})
			r_dict.update({'rincluihistorico': str(r.status_code)})
		except Exception as e:
			print('Exception post incluihistorico: ' + str(e))
			r_dict.update({'incluihistorico': 'erro'})
			r_dict.update({'Except_incluihistorico': str(e)})
			r_dict.update({'rhistorico': 'erro'})
		print('apos session.post inclui historico')
		# print(r.text)
		# print(r.status_code)
		return r_dict


	def cadastro_cliente(self, data):
		'''
		campo acao do payload: atendimento (criar contrato) , recado (so historico)
		'''

		self.verifica_e_loga()

		urlverificacontrato = 'https://atitudesf.portalderepasse.com.br/v3/combo_verificar_cpf.asp?ID={}&contrato='.format(data.get("cpf1"))
		#answer:  <input type="hidden" name="contrato_cpf" id="contrato_cpf" value="AT023904"/>
		print("cadastro cliente")
		
		r = self.session.get(self.url_incluir)
		body = r.text
		soup = BeautifulSoup(body, "html.parser")
		nroContrato = soup.find("form", attrs={"name": "f2"})
		#print(nroContrato)
		try:
		    nroContrato = nroContrato.get_text()
		except:
			print(body)
			print("erro get_text nro contrato")
			return "erro get_text", "erro"  
		i = nroContrato.find(":") + 2
		f = i + 8
		nro_contrato = nroContrato[i:f]
		print(nro_contrato)
		#time.sleep(5)

		# preencha peayload
		self.load_payload(INCLUSAO)
		self.preenche_payload(data,"cadastro")
		self.payload.update({"contrato_nro": nro_contrato.encode('latin-1')})
		
		if data['tipoPesquisa'] == "teste":
		    self.payload.update({"cod_pasta": "1361"})
		    self.payload.update({"cod_pasta3": "391"})
		elif data['tipoPesquisa'] == "criarPasta":
		    self.payload.update({"cod_pasta": "1130"})
		else:
			self.payload.update({"cod_pasta": "1130"})
		
		#print(self.payload)
		# POST para incluir somente contrato
		r = self.session.post(self.url_incluir, data={"contrato_nro": nro_contrato,"contrato":''})
		#pprint(r.text)
		# POST para incluir restante dos dados
		r = self.session.post(self.url_incluir, data=self.payload)
		#pprint(self.payload)
		
		body = r.text
		soup = BeautifulSoup(body, "html.parser")
		# <input type="hidden" name="contrato" value="283629" />
		contrato = soup.find("input", attrs={"name": "contrato"})

		try:
			contrato = contrato.attrs.get("value")
		except:
			print(body)
			contrato = 'na attrs.get'
			nro_contrato, contrato = "erro attrs.get", "erro na attrs.get"

		print("=======================================================")
		print("fim cadastro cliente, contrato: {}".format(contrato))
		print("=======================================================")

		data['contrato'] = contrato
		self.inclui_historico(data)

		return nro_contrato, contrato


	def consulta_contrato(self, contrato):
		return 'consulta cpf em construção'

	def preenche_payload(self, data, operacao):
		'''
		PAYLOAD DE CADASTRO E DIFERENTE DO PAYLOAD HISTORICO
		data: dict com informacoes
		operacao: cadastro ou historico
		'''
		print("preenche payload")
		print(data)
		payload = self.payload
		if data['codempreendimento'] in ['', 'None', None]:
			data['codempreendimento'] = '2473'
		payload.update({"empreend": str(data['codempreendimento'])}) # .encode('latin-1')})
		payload.update({"construtora": str(data.get('construtora', '80'))}) #.encode('latin-1')})

		if operacao == 'cadastro':
			payload.update({'acao':'gravar'})	
			if data['nome1'] == '':
				data['nome1'] = 'NOME NAO PREENCHIDO'
			payload.update({"nome": data['nome1'].encode('latin-1')})
			# aqui o cpf_cnpj nao possui 1
			payload.update({"cpf_cnpj": data['cpf1']})


		elif operacao == 'historico':
			payload.update({'acao':'atendimento'})

			payload.update({'contrato': data['contrato']})
			### Caminho google drive na observacao
			caminhoPadrao = data['url_folder']
			observacao = caminhoPadrao  # data.get('caminho', caminhoPadrao)

			### VERIFICA NA FUNC CXAQUI ###
			payload.update({'restr_cad': data.get('restr_cad', '')})
			dt_prazo_etapa = datetime.now() + timedelta(days=1)
			dt_prazo_etapa = dt_prazo_etapa.strftime("%d/%m/%Y")
			payload.update({'dt_prazo_etapa': dt_prazo_etapa})
			payload.update({'observacao': observacao.encode('latin-1')})
			payload.update({'imobiliaria': data.get('codimob', '')})
			payload.update({'diretor': data.get('codgerente', '')})
			payload.update({'telefone': data.get('telefone', '')})
			payload.update({'email_prop1': data.get('email_prop', '')})
			
			# payload.update({'declara_irpf': data.get('declara_irpf', '').encode('latin-1')})
			payload.update({'fgts': data.get('fgts', '').encode('latin-1')})
			payload.update({'pendencia': data.get('obs', '')})
			
			### USUARIO 1 ###
			payload.update({"cpf_cnpj1": data['cpf1']})
			payload.update({"sexo1": data.get('sexo1', '')})
			payload.update({"dt_nasc1": data.get('nasc1', '')})
			payload.update({"nome1": data.get('nome1', '').encode('latin-1')})

			estadocivil1 = data.get('estadocivil1', '')
			if estadocivil1 == '':
				pass
			elif 'solteir' in estadocivil1.lower():
				payload.update({"estado_civil1": 'Solteiro(a)'})
			elif 'casado' in estadocivil1.lower():
				payload.update({"estado_civil1": 'Casado(a)'})
			elif 'separad' in estadocivil1.lower():
				payload.update({"estado_civil1": 'Separado(a)'})
			elif 'Divorciado(a)' == estadocivil1:
				payload.update({"estado_civil1": 'Divorciado(a)'})
			elif 'viúv' in estadocivil1.lower():
				payload.update({"estado_civil1": 'Viúvo(a)'})

			### Usuarios 2 e 3 podem ser preenchidos somente no hiostorico 
			if len(data.get('cpf2', '')) > 3:
				### USUARIO 2 ###
				payload.update({"sexo2": data.get('sexo2', '')})
				payload.update({"cpf_cnpj2": data.get('cpf2', '')})
				payload.update({"nome2": data.get('nome2', '').encode('latin-1')})
				payload.update({"dt_nasc2": data.get('nasc2', '')})

			if len(data.get('cpf3', '')) > 3:
				### USUARIO 3 ###
				payload.update({"sexo3": data.get('sexo3', '')})
				payload.update({"cpf_cnpj3": data.get('cpf3', '')})
				payload.update({"nome3": data.get('nome3', '').encode('latin-1')})
				payload.update({"dt_nasc3": data.get('nasc3', '')})

		else:  # if operacao == 'cadastro' ou historico
			payload = {}
		print('fim preenche payload')
		
		# define payload do objeto como payload preenchido acima
		self.payload = payload
		return 'self.payload atualizado'
	

	def extrair_dados_contrato(self, html):
    	### Esta função faz a extração de todos os dados do portal e retorna eles em uma dict ###
    	### O atributo 'name' de cada uma das informações do portal é o mesmo nome que estará na dict ###
    	### Importante salientar que todos os valores precisam ser codificados em 'latin-1' para que o servidor do portal ###
    	### entenda caracteres como: acentos, barras etc. ###
		soup = BeautifulSoup(html, "html.parser")
		inputs = soup.find_all("input")
		for i in inputs:
		    nomedict = i.attrs.get("name")
		    ## Como o html da página não me retorna o gerente da venda da mesma forma que as outras informações ##
		    ## preciso precura-lo dentro de um atributo que está chamando uma função em javascript para depois coloca-lo dentro da dict ##
		    if nomedict == "contrato":
		        try:
		            i = i.find_previous("body")
		            diretor = i.attrs.get("onload")
		            inicio = diretor.find("diretor") + 8
		            fim = diretor.find(",") - 1
		            diretor = diretor[inicio:fim]
		            plus = {"diretor": diretor}
		            self.update(plus)
		        except Exception as e:
		            print("NÃO PEGOU O GERENTE")
		            print(e)
		    valuedict = i.attrs.get("value")
		    if nomedict != None:
		        valuedict = i.attrs.get("value")
		        if valuedict != None:
		            plusstring = {nomedict: valuedict}
		            valuedict = valuedict.encode('latin-1')
		            plus = {nomedict: valuedict}
		            self.update(plus)
		            #PAYLOADSTRING.update(plusstring)
		### O html da página tambem me retorna as observações e pendências de uma forma diferente ###
		### preciso procurar o texto contido dentro da tag 'textarea' ###
		pendencia = soup.find("textarea", attrs={"name": "pendencia"})
		pendencia = pendencia.getText()
		plusstring = {"pendencia": pendencia}
		plus = {"pendencia": pendencia.encode('latin-1')}
		self.payload.update(plus)
		#PAYLOADSTRING.update(plusstring)
		### Os seguintes itens serão adquiridos de uma forma diferente pois eles não estão dentro de tags 'input', mas sim dentro de tags select ###
		self.pegaOption(soup, "banco")
		self.pegaOption(soup, "tipo_dependente")
		self.pegaOption(soup, "tipo_renda")
		self.pegaOption(soup, "imobiliaria")
		self.pegaOption(soup, "ag_vinculacao")
		self.pegaOption(soup, "tipo_tabela")
		self.pegaOption(soup, "modalidade")
		self.pegaOption(soup, "sexo1")
		self.pegaOption(soup, "sexo2")
		self.pegaOption(soup, "sexo3")
		self.pegaOption(soup, "estado_civil1")
		self.pegaOption(soup, "estado_civil2")
		self.pegaOption(soup, "estado_civil3")
		self.pegaOption(soup, "regime_matrimonio1")
		self.pegaOption(soup, "regime_matrimonio2")
		self.pegaOption(soup, "regime_matrimonio3")
		self.pegaOption(soup, "resp_assinatura")
		self.pegaOption(soup, "usuario_pasta")
		self.pegaOption(soup, "resp_aprovacao")
		self.pegaOption(soup, "primeira_aquisicao")

		return self.payload


	def pegaOption(self, soup, name):
	    try:
	        itemq = soup.find("select", attrs={"name": name})
	        itemq = itemq.find_all("option")
	        for i in itemq:
	            if str(i).find("selected") > -1:
	                item = i.attrs.get("value")
	                break
	            else:
	                item = ""
	        plusstring = {name: item}
	        plus = {name: item.encode('latin-1')}
	        self.payload.update(plus)
	        #PAYLOADSTRING.update(plusstring)
	    except:
	        print("Não conseguiu pegar o item: " + name)
	        item = None

	def excluir_contrato(self):
		'''
		exclui contrato de um payload com dados de contrato, nome e cpf ja preenchido. deve atualizar apenas acao e cod_pasta
		usa o payload atual da instancia
		'''
		#self.payload.update({"contrato":data.get("contrato")})
		#self.payload.update({"cpf_cnpj1":data.get("contrato")})
		#self.payload.update({"nome1":data.get("contrato")})
		self.payload.update({"acao":"atendimento"})
		self.payload.update({
			"cod_pasta":"1132",
			"cod_pasta1":"1128",
			"cod_pasta2":"1182",
			"cod_pasta3":"239",
		})
		r = self.session.post(self.url_detalhe_contrato, data=self.payload)
		return r.status_code
		

#PAYLOAD = {}
#PAYLOADSTRING = {}

'''
	def cria_contrato(self, data, payload):
		# https://atitudesf.portalderepasse.com.br/v3/combo_situacao_incluir.asp?ID=1130&cod_pasta3=
		#print('cadastro contrato')
		# urlverificacontrato = 'https://atitudesf.portalderepasse.com.br/v3/combo_verificar_cpf.asp?ID=12345678909&contrato='
		# answer:  <input type="hidden" name="contrato_cpf" id="contrato_cpf" value="AT023904"/>
		print("cadastro cliente")
		urlIncluir = "https://atitudesf.portalderepasse.com.br/v3/contrato_incluir.asp"
		r = self.session.get(urlIncluir)
		body = r.text
		soup = BeautifulSoup(body, "html.parser")
		bodytext = soup.find('main')
		f = open('body.txt','w')
		f.write(r.text)
		f.close()
		print('======')

		nroContrato = soup.find("form", attrs={"name": "f2"})
		# print(nroContrato)
		nroContrato = nroContrato.get_text()
		i = nroContrato.find(":") + 2
		f = i + 8
		nro_contrato = nroContrato[i:f]
		print(nro_contrato)
		# time.sleep(5)
		print(payload)
		if data['tipoPesquisa'] == "teste":
			payload.update({"cod_pasta": "1361"})
			payload.update({"cod_pasta3": "391"})
		elif data['tipoPesquisa'] == "criarPasta":
			payload.update({"cod_pasta": "1130"})
		payload.update({"contrato_nro": nro_contrato.encode('latin-1')})
		payload.update({"tabs": "1"})
		
		r = self.session.post(urlIncluir, data={"contrato_nro": nro_contrato, "contrato": ''})
		# pprint(r.text)

		# POST para incluir novo contrato
		r = self.session.post(urlIncluir, data=payload)
		
		# verifica se contrato foi criado com sucesso
		if str(r.status_code) == '200':
			body = r.text
			soup = BeautifulSoup(body, "html.parser")
			# <input type="hidden" name="contrato" value="283629" />
			contrato = soup.find("input", attrs={"name": "contrato"})
			print(contrato)
			try:
				# contrato = contrato['value']
				contrato = contrato.attrs.get("value")
			except:
				contrato = 'na'
			print("====")
			print('contrato: {}'.format(contrato))
		else:
			contrato = 'na'
		# time.sleep(2)
		# pprint(body)
		print("fim cadastro cliente")
		# inclui campos do contrato no dict com dados
		data['nro_contrato'] = nro_contrato
		data['contrato'] = contrato
		data['rstatuscode'] = str(r.status_code)
		return data  # nro_contrato, contrato, r.status_code

	def cadastroCliente(session, payload, data):
		# urlverificacontrato = 'https://atitudesf.portalderepasse.com.br/v3/combo_verificar_cpf.asp?ID=12345678909&contrato='
		# answer:  <input type="hidden" name="contrato_cpf" id="contrato_cpf" value="AT023904"/>
		print("cadastro cliente")
		urlIncluir = "https://atitudesf.portalderepasse.com.br/v3/contrato_incluir.asp"
		r = session.get(urlIncluir)
		body = r.text
		soup = BeautifulSoup(body, "html.parser")
		nroContrato = soup.find("form", attrs={"name": "f2"})

		nroContrato = nroContrato.get_text()
		i = nroContrato.find(":") + 2
		f = i + 8
		nro_contrato = nroContrato[i:f]
		print(nro_contrato)
		# time.sleep(5)
		if data['tipoPesquisa'] == "teste":
			payload.update({"cod_pasta": "1361"})
			payload.update({"cod_pasta3": "391"})
		elif data['tipoPesquisa'] == "criarPasta":
			payload.update({"cod_pasta": "1130"})
		payload.update({"contrato_nro": nro_contrato.encode('latin-1')})
		payload.update({"tabs": "1"})
		r = session.post(
			urlIncluir, data={"contrato_nro": nro_contrato, "contrato": ''})
		# pprint(r.text)
		r = session.post(urlIncluir, data=payload)
		if str(r.status_code) == '200':
			body


def somenteHistorico(request, contrato):
    r = 'na'
    data = get_data(request)
    with requests.Session() as session:
        login, senha = '08114306777', 'novasenha456'
        retloginPortal = loginPortal(session, login, senha)
        if retloginPortal == True:
            r = incluiHistorico(session, contrato, data)
    return r
'''
