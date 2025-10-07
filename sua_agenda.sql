-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.agenda (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  data date,
  horario time without time zone,
  cliente_id bigint,
  usuario_id bigint,
  servico_id bigint,
  id_empresa bigint,
  descricao text,
  status character varying,
  visto boolean DEFAULT false,
  notificado boolean DEFAULT false,
  conta_receber boolean DEFAULT false,
  conta_pagar boolean DEFAULT false,
  CONSTRAINT agenda_pkey PRIMARY KEY (id),
  CONSTRAINT agenda_id_empresa_fkey FOREIGN KEY (id_empresa) REFERENCES public.empresa(id),
  CONSTRAINT agendamentos_cliente_id_fkey FOREIGN KEY (cliente_id) REFERENCES public.clientes(id),
  CONSTRAINT agendamentos_servico_id_fkey FOREIGN KEY (servico_id) REFERENCES public.servicos(id),
  CONSTRAINT agendamentos_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id),
  CONSTRAINT fk_cliente FOREIGN KEY (cliente_id) REFERENCES public.clientes(id),
  CONSTRAINT fk_servico FOREIGN KEY (servico_id) REFERENCES public.servicos(id),
  CONSTRAINT fk_usuario FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id)
);
CREATE TABLE public.auditoria (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  tabela character varying NOT NULL,
  operacao character varying NOT NULL,
  registro_id bigint,
  dados_antigos jsonb,
  dados_novos jsonb,
  usuario_id bigint,
  timestamp timestamp without time zone DEFAULT now(),
  CONSTRAINT auditoria_pkey PRIMARY KEY (id)
);
CREATE TABLE public.clientes (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  nome_cliente character varying,
  telefone numeric CHECK (telefone IS NULL OR telefone::text ~* '^[0-9]{10,11}$'::text),
  id_empresa bigint,
  id_usuario_cliente integer,
  CONSTRAINT clientes_pkey PRIMARY KEY (id),
  CONSTRAINT clientes_id_empresa_fkey FOREIGN KEY (id_empresa) REFERENCES public.empresa(id),
  CONSTRAINT clientes_id_usuario_cliente_fkey FOREIGN KEY (id_usuario_cliente) REFERENCES public.usuarios_clientes(id)
);
CREATE TABLE public.contas_pagar (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  id_empresa bigint,
  id_usuario bigint,
  data_vencimento timestamp without time zone,
  valor double precision,
  descricao text,
  baixa boolean DEFAULT false,
  plano_contas text,
  data_emissao date,
  id_agendamento_pagamento bigint,
  status text DEFAULT 'Pendente'::text,
  CONSTRAINT contas_pagar_pkey PRIMARY KEY (id),
  CONSTRAINT contas_pagar_id_agendamento_pagamento_fkey FOREIGN KEY (id_agendamento_pagamento) REFERENCES public.agenda(id),
  CONSTRAINT contas_pagar_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.usuarios(id),
  CONSTRAINT contas_pagar_id_empresa_fkey FOREIGN KEY (id_empresa) REFERENCES public.empresa(id)
);
CREATE TABLE public.contas_receber (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  id_empresa bigint,
  id_cliente bigint,
  id_venda bigint,
  id_agendamento bigint,
  id_usuario bigint,
  data_vencimento timestamp without time zone,
  valor double precision,
  descricao text,
  baixa boolean DEFAULT false,
  plano_contas text,
  data_emissao date,
  id_agendamento_pagamento bigint,
  status text DEFAULT 'Pendente'::text,
  CONSTRAINT contas_receber_pkey PRIMARY KEY (id),
  CONSTRAINT contas_receber_id_empresa_fkey FOREIGN KEY (id_empresa) REFERENCES public.empresa(id),
  CONSTRAINT contas_receber_id_cliente_fkey FOREIGN KEY (id_cliente) REFERENCES public.clientes(id),
  CONSTRAINT contas_receber_id_venda_fkey FOREIGN KEY (id_venda) REFERENCES public.vendas(id),
  CONSTRAINT contas_receber_id_agendamento_fkey FOREIGN KEY (id_agendamento) REFERENCES public.agenda(id),
  CONSTRAINT contas_receber_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.usuarios(id),
  CONSTRAINT contas_receber_id_agendamento_pagamento_fkey FOREIGN KEY (id_agendamento_pagamento) REFERENCES public.agenda(id)
);
CREATE TABLE public.empresa (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  nome_empresa text NOT NULL UNIQUE,
  cnpj text UNIQUE CHECK (cnpj IS NULL OR cnpj ~* '^[0-9]{2}\.[0-9]{3}\.[0-9]{3}/[0-9]{4}-[0-9]{2}$'::text),
  email text DEFAULT 'sua.agenda.notificacoes@gmail.com'::text CHECK (email IS NULL OR email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'::text),
  senha_app text DEFAULT 'bous nxkb ynqz uiiy'::text,
  setor text,
  descricao text,
  logo text DEFAULT 'https://gccxbkoejigwkqwyvcav.supabase.co/storage/v1/object/public/LOGOS/sua%20agenda.png?t=2025-01-08T15%3A15%3A52.477Z'::text,
  status boolean DEFAULT true,
  cor_emp text DEFAULT '#030413'::text,
  tel_empresa text,
  kids boolean NOT NULL DEFAULT false,
  acessibilidade boolean NOT NULL DEFAULT false,
  estacionamento boolean NOT NULL DEFAULT false,
  wifi boolean NOT NULL DEFAULT false,
  horario text NOT NULL DEFAULT 'De Segunda a sexta das 8hrs as 18hrs'::text,
  dias_restantes integer,
  teste_de_app boolean DEFAULT false,
  acesso boolean DEFAULT true,
  cep text CHECK (cep IS NULL OR cep ~* '^[0-9]{5}-?[0-9]{3}$'::text),
  endereco text,
  email_empresa text UNIQUE CHECK (email_empresa IS NULL OR email_empresa ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'::text),
  cidade text,
  data_cadastro date,
  CONSTRAINT empresa_pkey PRIMARY KEY (id)
);
CREATE TABLE public.finalizados (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  meio_pagamento text NOT NULL,
  valor double precision,
  id_agenda bigint,
  id_empresa bigint,
  data_hora_finalizacao timestamp without time zone,
  CONSTRAINT finalizados_pkey PRIMARY KEY (id),
  CONSTRAINT finalizados_id_agenda_fkey FOREIGN KEY (id_agenda) REFERENCES public.agenda(id),
  CONSTRAINT finalizados_id_empresa_fkey FOREIGN KEY (id_empresa) REFERENCES public.empresa(id)
);
CREATE TABLE public.financeiro_entrada (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  data timestamp without time zone NOT NULL,
  valor_entrada real,
  motivo text,
  id_empresa bigint,
  id_usuario bigint,
  id_cliente bigint,
  id_agenda bigint,
  meio_pagamento text,
  id_servico bigint,
  CONSTRAINT financeiro_entrada_pkey PRIMARY KEY (id),
  CONSTRAINT financeiro entrada_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.usuarios(id),
  CONSTRAINT financeiro entrada_id_empresa_fkey FOREIGN KEY (id_empresa) REFERENCES public.empresa(id),
  CONSTRAINT financeiro_entrada_id_cliente_fkey FOREIGN KEY (id_cliente) REFERENCES public.clientes(id),
  CONSTRAINT financeiro_entrada_id_agenda_fkey FOREIGN KEY (id_agenda) REFERENCES public.agenda(id),
  CONSTRAINT financeiro_entrada_id_servico_fkey FOREIGN KEY (id_servico) REFERENCES public.servicos(id)
);
CREATE TABLE public.financeiro_saida (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  data timestamp without time zone NOT NULL,
  valor_saida real,
  motivo text,
  id_empresa bigint,
  id_usuario bigint,
  meio_pagamento text,
  CONSTRAINT financeiro_saida_pkey PRIMARY KEY (id),
  CONSTRAINT financeiro saida_id_empresa_fkey FOREIGN KEY (id_empresa) REFERENCES public.empresa(id),
  CONSTRAINT financeiro saida_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.usuarios(id)
);
CREATE TABLE public.plano_contas (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  decricao text,
  tipo text,
  CONSTRAINT plano_contas_pkey PRIMARY KEY (id)
);
CREATE TABLE public.produtos (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  nome_produto text,
  preco real CHECK (preco > 0::double precision),
  estoque real CHECK (estoque >= 0::double precision),
  grupo text,
  id_empresa bigint,
  preco_custo real CHECK (preco_custo >= 0::double precision),
  cod_barras numeric,
  identificador_empresa bigint,
  status boolean DEFAULT true,
  un_medida text,
  UUID_IMG text UNIQUE,
  CONSTRAINT produtos_pkey PRIMARY KEY (id),
  CONSTRAINT produtos_id_empresa_fkey FOREIGN KEY (id_empresa) REFERENCES public.empresa(id)
);
CREATE TABLE public.push_subscriptions (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  endpoint text NOT NULL,
  keys jsonb NOT NULL,
  created_at timestamp without time zone DEFAULT now(),
  subscription jsonb,
  user_id bigint,
  CONSTRAINT push_subscriptions_pkey PRIMARY KEY (id),
  CONSTRAINT push_subscriptions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.usuarios(id)
);
CREATE TABLE public.servicos (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  nome_servico character varying,
  preco real CHECK (preco > 0::double precision),
  tempo character varying,
  id_empresa bigint,
  id_usuario bigint,
  disp_cliente boolean DEFAULT true,
  status boolean DEFAULT true,
  CONSTRAINT servicos_pkey PRIMARY KEY (id),
  CONSTRAINT servicos_id_empresa_fkey FOREIGN KEY (id_empresa) REFERENCES public.empresa(id),
  CONSTRAINT servicos_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.usuarios(id)
);
CREATE TABLE public.usuarios (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  nome_usuario character varying,
  senha character varying CHECK (char_length(senha::text) >= 6),
  email text UNIQUE CHECK (email IS NULL OR email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'::text),
  telefone character varying CHECK (telefone IS NULL OR telefone::text ~* '^[0-9]{10,11}$'::text),
  id_empresa bigint,
  ft_perfil text,
  CONSTRAINT usuarios_pkey PRIMARY KEY (id),
  CONSTRAINT usuarios_id_empresa_fkey FOREIGN KEY (id_empresa) REFERENCES public.empresa(id)
);
CREATE TABLE public.usuarios_clientes (
  id integer NOT NULL DEFAULT nextval('usuarios_clientes_id_seq'::regclass),
  email text NOT NULL UNIQUE CHECK (email IS NULL OR email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'::text),
  senha text NOT NULL CHECK (char_length(senha) >= 6),
  nome text,
  telefone text,
  status boolean DEFAULT true,
  created_at timestamp without time zone DEFAULT now(),
  CONSTRAINT usuarios_clientes_pkey PRIMARY KEY (id)
);
CREATE TABLE public.venda_itens (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  id_venda bigint NOT NULL,
  id_produto bigint NOT NULL,
  quantidade integer NOT NULL CHECK (quantidade > 0),
  valor_unitario double precision NOT NULL CHECK (valor_unitario >= 0::double precision),
  subtotal bigint,
  CONSTRAINT venda_itens_pkey PRIMARY KEY (id),
  CONSTRAINT venda_itens_id_venda_fkey FOREIGN KEY (id_venda) REFERENCES public.vendas(id),
  CONSTRAINT venda_itens_id_produto_fkey FOREIGN KEY (id_produto) REFERENCES public.produtos(id)
);
CREATE TABLE public.vendas (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  data timestamp without time zone NOT NULL,
  id_usuario bigint,
  id_empresa bigint,
  id_produto bigint,
  valor double precision,
  observacao text,
  plano_contas text,
  meio_pagamento text,
  id_cliente bigint,
  CONSTRAINT vendas_pkey PRIMARY KEY (id),
  CONSTRAINT vendas_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.usuarios(id),
  CONSTRAINT vendas_id_empresa_fkey FOREIGN KEY (id_empresa) REFERENCES public.empresa(id),
  CONSTRAINT vendas_id_produto_fkey FOREIGN KEY (id_produto) REFERENCES public.produtos(id),
  CONSTRAINT vendas_id_cliente_fkey FOREIGN KEY (id_cliente) REFERENCES public.clientes(id)
);