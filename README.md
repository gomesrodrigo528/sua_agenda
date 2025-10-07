# Sua Agenda - Sistema de Gestão de Agendamentos

## 🔧 Configuração do Ambiente

### 1. Instalação das Dependências

```bash
pip install -r requirements.txt
```

### 2. Configuração das Variáveis de Ambiente

1. Copie o arquivo `env.example` para `.env`:
```bash
cp env.example .env
```

2. Preencha o arquivo `.env` com suas credenciais:

```env
# Flask
FLASK_SECRET_KEY=sua_chave_secreta_aqui

# Supabase
SUPABASE_URL=https://gccxbkoejigwkqwyvcav.supabase.co
SUPABASE_KEY=sua_chave_supabase_aqui

# MercadoPago
MERCADOPAGO_ACCESS_TOKEN=seu_token_mercadopago_aqui

# Email (SMTP) - Opcional
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=seu_email_aqui
SMTP_PASSWORD=sua_senha_app_aqui

# Push Notifications - Opcional
VAPID_PRIVATE_KEY=sua_chave_privada_vapid_aqui
VAPID_PUBLIC_KEY=sua_chave_publica_vapid_aqui
```

### 3. Executar a Aplicação

```bash
python main.py
```

A aplicação estará disponível em `http://localhost:5000`

## 🔒 Segurança

⚠️ **IMPORTANTE**: Nunca commite o arquivo `.env` no repositório. Ele contém informações sensíveis.

## 📋 Variáveis Obrigatórias

- `SUPABASE_KEY`: Chave de API do Supabase
- `MERCADOPAGO_ACCESS_TOKEN`: Token de acesso do MercadoPago

## 📋 Variáveis Opcionais

- `FLASK_SECRET_KEY`: Chave secreta do Flask (gerada automaticamente se não fornecida)
- `SMTP_*`: Configurações de email para envio de notificações
- `VAPID_*`: Chaves para push notifications

## 🚀 Deploy

Para deploy no Render.com, configure as variáveis de ambiente diretamente no painel do Render.
