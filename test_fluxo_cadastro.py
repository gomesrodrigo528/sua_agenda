import requests
import json
import time

def test_fluxo_cadastro():
    # Usar timestamp para garantir dados únicos
    timestamp = int(time.time())
    base_url = "http://localhost:5000"
    
    print("=== TESTE DO FLUXO DE CADASTRO ===")
    
    # 1. Testar acesso à página de pagamento aprovado
    print("\n1. Testando acesso à página de pagamento aprovado...")
    response = requests.get(f"{base_url}/pagamentoaprovado/teste")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Página acessível")
    else:
        print("❌ Erro ao acessar página")
        return
    
    # 2. Testar cadastro de empresa
    print("\n2. Testando cadastro de empresa...")
    dados_empresa = {
        "nome_empresa": f"EMPRESA TESTE {timestamp} LTDA",
        "cnpj": f"12345678{timestamp % 10000:04d}",
        "email": f"teste{timestamp}@empresa.com",
        "descricao": "Empresa de teste",
        "setor": "Tecnologia",
        "tel_empresa": "11999999999",
        "endereco": "Rua Teste, 123",
        "cep": "01234567",
        "cidade": "SAO PAULO"
    }
    
    response = requests.post(
        f"{base_url}/pagamentoaprovado/teste",
        headers={"Content-Type": "application/json"},
        json=dados_empresa
    )
    
    print(f"Status: {response.status_code}")
    print(f"Resposta: {response.text}")
    
    if response.status_code == 201:
        data = response.json()
        if data.get("success"):
            empresa_id = data.get("empresa_id")
            print(f"✅ Empresa cadastrada com ID: {empresa_id}")
            
            # 3. Testar cadastro de usuário
            print("\n3. Testando cadastro de usuário...")
            dados_usuario = {
                "nome_usuario": f"USUARIO TESTE {timestamp}",
                "email_usuario": f"usuario{timestamp}@teste.com",
                "telefone": "11988888888",
                "senha": "Senha123",
                "empresa_id": empresa_id
            }
            
            response = requests.post(
                f"{base_url}/pagamentoaprovado/teste",
                headers={"Content-Type": "application/json"},
                json=dados_usuario
            )
            
            print(f"Status: {response.status_code}")
            print(f"Resposta: {response.text}")
            
            if response.status_code == 201:
                data = response.json()
                if data.get("success"):
                    print("✅ Usuário cadastrado com sucesso!")
                else:
                    print(f"❌ Erro ao cadastrar usuário: {data.get('error')}")
            else:
                print(f"❌ Erro HTTP ao cadastrar usuário: {response.status_code}")
        else:
            print(f"❌ Erro ao cadastrar empresa: {data.get('error')}")
    else:
        print(f"❌ Erro HTTP ao cadastrar empresa: {response.status_code}")

if __name__ == "__main__":
    test_fluxo_cadastro() 