from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import logging
import os
import socket
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailSender:
    @staticmethod
    def enviar_email_continuacao(aluno):
        """
        Sistema híbrido: tenta SMTP com timeout, se falhar salva em arquivo
        """
        print(f"📧 Enviando email para {aluno.email}...")
        
        # Tentar SMTP primeiro (com timeout curto)
        try:
            if EmailSender._testar_smtp_rapido():
                print("✅ SMTP disponível, tentando envio...")
                return EmailSender._enviar_via_smtp(aluno)
            else:
                print("⚠️ SMTP não disponível, usando backup...")
                return EmailSender._salvar_em_arquivo(aluno)
        except Exception as e:
            print(f"❌ SMTP falhou: {e}")
            print("📁 Salvando em arquivo...")
            return EmailSender._salvar_em_arquivo(aluno)
    
    @staticmethod
    def _testar_smtp_rapido():
        """Teste rápido de conectividade SMTP"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)  # Timeout de 3 segundos
            result = sock.connect_ex(('localhost', 25))
            sock.close()
            return result == 0
        except:
            return False
    
    @staticmethod
    def _enviar_via_smtp(aluno):
        """Envio via SMTP com timeout"""
        try:
            # Configurar timeout global
            socket.setdefaulttimeout(10)
            
            assunto = 'PhotoApp - Complete seu cadastro'
            link_continuacao = f"{settings.SITE_URL}/cadastro/{aluno.id}/{aluno.token}/"
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px;">
                    <h2 style="color: #007bff;">📸 PhotoApp - Complete seu cadastro</h2>
                    <p>Olá, <strong>{aluno.nome}</strong>!</p>
                    
                    <div style="background: white; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p>Você iniciou seu cadastro mas não finalizou. Complete agora clicando no botão abaixo:</p>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{link_continuacao}" 
                               style="background: #007bff; color: white; padding: 12px 30px; 
                                      text-decoration: none; border-radius: 5px; font-weight: bold;">
                                ✅ Completar Cadastro
                            </a>
                        </div>
                        
                        <p style="font-size: 12px; color: #6c757d;">
                            Se o botão não funcionar, copie e cole este link no navegador:<br>
                            <code>{link_continuacao}</code>
                        </p>
                    </div>
                    
                    <p style="color: #28a745;">🎉 Estamos ansiosos para sua participação!</p>
                    
                    <hr style="margin: 20px 0;">
                    <p style="font-size: 11px; color: #6c757d;">
                        Este email foi enviado automaticamente pelo sistema PhotoApp.<br>
                        Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
                    </p>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
PhotoApp - Complete seu cadastro

Olá, {aluno.nome}!

Você iniciou seu cadastro mas não finalizou. 
Complete agora acessando o link abaixo:

{link_continuacao}

Estamos ansiosos para sua participação!

---
Este email foi enviado automaticamente pelo sistema PhotoApp.
Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            """
            
            email = EmailMultiAlternatives(
                subject=assunto,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[aluno.email]
            )
            email.attach_alternative(html_content, "text/html")
            
            resultado = email.send(fail_silently=False)
            
            if resultado:
                print(f"✅ Email enviado via SMTP para {aluno.email}")
                logger.info(f'Email enviado via SMTP para {aluno.email}')
                return True
            else:
                raise Exception('SMTP send() retornou 0')
                
        except Exception as e:
            print(f"❌ Erro SMTP: {e}")
            raise e
        finally:
            # Restaurar timeout padrão
            socket.setdefaulttimeout(None)
    
    @staticmethod
    def _salvar_em_arquivo(aluno):
        """Backup - salvar email em arquivo e mostrar link"""
        try:
            backup_dir = '/tmp/photoapp-emails-backup'
            os.makedirs(backup_dir, exist_ok=True)
            
            link_continuacao = f"{settings.SITE_URL}/cadastro/{aluno.id}/{aluno.token}/"
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{backup_dir}/email_{aluno.id}_{timestamp}.txt"
            
            conteudo = f"""
=== EMAIL PHOTOAPP ===
Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
Para: {aluno.email}
Nome: {aluno.nome}
Assunto: PhotoApp - Complete seu cadastro

LINK DE CONTINUAÇÃO:
{link_continuacao}

MENSAGEM:
Olá, {aluno.nome}!

Você iniciou seu cadastro mas não finalizou. 
Complete agora acessando o link acima.

Estamos ansiosos para sua participação!

=== FIM EMAIL ===
            """
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(conteudo)
            
            # Mostrar informações importantes
            print(f"📁 Email salvo em: {filename}")
            print(f"👤 Usuário: {aluno.nome} ({aluno.email})")
            print(f"🔗 Link de continuação:")
            print(f"   {link_continuacao}")
            print(f"📋 Para enviar manualmente, use o link acima")
            
            logger.info(f'Email salvo em arquivo: {filename}')
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao salvar email: {e}")
            logger.error(f'Erro ao salvar email em arquivo: {e}')
            return False

    @staticmethod
    def listar_emails_pendentes():
        """Listar emails salvos em arquivo"""
        backup_dir = '/tmp/photoapp-emails-backup'
        if not os.path.exists(backup_dir):
            print("📁 Nenhum email em backup encontrado")
            return
        
        arquivos = sorted([f for f in os.listdir(backup_dir) if f.endswith('.txt')])
        
        if not arquivos:
            print("📁 Nenhum email em backup encontrado")
            return
        
        print(f"📧 {len(arquivos)} emails em backup:")
        print("-" * 60)
        
        for arquivo in arquivos[-10:]:  # Últimos 10
            caminho = os.path.join(backup_dir, arquivo)
            with open(caminho, 'r', encoding='utf-8') as f:
                conteudo = f.read()
                
            # Extrair informações
            linhas = conteudo.split('\n')
            data = next((l.split('Data: ')[1] for l in linhas if l.startswith('Data:')), 'N/A')
            para = next((l.split('Para: ')[1] for l in linhas if l.startswith('Para:')), 'N/A')
            nome = next((l.split('Nome: ')[1] for l in linhas if l.startswith('Nome:')), 'N/A')
            
            print(f"📅 {data}")
            print(f"👤 {nome} ({para})")
            print(f"📁 {arquivo}")
            print("-" * 60)