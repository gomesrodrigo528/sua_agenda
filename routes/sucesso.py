from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from supabase import create_client
import os
import re
from datetime import datetime, timedelta
import requests

# Configuração do Supabase
supabase_url = 'https://gccxbkoejigwkqwyvcav.supabase.co'
supabase_key = os.getenv(
    'SUPABASE_KEY',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdjY3hia29lamlnd2txd3l2Y2F2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzM2OTg5OTYsImV4cCI6MjA0OTI3NDk5Nn0.ADRY3SLagP-NjhAAvRRP8A4Ogvo7AbWvcW-J5gAbyr4'
)
supabase = create_client(supabase_url, supabase_key)

# Blueprint para sucesso
sucesso_bp = Blueprint('sucesso', __name__)

def validar_plano(plano):
    """Valida se o plano é válido e retorna os dias correspondentes"""
    planos_validos = {
        'mensal': 30,
        'trimestral': 90,
        'anual': 365,
        'teste': 30
    }
    return planos_validos.get(plano, None)

def validar_email(email):
    """Valida formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validar_cnpj_cpf(documento):
    """Valida CNPJ ou CPF"""
    documento = re.sub(r'[^\d]', '', documento)
    
    if len(documento) == 11:  # CPF
        return validar_cpf(documento)
    elif len(documento) == 14:  # CNPJ
        return validar_cnpj(documento)
    return False

def validar_cpf(cpf):
    cpf = re.sub(r'[^0-9]', '', cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for i in range(9, 11):
        soma = sum(int(cpf[num]) * ((i+1) - num) for num in range(0, i))
        digito = ((soma * 10) % 11) % 10
        if digito != int(cpf[i]):
            return False
    return True

def validar_cnpj(cnpj):
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    if len(cnpj) != 14:
        return False
    if cnpj == cnpj[0] * 14:
        return False
    def calc_digito(cnpj, peso):
        soma = sum(int(cnpj[i]) * peso[i] for i in range(len(peso)))
        resto = soma % 11
        return '0' if resto < 2 else str(11 - resto)
    peso1 = [5,4,3,2,9,8,7,6,5,4,3,2]
    peso2 = [6] + peso1
    if calc_digito(cnpj, peso1) != cnpj[12]:
        return False
    if calc_digito(cnpj, peso2) != cnpj[13]:
        return False
    return True

def consultar_receitaws_cnpj(cnpj):
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    try:
        resp = requests.get(f'https://www.receitaws.com.br/v1/cnpj/{cnpj}', timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f'Erro ao consultar ReceitaWS: {e}')
    return None

def verificar_empresa_existente(email, cnpj):
    """Verifica se a empresa já existe no banco"""
    try:
        # Verificar por email
        response_email = supabase.table('empresa').select('*').eq('email_empresa', email).execute()
        if response_email.data:
            return response_email.data[0]
        
        # Verificar por CNPJ
        response_cnpj = supabase.table('empresa').select('*').eq('cnpj', cnpj).execute()
        if response_cnpj.data:
            return response_cnpj.data[0]
        
        return None
    except Exception as e:
        print(f"Erro ao verificar empresa: {e}")
        return None

def verificar_teste_ativo(empresa):
    """Verifica se a empresa tem teste ativo"""
    if not empresa:
        return False
    
    # Verifica se tem teste ativo
    if not empresa.get('teste_de_app', False):
        return False
    
    # Verifica se ainda tem dias restantes
    dias_restantes = empresa.get('dias_restantes', 0)
    if dias_restantes <= 0:
        return False
    
    return True

@sucesso_bp.route('/pagamentoaprovado/<plano>', methods=['GET', 'POST'])
def sucesso(plano):
    print(f"DEBUG: Acessando rota /pagamentoaprovado/{plano}")
    
    # Validação de segurança: verificar se o plano é válido
    dias_plano = validar_plano(plano)
    print(f"DEBUG: Plano '{plano}' - dias_plano: {dias_plano}")
    
    if dias_plano is None:
        print(f"DEBUG: Plano inválido '{plano}', redirecionando para /adquirir")
        flash("Plano inválido! Redirecionando para página de planos.", "error")
        return redirect('/adquirir')
    
    # Proteção contra acesso direto à URL sem pagamento
    if plano != 'teste' and request.method == 'GET':
        # Para planos pagos, verificar se veio do MercadoPago
        referer = request.headers.get('Referer', '')
        print(f"DEBUG: Referer: {referer}")
        if not referer or 'mercadopago' not in referer.lower():
            print(f"DEBUG: Acesso não autorizado - referer: {referer}")
            flash("Acesso não autorizado. Redirecionando para página de planos.", "error")
            return redirect('/adquirir')
    
    # Verificar se há empresa cadastrada na session
    empresa_cadastrada = session.get('empresa_cadastrada', {})
    
    if request.method == 'POST':
        # Verificar se é JSON ou form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form
        
        # Verificar se é cadastro de empresa ou de usuário
        if 'nome_empresa' in data:
            # Cadastro da empresa
            nome_empresa = data.get('nome_empresa', '').strip().upper()
            cnpj = data.get('cnpj', '').strip()
            email = data.get('email', '').strip()
            descricao = data.get('descricao', '').strip()
            setor = data.get('setor', '').strip().upper()
            tel_empresa = data.get('tel_empresa', '').strip()
            endereco = data.get('endereco', '').strip()
            cep = data.get('cep', '').strip()
            cidade = data.get('cidade', '').strip().upper()
            
            # Validações de segurança
            if not all([nome_empresa, cnpj, email, descricao, setor, tel_empresa, endereco, cep, cidade]):
                flash("Todos os campos são obrigatórios.", "error")
                return render_template('pagamentoaprovado.html', empresa_cadastrada=empresa_cadastrada, plano=plano)
            
            # Validar email
            if not validar_email(email):
                flash("Formato de email inválido.", "error")
                return render_template('pagamentoaprovado.html', empresa_cadastrada=empresa_cadastrada, plano=plano)
            
            # Validar CNPJ/CPF
            if len(cnpj) == 14:
                # if not validar_cnpj(cnpj):
                #     return jsonify({"success": False, "error": "CNPJ inválido."}), 400
                # # Consultar ReceitaWS
                # dados_receita = consultar_receitaws_cnpj(cnpj)
                # if dados_receita and dados_receita.get('status') == 'OK':
                #     # Preencher automaticamente os dados se não enviados
                #     if not nome_empresa:
                #         nome_empresa = dados_receita.get('nome', '').upper()
                #     if not endereco:
                #         endereco = dados_receita.get('logradouro', '')
                #     if not cidade:
                #         cidade = dados_receita.get('municipio', '').upper()
                pass
            elif len(cnpj) == 11:
                if not validar_cpf(cnpj):
                    return jsonify({"success": False, "error": "CPF inválido."}), 400
            else:
                return jsonify({"success": False, "error": "CNPJ ou CPF inválido."}), 400
            # Verificar se empresa já existe
            empresa_existente = verificar_empresa_existente(email, cnpj)
            if empresa_existente:
                return jsonify({"success": False, "error": "Empresa já cadastrada."}), 409
            
            # Dados da empresa
            data = {
                "nome_empresa": nome_empresa,
                "cnpj": cnpj,
                "email_empresa": email,
                "descricao": descricao,
                "tel_empresa": tel_empresa,
                "endereco": endereco,
                "setor": setor,
                "cep": cep,
                "dias_restantes": dias_plano,
                "teste_de_app": plano == 'teste',  # True apenas para teste gratuito
                "cidade": cidade,
                "data_cadastro": datetime.now().isoformat()
            }

            try:
                response = supabase.table("empresa").insert(data).execute()
                empresa_id = response.data[0]['id']
                session['empresa_cadastrada'] = {"id": empresa_id}
                return jsonify({"success": True, "empresa_id": empresa_id}), 201
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500

        elif 'nome_usuario' in data:
            # Cadastro do primeiro usuário
            nome_usuario = data.get('nome_usuario', '').strip().upper()
            email_usuario = data.get('email_usuario', '').strip()
            telefone = data.get('telefone', '').strip()
            senha = data.get('senha', '').strip()

            print(f"DEBUG: Cadastro de usuário - Nome: {nome_usuario}, Email: {email_usuario}")
            print(f"DEBUG: Empresa cadastrada na session: {session.get('empresa_cadastrada')}")

            # Validações de segurança
            if not all([nome_usuario, email_usuario, telefone, senha]):
                return jsonify({"success": False, "error": "Todos os campos são obrigatórios."}), 400
            
            # Validar email do usuário
            if not validar_email(email_usuario):
                return jsonify({"success": False, "error": "Formato de email inválido."}), 400
            
            # Validar senha (mínimo 8 caracteres, pelo menos uma maiúscula, uma minúscula e um número)
            if len(senha) < 8 or not re.search(r'[A-Z]', senha) or not re.search(r'[a-z]', senha) or not re.search(r'\d', senha):
                return jsonify({"success": False, "error": "A senha deve ter pelo menos 8 caracteres, uma letra maiúscula, uma minúscula e um número."}), 400

            try:
                # Verificar se o usuário já existe
                response = supabase.table('usuarios').select('*').eq('email', email_usuario).execute()
                if response.data:
                    return jsonify({"success": False, "error": "Este email já está cadastrado. Use outro email."}), 409
                
                print(f"DEBUG: Inserindo usuário no banco")
                # Inserir o usuário associado à empresa recém-cadastrada
                supabase.table('usuarios').insert({
                    'nome_usuario': nome_usuario,
                    'email': email_usuario,
                    'telefone': telefone,
                    'senha': senha,
                    'id_empresa': session.get('empresa_cadastrada', {}).get("id")  # Associar ao ID da empresa
                }).execute()

                print(f"DEBUG: Usuário cadastrado com sucesso")
                session.pop('empresa_cadastrada', None)  # Limpar a session após o cadastro

                return jsonify({"success": True, "message": "Usuário cadastrado com sucesso! Você pode fazer login agora."}), 201
            except Exception as e:
                print(f"DEBUG: Erro ao cadastrar usuário: {e}")
                return jsonify({"success": False, "error": f"Erro ao cadastrar usuário: {e}"}), 500

    return render_template('pagamentoaprovado.html', empresa_cadastrada=empresa_cadastrada, plano=plano)

