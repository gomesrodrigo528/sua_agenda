
from datetime import timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, jsonify
from flask import jsonify, request, make_response, url_for
from datetime import timedelta

from supabase import create_client
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

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
        # Buscar cliente pelo email
        cliente_data = supabase.table('clientes').select('*').eq('email', email).single().execute()
        
        if not cliente_data.data:
            return jsonify(success=False, message='Email não encontrado, verifique o email e tente novamente.'), 404
        
        # Verificar senha
        if cliente_data.data['senha'] != senha:
            return jsonify(success=False, message='Senha incorreta, tente novamente.'), 401
        
        # Login bem-sucedido, criar cookies
        resp = make_response(jsonify(success=True, redirect_url=url_for('agendamento_bp.pagina_agendamento')))
        resp.set_cookie('cliente_id', str(cliente_data.data['id']), max_age=timedelta(days=30))
        resp.set_cookie('cliente_name', str(cliente_data.data['nome_cliente']), max_age=timedelta(days=30))
        resp.set_cookie('cliente_email', str(cliente_data.data['email']), max_age=timedelta(days=30))
        resp.set_cookie('cliente_empresa', str(cliente_data.data['id_empresa']), max_age=timedelta(days=30))
        return resp

    except Exception as e:
        print(f"Erro no login do cliente: {str(e)}")
        return jsonify(success=False, message='Erro interno no servidor. Tente novamente mais tarde.'), 500

@login_bp.route('/logout_cliente')
def logout_cliente():
    resp = make_response(redirect(url_for('login.login')))
    resp.delete_cookie('cliente_id')
    resp.delete_cookie('cliente_name')
    resp.delete_cookie('cliente_email')
    resp.delete_cookie('cliente_empresa')
    return resp

