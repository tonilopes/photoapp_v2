# 🔑 SSH Setup - Acesso VPS SEM Senha

## ⚡ Quick Start (3 passos)

### 1. Executar Setup Script

```powershell
# Abra PowerShell e execute:
cd d:\photoapp_v2
./setup-ssh.ps1
```

**Ou use o arquivo .bat (simpler):**
```batch
d:\photoapp_v2\setup-ssh.bat
```

### 2. Configurar Chave no Servidor (SE NÃO FUNCIONAR)

Se receber erro, a chave precisa ser adicionada ao servidor:

1. **Acesse o console web da VPS:**
   - Vá para https://www.locaweb.com.br/
   - Faça login
   - VPS → Console Web (ou VNC)

2. **No console, execute:**
   ```bash
   mkdir -p ~/.ssh
   chmod 700 ~/.ssh
   
   # Cole o conteúdo da chave pública (próxima seção)
   nano ~/.ssh/authorized_keys
   # Ctrl+X, Y, Enter para salvar
   
   chmod 600 ~/.ssh/authorized_keys
   sudo systemctl restart sshd
   ```

3. **Chave pública a adicionar:**
   ```
   ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDlq....(muito texto)....toni@photum.com.br
   ```
   
   (Copie do arquivo: `d:\photoapp_v2\toni@photum.com.br.pub`)

### 3. Testar Conexão

```powershell
# Teste rápido:
ssh photum whoami

# Deve retornar: root
```

---

## 🎯 Como Usar no Futuro

### Via Terminal Manual
```powershell
ssh photum "cd /var/www/photoapp && git pull origin main"
```

### Via execution_subagent
```
No futuro, em vez de:
ssh root@179.0.178.106 "comando"

Use:
ssh photum "comando"
```

### Com Múltiplos Comandos
```powershell
ssh photum << 'EOF'
cd /var/www/photoapp
git pull origin main
systemctl restart photoapp
systemctl status photoapp | head -3
EOF
```

---

## 🔐 Segurança da Chave Privada

- **Localização:** `~/.ssh/photum_key`
- **Permissões:** Automáticas (600)
- **Passphrase:** Se tiver, será pedida UMA VEZ (por sessão)
- **Nunca** compartilhe a chave privada!

---

## ❌ Se Continuar Pedindo Senha

### Opção 1: Remover Passphrase da Chave (MENOS SEGURO)
```powershell
ssh-keygen -p -f "~/.ssh/photum_key" -N "" -P "sua_passphrase"
```

### Opção 2: Usar ssh-agent (RECOMENDADO)
```powershell
# Iniciar o ssh-agent
Get-Service ssh-agent | Set-Service -StartupType Automatic
Start-Service ssh-agent

# Adicionar chave
ssh-add "$env:USERPROFILE\.ssh\photum_key"

# Agora NÃO vai pedir senha na sessão atual
```

### Opção 3: Usar no PowerShell Profile
```powershell
# Editar perfil PowerShell
notepad $PROFILE

# Adicionar essas linhas:
if ((Get-Service ssh-agent).Status -eq 'Stopped') { 
    Start-Service ssh-agent 
}
ssh-add "$env:USERPROFILE\.ssh\photum_key" 2>$null
```

---

## 📊 Verificação

```powershell
# Ver se a chave foi adicionada ao agente:
ssh-add -L

# Deve listar: ssh-rsa AAAA... toni@photum.com.br

# Testar conexão:
ssh -v photum "echo teste"

# Se vir "Offering public key" = ✅ FUNCIONANDO
```

---

## 🚀 Resultado Final

Após configurar:
- ✅ Sem digitar senha (ou só UMA VEZ por sessão)
- ✅ Múltiplos comandos SSH rápidos
- ✅ Integração automática com execution_subagent

Pronto! 🎉
