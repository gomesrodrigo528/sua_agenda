from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask import jsonify
from supabase import create_client
import os

supabase_url = 'https://gccxbkoejigwkqwyvcav.supabase.co'
supabase_key = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdjY3hia29lamlnd2txd3l2Y2F2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzM2OTg5OTYsImV4cCI6MjA0OTI3NDk5Nn0.ADRY3SLagP-NjhAAvRRP8A4Ogvo7AbWvcW-J5gAbyr4')
supabase = create_client(supabase_url, supabase_key)

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
    if not response.data:
        flash('Empresa não encontrada.', 'danger')
        return redirect(url_for('login.login'))  # Redireciona para a página de login

    empresa = response.data[0]
    return render_template('configuracao.html', empresa=empresa)

# Rota para atualizar os dados da empresa
@config_bp.route('/configuracao/atualizar', methods=['POST'])
def atualizar_configuracao():
    login_redirect = verificar_login()
    if login_redirect:
        return login_redirect

    empresa_id = request.cookies.get('empresa_id')

    # Dados enviados pelo formulário
    dados_atualizados = {
        "kids": request.form.get("kids") == 'on',
        "estacionamento": request.form.get("estacionamento") == 'on',
        "wifi": request.form.get("wifi") == 'on',
        "acessibilidade": request.form.get("acessibilidade") == 'on',
        "horario": request.form.get("horario"),
        "endereco": request.form.get("endereco"),
        "cep": request.form.get("cep"),
        "cidade": request.form.get("cidade"),
        "setor" : request.form.get("setor"),
        "tel_empresa": request.form.get("tel_empresa"),
        "status": request.form.get("status"),
        "descricao": request.form.get("descricao"),
        "cor_emp": request.form.get("cor")
    }

    try:
        # Atualiza os dados no banco de dados
        response = supabase.table("empresa").update(dados_atualizados).eq("id", empresa_id).execute()
        if response.status_code == 204:
            flash('Configurações atualizadas com sucesso!', 'success')
        else:
            flash('Erro ao atualizar configurações.', 'danger')
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

