from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from supabase import create_client
import os
import re
from datetime import datetime, timedelta

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
    """Valida CPF"""
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    
    # Validação do primeiro dígito
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = 11 - (soma % 11)
    digito1 = 0 if resto > 9 else resto
    
    if int(cpf[9]) != digito1:
        return False
    
    # Validação do segundo dígito
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = 11 - (soma % 11)
    digito2 = 0 if resto > 9 else resto
    
    return int(cpf[10]) == digito2

def validar_cnpj(cnpj):
    """Valida CNPJ"""
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False
    
    # Validação do primeiro dígito
    multiplicadores = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * multiplicadores[i] for i in range(12))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    if int(cnpj[12]) != digito1:
        return False
    
    # Validação do segundo dígito
    multiplicadores = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * multiplicadores[i] for i in range(13))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    return int(cnpj[13]) == digito2

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
    # Validação de segurança: verificar se o plano é válido
    dias_plano = validar_plano(plano)
    if dias_plano is None:
        flash("Plano inválido! Redirecionando para página de planos.", "error")
        return redirect('/adquirir')
    
    # Proteção contra acesso direto à URL sem pagamento
    if plano != 'teste' and request.method == 'GET':
        # Para planos pagos, verificar se veio do MercadoPago
        referer = request.headers.get('Referer', '')
        if not referer or 'mercadopago' not in referer.lower():
            flash("Acesso não autorizado. Redirecionando para página de planos.", "error")
            return redirect('/adquirir')
    
    # Verificar se há empresa cadastrada na session
    empresa_cadastrada = session.get('empresa_cadastrada', {})
    
    if request.method == 'POST':
        # Verificar se é cadastro de empresa ou de usuário
        if 'nome_empresa' in request.form:
            # Cadastro da empresa
            nome_empresa = request.form.get('nome_empresa', '').strip().upper()
            cnpj = request.form.get('cnpj', '').strip()
            email = request.form.get('email', '').strip()
            descricao = request.form.get('descricao', '').strip()
            setor = request.form.get('setor', '').strip().upper()
            tel_empresa = request.form.get('tel_empresa', '').strip()
            endereco = request.form.get('endereco', '').strip()
            cep = request.form.get('cep', '').strip()
            cidade = request.form.get('cidade', '').strip().upper()
            
            # Validações de segurança
            if not all([nome_empresa, cnpj, email, descricao, setor, tel_empresa, endereco, cep, cidade]):
                flash("Todos os campos são obrigatórios.", "error")
                return render_template('pagamentoaprovado.html', empresa_cadastrada=empresa_cadastrada, plano=plano)
            
            # Validar email
            if not validar_email(email):
                flash("Formato de email inválido.", "error")
                return render_template('pagamentoaprovado.html', empresa_cadastrada=empresa_cadastrada, plano=plano)
            
            # Validar CNPJ/CPF
            if not validar_cnpj_cpf(cnpj):
                print(f"DEBUG: CNPJ/CPF inválido: {cnpj}")
                # Temporariamente comentar para testar
                # flash("CNPJ ou CPF inválido.", "error")
                # return render_template('pagamentoaprovado.html', empresa_cadastrada=empresa_cadastrada, plano=plano)
            
            # Verificar se empresa já existe
            empresa_existente = verificar_empresa_existente(email, cnpj)
            print(f"DEBUG: Verificando empresa - Email: {email}, CNPJ: {cnpj}")
            print(f"DEBUG: Empresa existente: {empresa_existente}")
            
            if empresa_existente:
                print(f"DEBUG: Empresa encontrada - ID: {empresa_existente.get('id')}")
                # Se empresa existe e tem teste ativo, permitir acesso
                if verificar_teste_ativo(empresa_existente):
                    print(f"DEBUG: Teste ativo encontrado")
                    flash("Empresa já cadastrada com teste ativo. Você pode continuar usando o sistema.", "info")
                    session['empresa_cadastrada'] = {"id": empresa_existente['id']}
                    return render_template('pagamentoaprovado.html', empresa_cadastrada=session['empresa_cadastrada'], plano=plano)
                else:
                    print(f"DEBUG: Teste não ativo - exibindo popup de erro")
                    return render_template('pagamentoaprovado.html', empresa_cadastrada={}, plano=plano, erro_empresa_cadastrada=True)
            else:
                print(f"DEBUG: Empresa não encontrada - prosseguindo com cadastro")
            
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
                print(f"DEBUG: Inserindo empresa no banco")
                # Inserir os dados da empresa no Supabase
                response = supabase.table("empresa").insert(data).execute()
                empresa_id = response.data[0]['id']  # Obter o ID da empresa recém-criada
                print(f"DEBUG: Empresa inserida com ID: {empresa_id}")

                # Salvar o ID na session para associar ao usuário
                session['empresa_cadastrada'] = {"id": empresa_id}
                flash("Empresa cadastrada com sucesso!", "success")
                print(f"DEBUG: Empresa cadastrada, aguardando cadastro do usuário")
            except Exception as e:
                print(f"DEBUG: Erro ao cadastrar empresa: {e}")
                flash(f"Ocorreu um erro ao cadastrar a empresa: {e}", "error")

        elif 'nome_usuario' in request.form:
            # Cadastro do primeiro usuário
            nome_usuario = request.form.get('nome_usuario', '').strip().upper()
            email_usuario = request.form.get('email_usuario', '').strip()
            telefone = request.form.get('telefone', '').strip()
            senha = request.form.get('senha', '').strip()

            print(f"DEBUG: Cadastro de usuário - Nome: {nome_usuario}, Email: {email_usuario}")
            print(f"DEBUG: Empresa cadastrada na session: {session.get('empresa_cadastrada')}")

            # Validações de segurança
            if not all([nome_usuario, email_usuario, telefone, senha]):
                flash("Todos os campos são obrigatórios.", "error")
                return render_template('pagamentoaprovado.html', empresa_cadastrada=empresa_cadastrada, plano=plano)
            
            # Validar email do usuário
            if not validar_email(email_usuario):
                flash("Formato de email inválido.", "error")
                return render_template('pagamentoaprovado.html', empresa_cadastrada=empresa_cadastrada, plano=plano)
            
            # Validar senha (mínimo 8 caracteres, pelo menos uma maiúscula, uma minúscula e um número)
            if len(senha) < 8 or not re.search(r'[A-Z]', senha) or not re.search(r'[a-z]', senha) or not re.search(r'\d', senha):
                flash("A senha deve ter pelo menos 8 caracteres, uma letra maiúscula, uma minúscula e um número.", "error")
                return render_template('pagamentoaprovado.html', empresa_cadastrada=empresa_cadastrada, plano=plano)

            try:
                # Verificar se o usuário já existe
                response = supabase.table('usuarios').select('*').eq('email', email_usuario).execute()
                if response.data:
                    flash("Este email já está cadastrado. Use outro email.", "error")
                    return render_template('pagamentoaprovado.html', empresa_cadastrada=empresa_cadastrada, plano=plano)
                
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
                flash("Usuário cadastrado com sucesso! Você pode fazer login agora.", "success")
                session.pop('empresa_cadastrada', None)  # Limpar a session após o cadastro

                # Redirecionar para a rota de login
                return redirect(url_for('login.login'))
            except Exception as e:
                print(f"DEBUG: Erro ao cadastrar usuário: {e}")
                flash(f"Erro ao cadastrar usuário: {e}", "error")

    return render_template('pagamentoaprovado.html', empresa_cadastrada=empresa_cadastrada, plano=plano)

