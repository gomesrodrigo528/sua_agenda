from flask import Flask, Blueprint, render_template, request, redirect, url_for, jsonify
from flask import flash, session
from flask import current_app as app
from datetime import datetime
from supabase_config import supabase

import os
import datetime



financeiro_bp = Blueprint('financeiro_bp' , __name__)

dataatual = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
print(dataatual)



@financeiro_bp.route('/financeiro')
def render_financeiro():
    return render_template('financeiro.html')


def verificar_login():
    if not request.cookies.get('user_id') or not request.cookies.get('empresa_id'):
        return redirect(url_for('login.login'))  # Redireciona para a página de login se não estiver autenticado
    return None




@financeiro_bp.route('/financeiro/entrada', methods=['POST'])
def receber():
    try:
        if verificar_login():
            return verificar_login()
        
        data = request.get_json()
        print("Payload recebido:", data)

        id_empresa = request.cookies.get('empresa_id')
        id_usuario = request.cookies.get('user_id')

        if not id_empresa or not id_usuario:
            return jsonify({"error": "Usuário não autenticado"}), 401

        # Validação de campos obrigatórios
        motivo = data.get('motivo')
        valor = data.get('valor')
        meio_pagamento = data.get('meio_pagamento')
        servico = data.get('servico')
        cliente = data.get('cliente')

        erros = []

        if not motivo:
            erros.append("Motivo é obrigatório.")
        if not valor:
            erros.append("Valor é obrigatório.")
        else:
            try:
                valor = float(valor)
            except ValueError:
                erros.append("Valor deve ser numérico.")

        if not meio_pagamento:
            erros.append("Meio de pagamento é obrigatório.")

        try:
            servico = int(servico) if servico else None
        except (TypeError, ValueError):
            erros.append("Serviço inválido.")

        try:
            cliente = int(cliente) if cliente else None
        except (TypeError, ValueError):
            erros.append("Cliente inválido.")

        if erros:
            return jsonify({"error": erros}), 400

        # Verifica se já existe uma entrada com os mesmos dados nos últimos 5 minutos
        cinco_minutos_atras = (datetime.datetime.now() - datetime.timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
        
        response = supabase.table("financeiro_entrada") \
            .select("*") \
            .eq("id_empresa", id_empresa) \
            .eq("valor_entrada", valor) \
            .eq("motivo", motivo) \
            .eq("meio_pagamento", meio_pagamento) \
            .gte("data", cinco_minutos_atras) \
            .execute()

        if response.data:
            return jsonify({"error": "Uma receita idêntica foi registrada nos últimos 5 minutos. Aguarde para evitar duplicidade."}), 400

        response = supabase.table("financeiro_entrada").insert({
            "data": dataatual,
            "id_empresa": id_empresa,
            "valor_entrada": valor,
            "motivo": motivo,
            "meio_pagamento": meio_pagamento,
            "id_servico": servico,
            "id_cliente": cliente,
            "id_usuario": id_usuario
        }).execute()

        return jsonify({"message": "Receita registrada com sucesso!"}), 201

    except Exception as e:
        print(f"Erro ao registrar receita: {e}")
        return jsonify({"error": str(e)}), 500

@financeiro_bp.route('/financeiro/saida', methods=['POST'])
def despesa():
    try:
        if verificar_login():
            return verificar_login()

        data = request.get_json()
        print("JSON recebido:", data)

        id_empresa = request.cookies.get('empresa_id')
        id_usuario = request.cookies.get('user_id')

        if not id_empresa or not id_usuario:
            return jsonify({"error": "Usuário não autenticado"}), 401

        # Validação de campos obrigatórios
        motivo = data.get('motivo')
        valor = data.get('valor')

        if not motivo or not valor:
            return jsonify({"error": "Motivo e valor são obrigatórios"}), 400

        try:
            valor = float(valor)
        except ValueError:
            return jsonify({"error": "Valor deve ser numérico"}), 400

        # Verifica se já existe uma saída com os mesmos dados nos últimos 5 minutos
        cinco_minutos_atras = (datetime.datetime.now() - datetime.timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
        
        response = supabase.table("financeiro_saida") \
            .select("*") \
            .eq("id_empresa", id_empresa) \
            .eq("valor_saida", valor) \
            .eq("motivo", motivo) \
            .gte("data", cinco_minutos_atras) \
            .execute()

        if response.data:
            return jsonify({"error": "Uma despesa idêntica foi registrada nos últimos 5 minutos. Aguarde para evitar duplicidade."}), 400

        response = supabase.table("financeiro_saida").insert({
            "data": dataatual,
            "id_empresa": id_empresa,
            "valor_saida": valor,
            "motivo": motivo,
            "id_usuario": id_usuario
        }).execute()

        return jsonify({"message": "Despesa registrada com sucesso!"}), 201

    except Exception as e:
        print("ERRO:", str(e))
        return jsonify({"error": str(e)}), 500
    

@financeiro_bp.route('/financeiro/entrada/excluir/<int:id>', methods=['DELETE'])
def excluir(id):
    try:
        if verificar_login():
            return verificar_login()
        
        id_empresa = request.cookies.get('empresa_id')
        
        # Verifica se a entrada existe e pertence à empresa
        entrada = supabase.table("financeiro_entrada") \
            .select("*") \
            .eq("id", id) \
            .eq("id_empresa", id_empresa) \
            .single() \
            .execute()

        if not entrada.data:
            return jsonify({"error": "Receita não encontrada ou sem permissão para excluir"}), 404

        # Exclui a entrada
        supabase.table("financeiro_entrada").delete().eq("id", id).execute()
        return jsonify({"message": "Receita excluída com sucesso!"}), 200

    except Exception as e:
        print(f"Erro ao excluir receita: {e}")
        return jsonify({"error": f"Erro ao excluir receita: {str(e)}"}), 500

@financeiro_bp.route('/financeiro/saida/excluir/<int:id>', methods=['DELETE'])
def excluir_saida(id):
    try:
        if verificar_login():
            return verificar_login()
        
        id_empresa = request.cookies.get('empresa_id')
        
        # Verifica se a saída existe e pertence à empresa
        saida = supabase.table("financeiro_saida") \
            .select("*") \
            .eq("id", id) \
            .eq("id_empresa", id_empresa) \
            .single() \
            .execute()

        if not saida.data:
            return jsonify({"error": "Despesa não encontrada ou sem permissão para excluir"}), 404

        # Exclui a saída
        supabase.table("financeiro_saida").delete().eq("id", id).execute()
        return jsonify({"message": "Despesa excluída com sucesso!"}), 200

    except Exception as e:
        print(f"Erro ao excluir despesa: {e}")
        return jsonify({"error": f"Erro ao excluir despesa: {str(e)}"}), 500


@financeiro_bp.route('/financeiro/listar', methods=['GET'])
def listar_financeiro():
    try:
        if verificar_login():
            return verificar_login()

        id_empresa = request.cookies.get('empresa_id')

        if not id_empresa:
            return jsonify({"error": "Usuário não autenticado"}), 401

        # Busca todas as entradas
        response_entrada = supabase.table("financeiro_entrada") \
            .select("*") \
            .eq("id_empresa", id_empresa) \
            .order("data", desc=True) \
            .execute()

        entradas_raw = response_entrada.data if response_entrada.data else []
        entradas_formatadas = []

        for entrada in entradas_raw:
            try:
                # Resolvendo os nomes das FKs com tratamento de erro para cada consulta
                cliente_nome = "Não identificado"
                usuario_nome = "Não identificado"
                servico_nome = "Não identificado"

                if entrada.get("id_cliente"):
                    cliente = supabase.table("clientes").select("nome_cliente").eq("id", entrada["id_cliente"]).single().execute()
                    if cliente.data:
                        cliente_nome = cliente.data.get("nome_cliente", "Não identificado")

                if entrada.get("id_usuario"):
                    usuario = supabase.table("usuarios").select("nome_usuario").eq("id", entrada["id_usuario"]).single().execute()
                    if usuario.data:
                        usuario_nome = usuario.data.get("nome_usuario", "Não identificado")

                if entrada.get("id_servico"):
                    servico = supabase.table("servicos").select("nome_servico").eq("id", entrada["id_servico"]).single().execute()
                    if servico.data:
                        servico_nome = servico.data.get("nome_servico", "Não identificado")

                entradas_formatadas.append({
                    "id_entrada": entrada.get("id"),
                    "data": entrada.get("data", ""),
                    "meio_pagamento": entrada.get("meio_pagamento", "Não informado"),
                    "motivo": entrada.get("motivo", "Não informado"),
                    "valor_entrada": float(entrada.get("valor_entrada", 0)),
                    "cliente": cliente_nome,
                    "usuario": usuario_nome,
                    "servico": servico_nome
                })
            except Exception as e:
                print(f"Erro ao processar entrada {entrada.get('id')}: {str(e)}")
                continue

        # Busca todas as saídas com tratamento de dados
        response_saida = supabase.table("financeiro_saida").select("*").eq("id_empresa", id_empresa).execute()
        saidas_raw = response_saida.data if response_saida.data else []
        
        saidas_formatadas = []
        for saida in saidas_raw:
            try:
                saidas_formatadas.append({
                    "id": saida.get("id"),
                    "data": saida.get("data", ""),
                    "motivo": saida.get("motivo", "Não informado"),
                    "valor_saida": float(saida.get("valor_saida", 0))
                })
            except Exception as e:
                print(f"Erro ao processar saída {saida.get('id')}: {str(e)}")
                continue

        return jsonify({
            "entradas": entradas_formatadas,
            "saidas": saidas_formatadas
        }), 200

    except Exception as e:
        print(f"Erro em /financeiro/listar: {e}")
        return jsonify({"error": str(e)}), 500



@financeiro_bp.route('/financeiro/totais', methods = ['GET'])
def total_entradas():
    try:
        id_empresa = request.cookies.get('empresa_id')

        if not id_empresa:
            return jsonify({"error": "Usuário não autenticado"}), 401

        try:
            response_entrada = supabase.table("financeiro_entrada").select("valor_entrada").eq("id_empresa", id_empresa).execute()
            total_entradas = sum(float(item.get('valor_entrada', 0)) for item in (response_entrada.data or []))
        except Exception as e:
            print(f"Erro ao calcular total de entradas: {e}")
            total_entradas = 0

        try:
            response_saida = supabase.table("financeiro_saida").select("valor_saida").eq("id_empresa", id_empresa).execute()
            total_saidas = sum(float(item.get('valor_saida', 0)) for item in (response_saida.data or []))
        except Exception as e:
            print(f"Erro ao calcular total de saídas: {e}")
            total_saidas = 0

        saldo = total_entradas - total_saidas

        return jsonify({
            "total_entradas": total_entradas,
            "total_saidas": total_saidas,
            "saldo": saldo
        }), 200
    except Exception as e:
        print(f"Erro ao calcular totais: {e}")
        return jsonify({
            "error": "Erro ao calcular totais",
            "total_entradas": 0,
            "total_saidas": 0,
            "saldo": 0
        }), 500
    

@financeiro_bp.route('/financeiro/ultimas_entradas', methods=['GET'])
def ultimas_entradas():
    try:
        if verificar_login():
            return verificar_login()

        id_empresa = request.cookies.get('empresa_id')

        if not id_empresa:
            return jsonify({"error": "Usuário não autenticado"}), 401

        # Busca as últimas 10 entradas
        response = supabase.table("financeiro_entrada") \
            .select("*") \
            .eq("id_empresa", id_empresa) \
            .order("data", desc=True) \
            .limit(3) \
            .execute()

        entradas = response.data if response.data else []
        entradas_formatadas = []

        for entrada in entradas:
            try:
                # Busca informações relacionadas
                cliente_nome = "Não identificado"
                usuario_nome = "Não identificado"
                servico_nome = "Não identificado"

                if entrada.get("id_cliente"):
                    cliente = supabase.table("clientes").select("nome_cliente").eq("id", entrada["id_cliente"]).single().execute()
                    if cliente.data:
                        cliente_nome = cliente.data.get("nome_cliente", "Não identificado")

                if entrada.get("id_usuario"):
                    usuario = supabase.table("usuarios").select("nome_usuario").eq("id", entrada["id_usuario"]).single().execute()
                    if usuario.data:
                        usuario_nome = usuario.data.get("nome_usuario", "Não identificado")

                if entrada.get("id_servico"):
                    servico = supabase.table("servicos").select("nome_servico").eq("id", entrada["id_servico"]).single().execute()
                    if servico.data:
                        servico_nome = servico.data.get("nome_servico", "Não identificado")

                entradas_formatadas.append({
                    "id": entrada.get("id"),
                    "data": entrada.get("data"),
                    "meio_pagamento": entrada.get("meio_pagamento"),
                    "motivo": entrada.get("motivo"),
                    "valor_entrada": float(entrada.get("valor_entrada", 0)),
                    "cliente": cliente_nome,
                    "usuario": usuario_nome,
                    "servico": servico_nome
                })
            except Exception as e:
                print(f"Erro ao processar entrada {entrada.get('id')}: {str(e)}")
                continue

        return jsonify(entradas_formatadas)

    except Exception as e:
        print(f"Erro ao listar últimas entradas: {e}")
        return jsonify([]), 500

@financeiro_bp.route('/financeiro/ultimas_saidas', methods=['GET'])
def ultimas_saidas():
    try:
        if verificar_login():
            return verificar_login()

        id_empresa = request.cookies.get('empresa_id')

        if not id_empresa:
            return jsonify({"error": "Usuário não autenticado"}), 401

        # Busca as últimas 10 saídas
        response = supabase.table("financeiro_saida") \
            .select("*") \
            .eq("id_empresa", id_empresa) \
            .order("data", desc=True) \
            .limit(3) \
            .execute()

        saidas = response.data if response.data else []
        saidas_formatadas = []

        for saida in saidas:
            try:
                saidas_formatadas.append({
                    "id": saida.get("id"),
                    "data": saida.get("data"),
                    "motivo": saida.get("motivo"),
                    "valor_saida": float(saida.get("valor_saida", 0))
                })
            except Exception as e:
                print(f"Erro ao processar saída {saida.get('id')}: {str(e)}")
                continue

        return jsonify(saidas_formatadas)

    except Exception as e:
        print(f"Erro ao listar últimas saídas: {e}")
        return jsonify([]), 500
    
