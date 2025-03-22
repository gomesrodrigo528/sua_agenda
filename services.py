from flask import Flask, Blueprint, render_template, request, redirect, url_for, flash ,jsonify
from supabase import create_client

import os

# Configuração do Supabase
supabase_url = 'https://gccxbkoejigwkqwyvcav.supabase.co'
supabase_key = os.getenv(
    'SUPABASE_KEY',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdjY3hia29lamlnd2txd3l2Y2F2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzM2OTg5OTYsImV4cCI6MjA0OTI3NDk5Nn0.ADRY3SLagP-NjhAAvRRP8A4Ogvo7AbWvcW-J5gAbyr4'
)
supabase = create_client(supabase_url, supabase_key)
app = Flask(__name__)
services_bp = Blueprint('services', __name__)

# Função de verificação de login
def verificar_login():
    if 'user_id' not in request.cookies or 'empresa_id' not in request.cookies:
        flash('Você precisa estar logado para acessar essa página.', 'danger')
        return redirect(url_for('login.login'))  # Redireciona para a página de login
    return None

# Página de serviços com funcionalidade de pesquisa
@services_bp.route('/servicos', methods=['GET', 'POST'])
def index():
    # Verifica se o usuário está logado
    if verificar_login():
        return verificar_login()

    search_query = request.form.get('search_query') if request.method == 'POST' else None
    services = get_services(search_query)
    return render_template('servicos.html', services=services)
def obter_id_empresa():
    return request.cookies.get('empresa_id')

# Função para buscar serviços
def get_services(search_query=None):
    try:
        empresa_id = request.cookies.get('empresa_id')  # Pega a empresa logada do cookie
        if search_query:
            response = (supabase.table('servicos')
                        .select('*')
                        .eq('id_empresa', empresa_id)
                        .ilike('nome_servico', f'%{search_query}%')
                        .execute())
        else:
            response = (supabase.table('servicos')
                        .select('*')
                        .eq('id_empresa', empresa_id)
                        .execute())
        return response.data if response.data else []
    except Exception as e:
        print(f"Erro ao buscar serviços: {e}")
        return []

# Função para adicionar um novo serviço
@services_bp.route('/add_service', methods=['POST'])
def add_service():
    # Verifica se o usuário está logado
    if verificar_login():
        return verificar_login()

    try:
        nome_servico = request.form['nome_servico']
        preco = float(request.form['preco'])
        tempo = int(request.form['tempo'])
        responsavel = request.form['responsavel']
        disp_cliente = request.form.get('disp_cliente', '0')
        disp_cliente = True if disp_cliente == '1' else False  # Padrão: '0' (não visível)

        # Verifica se 'responsavel' está vazio e o define como None
        id_usuario = None if not responsavel else int(responsavel)

        # Adiciona o id_empresa do cookie
        empresa_id = request.cookies.get('empresa_id')
        supabase.table('servicos').insert([{
            'nome_servico': nome_servico,
            'preco': preco,
            'tempo': tempo,
            'id_usuario': id_usuario,
            'id_empresa': empresa_id,
            'disp_cliente': disp_cliente  # Salva como True/False
        }]).execute()

        print('Serviço adicionado com sucesso!')

        # Retorna um JSON com a mensagem de sucesso
        return jsonify({"message": "Serviço cadastrado com sucesso!"}), 200
    except Exception as e:
        print(f"Erro ao cadastrar serviço: {e}")
        # Retorna um JSON com a mensagem de erro
        return jsonify({"error": "Erro ao cadastrar serviço"}), 500



# Função para excluir um serviço
@services_bp.route('/excluir_servico/<int:service_id>', methods=['GET'])
def excluir_servico(service_id):
    # Verifica se o usuário está logado
    if verificar_login():
        return verificar_login()

    try:
        # Exclui apenas se o serviço pertence à empresa logada
        empresa_id = request.cookies.get('empresa_id')
        supabase.table('servicos').delete().eq('id', service_id).eq('id_empresa', empresa_id).execute()
    except Exception as e:
        print(f"Erro ao excluir serviço: {e}")
        flash('Erro ao excluir serviço. Tente novamente.', 'danger')
    return redirect(url_for('services.index'))




@services_bp.route('/api/usuarios', methods=['GET'])
def listar_usuarios():
    if verificar_login():
        return verificar_login()

    empresa_id = obter_id_empresa()

    response = supabase.table("usuarios").select("id, nome_usuario").eq("id_empresa", empresa_id).execute()
    
    return jsonify(response.data), 200
