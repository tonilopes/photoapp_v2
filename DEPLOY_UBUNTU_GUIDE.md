# 📋 Guia Completo de Deploy - PhotoApp no Ubuntu VPS

Este documento contém todas as etapas necessárias para fazer deploy da aplicação PhotoApp em um servidor Ubuntu.

---

## 📑 Índice

1. [Pré-requisitos](#pré-requisitos)
2. [Preparação do Servidor](#preparação-do-servidor)
3. [Instalação de Dependências](#instalação-de-dependências)
4. [Configuração do Banco de Dados](#configuração-do-banco-de-dados)
5. [Configuração da Aplicação](#configuração-da-aplicação)
6. [Configuração do Gunicorn](#configuração-do-gunicorn)
7. [Configuração do Nginx](#configuração-do-nginx)
8. [Configuração do SSL (Let's Encrypt)](#configuração-do-ssl)
9. [Inicialização e Testes](#inicialização-e-testes)
10. [Manutenção e Monitoramento](#manutenção-e-monitoramento)
11. [Solução de Problemas](#solução-de-problemas)
12. [Scripts Úteis](#scripts-úteis)

---

## 🔧 Pré-requisitos

### Informações Necessárias
- **Servidor Ubuntu** (20.04 ou 22.04 recomendado)
- **Usuário com privilégios sudo**
- **Domínio apontando para o IP do servidor** (ex: cliente.photum.com.br)
- **Acesso SSH ao servidor**

### Informações da Aplicação
- **Nome do projeto**: photoapp
- **Diretório de instalação**: `/var/www/photoapp`
- **Usuário da aplicação**: `www-data` (padrão do Ubuntu)
- **Porta da aplicação**: 8000 (Gunicorn)
- **Porta HTTP**: 80
- **Porta HTTPS**: 443

---

## 🖥️ Preparação do Servidor

### 1. Acessar o servidor via SSH
```bash
ssh usuario@seu-servidor.com
```

### 2. Atualizar o sistema
```bash
sudo apt update && sudo apt upgrade -y
```

### 3. Instalar ferramentas básicas
```bash
sudo apt install -y git curl wget build-essential python3-pip python3-venv python3-dev
```

### 4. Criar diretório da aplicação
```bash
sudo mkdir -p /var/www/photoapp
sudo chown $USER:$USER /var/www/photoapp
cd /var/www/photoapp
```

---

## 📦 Instalação de Dependências

### 1. Instalar Python e dependências do sistema
```bash
sudo apt install -y python3 python3-pip python3-venv python3-dev \
    libpq-dev gcc mysql-server libmysqlclient-dev \
    nginx supervisor \
    libjpeg-dev zlib1g-dev libfreetype6-dev
```

### 2. Clonar o repositório (ou fazer upload)
```bash
# Se estiver no GitHub:
git clone https://github.com/tonilopes/photoapp.git .
# ou
git clone git@github.com:tonilopes/photoapp.git .

# Se for upload manual, use scp:
# scp -r photoapp/* usuario@servidor:/var/www/photoapp/
```

### 3. Criar ambiente virtual Python
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Instalar dependências Python
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Instalar dependências específicas se necessário
```bash
# Se houver erro com mysqlclient:
sudo apt install -y default-libmysqlclient-dev build-essential pkg-config

# Instalar novamente:
pip install mysqlclient
```

---

## 🗄️ Configuração do Banco de Dados

### 1. Instalar e configurar MySQL/MariaDB
```bash
sudo systemctl start mysql
sudo systemctl enable mysql
sudo mysql_secure_installation
```

### 2. Criar banco de dados e usuário
```bash
sudo mysql -u root -p
```

No prompt do MySQL:
```sql
CREATE DATABASE photoapp_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'photoapp_user'@'localhost' IDENTIFIED BY 'SuaSenhaForte123!';
GRANT ALL PRIVILEGES ON photoapp_db.* TO 'photoapp_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 3. Testar conexão
```bash
mysql -u photoapp_user -p photoapp_db
```

### 4. Configurar variáveis de ambiente
```bash
cd /var/www/photoapp
nano .env
```

Conteúdo do `.env`:
```env
# Segurança
SECRET_KEY='sua-secret-key-gerada-aqui-muito-segura'
DEBUG=False

# Hosts permitidos
ALLOWED_HOSTS=cliente.photum.com.br,www.cliente.photum.com.br,localhost,127.0.0.1

# Banco de dados
DATABASE_URL=mysql://photoapp_user:SuaSenhaForte123!@localhost:3306/photoapp_db

# URLs do site
SITE_URL=https://cliente.photum.com.br
QR_CODE_BASE_URL=https://cliente.photum.com.br

# Log
LOG_FILE_PATH=/var/log/django/photoapp.log

# Email (se for usar)
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=seu-email@gmail.com
# EMAIL_HOST_PASSWORD=sua-senha-de-app
# DEFAULT_FROM_EMAIL=PhotoApp <naoresponda@photum.com.br>
```

### 5. Gerar SECRET_KEY
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 6. Executar migrações
```bash
source venv/bin/activate
python manage.py migrate
```

### 7. Criar superusuário
```bash
python manage.py createsuperuser
```

### 8. Coletar arquivos estáticos
```bash
python manage.py collectstatic --noinput
```

### 9. Configurar permissões
```bash
sudo chown -R www-data:www-data /var/www/photoapp
sudo chmod -R 755 /var/www/photoapp
sudo chown -R www-data:www-data /var/www/photoapp/mediafiles
sudo chmod -R 755 /var/www/photoapp/mediafiles
```

---

## 🔫 Configuração do Gunicorn

### 1. Criar arquivo de serviço do Gunicorn
```bash
sudo nano /etc/systemd/system/gunicorn_photoapp.service
```

Conteúdo do arquivo:
```ini
[Unit]
Description=Gunicorn instance to serve PhotoApp
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/photoapp
ExecStart=/var/www/photoapp/venv/bin/gunicorn --access-logfile - \
    --workers 3 \
    --bind unix:/var/www/photoapp/photoapp.sock \
    photoapp.wsgi:application

# Restart policy
Restart=always
RestartSec=5

# Security settings
NoNewPrivileges=true
PrivateTmp=true

# Environment
Environment="PATH=/var/www/photoapp/venv/bin"
EnvironmentFile=/var/www/photoapp/.env

[Install]
WantedBy=multi-user.target
```

### 2. Habilitar e iniciar serviço
```bash
sudo systemctl daemon-reload
sudo systemctl start gunicorn_photoapp
sudo systemctl enable gunicorn_photoapp
```

### 3. Verificar status
```bash
sudo systemctl status gunicorn_photoapp
```

### 4. Verificar socket
```bash
ls -la /var/www/photoapp/photoapp.sock
```

---

## 🌐 Configuração do Nginx

### 1. Criar configuração do Nginx
```bash
sudo nano /etc/nginx/sites-available/photoapp
```

Conteúdo do arquivo:
```nginx
upstream photoapp_server {
    server unix:/var/www/photoapp/photoapp.sock fail_timeout=0;
}

server {
    listen 80;
    server_name cliente.photum.com.br www.cliente.photum.com.br;
    
    # Redirecionar HTTP para HTTPS (descomente após configurar SSL)
    # return 301 https://$server_name$request_uri;
    
    # Para testes antes do SSL:
    location / {
        proxy_pass http://photoapp_server;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;
        proxy_set_header X-Forwarded-Port $server_port;
        
        # Timeout para uploads grandes
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
        send_timeout 300;
        
        # Tamanho máximo de upload
        client_max_body_size 20M;
    }
    
    # Arquivos estáticos
    location /static/ {
        alias /var/www/photoapp/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Arquivos de mídia (fotos)
    location /media/ {
        alias /var/www/photoapp/mediafiles/;
        expires 7d;
        add_header Cache-Control "public";
    }
}

# Servidor HTTPS (após configurar SSL)
# server {
#     listen 443 ssl http2;
#     server_name cliente.photum.com.br www.cliente.photum.com.br;
#     
#     ssl_certificate /etc/letsencrypt/live/cliente.photum.com.br/fullchain.pem;
#     ssl_certificate_key /etc/letsencrypt/live/cliente.photum.com.br/privkey.pem;
#     
#     # SSL strong settings
#     ssl_protocols TLSv1.2 TLSv1.3;
#     ssl_ciphers HIGH:!aNULL:!MD5;
#     ssl_prefer_server_ciphers on;
#     
#     # HSTS
#     add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
#     
#     location / {
#         proxy_pass http://photoapp_server;
#         proxy_set_header Host $host;
#         proxy_set_header X-Real-IP $remote_addr;
#         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
#         proxy_set_header X-Forwarded-Proto $scheme;
#         proxy_set_header X-Forwarded-Host $server_name;
#         proxy_set_header X-Forwarded-Port $server_port;
#         
#         proxy_connect_timeout 300;
#         proxy_send_timeout 300;
#         proxy_read_timeout 300;
#         send_timeout 300;
#         
#         client_max_body_size 20M;
#     }
#     
#     location /static/ {
#         alias /var/www/photoapp/staticfiles/;
#         expires 30d;
#         add_header Cache-Control "public, immutable";
#     }
#     
#     location /media/ {
#         alias /var/www/photoapp/mediafiles/;
#         expires 7d;
#         add_header Cache-Control "public";
#     }
# }
```

### 2. Habilitar site
```bash
sudo ln -s /etc/nginx/sites-available/photoapp /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Remove default se existir
```

### 3. Testar configuração
```bash
sudo nginx -t
```

### 4. Reiniciar Nginx
```bash
sudo systemctl restart nginx
sudo systemctl enable nginx
```

---

## 🔒 Configuração do SSL (Let's Encrypt)

### 1. Instalar Certbot
```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 2. Obter certificado
```bash
sudo certbot --nginx -d cliente.photum.com.br -d www.cliente.photum.com.br
```

### 3. Configurar renovação automática
```bash
sudo certbot renew --dry-run  # Testar renovação
```

### 4. Verificar agendamento
```bash
sudo systemctl status certbot.timer
```

### 5. Atualizar configuração Nginx (após certificado)
Descomente a seção HTTPS no arquivo de configuração do Nginx e comente a seção HTTP.

```bash
sudo nginx -t && sudo systemctl reload nginx
```

---

## 🚀 Inicialização e Testes

### 1. Verificar serviços
```bash
sudo systemctl status gunicorn_photoapp
sudo systemctl status nginx
sudo systemctl status mysql
```

### 2. Verificar logs
```bash
# Logs do Gunicorn
sudo journalctl -u gunicorn_photoapp -f

# Logs do Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Logs da aplicação
sudo tail -f /var/log/django/photoapp.log
```

### 3. Testar aplicação
```bash
# Testar localmente
curl -I http://localhost

# Testar domínio
curl -I https://cliente.photum.com.br
```

### 4. Testar upload de arquivos
```bash
# Criar arquivo de teste
echo "Teste de upload" > /var/www/photoapp/mediafiles/test.txt

# Acessar via navegador: https://cliente.photum.com.br/media/test.txt
```

---

## 🔧 Manutenção e Monitoramento

### 1. Scripts de manutenção

Criar script de backup:
```bash
sudo nano /var/www/photoapp/backup.sh
```

Conteúdo:
```bash
#!/bin/bash
# Backup do banco de dados
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/photoapp"
mkdir -p $BACKUP_DIR

# Backup MySQL
mysqldump -u photoapp_user -p'SuaSenhaForte123!' photoapp_db > $BACKUP_DIR/db_$DATE.sql

# Backup de mídia (opcional, pode ser grande)
# tar -czf $BACKUP_DIR/media_$DATE.tar.gz /var/www/photoapp/mediafiles/

# Manter apenas últimos 7 backups
find $BACKUP_DIR -name "db_*.sql" -mtime +7 -delete
# find $BACKUP_DIR -name "media_*.tar.gz" -mtime +7 -delete

echo "Backup completado: $DATE"
```

Tornar executável:
```bash
chmod +x /var/www/photoapp/backup.sh
```

### 2. Agendar backup automático
```bash
sudo crontab -e
```

Adicionar linha:
```bash
0 2 * * * /var/www/photoapp/backup.sh
```

### 3. Monitoramento de recursos
```bash
# Instalar ferramentas de monitoramento
sudo apt install -y htop netdata

# Iniciar Netdata (monitoramento em tempo real)
sudo systemctl start netdata
sudo systemctl enable netdata

# Acessar: http://seu-servidor:19999
```

### 4. Logs e debugging
```bash
# Ver espaço em disco
df -h

# Ver uso de memória
free -h

# Ver processos
ps aux | grep gunicorn
ps aux | grep nginx

# Ver conexões MySQL
mysql -u root -p -e "SHOW PROCESSLIST;"
```

---

## 🛠️ Solução de Problemas

### Problema: Erro 502 Bad Gateway
```bash
# Verificar se Gunicorn está rodando
sudo systemctl status gunicorn_photoapp

# Verificar socket
ls -la /var/www/photoapp/photoapp.sock

# Verificar permissões
sudo chown www-data:www-data /var/www/photoapp/photoapp.sock

# Reiniciar serviços
sudo systemctl restart gunicorn_photoapp
sudo systemctl restart nginx
```

### Problema: Erro 500 Internal Server Error
```bash
# Verificar logs do Django
sudo tail -f /var/log/django/photoapp.log

# Verificar logs do Nginx
sudo tail -f /var/log/nginx/error.log

# Ativar DEBUG temporariamente no .env
# DEBUG=True (apenas para debugging!)
```

### Problema: Upload de arquivos não funciona
```bash
# Verificar permissões da pasta media
sudo chown -R www-data:www-data /var/www/photoapp/mediafiles
sudo chmod -R 755 /var/www/photoapp/mediafiles

# Verificar client_max_body_size no Nginx
sudo nginx -t
```

### Problema: Arquivos estáticos não carregam
```bash
# Coletar estáticos novamente
source /var/www/photoapp/venv/bin/activate
python manage.py collectstatic --noinput

# Verificar permissões
sudo chown -R www-data:www-data /var/www/photoapp/staticfiles
```

### Problema: Erro de conexão com banco de dados
```bash
# Verificar se MySQL está rodando
sudo systemctl status mysql

# Testar conexão
mysql -u photoapp_user -p photoapp_db

# Verificar credenciais no .env
cat /var/www/photoapp/.env | grep DATABASE
```

### Problema: SSL não funciona
```bash
# Verificar certificados
sudo ls -la /etc/letsencrypt/live/cliente.photum.com.br/

# Testar renovação
sudo certbot renew --dry-run

# Verificar configuração Nginx
sudo nginx -t
```

---

## 📜 Scripts Úteis

### Script de deploy automático
```bash
#!/bin/bash
# deploy.sh - Script para deploy automático

echo "🚀 Iniciando deploy do PhotoApp..."

# 1. Atualizar repositório
cd /var/www/photoapp
sudo -u www-data git pull origin main

# 2. Atualizar dependências
source venv/bin/activate
pip install -r requirements.txt

# 3. Executar migrações
python manage.py migrate --noinput

# 4. Coletar estáticos
python manage.py collectstatic --noinput

# 5. Reiniciar Gunicorn
sudo systemctl restart gunicorn_photoapp

echo "✅ Deploy completado com sucesso!"
```

### Script de monitoramento
```bash
#!/bin/bash
# monitor.sh - Script de monitoramento

echo "📊 Status do PhotoApp"
echo "===================="

echo "🟢 Serviços:"
sudo systemctl is-active gunicorn_photoapp
sudo systemctl is-active nginx
sudo systemctl is-active mysql

echo "💾 Disco:"
df -h /var/www/photoapp

echo "🧠 Memória:"
free -h

echo "🔗 Conexões MySQL:"
mysql -u root -p -e "SHOW STATUS LIKE 'Threads_connected';"

echo "📝 Últimos logs de erro:"
sudo tail -20 /var/log/nginx/error.log
```

### Script de rollback
```bash
#!/bin/bash
# rollback.sh - Script para rollback

if [ -z "$1" ]; then
    echo "Uso: ./rollback.sh <commit_hash>"
    exit 1
fi

cd /var/www/photoapp
sudo -u www-data git reset --hard $1
sudo systemctl restart gunicorn_photoapp

echo "✅ Rollback para $1 completado"
```

---

## 🔐 Segurança Adicional

### 1. Configurar firewall (UFW)
```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

### 2. Configurar fail2ban
```bash
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 3. Configurar SSH seguro
```bash
sudo nano /etc/ssh/sshd_config
```

Alterar:
```
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
```

Reiniciar SSH:
```bash
sudo systemctl restart sshd
```

### 4. Configurar atualizações automáticas
```bash
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

---

## 📊 Performance e Otimização

### 1. Configurar cache do Nginx
Adicionar ao nginx.conf:
```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=photoapp_cache:10m max_size=1g inactive=60m use_temp_path=off;
```

### 2. Otimizar Gunicorn
Ajustar no arquivo de serviço:
```ini
--workers 3  # Ajustar baseado em CPUs: (2 x $num_cores) + 1
--worker-class sync
--worker-connections 1000
--timeout 120
--keep-alive 5
```

### 3. Otimizar MySQL
```bash
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
```

Adicionar:
```ini
[mysqld]
innodb_buffer_pool_size = 1G
innodb_log_file_size = 256M
query_cache_size = 64M
max_connections = 200
```

---

## 📞 Contatos e Suporte

### Links Úteis
- **Documentação Django**: https://docs.djangoproject.com/
- **Documentação Gunicorn**: https://docs.gunicorn.org/
- **Documentação Nginx**: https://nginx.org/en/docs/
- **Certbot**: https://certbot.eff.org/

### Logs Importantes
- **Aplicação**: `/var/log/django/photoapp.log`
- **Gunicorn**: `journalctl -u gunicorn_photoapp`
- **Nginx**: `/var/log/nginx/error.log`
- **MySQL**: `/var/log/mysql/error.log`

### Comandos de Emergência
```bash
# Parar todos os serviços
sudo systemctl stop gunicorn_photoapp nginx mysql

# Reiniciar tudo
sudo systemctl restart mysql
sudo systemctl restart gunicorn_photoapp
sudo systemctl restart nginx

# Modo de manutenção
sudo mv /etc/nginx/sites-enabled/photoapp /etc/nginx/sites-available/
sudo nginx -s reload
```

---

## ✅ Checklist de Deploy

- [ ] Servidor Ubuntu atualizado
- [ ] Dependências do sistema instaladas
- [ ] Python e pip configurados
- [ ] Ambiente virtual criado
- [ ] Dependências Python instaladas
- [ ] MySQL/MariaDB instalado e configurado
- [ ] Banco de dados e usuário criados
- [ ] Arquivo .env configurado
- [ ] Migrações executadas
- [ ] Superusuário criado
- [ ] Arquivos estáticos coletados
- [ ] Permissões configuradas
- [ ] Gunicorn configurado e rodando
- [ ] Nginx configurado e rodando
- [ ] SSL configurado (Let's Encrypt)
- [ ] Firewall configurado
- [ ] Backup automatizado configurado
- [ ] Monitoramento configurado
- [ ] Testes realizados
- [ ] Documentação atualizada

---

**📝 Nota**: Este guia foi criado com base na análise do projeto PhotoApp. Adapte as configurações conforme necessário para seu ambiente específico.

**🔄 Atualização**: 06/05/2026
**👤 Autor**: Assistente de IA baseado na análise do código