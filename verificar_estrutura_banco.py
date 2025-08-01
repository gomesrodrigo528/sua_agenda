#!/usr/bin/env python3
"""
Script para verificar a estrutura das tabelas do banco de dados
"""

from supabase import create_client
import os

# Configuração do Supabase
supabase_url = 'https://gccxbkoejigwkqwyvcav.supabase.co'
supabase_key = os.getenv(
    'SUPABASE_KEY',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdjY3hia29lamlnd2txd3l2Y2F2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzM2OTg5OTYsImV4cCI6MjA0OTI3NDk5Nn0.ADRY3SLagP-NjhAAvRRP8A4Ogvo7AbWvcW-J5gAbyr4'
)
supabase = create_client(supabase_url, supabase_key)

def verificar_tabelas():
    print("=== VERIFICAÇÃO DA ESTRUTURA DO BANCO ===")
    
    # Lista de tabelas para verificar
    tabelas = ['vendas', 'venda_itens', 'produtos', 'clientes']
    
    for tabela in tabelas:
        print(f"\n--- Verificando tabela: {tabela} ---")
        try:
            # Tenta buscar alguns registros para verificar se a tabela existe
            response = supabase.table(tabela).select("*").limit(1).execute()
            print(f"✅ Tabela {tabela} existe")
            print(f"   Registros encontrados: {len(response.data) if response.data else 0}")
            
            # Se há dados, mostra a estrutura do primeiro registro
            if response.data and len(response.data) > 0:
                primeiro_registro = response.data[0]
                print(f"   Estrutura do primeiro registro:")
                for campo, valor in primeiro_registro.items():
                    print(f"     {campo}: {type(valor).__name__} = {valor}")
        except Exception as e:
            print(f"❌ Erro ao acessar tabela {tabela}: {str(e)}")

def verificar_venda_recente():
    print("\n=== VERIFICANDO VENDA MAIS RECENTE ===")
    try:
        # Busca a venda mais recente
        vendas = supabase.table("vendas").select("*").order("id", desc=True).limit(1).execute()
        
        if vendas.data and len(vendas.data) > 0:
            venda = vendas.data[0]
            print(f"Venda mais recente: ID {venda['id']}")
            print(f"Data: {venda.get('data')}")
            print(f"Valor: {venda.get('valor')}")
            print(f"Cliente: {venda.get('id_cliente')}")
            
            # Busca os itens desta venda
            itens = supabase.table("venda_itens").select("*").eq("id_venda", venda['id']).execute()
            print(f"Itens da venda: {len(itens.data) if itens.data else 0}")
            
            if itens.data:
                for item in itens.data:
                    print(f"  - Produto ID: {item.get('id_produto')}, Qtd: {item.get('quantidade')}, Valor: {item.get('valor_unitario')}")
            else:
                print("  Nenhum item encontrado para esta venda!")
        else:
            print("Nenhuma venda encontrada no banco")
            
    except Exception as e:
        print(f"Erro ao verificar venda recente: {str(e)}")

def testar_insercao_item():
    print("\n=== TESTANDO INSERÇÃO DE ITEM ===")
    try:
        # Busca uma venda existente
        vendas = supabase.table("vendas").select("id").limit(1).execute()
        
        if vendas.data and len(vendas.data) > 0:
            venda_id = vendas.data[0]['id']
            
            # Busca um produto existente
            produtos = supabase.table("produtos").select("id").limit(1).execute()
            
            if produtos.data and len(produtos.data) > 0:
                produto_id = produtos.data[0]['id']
                
                # Tenta inserir um item de teste
                item_teste = {
                    "id_venda": venda_id,
                    "id_produto": produto_id,
                    "quantidade": 1,
                    "valor_unitario": 1000,  # 10.00 em centavos
                    "subtotal": 1000  # 10.00 em centavos
                }
                
                print(f"Tentando inserir item de teste: {item_teste}")
                response = supabase.table("venda_itens").insert(item_teste).execute()
                
                if response.data:
                    print("✅ Inserção de teste bem-sucedida!")
                    print(f"Item inserido: {response.data}")
                    
                    # Remove o item de teste
                    supabase.table("venda_itens").delete().eq("id", response.data[0]['id']).execute()
                    print("Item de teste removido")
                else:
                    print("❌ Falha na inserção de teste")
            else:
                print("Nenhum produto encontrado para teste")
        else:
            print("Nenhuma venda encontrada para teste")
            
    except Exception as e:
        print(f"Erro no teste de inserção: {str(e)}")

if __name__ == "__main__":
    verificar_tabelas()
    verificar_venda_recente()
    testar_insercao_item() 