from flask import Blueprint, jsonify, request
from supabase import create_client
import os
import datetime

contas_pagar_bp = Blueprint('contas_pagar_bp', __name__)

supabase_url = 'https://gccxbkoejigwkqwyvcav.supabase.co'
supabase_key = os.getenv(
    'SUPABASE_KEY',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdjY3hia29lamlnd2txd3l2Y2F2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzM2OTg5OTYsImV4cCI6MjA0OTI3NDk5Nn0.ADRY3SLagP-NjhAAvRRP8A4Ogvo7AbWvcW-J5gAbyr4'
)
supabase = create_client(supabase_url, supabase_key)

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

        return jsonify({"message": "Conta baixada com sucesso"}), 200

    except Exception as e:
        print("Erro ao baixar conta:", str(e))
        return jsonify({"error": str(e)}), 500 