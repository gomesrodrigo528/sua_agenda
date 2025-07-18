
from datetime import timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, jsonify
from flask import jsonify, request, make_response, url_for
from datetime import timedelta

from supabase import create_client
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from werkzeug.security import check_password_hash

# Configuração do Supabase
supabase_url = 'https://gccxbkoejigwkqwyvcav.supabase.co'
supabase_key = os.getenv(
    'SUPABASE_KEY',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdjY3hia29lamlnd2txd3l2Y2F2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzM2OTg5OTYsImV4cCI6MjA0OTI3NDk5Nn0.ADRY3SLagP-NjhAAvRRP8A4Ogvo7AbWvcW-J5gAbyr4'
)
supabase = create_client(supabase_url, supabase_key)

login_bp = Blueprint('login', __name__)



@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    # Obtém os valores do formulário e faz validação inicial
    email = request.form.get('email', '').strip()
    senha = request.form.get('senha', '').strip()

    if not senha:
        return jsonify(success=False, message='O campo "Senha" é obrigatório.'), 400

    try:
        # Busca email:
        usuario_data = supabase.table('usuarios').select('id, nome_usuario, senha, id_empresa').eq('email', email).single().execute()
        if not usuario_data.data:
            return jsonify(success=False, message='Email não encontrado. Verifique o email e tente novamente.'), 404

        # Verifica a senha
        if usuario_data.data['senha'] != senha:
            return jsonify(success=False, message='Senha incorreta. Tente novamente.'), 401

        # Buscar dados da empresa, incluindo o campo 'acesso'
        empresa_id = usuario_data.data['id_empresa']
        empresa_data = supabase.table('empresa').select('id, nome_empresa, acesso').eq('id', empresa_id).single().execute()
        if not empresa_data.data:
            return jsonify(success=False, message='Empresa não encontrada.'), 404

        if not empresa_data.data.get('acesso', True):
            # Setar cookies mesmo com acesso bloqueado
            resp = make_response(jsonify(success=False, bloqueio=True, message='Seu acesso está bloqueado. É necessário renovar seu plano para continuar usando o sistema.'))
            resp.set_cookie('user_id', str(usuario_data.data['id']), max_age=timedelta(days=30))
            resp.set_cookie('user_name', str(usuario_data.data['nome_usuario']), max_age=timedelta(days=30))
            resp.set_cookie('empresa_id', str(usuario_data.data['id_empresa']), max_age=timedelta(days=30))
            return resp, 403

        # Login bem-sucedido, cria cookies
        resp = make_response(jsonify(success=True, redirect_url=url_for('agenda_bp.renderizar_agenda')))
        resp.set_cookie('user_id', str(usuario_data.data['id']), max_age=timedelta(days=30))
        resp.set_cookie('user_name', str(usuario_data.data['nome_usuario']), max_age=timedelta(days=30))
        resp.set_cookie('empresa_id', str(usuario_data.data['id_empresa']), max_age=timedelta(days=30))
        return resp

    except Exception as e:
        print("Erro no login:", e)
        return jsonify(success=False, message='Erro interno no servidor. Tente novamente mais tarde.'), 500


@login_bp.route('/logout')
def logout():
    resp = make_response(redirect(url_for('login.login')))
    resp.delete_cookie('user_id')  # Remove o cookie user_id
    resp.delete_cookie('user_name')  # Remove o cookie user_name
    resp.delete_cookie('id_empresa')  # Remove o cookie empresa_id
    flash('Você foi desconectado com sucesso!', 'success')
    return resp


@login_bp.route('/verificar-cookies')
def verificar_cookies():
    # Verifica se os cookies estão sendo enviados corretamente
    user_id = request.cookies.get('user_id')
    user_name = request.cookies.get('user_name')
    empresa_id = request.cookies.get('empresa_id')

    # Retorna uma mensagem com os valores dos cookies
    if user_id and user_name and empresa_id:
        return f'Cookies armazenados com sucesso: user_id={user_id}, user_name={user_name}, empresa_id={empresa_id}'
    else:
        return 'Cookies não encontrados.'

@login_bp.route('/login_cliente', methods=['POST'])
def login_cliente():
    email = request.form.get('email', '').strip()
    senha = request.form.get('senha', '').strip()

    # Validações
    if not email:
        return jsonify(success=False, message='O campo "Email" é obrigatório.'), 400
    if not senha:
        return jsonify(success=False, message='O campo "Senha" é obrigatório.'), 400

    try:
        # Buscar usuário_cliente pelo email
        usuarios_cliente = supabase.table('usuarios_clientes').select('*').eq('email', email).execute()
        if not usuarios_cliente.data or len(usuarios_cliente.data) == 0:
            return jsonify(success=False, message='Email não encontrado, verifique o email e tente novamente.'), 404
        if len(usuarios_cliente.data) > 1:
            return jsonify(success=False, message='Há um problema com seu cadastro. Existem múltiplos usuários com este email. Contate o suporte.'), 409
        usuario_cliente = usuarios_cliente.data[0]

        # Verificar senha (comparação direta)
        if usuario_cliente['senha'] != senha:
            return jsonify(success=False, message='Senha incorreta, tente novamente.'), 401

        # Buscar dados do cliente comercial vinculado
        clientes_resp = supabase.table('clientes').select('id, nome_cliente, telefone, id_empresa').eq('id_usuario_cliente', usuario_cliente['id']).execute()
        clientes = clientes_resp.data if clientes_resp and clientes_resp.data else []
        cliente = None
        if len(clientes) == 1:
            cliente = clientes[0]
        elif len(clientes) > 1:
            id_empresa_cookie = request.cookies.get('id_empresa')
            if id_empresa_cookie is not None:
                for c in clientes:
                    if str(c['id_empresa']) == str(id_empresa_cookie):
                        cliente = c
                        break
            if not cliente:
                cliente = clientes[0]  # fallback: pega o primeiro
        # Verificar se há dados nos cookies e sincronizar se necessário
        dados_atualizados = False
        
        # Verificar dados do cliente comercial
        if cliente:
            # Verificar se os dados do cookie são diferentes dos dados do banco
            cookie_nome = request.cookies.get('cliente_name', '')
            cookie_telefone = request.cookies.get('cliente_telefone', '')
            cookie_email = request.cookies.get('cliente_email', '')
            
            # Comparar dados
            if (cookie_nome != cliente['nome_cliente'] or 
                cookie_telefone != str(cliente['telefone']) or 
                cookie_email != usuario_cliente['email']):
                
                # Atualizar dados do cliente comercial se necessário
                update_cliente = {}
                if cookie_nome != cliente['nome_cliente']:
                    update_cliente['nome_cliente'] = cliente['nome_cliente']
                if cookie_telefone != str(cliente['telefone']):
                    update_cliente['telefone'] = cliente['telefone']
                
                if update_cliente:
                    supabase.table('clientes').update(update_cliente).eq('id', cliente['id']).execute()
                
                # Atualizar dados do usuário cliente se necessário
                update_usuario = {}
                if cookie_email != usuario_cliente['email']:
                    update_usuario['email'] = usuario_cliente['email']
                
                if update_usuario:
                    supabase.table('usuarios_clientes').update(update_usuario).eq('id', usuario_cliente['id']).execute()
                
                dados_atualizados = True
        
        # Login bem-sucedido: setar cookies de usuarios_clientes e clientes
        response = jsonify(success=True, message='Login realizado com sucesso.', redirect_url='/agenda_cliente',
            cliente={
                'id': str(cliente['id']) if cliente else '',
                'nome': str(cliente['nome_cliente']) if cliente else '',
                'telefone': str(cliente['telefone']) if cliente else '',
                'email': str(usuario_cliente['email']),
                'id_usuario_cliente': str(usuario_cliente['id'])
            },
            dados_atualizados=dados_atualizados
        )
        response.set_cookie('cliente_id', str(cliente['id']) if cliente else '', max_age=timedelta(days=30))
        response.set_cookie('cliente_name', str(cliente['nome_cliente']) if cliente else '', max_age=timedelta(days=30))
        response.set_cookie('cliente_email', str(usuario_cliente['email']), max_age=timedelta(days=30))
        response.set_cookie('cliente_telefone', str(cliente['telefone']) if cliente else '', max_age=timedelta(days=30))
        response.set_cookie('id_usuario_cliente', str(usuario_cliente['id']), max_age=timedelta(days=30))
        response.set_cookie('id_empresa', str(cliente['id_empresa']) if cliente else '', max_age=timedelta(days=30))
        return response
    except Exception as e:
        print('Erro no login do cliente:', e)
        return jsonify(success=False, message='Erro interno no login. Tente novamente.'), 500

@login_bp.route('/logout_cliente')
def logout_cliente():
    resp = make_response(redirect(url_for('login.login')))
    resp.delete_cookie('cliente_id')
    resp.delete_cookie('cliente_name')
    resp.delete_cookie('cliente_email')
    resp.delete_cookie('cliente_telefone')
    resp.delete_cookie('id_usuario_cliente')
    resp.delete_cookie('id_empresa')
    return resp

