from flask import Blueprint, render_template, request, redirect, url_for, flash
from supabase import create_client, Client
import os

# Configuração do Supabase
supabase_url = 'https://gccxbkoejigwkqwyvcav.supabase.co'
supabase_key = os.getenv(
    'SUPABASE_KEY',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdjY3hia29lamlnd2txd3l2Y2F2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzM2OTg5OTYsImV4cCI6MjA0OTI3NDk5Nn0.ADRY3SLagP-NjhAAvRRP8A4Ogvo7AbWvcW-J5gAbyr4'
)
supabase: Client = create_client(supabase_url, supabase_key)

# Define o Blueprint para a rota de usuários
users_bp = Blueprint('users', __name__)

# Função para verificar se o usuário está logado
def verificar_login():
    if 'user_id' not in request.cookies or 'empresa_id' not in request.cookies:
        flash('Você precisa estar logado para acessar essa página.', 'danger')
        return redirect(url_for('login.login'))  # Redireciona para a página de login
    return None

@users_bp.route('/usuarios', methods=['GET', 'POST'])
def gerenciar_usuarios():
    # Verifica se o usuário está logado
    if verificar_login():
        return verificar_login()

    if request.method == 'POST':
        # Cadastro de novo usuário
        nome_usuario = request.form.get('nome').strip().upper()  # Converte para maiúsculas
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

    try:
        if search_query:
            # Filtra usuários pelo nome e pela empresa logada
            response = (supabase.table('usuarios')
                        .select('*')
                        .eq('id_empresa', request.cookies.get('empresa_id'))
                        .ilike('nome_usuario', f'%{search_query}%')
                        .execute())
        else:
            # Lista todos os usuários da empresa logada
            response = (supabase.table('usuarios')
                        .select('*')
                        .eq('id_empresa', request.cookies.get('empresa_id'))
                        .execute())

        usuarios = response.data
        return render_template('usuarios.html', usuarios=usuarios)
    except Exception as e:
        print(f"Erro ao listar usuários: {e}")
        return render_template('usuarios.html', error="Erro ao listar usuários.")

@users_bp.route('/usuarios/editar', methods=['POST'])
def editar_usuario():
    # Verifica se o usuário está logado
    if verificar_login():
        return verificar_login()

    try:
        id_usuario = request.form.get('id')
        nome_usuario = request.form.get('nome').strip().upper()  
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

