def obter_servico_padrao_financeiro(supabase, id_empresa, tipo="conta_receber"):
    """
    Obtém ou cria um serviço padrão para operações financeiras.
    
    Args:
        supabase: Cliente Supabase
        id_empresa: ID da empresa
        tipo: "conta_receber" ou "conta_pagar"
    
    Returns:
        ID do serviço padrão
    """
    try:
        # Nomes dos serviços padrão
        nome_servico = "Conta a Receber" if tipo == "conta_receber" else "Conta a Pagar"
        
        # Buscar serviço existente
        response = supabase.table('servicos').select('id').eq('id_empresa', id_empresa).eq('nome_servico', nome_servico).execute()
        
        if response.data:
            return response.data[0]['id']
        
        # Se não existir, criar um novo serviço padrão
        novo_servico = supabase.table('servicos').insert({
            'nome_servico': nome_servico,
            'preco': 0.0,  # Preço 0 para serviços financeiros (constraint modificada)
            'tempo': '00:00',
            'id_empresa': id_empresa,
            'id_usuario': None,
            'disp_cliente': False,
            'status': True
        }).execute()
        
        if novo_servico.data:
            return novo_servico.data[0]['id']
        
        # Fallback: buscar qualquer serviço da empresa
        fallback = supabase.table('servicos').select('id').eq('id_empresa', id_empresa).limit(1).execute()
        if fallback.data:
            return fallback.data[0]['id']
        
        # Último fallback: retornar None (será tratado no código chamador)
        return None
        
    except Exception as e:
        print(f"Erro ao obter serviço padrão financeiro: {e}")
        return None
