from flask import Blueprint, render_template, request, redirect, url_for, flash,jsonify
from supabase import create_client
from flask import request, redirect
import os

# Configuração do Supabase
supabase_url = 'https://gccxbkoejigwkqwyvcav.supabase.co'
supabase_key = os.getenv(
    'SUPABASE_KEY',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdjY3hia29lamlnd2txd3l2Y2F2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzM2OTg5OTYsImV4cCI6MjA0OTI3NDk5Nn0.ADRY3SLagP-NjhAAvRRP8A4Ogvo7AbWvcW-J5gAbyr4'
)
supabase = create_client(supabase_url, supabase_key)

# Define o Blueprint para as rotas de clientes
clientes_bp = Blueprint('clientes_bp', __name__)

# Função de Verificação de Login
def verificar_login():
    if 'user_id' not in request.cookies or 'empresa_id' not in request.cookies:
        return redirect(url_for('login.login'))  # Redireciona para o login se não estiver autenticado
    return None

# Rota para listar todos os clientes
# Função para pegar os dados do usuário logado
def get_user_data():
    user_id = request.cookies.get('user_id')
    if user_id:
        # Supondo que você tenha uma tabela de usuários no Supabase, vamos pegar o nome do usuário logado
        response = supabase.table('usuarios').select('nome_usuario').eq('id', user_id).execute()
        if response.data:
            return response.data[0]['nome_usuario']
    return None

# Rota para listar todos os clientes
@clientes_bp.route('/clientes')
def clientes():
    # Verifica se o usuário está logado
    redirecionar = verificar_login()
    if redirecionar:
        return redirecionar

    query = request.args.get('query', '')  # Obtém o termo de pesquisa da URL
    error = request.args.get('error', '')  # Obtém mensagem de erro, se existir
    
    try:
        # Filtra os clientes pela empresa associada no cookie
        empresa_id = request.cookies.get('empresa_id')

        if query:
            response = (supabase.table('clientes')
                        .select('*')
                        .eq('id_empresa', empresa_id)
                        .ilike('nome_cliente', f'%{query}%')
                        .execute())
        else:
            response = (supabase.table('clientes')
                        .select('*')
                        .eq('id_empresa', empresa_id)
                        .execute())

        clientes = response.data if response.data else []
        nome_usuario = get_user_data()  # Recupera o nome do usuário logado
        return render_template('clientes.html', clientes=clientes, query=query, error=error, nome_usuario=nome_usuario)
    except Exception as e:
        print(f"Erro ao listar clientes: {e}")
        return render_template('clientes.html', clientes=[], query=query, error="Erro ao listar clientes.")


@clientes_bp.route('/add_cliente', methods=['POST'])
def cadastrar_cliente():
    # Verifica se o usuário está logado
    redirecionar = verificar_login()
    if redirecionar:
        return jsonify({"error": "Usuário não autenticado"}), 403

    nome_cliente = request.form['nome']
    telefone = request.form['telefone']
    email = request.form['email']

    try:
        empresa_id = request.cookies.get('empresa_id')
        supabase.table('clientes').insert([{
            'nome_cliente': nome_cliente,
            'telefone': telefone,
            'email': email,
            'id_empresa': empresa_id
        }]).execute()

        return jsonify({"message": "Cliente cadastrado com sucesso!"}), 200  # Retorno JSON
    except Exception as e:
        print(f"Erro ao cadastrar cliente: {e}")  # Log no terminal
        return jsonify({"error": "Erro ao cadastrar cliente"}), 500  # Retorno JSON de erro

# Rota para editar cliente
@clientes_bp.route('/editar_cliente/<int:id>', methods=['GET', 'POST'])
def editar_cliente(id):
    # Verifica se o usuário está logado
    redirecionar = verificar_login()
    if redirecionar:
        return redirecionar

    if request.method == 'GET':
        try:
            # Busca o cliente pelo ID e filtra pela empresa
            empresa_id = request.cookies.get('empresa_id')
            response = (supabase.table('clientes')
                        .select('*')
                        .eq('id', id)
                        .eq('id_empresa', empresa_id)
                        .execute())
            cliente = response.data[0] if response.data else None

            if not cliente:
                return redirect(url_for('clientes_bp.clientes', error="Cliente não encontrado."))

            return render_template('editar_cliente.html', cliente=cliente)
        except Exception as e:
            print(f"Erro ao buscar cliente: {e}")
            return redirect(url_for('clientes_bp.clientes', error="Erro ao buscar cliente."))

    if request.method == 'POST':
        nome_cliente = request.form['nome']
        telefone = request.form['telefone']
        email = request.form['email']

        try:
            # Atualiza o cliente apenas se pertence à empresa
            empresa_id = request.cookies.get('empresa_id')
            supabase.table('clientes').update({
                'nome_cliente': nome_cliente,
                'telefone': telefone,
                'email': email
            }).eq('id', id).eq('id_empresa', empresa_id).execute()

            return redirect(url_for('clientes_bp.clientes'))
        except Exception as e:
            print(f"Erro ao editar cliente: {e}")
            return redirect(url_for('clientes_bp.clientes', error="Erro ao editar cliente."))

# Rota para excluir cliente
@clientes_bp.route('/excluir_cliente/<int:id>', methods=['POST'])
def excluir_cliente(id):
    # Verifica se o usuário está logado
    redirecionar = verificar_login()
    if redirecionar:
        return redirecionar

    try:
        # Remove o cliente apenas se pertence à empresa
        empresa_id = request.cookies.get('empresa_id')
        supabase.table('clientes').delete().eq('id', id).eq('id_empresa', empresa_id).execute()

        return redirect(url_for('clientes_bp.clientes'))
    except Exception as e:
        print(f"Erro ao excluir cliente: {e}")
        return redirect(url_for('clientes_bp.clientes', error="Erro ao excluir cliente."))