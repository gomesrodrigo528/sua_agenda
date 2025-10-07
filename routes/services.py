from flask import Flask, Blueprint, render_template, request, redirect, url_for, flash ,jsonify
from supabase_config import supabase

import os

app = Flask(__name__)
services_bp = Blueprint('services', __name__)

# Função de verificação de login
def verificar_login():
    if 'user_id' not in request.cookies or 'empresa_id' not in request.cookies:
        flash('Você precisa estar logado para acessar essa página.', 'danger')
        return redirect(url_for('login.login'))  # Redireciona para a página de login
    # Sempre retorna um Response, nunca None
    return None

# Página de serviços com funcionalidade de pesquisa
@services_bp.route('/servicos', methods=['GET', 'POST'])
def index():
    # Verifica se o usuário está logado
    redirecionar = verificar_login()
    if redirecionar:
        return redirecionar

    search_query = request.form.get('search_query') if request.method == 'POST' else request.args.get('search_query')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 7))
    offset = (page - 1) * per_page
    services, total_count = get_services(search_query, offset, per_page)
    total_pages = (total_count + per_page - 1) // per_page
    return render_template('servicos.html', services=services, page=page, per_page=per_page, total_pages=total_pages, total_count=total_count, search_query=search_query)
def obter_id_empresa():
    return request.cookies.get('empresa_id')

# Função para buscar serviços
def get_services(search_query=None, offset=0, per_page=7):
    try:
        empresa_id = request.cookies.get('empresa_id')  # Pega a empresa logada do cookie
        base_query = supabase.table('servicos').select('*').eq('id_empresa', empresa_id).eq('status', True)
        if search_query:
            base_query = base_query.ilike('nome_servico', f'%{search_query}%')
        # Contar total de serviços
        total_servicos = base_query.execute().data
        total_count = len(total_servicos) if total_servicos else 0
        # Buscar apenas a página atual
        response = base_query.range(offset, offset + per_page - 1).execute()
        services = response.data if response.data else []
        return services, total_count
    except Exception as e:
        print(f"Erro ao buscar serviços: {e}")
        return [], 0

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





@services_bp.route('/api/usuarios', methods=['GET'])
def listar_usuarios():
    if verificar_login():
        return verificar_login()

    empresa_id = obter_id_empresa()

    response = supabase.table("usuarios").select("id, nome_usuario").eq("id_empresa", empresa_id).execute()
    
    return jsonify(response.data), 200






@services_bp.route('/sevicos/listar')
def listar_servicos():
    try:
        empresa_id = request.cookies.get('empresa_id')
        response = (supabase.table('servicos')
                    .select('*')
                    .eq('id_empresa', empresa_id)
                    .eq('status', True)
                    .execute())
        servicos = response.data if response.data else []
        return jsonify(servicos)
    except Exception as e:
        return jsonify([]), 500
    


@services_bp.route('/servicos/editar/<int:id>', methods=['PUT', 'POST'])
def api_editar_servico(id):
    try:
        # Verifica login
        redirecionar = verificar_login()
        if redirecionar:
            return redirecionar

        dados = request.get_json()
        if not dados:
            return jsonify({"error": "JSON inválido"}), 400

        empresa_id = request.cookies.get('empresa_id')

        # Monta o update dinamicamente, só com os campos enviados
        update_data = {}

        if 'nome_servico' in dados:
            update_data['nome_servico'] = dados['nome_servico']

        if 'preco' in dados:
            update_data['preco'] = float(dados['preco'])

        if 'tempo' in dados:
            update_data['tempo'] = dados['tempo']

        if 'disp_cliente' in dados:
            update_data['disp_cliente'] = bool(dados['disp_cliente'])

        if 'status' in dados:
            update_data['status'] = bool(dados['status'])

        if not update_data:
            return jsonify({"error": "Nenhum dado para atualizar"}), 400

        # Executa o update
        supabase.table('servicos') \
            .update(update_data) \
            .eq('id', id) \
            .eq('id_empresa', empresa_id) \
            .execute()

        return jsonify({"success": True, "message": "Serviço atualizado com sucesso"})

    except Exception as e:
        print(f"Erro ao editar serviço: {e}")
        return jsonify({"error": str(e)}), 500
