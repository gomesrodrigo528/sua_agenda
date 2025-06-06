import mercadopago


def gerar_link_pagamento(plano, tipo="assinatura"):
    sdk = mercadopago.SDK("TEST-1242682277274715-060519-40f45c2b119be74c36a87e6263c9f5e5-1360530545")

    planos = {
        "mensal": {
            "id": "1",
            "title": "Assinatura da Sua Agenda - 1 mês",
            "unit_price": 35.0
        },
        "trimestral": {
            "id": "2",
            "title": "Assinatura da Sua Agenda - 3 meses",
            "unit_price": 85.0
        },
        "anual": {
            "id": "3",
            "title": "Assinatura da Sua Agenda - 1 ano",
            "unit_price": 125.0
        }
    }

    if plano not in planos:
        raise ValueError("Plano inválido!")

    # Garantir que todas as URLs estejam presentes
    if tipo == "renovacao":
            back_urls = {
                "success": "https://sua-agenda-dihe.onrender.com/renovacaoconfirmada/<plano>",
                "failure": "https://sua-agenda-dihe.onrender.com/pagamentonaoaprovado/<plano>",
                "pending": "https://sua-agenda-dihe.onrender.com/pagamentonaoaprovado/<plano>",
            }
    else:
        back_urls = {
            "success": "https://sua-agenda-dihe.onrender.com/pagamentoaprovado/<plano>",
            "failure": "https://sua-agenda-dihe.onrender.com/pagamentonaoaprovado/<plano>",
            "pending": "https://sua-agenda-dihe.onrender.com/pagamentonaoaprovado/<plano>",
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
        "auto_return": "all",  # Correto e suportado pela API
        "payment_methods": {
            "pix": {
                "expires_after_days": 1
            }
        }
    }

    try:
        result = sdk.preference().create(payment_data)
        payment = result.get("response", {})
        init_point = payment.get("init_point")

        if not init_point:
            print("Erro ao gerar link de pagamento:", payment)
            return None

        return init_point

    except Exception as e:
        print("Erro na criação do pagamento:", e)
        return None
