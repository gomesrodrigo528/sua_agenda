from flask import Blueprint, render_template, request, flash, redirect, url_for
from supabase import create_client
import os

# Configuração do Supabase
supabase_url = 'https://gccxbkoejigwkqwyvcav.supabase.co'
supabase_key = os.getenv(
    'SUPABASE_KEY',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdjY3hia29lamlnd2txd3l2Y2F2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzM2OTg5OTYsImV4cCI6MjA0OTI3NDk5Nn0.ADRY3SLagP-NjhAAvRRP8A4Ogvo7AbWvcW-J5gAbyr4'
)
supabase = create_client(supabase_url, supabase_key)

# Blueprint para sucesso
sucesso_bp = Blueprint('sucesso', __name__)

# Variável global para armazenar o ID da empresa recém-cadastrada
empresa_cadastrada = {}


@sucesso_bp.route('/sucesso', methods=['GET', 'POST'])
def sucesso():
    global empresa_cadastrada

    if request.method == 'POST':
        # Verificar se é cadastro de empresa ou de usuário
        if 'nome_empresa' in request.form:
            # Cadastro da empresa
            nome_empresa = request.form.get('nome_empresa').strip().upper()
            cnpj = request.form.get('cnpj').strip()
            email = request.form.get('email').strip()
            descricao = request.form.get('descricao').strip()
            setor = request.form.get('setor').strip().upper()
            tel_empresa = request.form.get('tel_empresa').strip()
            endereco = request.form.get('endereco').strip()
            cep = request.form.get('cep').strip()
            endereco = request.form.get('endereco').strip()
            cidade = request.form.get('cidade').strip().upper()


            # dias_restantes = {"1 mês": 30, "3 meses": 90, "1 ano": 365}.get(plano, 0)

            # Dados da empresa
            data = {
                "nome_empresa": nome_empresa,
                "cnpj": cnpj,
                "email_empresa": email,
                "descricao": descricao,
                "tel_empresa": tel_empresa,
                "endereco": endereco,
                "setor": setor,
                "cep": cep,
                "dias_restantes": 30,
                "teste_de_app": True,
                "cidade": cidade,
                "endereco": endereco ,
            }

            try:
                # Inserir os dados da empresa no Supabase
                response = supabase.table("empresa").insert(data).execute()
                empresa_id = response.data[0]['id']  # Obter o ID da empresa recém-criada

                # Salvar o ID para associar ao usuário
                empresa_cadastrada = {"id": empresa_id}
                flash("Empresa cadastrada com sucesso!", "success")
            except Exception as e:
                flash(f"Ocorreu um erro ao cadastrar a empresa: {e}", "danger")

        elif 'nome_usuario' in request.form:
            # Cadastro do primeiro usuário
            nome_usuario = request.form.get('nome_usuario').strip().upper()
            email_usuario = request.form.get('email_usuario').strip()
            telefone = request.form.get('telefone').strip()
            senha = request.form.get('senha').strip()

            if not nome_usuario or not email_usuario or not telefone or not senha:
                flash("Todos os campos são obrigatórios.", "danger")
                return render_template('pagamentoaprovado.html', empresa_cadastrada=empresa_cadastrada)

            try:
                # Inserir o usuário associado à empresa recém-cadastrada
                supabase.table('usuarios').insert({
                    'nome_usuario': nome_usuario,
                    'email': email_usuario,
                    'telefone': telefone,
                    'senha': senha,
                    'id_empresa': empresa_cadastrada.get("id")  # Associar ao ID da empresa
                }).execute()

                flash("Usuário cadastrado com sucesso!", "success")
                empresa_cadastrada = {}  # Limpar a variável após o cadastro

                # Redirecionar para a rota de login
                return redirect(url_for('login.login'))
            except Exception as e:
                flash(f"Erro ao cadastrar usuário: {e}", "danger")

    return render_template('pagamentoaprovado.html', empresa_cadastrada=empresa_cadastrada)
