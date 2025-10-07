#!/usr/bin/env python3
"""
Script para corrigir problemas de importação nos arquivos de rotas
"""

import os
import re

def corrigir_arquivo(caminho_arquivo):
    """Corrige um arquivo removendo configurações antigas do Supabase"""
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            linhas = f.readlines()
        
        linhas_corrigidas = []
        pular_linhas = False
        
        for i, linha in enumerate(linhas):
            # Se encontrar uma linha problemática, marcar para pular
            if re.search(r"supabase_key = os\.getenv", linha):
                pular_linhas = True
                continue
            
            # Se estiver pulando linhas e encontrar uma linha vazia ou comentário, parar de pular
            if pular_linhas and (linha.strip() == '' or linha.strip().startswith('#')):
                pular_linhas = False
                if linha.strip() == '':
                    continue
            
            # Se estiver pulando linhas, continuar pulando
            if pular_linhas:
                continue
            
            # Remover linhas com configurações antigas
            if re.search(r"supabase=create_client", linha):
                continue
            
            if re.search(r"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9", linha):
                continue
            
            if re.search(r"supabase_url =", linha):
                continue
            
            # Manter a linha
            linhas_corrigidas.append(linha)
        
        # Escrever arquivo corrigido
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            f.writelines(linhas_corrigidas)
        
        print(f"✅ Arquivo corrigido: {caminho_arquivo}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao corrigir {caminho_arquivo}: {e}")
        return False

def main():
    """Função principal"""
    print("🔧 Corrigindo arquivos de rotas...")
    
    # Lista de arquivos para corrigir
    arquivos_rotas = [
        'routes/agendamento.py',
        'routes/agenda_cliente.py', 
        'routes/contas_pagar.py',
        'routes/contas_receber.py',
        'routes/lembrete_email.py',
        'routes/produtos.py',
        'routes/push.py',
        'routes/relatorios.py',
        'routes/sucesso.py',
        'routes/tasks.py',
        'routes/vendas.py',
        'routes/check_health.py'
    ]
    
    sucessos = 0
    total = len(arquivos_rotas)
    
    for arquivo in arquivos_rotas:
        if os.path.exists(arquivo):
            if corrigir_arquivo(arquivo):
                sucessos += 1
        else:
            print(f"⚠️ Arquivo não encontrado: {arquivo}")
    
    print(f"\n📊 Resultado: {sucessos}/{total} arquivos corrigidos com sucesso")
    
    if sucessos == total:
        print("🎉 Todos os arquivos foram corrigidos!")
    else:
        print("⚠️ Alguns arquivos podem precisar de correção manual")

if __name__ == "__main__":
    main()

