import mercadopago


def gerar_link_pagamento(plano, tipo="assinatura"):
    sdk = mercadopago.SDK("TEST-8366438482131716-012512-3295b15c4cfa4a66d28bda499ab5eeda-1360530545")

    planos = {
        "mensal": {"id": "1", "title": "Assinatura da Sua Agenda - 1 mês", "unit_price": 1},
        "trimestral": {"id": "2", "title": "Assinatura da Sua Agenda - 3 meses", "unit_price": 3},
        "anual": {"id": "3", "title": "Assinatura da Sua Agenda - 1 ano", "unit_price": 12}
    }

    if plano not in planos:
        raise ValueError("Plano inválido!")

    # Definir as URLs de redirecionamento com base no tipo de pagamento
    if tipo == "renovacao":
        back_urls = {
            "success": "http://www.suaagenda.fun/renovacaoconfirmada",
            "failure": "http://www.suaagenda.fun/pagamentonaoaprovado",
            "pending": "http://www.suaagenda.fun/pagamentonaoaprovado",
        }
    else:
        back_urls = {
            "success": "http://www.suaagenda.fun/pagamentoaprovado",
            "failure": "http://www.suaagenda.fun/pagamentonaoaprovado",
            "pending": "http://www.suaagenda.fun/pagamentonaoaprovado",
        }

    payment_data = {
        "items": [
            {
                "id": planos[plano]["id"],
                "title": planos[plano]["title"],
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": planos[plano]["unit_price"]
            }
        ],
        "back_urls": back_urls,
        "auto_return": "all",
        "payment_methods": {
            "excluded_payment_methods": [{"id": "pix"}]  # Bloquear Pix
        }
    }

    result = sdk.preference().create(payment_data)
    payment = result.get("response", {})
    return payment.get("init_point", "Link de pagamento não disponível")
