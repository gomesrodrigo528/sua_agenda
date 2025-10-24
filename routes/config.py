from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask import jsonify
from supabase_config import supabase
import os

config_bp = Blueprint('config', __name__)

def verificar_login():
    if 'user_id' not in request.cookies or 'empresa_id' not in request.cookies:
        flash('Você precisa estar logado para acessar essa página.', 'danger')
        return redirect(url_for('login.login'))  # Redireciona para a página de login
    return None

# Rota para exibir o formulário de atualização
@config_bp.route('/configuracao', methods=['GET'])
def configuracao_empresa():
    login_redirect = verificar_login()
    if login_redirect:
        return login_redirect

    empresa_id = request.cookies.get('empresa_id')

    # Busca os dados da empresa no banco de dados
    response = supabase.table("empresa").select("*").eq("id", empresa_id).execute()
    print(response.data)
    if not response.data:
        flash('Empresa não encontrada.', 'danger')
        return redirect(url_for('login.login'))  # Redireciona para a página de login

    empresa = response.data[0]
    
    # Busca as configurações da empresa
    config_response = supabase.table("config_emp").select("*").eq("id_empresa", empresa_id).execute()
    config = config_response.data[0] if config_response.data else {}
    
    # Mescla os dados da empresa com as configurações
    empresa.update(config)

    # Adicionar configuração do WhatsApp API URL
    from flask import current_app
    whatsapp_api_url = current_app.config.get('WHATSAPP_API_URL', 'http://localhost:4000')

    return render_template('configuracao.html', empresa=empresa, config={'WHATSAPP_API_URL': whatsapp_api_url})

# Rota para atualizar os dados da empresa
@config_bp.route('/configuracao/atualizar', methods=['POST'])
def atualizar_configuracao():
    login_redirect = verificar_login()
    if login_redirect:
        return login_redirect

    empresa_id = request.cookies.get('empresa_id')

    # Separar dados da empresa das configurações
    dados_empresa = {
        "endereco": request.form.get("endereco"),
        "cep": request.form.get("cep"),
        "cidade": request.form.get("cidade"),
        "setor": request.form.get("setor"),
        "tel_empresa": request.form.get("tel_empresa"),
        "status": request.form.get("status") == 'on' if request.form.get("status") else True,
        "descricao": request.form.get("descricao")
    }

    # Remover campos vazios
    dados_empresa = {k: v for k, v in dados_empresa.items() if v is not None and v != ''}

    dados_config = {
        "kids": request.form.get("kids") == 'on',
        "estacionamento": request.form.get("estacionamento") == 'on',
        "wifi": request.form.get("wifi") == 'on',
        "acessibilidade": request.form.get("acessibilidade") == 'on',
        "horario": request.form.get("horario"),
        "cor_emp": request.form.get("cor")
    }

    # Remover campos vazios das configurações
    dados_config = {k: v for k, v in dados_config.items() if v is not None and v != ''}

    try:
        # Atualizar dados da empresa
        if dados_empresa:
            response_empresa = supabase.table("empresa").update(dados_empresa).eq("id", empresa_id).execute()
            print(f"Empresa atualizada: {response_empresa.data}")

        # Verificar se existe configuração para a empresa
        config_existente = supabase.table("config_emp").select("*").eq("id_empresa", empresa_id).execute()
        
        if config_existente.data:
            # Atualizar configuração existente
            if dados_config:
                response_config = supabase.table("config_emp").update(dados_config).eq("id_empresa", empresa_id).execute()
                print(f"Configuração atualizada: {response_config.data}")
        else:
            # Criar nova configuração
            dados_config['id_empresa'] = empresa_id
            response_config = supabase.table("config_emp").insert(dados_config).execute()
            print(f"Nova configuração criada: {response_config.data}")

        flash('Configurações atualizadas com sucesso!', 'success')
    except Exception as e:
        print(f"Erro ao atualizar configurações: {e}")
        flash('Erro ao atualizar configurações.', 'danger')

    return redirect(url_for('config.configuracao_empresa')) 


# Função que busca os dias restantes da empresa baseada no ID salvo nos cookies
def dias_restantes():
    try:
        empresa_id = request.cookies.get('empresa_id')  # Pega o empresa_id dos cookies
        if not empresa_id:
            return 0  # Se não houver empresa_id nos cookies, retorna 0 (ou outro valor default)

        response = supabase.table("empresa").select("dias_restantes").eq("id", empresa_id).execute()
        if response.data:
            empresa = response.data[0]
            return empresa['dias_restantes']
        return 0  # Caso não encontre a empresa
    except Exception as e:
        print(f"Erro ao buscar dias restantes: {e}")
        return 0  # Caso ocorra um erro, retorna 0

# Rota para retornar os dias restantes da empresa com base no cookie
@config_bp.route('/api/dias_restantes', methods=['GET'])
def get_dias_restantes():
    dias = dias_restantes()  # Agora não precisa passar o empresa_id
    return jsonify({"dias_restantes": dias})
