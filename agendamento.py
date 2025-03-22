
from flask import Blueprint, jsonify, request, render_template
from supabase import create_client
import os
from datetime import datetime
import smtplib
from zoneinfo import ZoneInfo
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Configuração do Supabase
supabase_url = 'https://gccxbkoejigwkqwyvcav.supabase.co'
supabase_key = os.getenv(
    'SUPABASE_KEY',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdjY3hia29lamlnd2txd3l2Y2F2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzM2OTg5OTYsImV4cCI6MjA0OTI3NDk5Nn0.ADRY3SLagP-NjhAAvRRP8A4Ogvo7AbWvcW-J5gAbyr4'
)
supabase = create_client(supabase_url, supabase_key)

# Criação do Blueprint
agendamento_bp = Blueprint('agendamento_bp', __name__)

# Função para enviar emails
def enviar_email(destinatario, assunto, mensagem, email_remetente, senha_remetente):
    try:
        servidor_smtp = 'smtp.gmail.com'
        porta_smtp = 587

        # Configuração da mensagem
        msg = MIMEMultipart()
        msg['From'] = email_remetente
        msg['To'] = destinatario
        msg['Subject'] = assunto
        msg.attach(MIMEText(mensagem, 'plain'))

        # Envio do e-mail
        with smtplib.SMTP(servidor_smtp, porta_smtp) as servidor:
            servidor.starttls()
            servidor.login(email_remetente, senha_remetente)
            servidor.send_message(msg)

        print("E-mail enviado com sucesso!")
    except smtplib.SMTPAuthenticationError:
        print("Erro de autenticação: verifique o e-mail e a senha fornecidos.")
    except smtplib.SMTPException as e:
        print(f"Erro ao enviar e-mail: {e}")

@agendamento_bp.route('/api/agendar-cliente', methods=['POST'])
def agendar_cliente():
    dados = request.get_json()

    # Validação simples: verifica se todos os campos obrigatórios estão presentes
    campos_obrigatorios = ["nome", "email", "usuario_id", "servico_id", "data", "horario"]
    for campo in campos_obrigatorios:
        if not dados.get(campo):
            return jsonify({"error": f"O campo '{campo}' é obrigatório"}), 400

    # Busca o id_empresa relacionado ao usuario_id
    usuario = supabase.table("usuarios").select("id_empresa").eq("id", dados["usuario_id"]).execute()
    if not usuario.data:
        return jsonify({"error": "Usuário não encontrado ou sem id_empresa"}), 404
    id_empresa = usuario.data[0]["id_empresa"]

    # Busca ou criação do cliente baseado no email
    cliente = supabase.table("clientes").select("id").eq("email", dados["email"]).execute()
    if cliente.data:
        cliente_id = cliente.data[0]["id"]  # Cliente já existe, usa o ID
    else:
        # Cria um novo cliente se não existir e inclui id_empresa
        cliente_response = supabase.table("clientes").insert({
            "nome_cliente": dados["nome"],
            "email": dados["email"],
            "telefone": dados.get("telefone"),
            "id_empresa": id_empresa  # Inclui o id_empresa automaticamente
        }).execute()
        if cliente_response.data:
            cliente_id = cliente_response.data[0]["id"]
        else:
            return jsonify({"error": "Erro ao registrar o cliente"}), 500

    # Inserção do agendamento na tabela "agenda" com todos os campos necessários
    response = supabase.table("agenda").insert({
        "cliente_id": cliente_id,
        "usuario_id": dados["usuario_id"],
        "servico_id": dados["servico_id"],
        "data": dados["data"],
        "horario": dados["horario"],
        "id_empresa": id_empresa,
        "descricao": dados.get("descricao"),
        "status": "ativo"
    }).execute()

    if response.data:
        empresa = supabase.table('empresa').select("email, senha_app").eq('id', id_empresa).execute().data[0]
        cliente = supabase.table("clientes").select("email, nome_cliente").eq("id", cliente_id).execute().data[0]
        usuario = supabase.table("usuarios").select("email, nome_usuario").eq("id", dados["usuario_id"]).execute().data[0]
        servico = supabase.table("servicos").select("nome_servico").eq("id", dados["servico_id"]).execute().data[0]

        nome_servico = servico["nome_servico"]
        descricao = dados.get("descricao", "Sem descrição")  # Obtem a descrição ou usa um valor padrão

        # Mensagem para o cliente
        assunto_cliente = f"Confirmação de Agendamento - {cliente['nome_cliente']}"
        mensagem_cliente = f"""
        Olá {cliente['nome_cliente']},

        Seu agendamento foi confirmado! Aqui estão os detalhes:

        - **Serviço**: {nome_servico}
        - **Data**: {dados['data']}
        - **Horário**: {dados['horario']}
        - **Profissional Responsável**: {usuario['nome_usuario']}
        - **Descrição**: {descricao}

        Em caso de dúvidas ou alterações no agendamento, entre em contato conosco.

        Atenciosamente,
        Equipe de Agendamento.
        """

        # Mensagem para o usuário
        assunto_usuario = f"Novo Agendamento - {usuario['nome_usuario']}"
        mensagem_usuario = f"""
        Olá {usuario['nome_usuario']},

        Você recebeu um novo agendamento! Confira os detalhes abaixo:

        - **Serviço**: {nome_servico}
        - **Data**: {dados['data']}
        - **Horário**: {dados['horario']}
        - **Cliente**: {cliente['nome_cliente']}
        - **Descrição**: {descricao}

        Lembre-se de verificar sua agenda regularmente para acompanhar todos os compromissos.

        Atenciosamente,
        Equipe de Agendamento.
        """

        # Enviar os e-mails
        enviar_email(cliente['email'], assunto_cliente, mensagem_cliente, empresa['email'], empresa['senha_app'])
        enviar_email(usuario['email'], assunto_usuario, mensagem_usuario, empresa['email'], empresa['senha_app'])

        return jsonify({"message": "Agendamento realizado com sucesso"}), 201
    else:
        return jsonify({"error": "Erro ao criar agendamento"}), 400





@agendamento_bp.route('/api/empresas', methods=['GET'])
def listar_empresas():
    try:
        nome_empresa = request.args.get('nome_empresa', '').strip()
        cidade = request.args.get('cidade', '').strip().lower()

        

        query = supabase.table("empresa").select(
            "id, nome_empresa, logo, descricao, setor, horario, kids, acessibilidade, estacionamento, wifi, tel_empresa, cidade,endereco"
        ).eq("status", True)

        # Adicionar filtro de cidade apenas se ela não for vazia
      

        if nome_empresa:
            query = query.ilike("nome_empresa", f"%{nome_empresa}%")

        if cidade:
            query = query.ilike("cidade", cidade)  # Filtro de cidade

        response = query.execute()

     

        return jsonify(response.data), 200  

    except Exception as e:
        print(f"[ERRO] Falha ao buscar empresas: {e}")
        return jsonify([]), 500  


@agendamento_bp.route('/api/empresa/<int:empresa_id>', methods=['GET'])
def obter_empresa(empresa_id):
    try:
        # Busca os detalhes da empresa com o ID especificado
        response = supabase.table("empresa").select("id, nome_empresa, logo, descricao, setor, horario, kids, acessibilidade, estacionamento, wifi, tel_empresa,endereco").eq("id", empresa_id).execute()

        # Verifica se a empresa foi encontrada
        if not response.data:
            return jsonify({"error": "Empresa não encontrada"}), 404

        return jsonify(response.data[0]), 200  # Retorna os dados da empresa como JSON

    except Exception as e:
        print(f"Erro ao buscar informações da empresa: {e}")
        return jsonify({"error": "Erro ao buscar informações da empresa"}), 500

@agendamento_bp.route('/api/servicos/detalhes/<int:servico_id>', methods=['GET'])
def obter_servico_detalhes(servico_id):
    try:
        # Seleciona o serviço com o nome do profissional associado
        response = supabase.table("servicos").select("id, nome_servico, preco, id_usuario, usuarios(nome_usuario)").eq("id", servico_id).execute()
        
        if not response.data:
            return jsonify({"error": "Serviço não encontrado"}), 404
        
        servico = response.data[0]

        if servico.get('id_usuario') is None:
            # Se id_usuario for NULL, retorna todos os usuários da empresa
            empresa_id = request.args.get('empresa_id')  # Recebe o ID da empresa como parâmetro
            usuarios_response = supabase.table("usuarios").select("id, nome_usuario").eq("id_empresa", empresa_id).execute()
            servico['usuarios'] = usuarios_response.data

        return jsonify(servico), 200  # Retorna os detalhes do serviço
    except Exception as e:
        print(f"Erro ao buscar detalhes do serviço: {e}")
        return jsonify({"error": "Erro ao buscar detalhes do serviço"}), 500

@agendamento_bp.route('/api/usuarios/<int:empresa_id>', methods=['GET'])
def listar_usuarios(empresa_id):
    # Lista usuários vinculados a uma empresa específica
    response = supabase.table("usuarios").select("id, nome_usuario,ft_perfil").eq("id_empresa", empresa_id).execute()
   
    return jsonify(response.data), 200

@agendamento_bp.route('/api/servicos/<int:empresa_id>', methods=['GET'])
def listar_servicos(empresa_id):
    # Lista serviços vinculados a uma empresa específica e visíveis para clientes
    response = supabase.table("servicos").select(
        "id, nome_servico, preco, id_usuario"
    ).eq("id_empresa", empresa_id).eq("disp_cliente", True).execute()  # Corrigido: condições encadeadas
    
    return jsonify(response.data), 200


@agendamento_bp.route('/agendamento', methods=['GET'])
def pagina_agendamento():
    # Renderiza a página HTML para o agendamento
    return render_template('agendamento_cli.html')



@agendamento_bp.route('/api/agenda/data', methods=['GET'])
def listar_horarios_disponiveis():
    usuario_id = request.args.get('usuario_id')
    data = request.args.get('data')

    if not usuario_id or not data:
        return jsonify({"error": "Os parâmetros 'usuario_id' e 'data' são obrigatórios."}), 400

    # Obtendo a data e o horário atual com fuso horário
    agora = datetime.now(ZoneInfo("America/Sao_Paulo"))
    data_atual = agora.strftime("%Y-%m-%d")

    if data == data_atual:
        horario_atual = agora.strftime("%H:%M")
        print(f"Horário atual: {horario_atual}")
    else:
        horario_atual = None

    # Definindo horários de funcionamento
    horarios_funcionamento = [
        f"{hora:02}:{minuto:02}" for hora in range(8, 18) for minuto in (0, 30)
    ]

    # Buscar agendamentos já ocupados
    response_agenda = supabase.table("agenda").select(
        "horario, servico_id"
    ).eq("usuario_id", usuario_id).eq("data", data).neq("status", "finalizado").execute()

    if not response_agenda.data:
        response_agenda.data = []

    # Buscar tempos de duração dos serviços
    response_servicos = supabase.table("servicos").select("id, tempo").execute()
    servicos = {item["id"]: int(item["tempo"]) for item in response_servicos.data}

    # Processar horários ocupados
    horarios_ocupados = set()
    for agendamento in response_agenda.data:
        horario_inicio = agendamento["horario"]
        servico_id = agendamento["servico_id"]
        duracao_minutos = servicos.get(servico_id, 60)

        # Ajustar para aceitar formatos HH:mm e HH:mm:ss
        try:
            hora, minuto = map(int, horario_inicio.split(":")[:2])  # Ignora os segundos, se existirem
        except ValueError:
            print(f"Erro ao processar horário: {horario_inicio}")
            continue

        minutos_totais = hora * 60 + minuto
        for i in range(0, duracao_minutos, 30):
            minutos_ocupados = minutos_totais + i
            hora_ocupada = minutos_ocupados // 60
            minuto_ocupado = minutos_ocupados % 60
            horarios_ocupados.add(f"{hora_ocupada:02}:{minuto_ocupado:02}")

    # Calcular horários disponíveis
    horarios_disponiveis = [
        horario for horario in horarios_funcionamento
        if horario not in horarios_ocupados and (not horario_atual or horario >= horario_atual)
    ]

    return jsonify({"horarios_disponiveis": horarios_disponiveis}), 200

# Função para enviar e-mails
def enviar_email(destinatario, assunto, mensagem, email_remetente, senha_remetente):
    try:
        servidor_smtp = 'smtp.gmail.com'
        porta_smtp = 587

        msg = MIMEMultipart()
        msg['From'] = email_remetente
        msg['To'] = destinatario
        msg['Subject'] = assunto
        msg.attach(MIMEText(mensagem, 'plain'))

        servidor = smtplib.SMTP(servidor_smtp, porta_smtp)
        servidor.starttls()
        servidor.login(email_remetente, senha_remetente)
        servidor.sendmail(email_remetente, destinatario, msg.as_string())
        servidor.quit()

        print("E-mail enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")


