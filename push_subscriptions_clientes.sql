-- Adicionar tabela para push subscriptions de clientes
CREATE TABLE public.push_subscriptions_clientes (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  endpoint text NOT NULL,
  keys jsonb NOT NULL,
  created_at timestamp without time zone DEFAULT now(),
  subscription jsonb,
  cliente_id integer,
  CONSTRAINT push_subscriptions_clientes_pkey PRIMARY KEY (id),
  CONSTRAINT push_subscriptions_clientes_cliente_id_fkey FOREIGN KEY (cliente_id) REFERENCES public.usuarios_clientes(id)
);
