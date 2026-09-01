# 🛡️ Guia de Instalação e Configuração do Fail2Ban

Este guia explica como instalar e configurar o Fail2Ban na VPS para proteger o PhotoApp contra ataques de força bruta e scanners maliciosos.

---

## 📋 Pré-requisitos

- Acesso SSH à VPS como root ou usuário com sudo
- Nginx instalado e configurado
- Ubuntu/Debian como sistema operacional

---

## 🚀 Instalação

### 1. Instalar o Fail2Ban

```bash
sudo apt update
sudo apt install fail2ban -y
```

### 2. Iniciar e Habilitar o Serviço

```bash
sudo systemctl start fail2ban
sudo systemctl enable fail2ban
```

### 3. Verificar Status

```bash
sudo systemctl status fail2ban
```

---

## ⚙️ Configuração

### 1. Criar Arquivo de Configuração Local

Nunca edite `jail.conf` diretamente. Crie uma cópia local:

```bash
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
```

### 2. Configurar Jails para Nginx

Edite o arquivo `/etc/fail2ban/jail.local`:

```bash
sudo nano /etc/fail2ban/jail.local
```

Adicione as seguintes configurações no final do arquivo:

```ini
# ============================================
# FAIL2BAN - PROTEÇÃO NGINX
# ============================================

[DEFAULT]
# Tempo de banimento (em segundos)
bantime = 3600
# Janela de tempo para contagem de tentativas (em segundos)
findtime = 600
# Número máximo de tentativas antes do banimento
maxretry = 5
# Email de notificação (opcional)
# destemail = admin@photum.com.br
# sender = fail2ban@photum.com.br
# mta = sendmail

# ============================================
# NGINX - AUTENTICAÇÃO HTTP
# ============================================
[nginx-http-auth]
enabled = true
port = http,https
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3
bantime = 3600

# ============================================
# NGINX - LIMIT REQUEST (Rate Limiting)
# ============================================
[nginx-limit-req]
enabled = true
port = http,https
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 10
bantime = 600
findtime = 60

# ============================================
# NGINX - BOT SEARCH (Scanners)
# ============================================
[nginx-botsearch]
enabled = true
port = http,https
filter = nginx-botsearch
logpath = /var/log/nginx/access.log
maxretry = 2
bantime = 86400

# ============================================
# NGINX - BAD REQUESTS
# ============================================
[nginx-badbots]
enabled = true
port = http,https
filter = nginx-badbots
logpath = /var/log/nginx/access.log
maxretry = 2
bantime = 86400

# ============================================
# NGINX - NOXXES (404 errors)
# ============================================
[nginx-noscript]
enabled = true
port = http,https
filter = nginx-noscript
logpath = /var/log/nginx/access.log
maxretry = 6
bantime = 86400

# ============================================
# NGINX - 404 ERRORS (Scanners)
# ============================================
[nginx-404]
enabled = true
port = http,https
filter = nginx-404
logpath = /var/log/nginx/access.log
maxretry = 10
bantime = 3600
```

### 3. Reiniciar o Fail2Ban

```bash
sudo systemctl restart fail2ban
```

### 4. Verificar Jails Ativos

```bash
sudo fail2ban-client status
```

### 5. Verificar Status de um Jail Específico

```bash
sudo fail2ban-client status nginx-http-auth
sudo fail2ban-client status nginx-botsearch
```

---

## 🔍 Comandos Úteis

### Ver IPs Banidos

```bash
# Listar todos os IPs banidos
sudo iptables -L -n

# Ver IPs banidos em um jail específico
sudo fail2ban-client get nginx-http-auth banip
```

### Desbanir um IP

```bash
sudo fail2ban-client set nginx-http-auth unbanip <IP_ADDRESS>
```

### Ver Logs do Fail2Ban

```bash
sudo tail -f /var/log/fail2ban.log
```

### Testar Configuração

```bash
# Testar se a configuração é válida
sudo fail2ban-client -t

# Testar um filtro específico
sudo fail2ban-client -t nginx-http-auth
```

---

## 🛡️ Filtros Personalizados (Opcional)

Se necessário, crie filtros personalizados em `/etc/fail2ban/filter.d/`:

### Filtro para Logs do Django

```ini
# /etc/fail2ban/filter.d/django-auth.conf
[Definition]
failregex = ^.*Failed login for user .* from <HOST>.*$
            ^.*Authentication Failed.*<HOST>.*$
ignoreregex =
```

---

## 📊 Monitoramento

### Dashboard de Status

```bash
# Status geral
sudo fail2ban-client status

# Status detalhado de todos os jails
for jail in $(sudo fail2ban-client status | grep Jail | awk '{print $2}'); do
    echo "=== $jail ==="
    sudo fail2ban-client status $jail
done
```

### Configurar Logrotate para Logs

```bash
sudo nano /etc/logrotate.d/fail2ban
```

Conteúdo:
```
/var/log/fail2ban.log {
    weekly
    rotate 4
    compress
    delaycompress
    missingok
    notifempty
    create 640 root adm
    postrotate
        fail2ban-client set logtarget /var/log/fail2ban.log
    endscript
}
```

---

## ⚠️ Solução de Problemas

### Fail2Ban não inicia

```bash
# Verificar erros
sudo journalctl -u fail2ban -n 50 --no-pager

# Testar configuração
sudo fail2ban-client -t
```

### IPs não estão sendo banidos

1. Verifique se os logs estão sendo gravados:
```bash
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

2. Verifique se o filtro está correto:
```bash
sudo fail2ban-regex /var/log/nginx/error.log /etc/fail2ban/filter.d/nginx-http-auth.conf
```

### Muitos falsos positivos

Aumente o `maxretry` ou `findtime` no jail específico.

---

## 🔒 Boas Práticas

1. **Não bane seu próprio IP**: Adicione seu IP à lista de ignorados:
```ini
[DEFAULT]
ignoreip = 127.0.0.1/8 ::1 203.0.113.0/24
```

2. **Use tempos de banimento progressivos**: Considere usar `fail2ban` com `recidive` jail para banir IPs reincidentes por períodos mais longos.

3. **Monitore regularmente**: Verifique os logs e status periodicamente.

4. **Mantenha atualizado**: `sudo apt update && sudo apt upgrade fail2ban`

---

## 📞 Suporte

- Documentação oficial: https://github.com/fail2ban/fail2ban
- Filtros prontos: `/etc/fail2ban/filter.d/`
- Logs: `/var/log/fail2ban.log`

---

**Última atualização:** 13/05/2026