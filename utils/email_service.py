from flask import Blueprint
from supabase_config import supabase
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import os

email_bp = Blueprint('email', __name__)

class EmailService:
    """Serviço centralizado para envio de emails com templates HTML"""
    
    @staticmethod
    def enviar_email(destinatario, assunto, template_html, email_remetente, senha_remetente):
        """Envia email com template HTML"""
        try:
            servidor_smtp = 'smtp.gmail.com'
            porta_smtp = 587

            # Configuração da mensagem
            msg = MIMEMultipart('alternative')
            msg['From'] = email_remetente
            msg['To'] = destinatario
            msg['Subject'] = assunto

            # Adicionar conteúdo HTML
            html_part = MIMEText(template_html, 'html', 'utf-8')
            msg.attach(html_part)

            # Envio do e-mail
            with smtplib.SMTP(servidor_smtp, porta_smtp) as servidor:
                servidor.starttls()
                servidor.login(email_remetente, senha_remetente)
                servidor.send_message(msg)

            print(f"E-mail enviado com sucesso para {destinatario}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"Erro de autenticação: {e}")
            return False
        except smtplib.SMTPException as e:
            print(f"Erro ao enviar e-mail: {e}")
            return False
        except Exception as e:
            print(f"Erro inesperado ao enviar e-mail: {e}")
            return False

    @staticmethod
    def criar_template_agendamento(tipo, dados):
        """Cria template HTML para emails de agendamento"""
        
        # Cores e estilos
        cor_primaria = "#667eea"
        cor_secundaria = "#764ba2"
        cor_sucesso = "#28a745"
        cor_erro = "#dc3545"
        cor_info = "#17a2b8"
        
        if tipo == "novo_agendamento_cliente":
            cor_tema = cor_sucesso
            icone = "✅"
            titulo = "Agendamento Confirmado!"
            mensagem_principal = f"Seu agendamento foi confirmado com sucesso!"
            
        elif tipo == "novo_agendamento_profissional":
            cor_tema = cor_info
            icone = "📅"
            titulo = "Novo Agendamento"
            mensagem_principal = f"Você recebeu um novo agendamento!"
            
        elif tipo == "cancelamento_cliente":
            cor_tema = cor_erro
            icone = "❌"
            titulo = "Agendamento Cancelado"
            mensagem_principal = f"Seu agendamento foi cancelado."
            
        elif tipo == "cancelamento_profissional":
            cor_tema = cor_erro
            icone = "⚠️"
            titulo = "Agendamento Cancelado"
            mensagem_principal = f"Um agendamento foi cancelado."
            
        else:
            cor_tema = cor_primaria
            icone = "📧"
            titulo = "Notificação"
            mensagem_principal = "Você recebeu uma notificação."
        
        template = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{titulo}</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background-color: #f8f9fa;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, {cor_tema} 0%, {cor_secundaria} 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                    font-weight: 600;
                }}
                .header .icon {{
                    font-size: 48px;
                    margin-bottom: 15px;
                    display: block;
                }}
                .content {{
                    padding: 30px;
                }}
                .message {{
                    background-color: #f8f9fa;
                    border-left: 4px solid {cor_tema};
                    padding: 20px;
                    margin: 20px 0;
                    border-radius: 0 8px 8px 0;
                }}
                .details {{
                    background-color: #ffffff;
                    border: 1px solid #e9ecef;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .detail-row {{
                    display: flex;
                    justify-content: space-between;
                    padding: 8px 0;
                    border-bottom: 1px solid #f1f3f4;
                }}
                .detail-row:last-child {{
                    border-bottom: none;
                }}
                .detail-label {{
                    font-weight: 600;
                    color: #495057;
                }}
                .detail-value {{
                    color: #212529;
                }}
                .footer {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    color: #6c757d;
                    font-size: 14px;
                }}
                .footer a {{
                    color: {cor_tema};
                    text-decoration: none;
                }}
                .footer a:hover {{
                    text-decoration: underline;
                }}
                .button {{
                    display: inline-block;
                    background: linear-gradient(135deg, {cor_tema} 0%, {cor_secundaria} 100%);
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: 600;
                    margin: 20px 0;
                }}
                .justificativa {{
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                    border-radius: 6px;
                    padding: 15px;
                    margin: 15px 0;
                }}
                .justificativa-label {{
                    font-weight: 600;
                    color: #856404;
                    margin-bottom: 8px;
                }}
                .justificativa-text {{
                    color: #856404;
                    font-style: italic;
                }}
                @media (max-width: 600px) {{
                    .container {{
                        margin: 10px;
                        border-radius: 8px;
                    }}
                    .header, .content {{
                        padding: 20px;
                    }}
                    .detail-row {{
                        flex-direction: column;
                    }}
                    .detail-label {{
                        margin-bottom: 4px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <span class="icon">{icone}</span>
                    <h1>{titulo}</h1>
                </div>
                
                <div class="content">
                    <div class="message">
                        <p style="margin: 0; font-size: 16px;">{mensagem_principal}</p>
                    </div>
                    
                    <div class="details">
                        <div class="detail-row">
                            <span class="detail-label">Serviço:</span>
                            <span class="detail-value">{dados.get('servico', 'N/A')}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Data:</span>
                            <span class="detail-value">{dados.get('data', 'N/A')}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Horário:</span>
                            <span class="detail-value">{dados.get('horario', 'N/A')}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Cliente:</span>
                            <span class="detail-value">{dados.get('cliente', 'N/A')}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Profissional:</span>
                            <span class="detail-value">{dados.get('profissional', 'N/A')}</span>
                        </div>
                        {f'<div class="detail-row"><span class="detail-label">Valor:</span><span class="detail-value">R$ {dados.get("valor", "0,00")}</span></div>' if dados.get('valor') else ''}
                        {f'<div class="detail-row"><span class="detail-label">Descrição:</span><span class="detail-value">{dados.get("descricao", "")}</span></div>' if dados.get('descricao') else ''}
                    </div>
                    
                    {f'''
                    <div class="justificativa">
                        <div class="justificativa-label">Justificativa do Cancelamento:</div>
                        <div class="justificativa-text">{dados.get('justificativa', '')}</div>
                    </div>
                    ''' if tipo in ['cancelamento_cliente', 'cancelamento_profissional'] and dados.get('justificativa') else ''}
                    
                    <p style="margin-top: 30px; color: #6c757d; font-size: 14px;">
                        Em caso de dúvidas ou alterações, entre em contato conosco através dos nossos canais de atendimento.
                    </p>
                </div>
                
                <div class="footer">
                    <p style="margin: 0;">
                        Este é um e-mail automático do sistema Sua Agenda.<br>
                        <a href="#">Não responda a este e-mail</a>
                    </p>
                    <p style="margin: 10px 0 0 0; font-size: 12px;">
                        Enviado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return template

    @staticmethod
    def enviar_agendamento_cliente(dados_agendamento, empresa_email, empresa_senha):
        """Envia email de confirmação para o cliente"""
        template = EmailService.criar_template_agendamento("novo_agendamento_cliente", dados_agendamento)
        assunto = f"Agendamento Confirmado - {dados_agendamento.get('servico', 'Serviço')}"
        
        return EmailService.enviar_email(
            dados_agendamento['email_cliente'],
            assunto,
            template,
            empresa_email,
            empresa_senha
        )

    @staticmethod
    def enviar_agendamento_profissional(dados_agendamento, empresa_email, empresa_senha):
        """Envia email de notificação para o profissional"""
        template = EmailService.criar_template_agendamento("novo_agendamento_profissional", dados_agendamento)
        assunto = f"Novo Agendamento - {dados_agendamento.get('cliente', 'Cliente')}"
        
        return EmailService.enviar_email(
            dados_agendamento['email_profissional'],
            assunto,
            template,
            empresa_email,
            empresa_senha
        )

    @staticmethod
    def enviar_cancelamento_cliente(dados_cancelamento, empresa_email, empresa_senha):
        """Envia email de cancelamento para o cliente"""
        template = EmailService.criar_template_agendamento("cancelamento_cliente", dados_cancelamento)
        assunto = f"Agendamento Cancelado - {dados_cancelamento.get('servico', 'Serviço')}"
        
        return EmailService.enviar_email(
            dados_cancelamento['email_cliente'],
            assunto,
            template,
            empresa_email,
            empresa_senha
        )

    @staticmethod
    def enviar_cancelamento_profissional(dados_cancelamento, empresa_email, empresa_senha):
        """Envia email de cancelamento para o profissional"""
        template = EmailService.criar_template_agendamento("cancelamento_profissional", dados_cancelamento)
        assunto = f"Agendamento Cancelado - {dados_cancelamento.get('cliente', 'Cliente')}"
        
        return EmailService.enviar_email(
            dados_cancelamento['email_profissional'],
            assunto,
            template,
            empresa_email,
            empresa_senha
        )
