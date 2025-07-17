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

def verificar_tabela_empresa():
    """Verifica a estrutura da tabela empresa"""
    print("=== ESTRUTURA DA TABELA EMPRESA ===")
    try:
        # Tentar buscar uma empresa para ver as colunas
        response = supabase.table('empresa').select('*').limit(1).execute()
        if response.data:
            empresa = response.data[0]
            print("Colunas encontradas:")
            for coluna in empresa.keys():
                print(f"  - {coluna}: {type(empresa[coluna]).__name__}")
        else:
            print("Tabela empresa está vazia")
    except Exception as e:
        print(f"Erro ao verificar tabela empresa: {e}")

def verificar_tabela_usuarios():
    """Verifica a estrutura da tabela usuarios"""
    print("\n=== ESTRUTURA DA TABELA USUARIOS ===")
    try:
        # Tentar buscar um usuário para ver as colunas
        response = supabase.table('usuarios').select('*').limit(1).execute()
        if response.data:
            usuario = response.data[0]
            print("Colunas encontradas:")
            for coluna in usuario.keys():
                print(f"  - {coluna}: {type(usuario[coluna]).__name__}")
        else:
            print("Tabela usuarios está vazia")
    except Exception as e:
        print(f"Erro ao verificar tabela usuarios: {e}")

def testar_insert_empresa():
    """Testa um insert simples na tabela empresa"""
    print("\n=== TESTE INSERT EMPRESA ===")
    try:
        dados_teste = {
            "nome_empresa": "EMPRESA TESTE",
            "cnpj": "12345678000199",
            "email_empresa": "teste@empresa.com",
            "descricao": "Empresa de teste",
            "tel_empresa": "(11) 99999-9999",
            "endereco": "Rua Teste, 123",
            "setor": "TECNOLOGIA",
            "cep": "01234-567",
            "dias_restantes": 30,
            "teste_de_app": True,
            "cidade": "SAO PAULO"
        }
        
        response = supabase.table("empresa").insert(dados_teste).execute()
        print(f"✅ Insert empresa bem-sucedido. ID: {response.data[0]['id']}")
        
        # Deletar o registro de teste
        supabase.table("empresa").delete().eq('id', response.data[0]['id']).execute()
        print("✅ Registro de teste removido")
        
    except Exception as e:
        print(f"❌ Erro no insert empresa: {e}")

def testar_insert_usuario():
    """Testa um insert simples na tabela usuarios"""
    print("\n=== TESTE INSERT USUARIO ===")
    try:
        # Primeiro, criar uma empresa para associar
        dados_empresa = {
            "nome_empresa": "EMPRESA TESTE USUARIO",
            "cnpj": "98765432000199",
            "email_empresa": "teste.usuario@empresa.com",
            "descricao": "Empresa para teste de usuário",
            "tel_empresa": "(11) 88888-8888",
            "endereco": "Rua Usuario, 456",
            "setor": "TECNOLOGIA",
            "cep": "01234-567",
            "dias_restantes": 30,
            "teste_de_app": True,
            "cidade": "SAO PAULO"
        }
        
        response_empresa = supabase.table("empresa").insert(dados_empresa).execute()
        empresa_id = response_empresa.data[0]['id']
        print(f"✅ Empresa criada para teste. ID: {empresa_id}")
        
        # Agora testar insert de usuário
        dados_usuario = {
            "nome_usuario": "USUARIO TESTE",
            "email": "usuario@teste.com",
            "telefone": "(11) 77777-7777",
            "senha": "senha123",
            "id_empresa": empresa_id
        }
        
        response_usuario = supabase.table("usuarios").insert(dados_usuario).execute()
        print(f"✅ Insert usuário bem-sucedido. ID: {response_usuario.data[0]['id']}")
        
        # Deletar os registros de teste
        supabase.table("usuarios").delete().eq('id', response_usuario.data[0]['id']).execute()
        supabase.table("empresa").delete().eq('id', empresa_id).execute()
        print("✅ Registros de teste removidos")
        
    except Exception as e:
        print(f"❌ Erro no insert usuário: {e}")

if __name__ == "__main__":
    print("Verificando estrutura do banco de dados...")
    
    verificar_tabela_empresa()
    verificar_tabela_usuarios()
    testar_insert_empresa()
    testar_insert_usuario()
    
    print("\n=== FIM DA VERIFICAÇÃO ===") 