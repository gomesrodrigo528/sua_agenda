
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
    empresa = request.form.get('empresa', '').strip().upper()
    usuario = request.form.get('usuario', '').strip().upper()
    senha = request.form.get('senha', '').strip()

    if not empresa:
        return jsonify(success=False, message='O campo "Nome da Empresa" é obrigatório.'), 400
    if not usuario:
        return jsonify(success=False, message='O campo "Usuário" é obrigatório.'), 400
    if not senha:
        return jsonify(success=False, message='O campo "Senha" é obrigatório.'), 400

    try:
        # Busca a empresa no banco
        empresa_data = supabase.table('empresa').select('id, acesso').eq('nome_empresa', empresa).single().execute()
        if not empresa_data.data:
            return jsonify(success=False, message='Empresa não encontrada. Verifique o nome e tente novamente.'), 404

        id_empresa = empresa_data.data['id']
        acesso_empresa = empresa_data.data['acesso']

        if not acesso_empresa:
            mensagem = (
                'Atenção! Sua licença está expirada. '
                '<a href="/renovacao" class="btn btn-warning btn-sm">Renovar Licença</a>'
            )
            return jsonify(success=False, message=mensagem), 403

        # Busca o usuário
        usuario_data = supabase.table('usuarios').select('id, nome_usuario, senha').eq('nome_usuario', usuario).eq('id_empresa', id_empresa).single().execute()
        if not usuario_data.data:
            return jsonify(success=False, message='Usuário não encontrado. Verifique o nome e tente novamente.'), 404

        # Verifica a senha
        if usuario_data.data['senha'] != senha:
            return jsonify(success=False, message='Senha incorreta. Tente novamente.'), 401

        # Login bem-sucedido, cria cookies
        resp = make_response(jsonify(success=True, redirect_url=url_for('agenda_bp.renderizar_agenda')))
        resp.set_cookie('user_id', str(usuario_data.data['id']), max_age=timedelta(days=30))
        resp.set_cookie('user_name', usuario_data.data['nome_usuario'], max_age=timedelta(days=30))
        resp.set_cookie('empresa_id', str(id_empresa), max_age=timedelta(days=30))
        return resp

    except Exception as e:
        print("Erro no login:", e)
        return jsonify(success=False, message='Erro interno no servidor. Tente novamente mais tarde.'), 500


@login_bp.route('/logout')
def logout():
    resp = make_response(redirect(url_for('login.login')))
    resp.delete_cookie('user_id')  # Remove o cookie user_id
    resp.delete_cookie('user_name')  # Remove o cookie user_name
    resp.delete_cookie('empresa_id')  # Remove o cookie empresa_id
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

