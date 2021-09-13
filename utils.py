#coding: utf-8

import time
import os, sys, pathlib

import settings as st
import weasyprint

from views import drive_service, portal_service

def time_wait(my_time):
	time.sleep(my_time)


def get_data(item):
	data = {}
	data['nome1'] = item.nome1
	data['nome2'] = item.nome2
	data['nome3'] = item.nome3
	data['cpf1'] = item.cpf1 #'12345678909'
	data['cpf2'] = item.cpf2
	data['cpf3'] = item.cpf3
	data['sexo1'] = item.sexo1#', 'M')
	data['sexo2'] = item.sexo2#', '')
	data['sexo3'] = item.sexo3#', '')
	data['nasc1'] = item.nasc1#', '01/01/1900')
	data['nasc2'] = item.nasc2#', '')
	data['nasc3'] = item.nasc3#', '')
	data['estadocivil1'] = item.estadocivil1#', '')#request.form.get('estadocivil1', '')
	data['codempreendimento'] =     item.codempreendimento#', '2473')
	data['nomeempr'] =     item.empreendimento#', '')
	data['gerente'] =      item.codgerente#', '2264')
	data['imob'] =         item.codimob#', '1339')
	data['obs'] =          item.obs#', 'obs')
	data['telefone'] =     item.telefone#', '(21) 2222-3333')
	data['email_prop1'] =  item.email#', 'sememail@email.com')
	data['construtora'] =  item.construtora#', '80')
	data['tipoPesquisa']=  item.tipoPesquisa#', 'teste')
	return data


def upload_file_to_google_drive(local_file_name, drive_file_name, folder_id, mime_type=''):
	print('upload_drive: {}'.format(local_file_name))
	file_id = drive_service.upload_file(
		local_file_name, drive_file_name, [folder_id], mime_type=mime_type)

	return file_id


def upload_gdrive(file_name,file_data, parents_list,mime_type='',file_write_type='wb'):
	if sys.platform == 'linux':
		folder_name = "/tmp/"
	else:
		folder_name = os.path.join(pathlib.Path(__file__).parent.absolute(), "files")
	
	print(folder_name)
	local_file_name = os.path.join(folder_name, file_name)
	
	f = open(local_file_name, file_write_type)
	f.write(file_data)
	f.close()
    
	# upload file to google drive
	file_id = drive_service.upload_file(local_file_name, file_name, parents_list,mime_type=mime_type)

	# remove local file
	if os.path.exists(local_file_name):
		os.remove(local_file_name)

	return file_id


def create_portal(data):
	print("cria contrato no Portal Atitude")
	nro_contrato, contrato = 'na', 'na'
	portal_service.verifica_e_loga()
	try:
	    payloadFinal = portal_service.preenche_payload(data, 'cadastro')
	except:
	    nro_contrato, contrato = 'na payload', 'na payload'
	try:
		# cadastrar cliente
	    nro_contrato, contrato = portal_service.cadastro_cliente(payloadFinal, data)
	except:
	    nro_contrato, contrato = 'na cad', 'na cad'
	try:
	    r = portal_service.inclui_historico(contrato, data)
	    print(r)
	except:
	    nro_contrato, contrato = 'na his', 'na his'
	return nro_contrato, contrato


def html_to_pdf(local_file_name):
	pdf = weasyprint.HTML(local_file_name).write_pdf()
	#len(pdf)
	pdf_file_name = local_file_name.split(".")[0] + ".pdf"
	with open(pdf_file_name, 'wb') as f:
		f.write(pdf)
	
	return pdf_file_name


def append_folder_to_file_name(folder,local_file_name):
	if sys.platform == 'linux':
		folder_name = "/tmp/"
	else:
		folder_name = os.path.join(pathlib.Path(__file__).parent.absolute(), folder)

	folder_file = os.path.join(folder_name, local_file_name)

	return folder_file



def change_css_img_links_cx_aqui_html(cx_aqui_html):
	modified_html = cx_aqui_html.replace(
		'src="/caixaaquistatic//images/caixaaqui_pequeno.png"','src="caixaaqui_pequeno.png"')

	modified_html = modified_html.replace(
		'="/caixaaquistatic/caixaaqui.css"', '="caixaaqui.css"')
	
	modified_html = modified_html.replace(
		'="/caixaaquistatic/caixaaqui_W3C.css"', '="caixaaqui_W3C.css"')
	
	modified_html = modified_html.replace(
		'url("/caixaaquistatic//images/marca-uso-interno.png")', 'url("marca-uso-interno.png")')

	modified_html = modified_html.replace('', '')

	return modified_html


def calcula_restr_cad(r_sicaq_cliente):
    retornoSipes = r_sicaq_cliente['cliente']['retornoSipes']
    sicow = retornoSipes['sicow']['codRetorno']
    siccf = retornoSipes['siccf']['codRetorno']
    cadin = retornoSipes['cadin']['codRetorno']
    sinad = retornoSipes['sinad']['codRetorno']
    serasa = retornoSipes['serasa']['codRetorno']
    spc = retornoSipes['spc']['codRetorno']

    print(sicow, siccf, cadin, sinad, serasa, spc)
    if sicow+siccf+cadin+sinad+serasa+spc == '000000000000':
        restr_cad = 'Não'
    else:
        restr_cad = 'Sim'

    return restr_cad

def upload_sicaq_file(r_sicaq,cpf_num):
		folder_id = r_sicaq['folder_id']
		
		cpf = 'cpf{}'.format(cpf_num)
		cpf_html = r_sicaq['data'][cpf]["pesquisa_cadastral"]
		
		nome = r_sicaq['data'][cpf]['cliente']['cliente']['nome'].title()
		restr_cad = calcula_restr_cad(r_sicaq['data'][cpf])
        # nome do arquivo
		file_name_html = nome + "_" + restr_cad + '_sicaq.html'
		file_name_pdf = nome + "_" + restr_cad + '_sicaq.pdf'

        #muda links dos arquivos css e jpg
		html_data = change_css_img_links_cx_aqui_html(cpf_html)

        # cria e salva html
		full_file_name_html = append_folder_to_file_name('files', file_name_html)
		create_local_file(full_file_name_html, html_data, 'w')

		upload_file_to_google_drive(
                    full_file_name_html, file_name_html, folder_id, mime_type='text/html')
		
        # cria e salva pdf
		#full_file_name_pdf = append_folder_to_file_name('files', file_name_pdf)
		full_file_name_pdf = html_to_pdf(full_file_name_html)
		file_id = upload_file_to_google_drive(
                    full_file_name_pdf, file_name_pdf, folder_id, mime_type='application/pdf')

		# remove arquivos locais
		remove_local_file(full_file_name_html)
		remove_local_file(full_file_name_pdf)

		
		return file_id

def create_local_file(file_name, file_data, write_type):
	f = open(file_name, write_type)
	f.write(file_data)
	f.close()
	return 'ok'

def remove_local_file(file_name):
	if os.path.exists(file_name):
		os.remove(file_name)


def upload_html_pdf_files(file_name_html, file_name_pdf, html, folder_id):
    '''
		cria e salva html e pdf no google drive
	'''
	# cria e salva html
    full_file_name_html = append_folder_to_file_name('files', file_name_html)
    create_local_file(full_file_name_html, html, 'w')

    upload_file_to_google_drive(
            full_file_name_html, file_name_html, folder_id, mime_type='text/html')

    print(full_file_name_html)
    # cria e salva pdf
    full_file_name_pdf = html_to_pdf(full_file_name_html)
    file_id = upload_file_to_google_drive(
        full_file_name_pdf, file_name_pdf, folder_id, mime_type='application/pdf')
	# remove arquivos locais
    remove_local_file(full_file_name_html)
    remove_local_file(full_file_name_pdf) 
	
    return file_id


if __name__=='__main__':
	html_to_pdf('/tmp/cxaqui_cadastro.html')

