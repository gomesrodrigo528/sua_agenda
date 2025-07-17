#!/usr/bin/env python3
"""
Script de teste para verificar as rotas de agenda_cliente
"""

import requests
import json

# Configuração
BASE_URL = "http://localhost:5000"  # Ajuste conforme necessário

def test_login_cliente():
    """Testa o login do cliente"""
    print("=== Testando Login do Cliente ===")
    
    # Dados de teste (ajuste conforme seus dados)
    login_data = {
        'email': 'cliente@teste.com',  # Ajuste para um email válido
        'senha': '123456'  # Ajuste para uma senha válida
    }
    
    try:
        response = requests.post(f"{BASE_URL}/login_cliente", data=login_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Login bem-sucedido!")
                return True
            else:
                print("❌ Login falhou:", data.get('message'))
                return False
        else:
            print("❌ Erro no login:", response.status_code)
            return False
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return False

def test_agenda_cliente_api():
    """Testa a API de agenda_cliente"""
    print("\n=== Testando API de Agenda Cliente ===")
    
    # Primeiro fazer login para obter cookies
    login_data = {
        'email': 'cliente@teste.com',  # Ajuste para um email válido
        'senha': '123456'  # Ajuste para uma senha válida
    }
    
    try:
        # Fazer login
        login_response = requests.post(f"{BASE_URL}/login_cliente", data=login_data)
        if login_response.status_code != 200:
            print("❌ Falha no login para teste da API")
            return False
        
        # Obter cookies da sessão
        cookies = login_response.cookies
        
        # Testar a API de agenda_cliente
        api_response = requests.get(f"{BASE_URL}/api/agenda_cliente", cookies=cookies)
        print(f"Status: {api_response.status_code}")
        print(f"Response: {api_response.text}")
        
        if api_response.status_code == 200:
            data = api_response.json()
            print("✅ API funcionando!")
            print(f"Dados recebidos: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return True
        else:
            print("❌ Erro na API:", api_response.status_code)
            return False
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return False

def test_agenda_cliente_page():
    """Testa a página de agenda_cliente"""
    print("\n=== Testando Página de Agenda Cliente ===")
    
    # Primeiro fazer login para obter cookies
    login_data = {
        'email': 'cliente@teste.com',  # Ajuste para um email válido
        'senha': '123456'  # Ajuste para uma senha válida
    }
    
    try:
        # Fazer login
        login_response = requests.post(f"{BASE_URL}/login_cliente", data=login_data)
        if login_response.status_code != 200:
            print("❌ Falha no login para teste da página")
            return False
        
        # Obter cookies da sessão
        cookies = login_response.cookies
        
        # Testar a página de agenda_cliente
        page_response = requests.get(f"{BASE_URL}/agenda_cliente", cookies=cookies)
        print(f"Status: {page_response.status_code}")
        
        if page_response.status_code == 200:
            print("✅ Página carregada com sucesso!")
            print(f"Tamanho da resposta: {len(page_response.text)} caracteres")
            return True
        else:
            print("❌ Erro na página:", page_response.status_code)
            return False
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return False

def main():
    """Função principal de teste"""
    print("Iniciando testes das rotas de agenda_cliente...")
    
    # Testar login
    login_success = test_login_cliente()
    
    if login_success:
        # Testar API
        test_agenda_cliente_api()
        
        # Testar página
        test_agenda_cliente_page()
    else:
        print("❌ Login falhou, pulando outros testes")
    
    print("\n=== Testes Concluídos ===")

if __name__ == "__main__":
    main() 