#!/usr/bin/env python3
"""
Versão temporária do login que funciona com senhas em texto claro
"""

from datetime import timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, jsonify
from supabase_config import supabase
import os

login_bp_temp = Blueprint('login_temp', __name__)

@login_bp_temp.route('/login_temp', methods=['GET', 'POST'])
def login_temp():
    """Versão temporária do login que funciona com senhas em texto claro"""
    if request.method == 'GET':
        return render_template('login.html')

    # Obtém os valores do formulário
    email = request.form.get('email', '').strip()
    senha = request.form.get('senha', '').strip()

    if not senha:
        return jsonify(success=False, message='O campo "Senha" é obrigatório.'), 400

    try:
        # Busca email:
        usuario_data = supabase.table('usuarios').select('id, nome_usuario, senha, id_empresa').eq('email', email).single().execute()
        if not usuario_data.data:
            return jsonify(success=False, message='Email não encontrado. Verifique o email e tente novamente.'), 404

        # Verifica a senha (comparação direta para senhas em texto claro)
        senha_banco = usuario_data.data['senha']
        
        # Se a senha está em hash, usar PasswordManager
        if senha_banco.startswith('$2b$') or senha_banco.startswith('scrypt:'):
            from utils.security import PasswordManager
            if not PasswordManager.verify_password(senha, senha_banco):
                return jsonify(success=False, message='Senha incorreta. Tente novamente.'), 401
        else:
            # Se a senha está em texto claro, comparar diretamente
            if senha_banco != senha:
                return jsonify(success=False, message='Senha incorreta. Tente novamente.'), 401

        # Buscar dados da empresa
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

@login_bp_temp.route('/login_cliente_temp', methods=['POST'])
def login_cliente_temp():
    """Versão temporária do login de cliente que funciona com senhas em texto claro"""
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

        # Verificar senha (comparação direta para senhas em texto claro)
        senha_banco = usuario_cliente['senha']
        
        # Se a senha está em hash, usar PasswordManager
        if senha_banco.startswith('$2b$') or senha_banco.startswith('scrypt:'):
            from utils.security import PasswordManager
            if not PasswordManager.verify_password(senha, senha_banco):
                return jsonify(success=False, message='Senha incorreta, tente novamente.'), 401
        else:
            # Se a senha está em texto claro, comparar diretamente
            if senha_banco != senha:
                return jsonify(success=False, message='Senha incorreta, tente novamente.'), 401

        # Resto do código igual ao original...
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

        # Login bem-sucedido: setar cookies
        response = jsonify(success=True, message='Login realizado com sucesso.', redirect_url='/agenda_cliente',
            cliente={
                'id': str(cliente['id']) if cliente else '',
                'nome': str(cliente['nome_cliente']) if cliente else '',
                'telefone': str(cliente['telefone']) if cliente else '',
                'email': str(usuario_cliente['email']),
                'id_usuario_cliente': str(usuario_cliente['id'])
            }
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
