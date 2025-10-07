from flask import Blueprint, render_template, request, redirect, url_for, flash
from supabase_config import supabase
import os

# Define o Blueprint para a rota de usuários
users_bp = Blueprint('users', __name__)

# Função para verificar se o usuário está logado
def verificar_login():
    if 'user_id' not in request.cookies or 'empresa_id' not in request.cookies:
        flash('Você precisa estar logado para acessar essa página.', 'danger')
        return redirect(url_for('login.login'))  # Redireciona para a página de login
    # Sempre retorna um Response, nunca None
    return None

@users_bp.route('/usuarios', methods=['GET', 'POST'])
def gerenciar_usuarios():
    # Verifica se o usuário está logado
    redirecionar = verificar_login()
    if redirecionar:
        return redirecionar

    if request.method == 'POST':
        # Cadastro de novo usuário
        nome_usuario = request.form.get('nome')
        nome_usuario = nome_usuario.strip().upper() if nome_usuario else ''
        email = request.form.get('email')
        telefone = request.form.get('telefone')
        senha = request.form.get('senha')

        if not nome_usuario or not email or not telefone or not senha:
            return render_template('usuarios.html', error="Todos os campos são obrigatórios.")

        try:
            # Cadastra usuário com a id_empresa associada ao cookie
            supabase.table('usuarios').insert({
                'nome_usuario': nome_usuario,
                'email': email,
                'telefone': telefone,
                'senha': senha,
                'id_empresa': request.cookies.get('empresa_id')  # Associa o usuário à empresa logada
            }).execute()

            return redirect(url_for('users.gerenciar_usuarios'))
        except Exception as e:
            print(f"Erro ao cadastrar usuário: {e}")
            return render_template('usuarios.html', error="Erro no servidor. Tente novamente mais tarde.")

    # Pesquisa de usuários
    search_query = request.args.get('search_query', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 7))
    offset = (page - 1) * per_page

    try:
        base_query = supabase.table('usuarios').select('*').eq('id_empresa', request.cookies.get('empresa_id'))
        if search_query:
            base_query = base_query.ilike('nome_usuario', f'%{search_query}%')
        # Contar total de usuários
        total_usuarios = base_query.execute().data
        total_count = len(total_usuarios) if total_usuarios else 0
        # Buscar apenas a página atual
        response = base_query.range(offset, offset + per_page - 1).execute()
        usuarios = response.data
        total_pages = (total_count + per_page - 1) // per_page
        return render_template('usuarios.html', usuarios=usuarios, page=page, per_page=per_page, total_pages=total_pages, total_count=total_count, search_query=search_query)
    except Exception as e:
        print(f"Erro ao listar usuários: {e}")
        return render_template('usuarios.html', error="Erro ao listar usuários.", usuarios=[], page=1, per_page=7, total_pages=1, total_count=0, search_query=search_query)

@users_bp.route('/usuarios/editar', methods=['POST'])
def editar_usuario():
    # Verifica se o usuário está logado
    if verificar_login():
        return verificar_login()

    try:
        id_usuario = request.form.get('id')
        nome_usuario = request.form.get('nome')
        nome_usuario = nome_usuario.strip().upper() if nome_usuario else ''
        email = request.form.get('email')
        telefone = request.form.get('telefone')
        senha = request.form.get('senha')

        if not id_usuario or not nome_usuario or not email or not telefone:
            return render_template('usuarios.html', error="Todos os campos são obrigatórios.")

        # Atualiza apenas se o usuário pertence à empresa logada
        supabase.table('usuarios').update({
            'nome_usuario': nome_usuario,
            'email': email,
            'telefone': telefone,
            'senha': senha,
        }).eq('id', id_usuario).eq('id_empresa', request.cookies.get('empresa_id')).execute()

        return redirect(url_for('users.gerenciar_usuarios'))
    except Exception as e:
        print(f"Erro ao editar usuário: {e}")
        return render_template('usuarios.html', error="Erro ao editar usuário.")

@users_bp.route('/usuarios/excluir/<int:id_usuario>', methods=['POST'])
def excluir_usuario(id_usuario):
    print(f"ID do Usuário a ser excluído: {id_usuario}")  # Exibe no log
    # Verifique se os dados estão chegando corretamente
    print(f"Dados recebidos: {request.form}")
    
    try:
        # Seu código de exclusão
        supabase.table('usuarios').delete().eq('id', id_usuario).eq('id_empresa', request.cookies.get('empresa_id')).execute()

        return '', 204  # Retorna sucesso sem corpo
    except Exception as e:
        print(f"Erro ao excluir usuário: {e}")
        return 'Erro ao excluir usuário.', 400

