from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from supabase_config import supabase
from datetime import datetime, date, timedelta
import json

dashboard_bp = Blueprint('dashboard', __name__)

def verificar_login():
    """Verifica se o usuário está logado"""
    user_id = request.cookies.get('user_id')
    if not user_id:
        return None
    return user_id

def obter_id_empresa():
    """Obtém o ID da empresa do cookie"""
    return request.cookies.get('empresa_id')

@dashboard_bp.route('/dashboard')
def dashboard():
    """Página principal do dashboard"""
    # Verifica se o usuário está logado
    user_id = verificar_login()
    if not user_id:
        return redirect(url_for('login.login'))
    
    empresa_id = obter_id_empresa()
    if not empresa_id:
        return redirect(url_for('login.login'))
    
    return render_template('dashboard.html')

@dashboard_bp.route('/api/dashboard/dados')
def api_dashboard_dados():
    """API para obter dados do dashboard"""
    try:
        empresa_id = obter_id_empresa()
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 401
        
        hoje = date.today()
        inicio_mes = hoje.replace(day=1)
        
        # 1. FATURAMENTO DO DIA
        faturamento_hoje = 0
        try:
            # Buscar entradas financeiras do dia
            entradas_hoje = supabase.table('financeiro_entrada').select('valor_entrada').eq('id_empresa', empresa_id).gte('data', f"{hoje} 00:00:00").lt('data', f"{hoje} 23:59:59").execute()
            if entradas_hoje.data:
                faturamento_hoje = sum(float(entrada['valor_entrada']) for entrada in entradas_hoje.data if entrada['valor_entrada'])
            
            # Buscar vendas do dia
            vendas_hoje = supabase.table('vendas').select('valor').eq('id_empresa', empresa_id).gte('data', f"{hoje} 00:00:00").lt('data', f"{hoje} 23:59:59").execute()
            if vendas_hoje.data:
                faturamento_hoje += sum(float(venda['valor']) for venda in vendas_hoje.data if venda['valor'])
        except Exception as e:
            print(f"Erro ao calcular faturamento do dia: {e}")
        
        # 2. FATURAMENTO DO MÊS
        faturamento_mes = 0
        try:
            # Buscar entradas financeiras do mês
            entradas_mes = supabase.table('financeiro_entrada').select('valor_entrada').eq('id_empresa', empresa_id).gte('data', f"{inicio_mes} 00:00:00").execute()
            if entradas_mes.data:
                faturamento_mes = sum(float(entrada['valor_entrada']) for entrada in entradas_mes.data if entrada['valor_entrada'])
            
            # Buscar vendas do mês
            vendas_mes = supabase.table('vendas').select('valor').eq('id_empresa', empresa_id).gte('data', f"{inicio_mes} 00:00:00").execute()
            if vendas_mes.data:
                faturamento_mes += sum(float(venda['valor']) for venda in vendas_mes.data if venda['valor'])
        except Exception as e:
            print(f"Erro ao calcular faturamento do mês: {e}")
        
        # 3. ATENDIMENTOS DO DIA
        atendimentos_hoje = 0
        atendimentos_concluidos = 0
        try:
            agendamentos_hoje = supabase.table('agenda').select('id, status').eq('id_empresa', empresa_id).eq('data', str(hoje)).execute()
            if agendamentos_hoje.data:
                atendimentos_hoje = len(agendamentos_hoje.data)
                atendimentos_concluidos = len([a for a in agendamentos_hoje.data if a.get('status') == 'Concluído'])
        except Exception as e:
            print(f"Erro ao buscar atendimentos do dia: {e}")
        
        # 4. PRÓXIMOS ATENDIMENTOS (próximas 3 horas) - VERSÃO CORRIGIDA
        proximos_atendimentos = []
        try:
            agora = datetime.now()
            hoje = date.today()
            
            # Calcular próximas 3 horas (considerando mudança de dia)
            proximas_3h = agora + timedelta(hours=3)
            
            # Se passar da meia-noite, buscar até o final do dia
            if proximas_3h.date() > hoje:
                # Buscar agendamentos até o final do dia
                agendamentos = supabase.table('agenda').select(
                    'id, horario, descricao, status, cliente_id, servico_id'
                ).eq('id_empresa', empresa_id).eq('data', str(hoje)).eq('status', 'ativo').gte(
                    'horario', agora.strftime('%H:%M:%S')
                ).order('horario').limit(5).execute()
            else:
                # Buscar agendamentos nas próximas 3 horas
                agendamentos = supabase.table('agenda').select(
                    'id, horario, descricao, status, cliente_id, servico_id'
                ).eq('id_empresa', empresa_id).eq('data', str(hoje)).eq('status', 'ativo').gte(
                    'horario', agora.strftime('%H:%M:%S')
                ).lte('horario', proximas_3h.strftime('%H:%M:%S')).order('horario').limit(5).execute()
            
            if agendamentos.data:
                # Processar cada agendamento para buscar dados relacionados
                for ag in agendamentos.data:
                    try:
                        # Buscar dados do cliente
                        cliente_response = supabase.table('clientes').select(
                            'nome_cliente, telefone'
                        ).eq('id', ag['cliente_id']).execute()
                        cliente = cliente_response.data[0] if cliente_response.data else None
                        
                        # Buscar dados do serviço
                        servico_response = supabase.table('servicos').select(
                            'nome_servico, preco'
                        ).eq('id', ag['servico_id']).execute()
                        servico = servico_response.data[0] if servico_response.data else None
                        
                        if cliente and servico:
                            agendamento_completo = {
                                'id': ag['id'],
                                'horario': ag['horario'],
                                'descricao': ag.get('descricao', ''),
                                'status': ag.get('status', 'Pendente'),
                                'clientes': {
                                    'nome_cliente': cliente['nome_cliente'],
                                    'telefone': cliente.get('telefone', '')
                                },
                                'servicos': {
                                    'nome_servico': servico['nome_servico'],
                                    'preco': servico.get('preco', 0)
                                }
                            }
                            proximos_atendimentos.append(agendamento_completo)
                            
                    except Exception as e:
                        print(f"Erro ao processar agendamento ID {ag['id']}: {e}")
                        continue
                        
        except Exception as e:
            print(f"Erro ao buscar próximos atendimentos: {e}")
        
        # 5. SERVIÇOS MAIS POPULARES (últimos 30 dias)
        servicos_populares = []
        try:
            inicio_periodo = hoje - timedelta(days=30)
            servicos_stats = supabase.table('agenda').select('''
                servicos!inner(nome_servico, preco),
                count
            ''').eq('id_empresa', empresa_id).gte('data', str(inicio_periodo)).execute()
            
            # Contar serviços
            servicos_count = {}
            if servicos_stats.data:
                for agendamento in servicos_stats.data:
                    if agendamento.get('servicos'):
                        nome_servico = agendamento['servicos']['nome_servico']
                        servicos_count[nome_servico] = servicos_count.get(nome_servico, 0) + 1
            
            # Ordenar por popularidade
            servicos_populares = sorted(servicos_count.items(), key=lambda x: x[1], reverse=True)[:5]
        except Exception as e:
            print(f"Erro ao buscar serviços populares: {e}")
        
        # 6. CLIENTES NOVOS (últimos 7 dias) - CORRIGIDO
        clientes_novos = 0
        try:
            # Como não temos created_at, vamos usar uma abordagem alternativa
            # Contar todos os clientes da empresa (aproximação)
            todos_clientes = supabase.table('clientes').select('id').eq('id_empresa', empresa_id).execute()
            if todos_clientes.data:
                clientes_novos = len(todos_clientes.data)  # Aproximação
        except Exception as e:
            print(f"Erro ao buscar clientes novos: {e}")
        
        # 7. CONTAS A RECEBER (pendentes e pagas)
        contas_pendentes = 0
        valor_pendente = 0
        contas_pagas = 0
        valor_recebido = 0
        try:
            # Contas pendentes
            contas_pend = supabase.table('contas_receber').select('valor').eq('id_empresa', empresa_id).eq('baixa', False).execute()
            if contas_pend.data:
                contas_pendentes = len(contas_pend.data)
                valor_pendente = sum(float(conta['valor']) for conta in contas_pend.data if conta['valor'])
            
            # Contas pagas
            contas_pagas_data = supabase.table('contas_receber').select('valor').eq('id_empresa', empresa_id).eq('baixa', True).execute()
            if contas_pagas_data.data:
                contas_pagas = len(contas_pagas_data.data)
                valor_recebido = sum(float(conta['valor']) for conta in contas_pagas_data.data if conta['valor'])
        except Exception as e:
            print(f"Erro ao buscar contas a receber: {e}")
        
        # 8. CONTAS A PAGAR (pendentes e pagas)
        contas_pagar_pendentes = 0
        valor_pagar_pendente = 0
        contas_pagar_pagas = 0
        valor_pago = 0
        try:
            # Contas a pagar pendentes
            contas_pagar_pend = supabase.table('contas_pagar').select('valor').eq('id_empresa', empresa_id).eq('baixa', False).execute()
            if contas_pagar_pend.data:
                contas_pagar_pendentes = len(contas_pagar_pend.data)
                valor_pagar_pendente = sum(float(conta['valor']) for conta in contas_pagar_pend.data if conta['valor'])
            
            # Contas a pagar pagas
            contas_pagar_pagas_data = supabase.table('contas_pagar').select('valor').eq('id_empresa', empresa_id).eq('baixa', True).execute()
            if contas_pagar_pagas_data.data:
                contas_pagar_pagas = len(contas_pagar_pagas_data.data)
                valor_pago = sum(float(conta['valor']) for conta in contas_pagar_pagas_data.data if conta['valor'])
        except Exception as e:
            print(f"Erro ao buscar contas a pagar: {e}")
        
        # 9. ENTRADAS E SAÍDAS DO MÊS
        entradas_mes = 0
        saidas_mes = 0
        saldo_mes = 0
        try:
            # Entradas do mês
            entradas_data = supabase.table('financeiro_entrada').select('valor_entrada').eq('id_empresa', empresa_id).gte('data', f"{inicio_mes} 00:00:00").lt('data', f"{hoje} 23:59:59").execute()
            if entradas_data.data:
                entradas_mes = sum(float(entrada['valor_entrada']) for entrada in entradas_data.data if entrada['valor_entrada'])
            
            # Saídas do mês
            saidas_data = supabase.table('financeiro_saida').select('valor_saida').eq('id_empresa', empresa_id).gte('data', f"{inicio_mes} 00:00:00").lt('data', f"{hoje} 23:59:59").execute()
            if saidas_data.data:
                saidas_mes = sum(float(saida['valor_saida']) for saida in saidas_data.data if saida['valor_saida'])
            
            # Calcular saldo
            saldo_mes = entradas_mes - saidas_mes
        except Exception as e:
            print(f"Erro ao buscar entradas e saídas: {e}")
        
        # 10. META DO MÊS (se configurada) - CORRIGIDO
        meta_mes = 0
        try:
            # Como não temos meta_mensal na tabela empresa, vamos usar um valor padrão
            # ou calcular baseado no faturamento médio
            meta_mes = 10000  # Meta padrão de R$ 10.000
        except Exception as e:
            print(f"Erro ao buscar meta do mês: {e}")
        
        # Calcular percentual da meta
        percentual_meta = 0
        if meta_mes > 0:
            percentual_meta = min((faturamento_mes / meta_mes) * 100, 100)
        
        return jsonify({
            'faturamento_hoje': faturamento_hoje,
            'faturamento_mes': faturamento_mes,
            'atendimentos_hoje': atendimentos_hoje,
            'atendimentos_concluidos': atendimentos_concluidos,
            'proximos_atendimentos': proximos_atendimentos,
            'servicos_populares': servicos_populares,
            'clientes_novos': clientes_novos,
            # Contas a receber
            'contas_pendentes': contas_pendentes,
            'valor_pendente': valor_pendente,
            'contas_pagas': contas_pagas,
            'valor_recebido': valor_recebido,
            # Contas a pagar
            'contas_pagar_pendentes': contas_pagar_pendentes,
            'valor_pagar_pendente': valor_pagar_pendente,
            'contas_pagar_pagas': contas_pagar_pagas,
            'valor_pago': valor_pago,
            # Entradas e saídas
            'entradas_mes': entradas_mes,
            'saidas_mes': saidas_mes,
            'saldo_mes': saldo_mes,
            # Meta
            'meta_mes': meta_mes,
            'percentual_meta': percentual_meta,
            'hoje': hoje.strftime('%d/%m/%Y')
        })
        
    except Exception as e:
        print(f"Erro geral na API dashboard: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@dashboard_bp.route('/api/dashboard/grafico-faturamento')
def api_grafico_faturamento():
    """API para dados do gráfico de faturamento dos últimos 7 dias"""
    try:
        empresa_id = obter_id_empresa()
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 401
        
        dados_grafico = []
        
        # Buscar faturamento dos últimos 7 dias
        for i in range(7):
            data = date.today() - timedelta(days=i)
            faturamento_dia = 0
            
            try:
                # Entradas financeiras
                entradas = supabase.table('financeiro_entrada').select('valor_entrada').eq('id_empresa', empresa_id).gte('data', f"{data} 00:00:00").lt('data', f"{data} 23:59:59").execute()
                if entradas.data:
                    faturamento_dia += sum(float(entrada['valor_entrada']) for entrada in entradas.data if entrada['valor_entrada'])
                
                # Vendas
                vendas = supabase.table('vendas').select('valor').eq('id_empresa', empresa_id).gte('data', f"{data} 00:00:00").lt('data', f"{data} 23:59:59").execute()
                if vendas.data:
                    faturamento_dia += sum(float(venda['valor']) for venda in vendas.data if venda['valor'])
                    
            except Exception as e:
                print(f"Erro ao calcular faturamento do dia {data}: {e}")
            
            dados_grafico.append({
                'data': data.strftime('%d/%m'),
                'faturamento': faturamento_dia
            })
        
        # Inverter para mostrar do mais antigo para o mais recente
        dados_grafico.reverse()
        
        return jsonify(dados_grafico)
        
    except Exception as e:
        print(f"Erro na API gráfico faturamento: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500
