#!/usr/bin/env python3
"""
Script de teste para verificar a lógica de cadastro de empresa e usuário
"""

import requests
import json

def test_cadastro_empresa():
    """Testa o cadastro de uma empresa nova"""
    print("=== TESTE: Cadastro de Empresa Nova ===")
    
    # Dados de teste
    dados_empresa = {
        'nome_empresa': 'EMPRESA TESTE LTDA',
        'cnpj': '12345678000199',
        'email': 'teste@empresa.com',
        'descricao': 'Empresa de teste',
        'setor': 'Tecnologia',
        'tel_empresa': '(11) 99999-9999',
        'endereco': 'Rua Teste, 123',
        'cep': '01234-567',
        'cidade': 'SAO PAULO'
    }
    
    # Simular POST para cadastro de empresa
    url = 'http://localhost:5000/pagamentoaprovado/teste'
    
    try:
        response = requests.post(url, data=dados_empresa)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}...")  # Primeiros 500 caracteres
        
        if response.status_code == 200:
            print("✅ Empresa cadastrada com sucesso")
            return True
        else:
            print("❌ Erro no cadastro da empresa")
            return False
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return False

def test_cadastro_usuario():
    """Testa o cadastro de usuário após empresa cadastrada"""
    print("\n=== TESTE: Cadastro de Usuário ===")
    
    # Dados de teste
    dados_usuario = {
        'nome_usuario': 'USUARIO TESTE',
        'email_usuario': 'usuario@teste.com',
        'telefone': '(11) 88888-8888',
        'senha': 'Senha123'
    }
    
    # Simular POST para cadastro de usuário
    url = 'http://localhost:5000/pagamentoaprovado/teste'
    
    try:
        response = requests.post(url, data=dados_usuario)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}...")  # Primeiros 500 caracteres
        
        if response.status_code == 200 and 'Login' in response.text:
            print("✅ Usuário cadastrado com sucesso - redirecionado para login")
            return True
        elif response.status_code == 302:
            print("✅ Usuário cadastrado com sucesso - redirecionado para login")
            return True
        else:
            print("❌ Erro no cadastro do usuário")
            return False
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return False

def test_empresa_existente():
    """Testa tentativa de cadastro de empresa que já existe"""
    print("\n=== TESTE: Empresa Já Existente ===")
    
    # Dados de empresa que já existe
    dados_empresa = {
        'nome_empresa': 'EMPRESA EXISTENTE LTDA',
        'cnpj': '12345678000199',  # Mesmo CNPJ do teste anterior
        'email': 'teste@empresa.com',  # Mesmo email do teste anterior
        'descricao': 'Empresa que já existe',
        'setor': 'Tecnologia',
        'tel_empresa': '(11) 77777-7777',
        'endereco': 'Rua Existente, 456',
        'cep': '01234-567',
        'cidade': 'SAO PAULO'
    }
    
    url = 'http://localhost:5000/pagamentoaprovado/teste'
    
    try:
        response = requests.post(url, data=dados_empresa)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        
        if response.status_code == 302:  # Redirecionamento para /adquirir
            print("✅ Empresa já existe - redirecionado corretamente")
            return True
        else:
            print("❌ Comportamento inesperado")
            return False
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return False

if __name__ == "__main__":
    print("Iniciando testes de cadastro...")
    
    # Teste 1: Cadastro de empresa nova
    sucesso_empresa = test_cadastro_empresa()
    
    if sucesso_empresa:
        # Teste 2: Cadastro de usuário
        sucesso_usuario = test_cadastro_usuario()
        
        if sucesso_usuario:
            print("\n✅ Todos os testes passaram!")
        else:
            print("\n❌ Falha no teste de usuário")
    else:
        print("\n❌ Falha no teste de empresa")
    
    # Teste 3: Tentativa de cadastro de empresa existente
    test_empresa_existente()
    
    print("\n=== FIM DOS TESTES ===") 