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
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 7))
    offset = (page - 1) * per_page
    
    try:
        # Filtra os clientes pela empresa associada no cookie
        empresa_id = request.cookies.get('empresa_id')

        base_query = supabase.table('clientes').select('id, nome_cliente, telefone, id_usuario_cliente').eq('id_empresa', empresa_id)
        if query:
            base_query = base_query.ilike('nome_cliente', f'%{query}%')

        # Contar total de clientes para paginação
        total_clientes = base_query.execute().data
        total_count = len(total_clientes) if total_clientes else 0

        # Buscar apenas a página atual
        response = base_query.range(offset, offset + per_page - 1).execute()
        clientes = response.data if response.data else []
        
        # Buscar emails dos clientes em usuarios_clientes
        for cliente in clientes:
            if cliente.get('id_usuario_cliente'):
                try:
                    usuario_cliente = supabase.table('usuarios_clientes').select('email').eq('id', cliente['id_usuario_cliente']).execute()
                    cliente['email'] = usuario_cliente.data[0].get('email') if usuario_cliente.data and len(usuario_cliente.data) > 0 else None
                except:
                    cliente['email'] = None
            else:
                cliente['email'] = None
        
        nome_usuario = get_user_data()  # Recupera o nome do usuário logado
        total_pages = (total_count + per_page - 1) // per_page
        return render_template('clientes.html', clientes=clientes, query=query, error=error, nome_usuario=nome_usuario, page=page, per_page=per_page, total_pages=total_pages, total_count=total_count)
    except Exception as e:
        print(f"Erro ao listar clientes: {e}")
        return render_template('clientes.html', clientes=[], query=query, error="Erro ao listar clientes.", page=1, per_page=10, total_pages=1, total_count=0)


@clientes_bp.route('/add_cliente', methods=['POST'])
def cadastrar_cliente():
    # Verifica se o usuário está logado
    redirecionar = verificar_login()
    if redirecionar:
        return jsonify({"error": "Usuário não autenticado"}), 403

    # Verificar se é JSON ou form data
    if request.is_json:
        data = request.get_json()
        nome_cliente = data.get('nome', '').strip()
        telefone = data.get('telefone', '').strip()
        email = data.get('email', '').strip()
        senha = data.get('senha', '123456')
    else:
        nome_cliente = request.form.get('nome', '').strip()
        telefone = request.form.get('telefone', '').strip()
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '123456')

    try:
        empresa_id = request.cookies.get('empresa_id')
        
        # Verificar se já existe usuário_cliente com este email
        usuario_existente = supabase.table('usuarios_clientes').select('id').eq('email', email).execute()
        
        if usuario_existente.data and len(usuario_existente.data) > 0:
            # Se já existe o usuário, apenas criar o cliente comercial associado
            id_usuario_cliente = usuario_existente.data[0]['id']
            
            # Verificar se já existe um cliente comercial associado a este usuário NA MESMA EMPRESA
            cliente_existente = supabase.table('clientes').select('id').eq('id_usuario_cliente', id_usuario_cliente).eq('id_empresa', empresa_id).execute()
            if cliente_existente.data and len(cliente_existente.data) > 0:
                return jsonify({"error": "Já existe um cliente cadastrado com este e-mail nesta empresa."}), 409
            
            # Criar apenas o cliente comercial vinculado ao usuário existente
            supabase.table('clientes').insert([{
                'nome_cliente': nome_cliente,
                'telefone': telefone,
                'id_usuario_cliente': id_usuario_cliente,
                'id_empresa': empresa_id
            }]).execute()
            
            return jsonify({"message": "Cliente cadastrado com sucesso! (Usuário existente associado)"}), 200
        else:
            # Se não existe o usuário, criar tanto o usuário quanto o cliente
            usuario_cliente_resp = supabase.table('usuarios_clientes').insert({
                'email': email,
                'senha': senha,  # Em breve: usar hash
                'telefone': telefone
            }).execute()
            
            if not usuario_cliente_resp.data:
                return jsonify({"error": "Erro ao criar usuário. Tente novamente."}), 500

            id_usuario_cliente = usuario_cliente_resp.data[0]['id']

            # Criar o cliente comercial vinculado
            supabase.table('clientes').insert([{
                'nome_cliente': nome_cliente,
                'telefone': telefone,
                'id_usuario_cliente': id_usuario_cliente,
                'id_empresa': empresa_id
            }]).execute()

            return jsonify({"message": "Cliente cadastrado com sucesso!"}), 200
            
    except Exception as e:
        print(f"Erro ao cadastrar cliente: {e}")
        return jsonify({"error": "Erro ao cadastrar cliente"}), 500

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
        senha = request.form.get('senha', '')

        try:
            empresa_id = request.cookies.get('empresa_id')
            
            # Buscar o cliente para obter o id_usuario_cliente
            cliente = supabase.table('clientes').select('id_usuario_cliente').eq('id', id).eq('id_empresa', empresa_id).execute()
            if not cliente.data or len(cliente.data) == 0 or not cliente.data[0].get('id_usuario_cliente'):
                return redirect(url_for('clientes_bp.clientes', error="Cliente não encontrado ou sem acesso de login."))
            
            id_usuario_cliente = cliente.data[0]['id_usuario_cliente']
            
            # Atualizar dados comerciais em clientes
            supabase.table('clientes').update({
                'nome_cliente': nome_cliente,
                'telefone': telefone
            }).eq('id', id).eq('id_empresa', empresa_id).execute()
            
            # Atualizar dados de login em usuarios_clientes
            update_usuario = {}
            if email:
                # Verificar se o novo email já existe em outro usuário
                email_existente = supabase.table('usuarios_clientes').select('id').eq('email', email).neq('id', id_usuario_cliente).execute()
                if email_existente.data and len(email_existente.data) > 0:
                    return redirect(url_for('clientes_bp.clientes', error="Já existe um cadastro com este e-mail."))
                update_usuario['email'] = email
            
            if senha:
                update_usuario['senha'] = senha
            
            if telefone:
                update_usuario['telefone'] = telefone
            
            if update_usuario:
                supabase.table('usuarios_clientes').update(update_usuario).eq('id', id_usuario_cliente).execute()

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
    
@clientes_bp.route('/clientes/listar')
def listar_clientes():
    try:
        # Verifica se o usuário está logado
        redirecionar = verificar_login()
        if redirecionar:
            return redirecionar

        # Filtra os clientes pela empresa associada no cookie
        empresa_id = request.cookies.get('empresa_id')
        response = (supabase.table('clientes')
                    .select('id, nome_cliente')
                    .eq('id_empresa', empresa_id)
                    .execute())

        clientes = response.data if response.data else []
        # Formata os dados para o frontend
        clientes_formatados = [{
            'id': c['id'],
            'nome': c['nome_cliente']
        } for c in clientes]
        return jsonify(clientes_formatados)
    except Exception as e:
        print(f"Erro ao listar clientes: {e}")
        return jsonify([]), 500



@clientes_bp.route('/clientes/buscar', methods=['GET'])
def buscar_clientes():
    try:
        termo = request.args.get('termo', '')
        empresa_id = request.cookies.get('empresa_id')
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 401
        if not termo:
            response = (supabase.table('clientes')
                        .select('id, nome_cliente, telefone, id_usuario_cliente')
                        .eq('id_empresa', empresa_id)
                        .limit(50)
                        .execute())
        else:
            response = (supabase.table('clientes')
                        .select('id, nome_cliente, telefone, id_usuario_cliente')
                        .eq('id_empresa', empresa_id)
                        .or_(
                            f"nome_cliente.ilike.%{termo}%",
                        )
                        .limit(50)
                        .execute())

        clientes = response.data if response.data else []
        
        # Buscar emails dos clientes em usuarios_clientes
        for cliente in clientes:
            if cliente.get('id_usuario_cliente'):
                try:
                    usuario_cliente = supabase.table('usuarios_clientes').select('email').eq('id', cliente['id_usuario_cliente']).execute()
                    cliente['email'] = usuario_cliente.data[0].get('email') if usuario_cliente.data and len(usuario_cliente.data) > 0 else None
                except:
                    cliente['email'] = None
            else:
                cliente['email'] = None
        # Formata os dados para o frontend
        clientes_formatados = [{
            'id': cliente['id'],
            'nome': cliente['nome_cliente'],
            'telefone': str(cliente['telefone']) if cliente['telefone'] else '-',
            'email': cliente['email'] or '-',
            'endereco': '-'  # compatibilidade com frontend
        } for cliente in clientes]

        return jsonify(clientes_formatados)

    except Exception as e:
        print(f"Erro ao buscar clientes: {str(e)}")
        return jsonify({'error': 'Erro ao buscar clientes'}), 500

@clientes_bp.route('/api/cliente/<int:cliente_id>', methods=['GET'])
def get_cliente(cliente_id):
    response = supabase.table('clientes').select('id, nome_cliente, telefone, id_usuario_cliente').eq('id', cliente_id).execute()
    if not response.data or len(response.data) == 0:
        return jsonify({'error': 'Cliente não encontrado'}), 404
    return jsonify(response.data[0])

@clientes_bp.route('/api/cliente/<int:cliente_id>', methods=['PUT'])
def update_cliente(cliente_id):
    data = request.get_json()
    update_cliente = {}
    update_usuario = {}

    # Buscar o cliente para obter o id_usuario_cliente
    cliente = supabase.table('clientes').select('id_usuario_cliente').eq('id', cliente_id).execute()
    if not cliente.data or len(cliente.data) == 0 or not cliente.data[0].get('id_usuario_cliente'):
        return jsonify({'error': 'Cliente não encontrado.'}), 404
    id_usuario_cliente = cliente.data[0]['id_usuario_cliente']

    # Atualizar dados comerciais
    for campo in ['telefone']:
        if campo in data:
            update_cliente[campo] = data[campo]
    if update_cliente:
        supabase.table('clientes').update(update_cliente).eq('id', cliente_id).execute()

    # Atualizar dados de login
    for campo in ['email', 'senha', 'telefone']:
        if campo in data:
            update_usuario[campo] = data[campo]
    # Se for atualizar email, validar se não existe outro usuario_cliente com esse email
    if 'email' in update_usuario:
        email_novo = update_usuario['email'].strip().lower()
        existe = supabase.table('usuarios_clientes').select('id').eq('email', email_novo).neq('id', id_usuario_cliente).execute()
        if existe.data and len(existe.data) > 0:
            return jsonify({'error': 'Já existe um cadastro com este e-mail.'}), 409
        update_usuario['email'] = email_novo
    if update_usuario:
        supabase.table('usuarios_clientes').update(update_usuario).eq('id', id_usuario_cliente).execute()

    if not update_cliente and not update_usuario:
        return jsonify({'error': 'Nenhum dado para atualizar'}), 400
    return jsonify({'message': 'Dados atualizados com sucesso!'})

@clientes_bp.route('/api/cliente', methods=['POST'])
def api_cadastrar_cliente():
    data = request.get_json()
    nome = data.get('nome', '').strip()
    telefone = data.get('telefone', '').strip()
    email = data.get('email', '').strip().lower()
    senha = data.get('senha', '')

    if not nome or not telefone or not email or not senha:
        return jsonify({'success': False, 'error': 'Preencha todos os campos.'}), 400

    # Verifica se já existe usuário_cliente com este email
    usuario_existente = supabase.table('usuarios_clientes').select('id').eq('email', email).execute()
    
    if usuario_existente.data and len(usuario_existente.data) > 0:
        # Se já existe o usuário, apenas criar o cliente comercial associado
        id_usuario_cliente = usuario_existente.data[0]['id']
        # Verificar se já existe um cliente comercial associado a este usuário
        cliente_existente = supabase.table('clientes').select('id').eq('id_usuario_cliente', id_usuario_cliente).execute()
        if cliente_existente.data and len(cliente_existente.data) > 0:
            return jsonify({'success': False, 'error': 'Já existe um cliente cadastrado com este e-mail.'}), 409
        # Criar apenas o cliente comercial vinculado ao usuário existente (sem endereco)
        cliente_resp = supabase.table('clientes').insert({
            'nome_cliente': nome,
            'telefone': telefone,
            'id_usuario_cliente': id_usuario_cliente
        }).execute()
        if not cliente_resp.data:
            return jsonify({'success': False, 'error': 'Erro ao criar cliente. Tente novamente.'}), 500
        return jsonify({'success': True, 'message': 'Cadastro realizado com sucesso! (Usuário existente associado)'}), 201
    else:
        # Se não existe o usuário, criar tanto o usuário quanto o cliente
        usuario_cliente_resp = supabase.table('usuarios_clientes').insert({
            'email': email,
            'senha': senha,  # Em breve: usar hash
            'telefone': telefone
        }).execute()
        if not usuario_cliente_resp.data:
            return jsonify({'success': False, 'error': 'Erro ao criar usuário. Tente novamente.'}), 500

        id_usuario_cliente = usuario_cliente_resp.data[0]['id']

        # Cria cliente comercial vinculado (sem endereco)
        cliente_resp = supabase.table('clientes').insert({
            'nome_cliente': nome,
            'telefone': telefone,
            'id_usuario_cliente': id_usuario_cliente
        }).execute()
        if not cliente_resp.data:
            return jsonify({'success': False, 'error': 'Erro ao criar cliente. Tente novamente.'}), 500

        return jsonify({'success': True, 'message': 'Cadastro realizado com sucesso!'}), 201