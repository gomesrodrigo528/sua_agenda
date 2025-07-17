#!/usr/bin/env python3
"""
Teste simples para verificar a API de agenda_cliente
"""

from flask import Flask, request, jsonify
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

@app.route('/teste_agenda', methods=['GET'])
def teste_agenda():
    """Rota de teste para verificar se a busca de agendamentos funciona"""
    try:
        print("=== TESTE SIMPLES DE AGENDA ===")
        
        # 1. Verificar se existem clientes na tabela
        print("1. Verificando clientes...")
        clientes = supabase.table('clientes').select('id, nome_cliente, id_usuario_cliente').limit(5).execute()
        print(f"   Total de clientes: {len(clientes.data) if clientes.data else 0}")
        
        if clientes.data:
            for cliente in clientes.data:
                print(f"   - Cliente {cliente['id']}: {cliente['nome_cliente']} (usuario: {cliente.get('id_usuario_cliente', 'N/A')})")
        
        # 2. Verificar se existem agendamentos na tabela
        print("\n2. Verificando agendamentos...")
        agendamentos = supabase.table('agenda').select('id, cliente_id, status, data, horario').limit(5).execute()
        print(f"   Total de agendamentos: {len(agendamentos.data) if agendamentos.data else 0}")
        
        if agendamentos.data:
            for agendamento in agendamentos.data:
                print(f"   - Agendamento {agendamento['id']}: Cliente {agendamento['cliente_id']}, Status {agendamento['status']}, Data {agendamento['data']}")
        
        # 3. Verificar se existem agendamentos ativos
        print("\n3. Verificando agendamentos ativos...")
        agendamentos_ativos = supabase.table('agenda').select('id, cliente_id, status, data, horario').eq('status', 'ativo').limit(5).execute()
        print(f"   Total de agendamentos ativos: {len(agendamentos_ativos.data) if agendamentos_ativos.data else 0}")
        
        if agendamentos_ativos.data:
            for agendamento in agendamentos_ativos.data:
                print(f"   - Agendamento ativo {agendamento['id']}: Cliente {agendamento['cliente_id']}, Data {agendamento['data']}")
        
        # 4. Testar busca específica por um cliente
        print("\n4. Testando busca por cliente específico...")
        if clientes.data and agendamentos_ativos.data:
            cliente_teste = clientes.data[0]
            agendamentos_cliente = supabase.table('agenda').select('*').eq('cliente_id', cliente_teste['id']).eq('status', 'ativo').execute()
            print(f"   Agendamentos ativos para cliente {cliente_teste['nome_cliente']} (ID: {cliente_teste['id']}): {len(agendamentos_cliente.data) if agendamentos_cliente.data else 0}")
        
        # 5. Verificar estrutura das tabelas relacionadas
        print("\n5. Verificando tabelas relacionadas...")
        
        # Serviços
        servicos = supabase.table('servicos').select('id, nome_servico').limit(3).execute()
        print(f"   Serviços disponíveis: {len(servicos.data) if servicos.data else 0}")
        
        # Usuários
        usuarios = supabase.table('usuarios').select('id, nome_usuario').limit(3).execute()
        print(f"   Usuários disponíveis: {len(usuarios.data) if usuarios.data else 0}")
        
        # Empresas
        empresas = supabase.table('empresa').select('id, nome_empresa').limit(3).execute()
        print(f"   Empresas disponíveis: {len(empresas.data) if empresas.data else 0}")
        
        resultado = {
            "status": "sucesso",
            "clientes_total": len(clientes.data) if clientes.data else 0,
            "agendamentos_total": len(agendamentos.data) if agendamentos.data else 0,
            "agendamentos_ativos": len(agendamentos_ativos.data) if agendamentos_ativos.data else 0,
            "servicos": len(servicos.data) if servicos.data else 0,
            "usuarios": len(usuarios.data) if usuarios.data else 0,
            "empresas": len(empresas.data) if empresas.data else 0
        }
        
        return jsonify(resultado), 200
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"erro": str(e)}), 500

@app.route('/teste_cliente_especifico/<int:cliente_id>', methods=['GET'])
def teste_cliente_especifico(cliente_id):
    """Testa a busca de agendamentos para um cliente específico"""
    try:
        print(f"=== TESTE CLIENTE ESPECÍFICO (ID: {cliente_id}) ===")
        
        # Buscar cliente
        cliente = supabase.table('clientes').select('*').eq('id', cliente_id).single().execute()
        if not cliente.data:
            return jsonify({"erro": "Cliente não encontrado"}), 404
        
        print(f"Cliente encontrado: {cliente.data['nome_cliente']}")
        
        # Buscar agendamentos do cliente
        agendamentos = supabase.table('agenda').select('*').eq('cliente_id', cliente_id).eq('status', 'ativo').execute()
        
        print(f"Agendamentos ativos encontrados: {len(agendamentos.data) if agendamentos.data else 0}")
        
        resultado = {
            "cliente": cliente.data,
            "agendamentos": agendamentos.data if agendamentos.data else []
        }
        
        return jsonify(resultado), 200
        
    except Exception as e:
        print(f"❌ Erro no teste específico: {e}")
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    print("Iniciando servidor de teste na porta 5001...")
    app.run(debug=True, port=5001) 