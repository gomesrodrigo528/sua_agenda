from flask import Blueprint, jsonify, request
from supabase_config import supabase
import os
import datetime

contas_pagar_bp = Blueprint('contas_pagar_bp', __name__)





def verificar_login():
    if not request.cookies.get('user_id') or not request.cookies.get('empresa_id'):
        return jsonify({"error": "Usuário não autenticado"}), 401
    return None

@contas_pagar_bp.route('/contas_pagar/listar', methods=['GET'])
def listar_contas():
    try:
        if verificar_login():
            return verificar_login()

        id_empresa = request.cookies.get('empresa_id')

        response = supabase.table("contas_pagar") \
            .select("*") \
            .eq("id_empresa", id_empresa) \
            .execute()

        contas = response.data if response.data else []
        
        # Formata as contas para exibição
        contas_formatadas = []
        for conta in contas:
            contas_formatadas.append({
                "id": conta.get("id"),
                "descricao": conta.get("descricao"),
                "valor": float(conta.get("valor", 0)),
                "data_vencimento": conta.get("data_vencimento"),
                "data_emissao": conta.get("data_emissao"),
                "status": conta.get("status", "pendente"),
                "plano_contas": conta.get("plano_contas")
            })

        return jsonify(contas_formatadas), 200

    except Exception as e:
        print("Erro ao listar contas a pagar:", str(e))
        return jsonify({"error": str(e)}), 500

@contas_pagar_bp.route('/contas_pagar/baixar/<int:id>', methods=['POST'])
def baixar_conta(id):
    try:
        if verificar_login():
            return verificar_login()

        id_empresa = request.cookies.get('empresa_id')
        id_usuario = request.cookies.get('user_id')
        data = request.get_json()

        # Busca a conta a pagar
        conta = supabase.table("contas_pagar") \
            .select("*") \
            .eq("id", id) \
            .eq("id_empresa", id_empresa) \
            .single() \
            .execute()

        if not conta.data:
            return jsonify({"error": "Conta não encontrada"}), 404

        if conta.data["status"] == "pago":
            return jsonify({"error": "Esta conta já foi paga"}), 400

        data_atual = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Registra a saída no financeiro
        supabase.table("financeiro_saida").insert({
            "data": data_atual,
            "id_empresa": id_empresa,
            "valor_saida": conta.data["valor"],
            "motivo": f"Pagamento: {conta.data['descricao']}",
            "id_usuario": id_usuario,
            "meio_pagamento": data.get("meio_pagamento", "não informado")
        }).execute()

        # Atualiza o status da conta para pago
        supabase.table("contas_pagar") \
            .update({"status": "pago"}) \
            .eq("id", id) \
            .execute()

        # Atualiza o status do agendamento para finalizado (se existir)
        if conta.data.get('id_agendamento'):
            supabase.table("agenda").update({"status": "finalizado"}).eq("id", conta.data['id_agendamento']).execute()

        return jsonify({"message": "Conta baixada com sucesso"}), 200

    except Exception as e:
        print("Erro ao baixar conta:", str(e))
        return jsonify({"error": str(e)}), 500

@contas_pagar_bp.route('/contas_pagar/incluir', methods=['POST'])
def incluir_conta_pagar():
    try:
        if verificar_login():
            return verificar_login()
        id_empresa = request.cookies.get('empresa_id')
        id_usuario = request.cookies.get('user_id')
        data = request.get_json()
        erros = []
        # Validação dos campos obrigatórios
        data_vencimento = data.get('data_vencimento')
        descricao = data.get('descricao')
        valor = data.get('valor')
        plano_contas = data.get('plano_contas')
        data_emissao = data.get('data_emissao')
        status = data.get('status')
        if not data_vencimento:
            erros.append('Data de vencimento é obrigatória.')
        if not descricao:
            erros.append('Descrição é obrigatória.')
        if not valor:
            erros.append('Valor é obrigatório.')
        if not data_emissao:
            erros.append('Data de emissão é obrigatória.')
        if not status:
            erros.append('Status é obrigatório.')
        if erros:
            return jsonify({'error': erros}), 400
        try:
            valor = float(valor)
        except Exception:
            return jsonify({'error': 'Valor deve ser numérico.'}), 400
        
        # Cria a conta a pagar
        response = supabase.table('contas_pagar').insert({
            'id_empresa': id_empresa,
            'id_usuario': id_usuario,
            'data_vencimento': data_vencimento,
            'valor': valor,
            'descricao': descricao,
            'plano_contas': plano_contas,
            'data_emissao': data_emissao,
            'status': status
        }).execute()
        
        # Cria agendamento para a data de vencimento
        insert_agendamento = supabase.table("agenda").insert({
            "data": data_vencimento,
            "horario": "12:00",
            "id_empresa": id_empresa,
            "usuario_id": id_usuario,
            "cliente_id": None,  # Contas a pagar não têm cliente
            "descricao": f"Vencimento: {descricao} - R$ {valor:.2f}",
            "servico_id": "146",  # ID padrão para contas a pagar
            "status": "ativo"
        }).execute()
        
        # Atualiza a conta a pagar com o ID do agendamento
        if insert_agendamento.data:
            id_agendamento = insert_agendamento.data[0]['id']
            supabase.table("contas_pagar").update({
                "id_agendamento": id_agendamento
            }).eq("id", response.data[0]['id']).execute()
        
        return jsonify({'message': 'Conta a pagar cadastrada com sucesso!'}), 201
    except Exception as e:
        print('Erro ao cadastrar conta a pagar:', str(e))
        return jsonify({'error': str(e)}), 500 
