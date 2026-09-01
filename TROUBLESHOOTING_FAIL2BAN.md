# 🔧 Troubleshooting Fail2Ban - Erro de Socket

## Problema Reportado

```bash
sudo fail2ban-client status
# Erro: Failed to access socket path: /var/run/fail2ban/fail2ban.sock. Is fail2ban running?
```

## Causas Prováveis

1. **Conflito de configuração no jail.local** - O arquivo pode ter configurações conflitantes
2. **Permissões do diretório /var/run/fail2ban/**
3. **Filtros ou ações com sintaxe inválida**
4. **Porta ou logpath incorretos**

## Solução Passo a Passo

### 1. Verificar Status do Serviço

```bash
# Verificar se o serviço está rodando
sudo systemctl status fail2ban

# Ver logs detalhados
sudo journalctl -u fail2ban -n 100 --no-pager

# Ver logs do fail2ban
sudo tail -f /var/log/fail2ban.log
```

### 2. Testar Configuração

```bash
# Testar se a configuração é válida
sudo fail2ban-client -t

# Se houver erro, ele mostrará qual jail está com problema
```

### 3. Verificar Conteúdo do jail.local

```bash
# Ver o conteúdo completo
sudo cat /etc/fail2ban/jail.local

# Ou usar nano para editar
sudo nano /etc/fail2ban/jail.local
```

### 4. Configuração Mínima Recomendada

Se houver muitos conflitos, substitua o conteúdo do `jail.local` por:

```ini
# /etc/fail2ban/jail.local
# Configuração mínima e segura

[DEFAULT]
# Tempo de banimento (30 minutos)
bantime = 1800
# Janela de tempo (10 minutos)
findtime = 600
# Máximo de tentativas
maxretry = 5
# Ignorar IPs locais e o seu IP (substitua pelo seu IP)
ignoreip = 127.0.0.1/8 ::1 177.83.92.62

# Ajustes específicos para Nginx
[nginx-http-auth]
enabled = true
port = http,https
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3
bantime = 3600

[nginx-botsearch]
enabled = true
port = http,https
filter = nginx-botsearch
logpath = /var/log/nginx/access.log
maxretry = 2
bantime = 86400

[nginx-noscript]
enabled = true
port = http,https
filter = nginx-noscript
logpath = /var/log/nginx/access.log
maxretry = 6
bantime = 86400

[nginx-404]
enabled = true
port = http,https
filter = nginx-404
logpath = /var/log/nginx/access.log
maxretry = 10
bantime = 3600
```

### 5. Reiniciar Serviço

```bash
# Parar completamente
sudo systemctl stop fail2ban

# Aguardar alguns segundos
sleep 3

# Iniciar novamente
sudo systemctl start fail2ban

# Verificar status
sudo systemctl status fail2ban

# Testar cliente
sudo fail2ban-client status
```

### 6. Verificar Permissões

```bash
# Verificar se o diretório existe
ls -la /var/run/fail2ban/

# Se não existir, criar
sudo mkdir -p /var/run/fail2ban
sudo chown root:root /var/run/fail2ban
sudo chmod 755 /var/run/fail2ban

# Reiniciar fail2ban
sudo systemctl restart fail2ban
```

### 7. Verificar Filtros

```bash
# Listar filtros disponíveis
ls -la /etc/fail2ban/filter.d/

# Testar um filtro específico
sudo fail2ban-regex /var/log/nginx/error.log /etc/fail2ban/filter.d/nginx-http-auth.conf
```

### 8. Verificar Ações

```bash
# Listar ações disponíveis
ls -la /etc/fail2ban/action.d/

# Verificar se iptables está disponível
sudo iptables -L -n
```

## Diagnóstico Rápido

Execute estes comandos e compartilhe a saída:

```bash
# 1. Status do serviço
sudo systemctl status fail2ban --no-pager

# 2. Logs recentes
sudo journalctl -u fail2ban -n 50 --no-pager

# 3. Teste de configuração
sudo fail2ban-client -t

# 4. Conteúdo do jail.local (apenas as últimas 30 linhas)
sudo tail -n 30 /etc/fail2ban/jail.local

# 5. Permissões do diretório
ls -la /var/run/fail2ban/

# 6. Verificar se há processos do fail2ban
ps aux | grep fail2ban
```

## Solução Alternativa (Se nada funcionar)

Se o problema persistir, reinstale o fail2ban:

```bash
# Remover completamente
sudo apt remove --purge fail2ban -y
sudo apt autoremove -y

# Limpar configurações antigas
sudo rm -rf /etc/fail2ban
sudo rm -f /var/log/fail2ban.log

# Reinstalar
sudo apt update
sudo apt install fail2ban -y

# Criar configuração básica
sudo nano /etc/fail2ban/jail.local
# (cole a configuração mínima acima)

# Iniciar
sudo systemctl start fail2ban
sudo systemctl enable fail2ban

# Verificar
sudo fail2ban-client status
```

## Notas Importantes

1. **IP do Usuário**: Notei que seu IP é `177.83.92.62`. Adicione-o à lista `ignoreip` para não ser banido acidentalmente.

2. **Conflitos de Configuração**: Se o `jail.local` já tinha configurações, pode haver conflitos. É melhor usar uma configuração limpa.

3. **Logs do Nginx**: Verifique se os logs do nginx estão sendo gravados:
```bash
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

4. **Reinicialização**: Após alterações no `jail.local`, sempre reinicie o fail2ban:
```bash
sudo systemctl restart fail2ban
```

## Próximos Passos

Após resolver o problema do fail2ban, continue com:
- ✅ Rate limiting no Django (já implementado)
- ✅ Configurações CSRF (já corrigidas)
- ⏳ Refatoração do views.py (em andamento)
- ⏳ Implementação de testes (pendente)