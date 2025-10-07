# 📊 Dashboard Principal - Sua Agenda

## 🎯 Visão Geral

O Dashboard Principal é uma página mobile-first que oferece uma visão completa do negócio, com métricas de faturamento, atendimentos e indicadores de performance em tempo real.

## 📱 Características Mobile-First

### Design Responsivo
- **Mobile**: Layout em colunas otimizado para telas pequenas
- **Tablet**: Grid 4x1 para métricas principais
- **Desktop**: Layout expandido com mais espaçamento

### Performance
- **Carregamento rápido**: Dados carregados via API
- **Atualização automática**: Refresh a cada 5 minutos
- **Cache inteligente**: Evita requisições desnecessárias

## 📊 Métricas Disponíveis

### 💰 Faturamento
- **Hoje**: Soma de entradas financeiras + vendas do dia
- **Mês**: Faturamento acumulado do mês atual
- **Meta**: Percentual de atingimento da meta mensal (se configurada)

### 📅 Atendimentos
- **Hoje**: Total de agendamentos do dia
- **Concluídos**: Quantidade de atendimentos finalizados
- **Próximos**: Atendimentos nas próximas 3 horas

### 📈 Indicadores
- **Serviços Populares**: Top 5 serviços dos últimos 30 dias
- **Clientes Novos**: Novos clientes dos últimos 7 dias
- **Contas a Receber**: Valor pendente de recebimento

## 🔧 Funcionalidades

### Gráfico de Faturamento
- **Período**: Últimos 7 dias
- **Tipo**: Gráfico de barras interativo
- **Biblioteca**: Chart.js
- **Responsivo**: Adapta-se ao tamanho da tela

### Ações Rápidas
- **Novo Agendamento**: Link direto para criação
- **Nova Venda**: Acesso rápido ao PDV
- **Novo Cliente**: Cadastro de clientes
- **Gerenciar Serviços**: Administração de serviços

### Atualização em Tempo Real
- **Refresh Manual**: Botão de atualização no header
- **Auto-refresh**: Atualização automática a cada 5 minutos
- **Indicador Visual**: Loading overlay durante carregamento

## 🛠️ Arquivos Criados

### Backend
- `routes/dashboard.py` - Rotas e lógica do dashboard
- `main.py` - Integração do blueprint

### Frontend
- `templates/dashboard.html` - Template HTML mobile-first
- `static/styles/dashboard.css` - Estilos responsivos
- `static/scripts/dashboard.js` - Interatividade e APIs

## 📡 APIs Disponíveis

### `/api/dashboard/dados`
Retorna todos os dados principais do dashboard:
```json
{
  "faturamento_hoje": 1500.00,
  "faturamento_mes": 25000.00,
  "atendimentos_hoje": 8,
  "atendimentos_concluidos": 5,
  "proximos_atendimentos": [...],
  "servicos_populares": [...],
  "clientes_novos": 3,
  "contas_pendentes": 5,
  "valor_pendente": 2000.00,
  "meta_mes": 30000.00,
  "percentual_meta": 83.33
}
```

### `/api/dashboard/grafico-faturamento`
Retorna dados para o gráfico dos últimos 7 dias:
```json
[
  {"data": "01/10", "faturamento": 1200.00},
  {"data": "02/10", "faturamento": 1500.00},
  ...
]
```

## 🎨 Design System

### Cores
- **Primary**: #667eea (Azul principal)
- **Success**: #28a745 (Verde para sucessos)
- **Info**: #17a2b8 (Azul para informações)
- **Warning**: #ffc107 (Amarelo para alertas)

### Tipografia
- **Títulos**: 1.5rem - 2rem (responsivo)
- **Métricas**: 1.4rem - 1.8rem (responsivo)
- **Labels**: 0.85rem
- **Subtítulos**: 0.75rem

### Espaçamento
- **Mobile**: 15px - 20px
- **Tablet**: 20px - 25px
- **Desktop**: 25px - 30px

## 📱 Responsividade

### Breakpoints
- **Mobile**: < 768px
- **Tablet**: 768px - 1024px
- **Desktop**: > 1024px

### Adaptações
- **Grid**: 2 colunas → 4 colunas
- **Cards**: Compactos → Expandidos
- **Gráficos**: Altura adaptável
- **Ações**: 2 colunas → 4 colunas

## 🚀 Como Usar

### Acesso
1. Faça login no sistema
2. O dashboard será a página inicial
3. Ou acesse diretamente: `/dashboard`

### Navegação
- **Header**: Data atual e botão de refresh
- **Métricas**: Cards com informações principais
- **Seções**: Links para páginas específicas
- **Ações**: Botões de acesso rápido

### Personalização
- **Meta Mensal**: Configure na tabela `empresa`
- **Serviços**: Gerencie na seção de serviços
- **Clientes**: Cadastre novos clientes

## 🔒 Segurança

### Autenticação
- Verificação de login obrigatória
- Validação de empresa via cookies
- Redirecionamento automático se não logado

### Dados
- Consultas otimizadas ao banco
- Tratamento de erros robusto
- Validação de entrada de dados

## 📊 Performance

### Otimizações
- **Lazy Loading**: Dados carregados sob demanda
- **Debounce**: Evita requisições excessivas
- **Cache**: Dados em memória por 5 minutos
- **Compressão**: Assets minificados

### Monitoramento
- **Tempo de Carregamento**: Logs de performance
- **Erros**: Tratamento e logging
- **Conectividade**: Detecção de offline/online

## 🎯 Próximas Melhorias

### Funcionalidades
- [ ] Notificações push para novos agendamentos
- [ ] Exportação de relatórios em PDF
- [ ] Filtros por período personalizado
- [ ] Comparação com períodos anteriores

### Performance
- [ ] Cache Redis para dados frequentes
- [ ] Compressão de imagens
- [ ] Service Worker para offline
- [ ] Lazy loading de componentes

### UX/UI
- [ ] Modo escuro
- [ ] Personalização de widgets
- [ ] Drag & drop para reorganizar
- [ ] Animações mais suaves

---

## 📞 Suporte

Para dúvidas ou problemas com o dashboard:
1. Verifique os logs do console do navegador
2. Teste a conectividade com o banco de dados
3. Confirme se todas as variáveis de ambiente estão configuradas
4. Consulte a documentação da API

**Dashboard criado com foco em mobile-first e performance! 🚀**
