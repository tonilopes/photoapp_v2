# 🔧 Troubleshooting - Erro 502 Bad Gateway

## Problema
Ao acessar `https://photoapp.photum.com.br/` retorna:
```
502 Bad Gateway
nginx/1.18.0 (Ubuntu)
```

## Causas Prováveis

1. **Gunicorn não está rodando**
2. **Gunicorn está rodando em porta/socket diferente**
3. **Problema de permissão no socket**
4. **Nginx configurado incorretamente**
5. **Erro na aplicação Django**

## Diagnóstico Passo a Passo

### 1. Verificar Status do Gunicorn

```bash
# Verificar se o serviço está rodando
sudo systemctl status gunicorn

# Ou verificar processos
ps aux | grep gunicorn

# Verificar se há erros
sudo journalctl -u gunicorn -n 50 --no-pager
```

### 2. Verificar Logs do Nginx

```bash
# Logs de erro do Nginx
sudo tail -f /var/log/nginx/error.log

# Logs de acesso
sudo tail -f /var/log/nginx/access.log

# Verificar erro específico
sudo tail -n 50 /var/log/nginx/error.log
```

### 3. Verificar Configuração do Nginx

```bash
# Verificar configuração
sudo cat /etc/nginx/sites-available/photoapp

# Ou
sudo nano /etc/nginx/sites-available/photoapp

# Testar configuração
sudo nginx -t

# Recarregar Nginx
sudo systemctl reload nginx
```

### 4. Verificar Socket/Porta do Gunicorn

```bash
# Verificar se o socket existe
ls -la /var/www/photoapp/gunicorn.sock

# Ou verificar porta
sudo netstat -tulpn | grep :8001

# Ou
sudo ss -tulpn | grep :8001
```

### 5. Verificar Permissões

```bash
# Verificar dono do socket
ls -la /var/www/photoapp/

# Verificar dono dos arquivos
ls -la /var/www/photoapp/

# Verificar se o usuário www-data tem acesso
sudo -u www-data ls -la /var/www/photoapp/
```

### 6. Verificar Ambiente Virtual

```bash
# Verificar se o ambiente virtual está ativo
source /var/www/photoapp/venv/bin/activate

# Verificar se o Django está instalado
python -c "import django; print(django.VERSION)"

# Verificar se o gunicorn está instalado
pip show gunicorn
```

## Soluções Comuns

### Solução 1: Reiniciar Gunicorn

```bash
# Parar
sudo systemctl stop gunicorn

# Aguardar
sleep 3

# Iniciar
sudo systemctl start gunicorn

# Verificar status
sudo systemctl status gunicorn

# Ver logs
sudo journalctl -u gunicorn -f
```

### Solução 2: Reiniciar Nginx

```bash
# Testar configuração
sudo nginx -t

# Recarregar
sudo systemctl reload nginx

# Ou reiniciar
sudo systemctl restart nginx
```

### Solução 3: Verificar Configuração do Gunicorn

```bash
# Ver arquivo de configuração
sudo cat /etc/systemd/system/photoapp.service

# Ou
sudo nano /etc/systemd/system/photoapp.service

# Conteúdo esperado:
# [Unit]
# Description=gunicorn daemon
# After=network.target
#
# [Service]
# User=root
# Group=www-data
# WorkingDirectory=/var/www/photoapp
# ExecStart=/var/www/photoapp/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/var/www/photoapp/gunicorn.sock photoapp.wsgi:application
#
# [Install]
# WantedBy=multi-user.target
```

### Solução 4: Recriar Socket

```bash
# Parar gunicorn
sudo systemctl stop gunicorn

# Remover socket antigo
sudo rm /var/www/photoapp/gunicorn.sock

# Verificar permissões
sudo chown -R root:www-data /var/www/photoapp
sudo chmod -R 775 /var/www/photoapp

# Iniciar gunicorn
sudo systemctl start gunicorn

# Verificar se socket foi criado
ls -la /var/www/photoapp/gunicorn.sock
```

### Solução 5: Testar Gunicorn Manualmente

```bash
# Ativar ambiente virtual
source /var/www/photoapp/venv/bin/activate

# Ir para diretório
cd /var/www/photoapp

# Testar execução manual
gunicorn --bind 127.0.0.1:8001 photoapp.wsgi:application

# Ou testar com socket
gunicorn --bind unix:/var/www/photoapp/gunicorn.sock photoapp.wsgi:application
```

### Solução 6: Verificar Erros do Django

```bash
# Verificar se há erros de importação
cd /var/www/photoapp
source venv/bin/activate
python manage.py check

# Verificar migrations
python manage.py showmigrations

# Verificar se o banco está acessível
python manage.py dbshell
```

## Diagnóstico Rápido

Execute estes comandos e compartilhe a saída:

```bash
# 1. Status do Gunicorn
sudo systemctl status gunicorn --no-pager

# 2. Logs do Gunicorn (últimas 20 linhas)
sudo journalctl -u gunicorn -n 20 --no-pager

# 3. Logs do Nginx (últimas 20 linhas)
sudo tail -n 20 /var/log/nginx/error.log

# 4. Configuração do Nginx
sudo cat /etc/nginx/sites-available/photoapp

# 5. Verificar socket
ls -la /var/www/photoapp/gunicorn.sock

# 6. Testar configuração Nginx
sudo nginx -t

# 7. Verificar processos
ps aux | grep gunicorn
```

## Configuração Esperada do Nginx

```nginx
server {
    listen 80;
    server_name photoapp.photum.com.br;
    
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# OU com socket Unix:
server {
    listen 80;
    server_name photoapp.photum.com.br;
    
    location / {
        proxy_pass http://unix:/var/www/photoapp/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Possíveis Causas Específicas

### Se o Gunicorn está rodando mas o Nginx não conecta:

1. **Socket com permissão errada:**
```bash
sudo chown root:www-data /var/www/photoapp/gunicorn.sock
sudo chmod 660 /var/www/photoapp/gunicorn.sock
```

2. **Nginx e Gunicorn usando métodos diferentes:**
- Verificar se ambos estão usando socket OU porta (não misturar)

3. **App Django com erro:**
```bash
cd /var/www/photoapp
source venv/bin/activate
python manage.py check --deploy
```

### Se houve atualização recente:

1. **Reinstalar dependências:**
```bash
cd /var/www/photoapp
source venv/bin/activate
pip install -r requirements.txt
```

2. **Aplicar migrations:**
```bash
python manage.py migrate
```

3. **Coletar estáticos:**
```bash
python manage.py collectstatic --noinput
```

4. **Reiniciar serviços:**
```bash
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

## Comandos de Recuperação Rápida

```bash
# 1. Parar tudo
sudo systemctl stop nginx
sudo systemctl stop gunicorn

# 2. Verificar erros
sudo journalctl -u gunicorn -n 50 --no-pager
sudo tail -n 50 /var/log/nginx/error.log

# 3. Iniciar Gunicorn
sudo systemctl start gunicorn

# 4. Verificar se está rodando
sudo systemctl status gunicorn

# 5. Testar configuração Nginx
sudo nginx -t

# 6. Iniciar Nginx
sudo systemctl start nginx

# 7. Verificar logs novamente
sudo tail -f /var/log/nginx/error.log
```

## Notas Importantes

1. **Socket vs Porta:** O Gunicorn pode estar configurado para usar socket Unix (`unix:/var/www/photoapp/gunicorn.sock`) OU porta TCP (`127.0.0.1:8001`). O Nginx deve usar o mesmo método.

2. **Permissões:** O usuário do Nginx (www-data) precisa ter acesso de leitura/escrita no socket.

3. **Ambiente Virtual:** Sempre ativar o venv antes de executar comandos Python/Django.

4. **Logs:** Os logs do Nginx e Gunicorn são essenciais para diagnosticar o problema exato.

5. **Reinicialização:** Após qualquer alteração de configuração, sempre reinicie os serviços.