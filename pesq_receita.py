#coding: utf-8
import requests
import json
from bs4 import BeautifulSoup
import time
import ast
from pprint import pprint
import base64
import shutil
import os, sys, pathlib
from utils import upload_gdrive
import utils
#from firebadminEu import get_info_db, set_info_db, upload_to_bucket, download_file

def main_receita(nome, cpf, nasc, caminho_local, pasta_servidor,drive_service):
	"""
	nome
	cpf
	nasc
	caminho_local
	pasta_servidor
	drive_service
	"""
	result = '-'
	with requests.Session() as session:
		cont = 0
		#for item in cpfs:
		try:
			result = pesqReceita(session, nome, cpf,
			          nasc, caminho_local, pasta_servidor, "2021",drive_service)
			#pesqReceita(session, name, item,
			#            nasc[cont], caminho, pastaPesquisas, "2020")
		except Exception as e:
				result = "Except receita: {}".format(e)
	
	return result
				

def pesqReceita(session, nome, cpf, nasc, caminho, pasta_servidor, ano, drive_service):
	correto = False
	# Loop para esperar solucao do captcha
	while correto == False:
		try:
			print('1')
			# /{}'.format(diahora)
			urlcaptcha = 'https://servicos.receita.fazenda.gov.br/Servicos/consrest/Atual.app/paginas/util/captcha.asp'
			r = session.get(urlcaptcha, verify=False, stream=True)
			
			if sys.platform == 'linux':
				folder_name = "/tmp/"
			else:
				folder_name = os.path.join(pathlib.Path(__file__).parent.absolute(), "files")
			path = os.path.join(folder_name,'captcha1.png')
			
			if r.status_code == 200:
				with open(path, 'wb') as out_file:
					r.raw.decode_content = True
					shutil.copyfileobj(r.raw, out_file)
			
			capt = preencheCaptcha(path)
			
			urlTarget = "https://servicos.receita.fazenda.gov.br/Servicos/consrest/Atual.app/paginas/view/restituicao.asp"
			payloadPesq = {'CPF': cpf, 'exercicio': ano, 'data_nascimento': nasc,
                            'txtTexto_captcha_serpro_gov_br': capt, 'btnConsultar': 'Consultar'}
			r = session.post(urlTarget, data=payloadPesq, verify=False)
			
			body = r.text
			soup = str(BeautifulSoup(body, 'html.parser'))
			invalid = soup.find("Código de segurança inválido!")
			if invalid > 0:
				correto = False
				print('codigo seguranca invalido')
			else:
				correto = True
				
				resultado = verificaResultado(
					body, nome, ano, caminho, pasta_servidor, drive_service)
				
				result = resultado
				
				#apaga arquivo de captcha
				os.remove(path)

			#body = soup.find("table")
			#body = body.getText()
			print('6')
		except Exception as e:
			print("Erro no pesqReceita")
			print(e)
			resultado = "_ERRO_"
			file_name = nome + resultado + "IRPF" + ano + ".html"
			full_file_name = caminho + "/" + file_name
			
			arquivo = open(full_file_name, 'w')
			arquivo.write("Ocorreu um erro com a verificação desse cliente.")
			arquivo.close()

			#file_data = "Ocorreu um erro com a verificação desse cliente."
			#upload_to_bucket(caminho, fileName, "attadmin.appspot.com")
			drive_service.upload_file(full_file_name,
                             			file_name,
                             			[pasta_servidor],
                             			mime_type='text/html')
			os.remove(file_name)
			correto = True
			result = 'erro'
	
	return result

def preencheCaptcha(nome_arquivo):
	try:
		print("em preenche captcha" + nome_arquivo)
		API_KEY = '5a66fb161041577c76acac2592c70edc'  # Your 2captcha API KEY
		image_file = open(nome_arquivo, "rb")
		data = {'key': API_KEY, 'method': 'post'}
		captchafile = {'file': image_file}
		r = requests.post('http://2captcha.com/in.php', files=captchafile, data=data)
		print(str(r.text))
		if r.ok and r.text.find('OK') > -1:
			reqid = r.text[r.text.find('|')+1:]
			print("[+] Capcha id: "+reqid)
		resp = ""
		print("solving ref capcha...")
		time.sleep(5)
		r_captcha = requests.get(
			'http://2captcha.com/res.php?key={0}&action=get&id={1}'.format(API_KEY, reqid))
		print("capcha: " + r_captcha.text)
		while 'CAPCHA_NOT_READY' in r_captcha.text:
			print("while")
			r_captcha = requests.get(
				'http://2captcha.com/res.php?key={0}&action=get&id={1}'.format(API_KEY, reqid))
			time.sleep(4)
			print(r_captcha.text)

		print("pos loop while")
		resp = r_captcha.text[r_captcha.text.find('|') + 1:]
		return resp
	except Exception as e:
		print("Erro no preenche captcha")
		print(e)


def verificaResultado(body, nome, ano, caminho, folder_id, drive_service):
	try:
		soup = BeautifulSoup(body, 'html.parser')
		body = soup.find_all("table")
		html = str(soup)
		print('0')
		#print(html)
		resp1 = html.find("declaração está na base de dados da")
		if resp1 > 0:
			print('1')
			resultado = "_Declara_"
		else:
			print("Zero else")
			resp1 = html.find("processada")
			if resp1 > 0:
				print('2')
				resultado = "_Declara_"
			else:
				resp1 = html.find("Creditada")
				if resp1 > 0:
					print('3')
					resultado = "_Declara_"
				else:
					resp1 = html.find("Sua declaração não consta")
					if resp1 > 0:
						print('4')
						resultado = "_NãoDeclara_"
					else:
						#resultado = "_MENSAGEM NAO IDENTIFICADA_"
						resp1 = html.find("Erro: ")
						if resp1 > 0:
							print("ESTE CPF NÃO POSSUI REGISTRO")
							return
						else:
							resultado = "_MENSAGEM NAO IDENTIFICADA_"

		#fileName = r"/" + nome + resultado + "IRPF" + ano + ".html"
		if sys.platform == 'linux':
			folder_name = "/tmp/"
		else:
			folder_name = os.path.join(pathlib.Path(__file__).parent.absolute(), "files")

		file_name_html = nome + ano + resultado + "IRPF.html"
		file_name_pdf = nome + ano + resultado + "IRPF.pdf"

		utils.upload_html_pdf_files(file_name_html, file_name_pdf, html, folder_id)

		return resultado
	except Exception as e:
		return "Erro no verificaresultado: {}".format(e)



