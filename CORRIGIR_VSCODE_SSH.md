# 🔧 Corrigir Erro de Conexão SSH no VS Code

## ❌ Problema Identificado

O erro mostra que o VS Code está tentando usar um arquivo de configuração SSH incorreto:

```
Can't open user config file ssh root@179.0.178.106: No such file or directory
```

Isso acontece porque:
1. O arquivo `config` está na pasta do projeto, mas o VS Code espera que esteja em `C:\Users\SeuUsuario\.ssh\config`
2. O VS Code está interpretando o caminho do arquivo de configuração de forma errada

## 🔧 Solução Passo a Passo

### Passo 1: Copiar o arquivo de configuração SSH para o local correto

Execute estes comandos no PowerShell:

```powershell
# 1. Criar diretório .ssh se não existir
if (!(Test-Path "$env:USERPROFILE\.ssh")) {
    New-Item -ItemType Directory -Path "$env:USERPROFILE\.ssh"
    Write-Host "Diretório .ssh criado em: $env:USERPROFILE\.ssh"
} else {
    Write-Host "Diretório .ssh já existe em: $env:USERPROFILE\.ssh"
}

# 2. Copiar o arquivo config corrigido para o local correto
Copy-Item "d:\photoapp_v2\ssh-config-corrigido" "$env:USERPROFILE\.ssh\config" -Force
Write-Host "Arquivo config copiado para: $env:USERPROFILE\.ssh\config"

# 3. Verificar se o arquivo existe
if (Test-Path "$env:USERPROFILE\.ssh\config") {
    Write-Host "✓ Arquivo de configuração SSH criado com sucesso!" -ForegroundColor Green
    Get-Content "$env:USERPROFILE\.ssh\config"
} else {
    Write-Host "✗ Erro ao criar arquivo de configuração" -ForegroundColor Red
}
```

### Passo 2: Corrigir Permissões do Arquivo da Chave SSH

No Windows, as permissões do arquivo da chave privada devem estar corretas:

```powershell
# Executar no PowerShell como Administrador
# Navegue até a pasta do projeto
cd d:\photoapp_v2

# Definir permissões corretas para a chave privada
icacls "toni@photum.com.br" /inheritance:r
icacls "toni@photum.com.br" /grant:r "$($env:USERNAME):R"

Write-Host "✓ Permissões da chave SSH atualizadas" -ForegroundColor Green
```

### Passo 3: Configurar o VS Code para usar o arquivo config correto

1. **Abra o VS Code**
2. **Pressione `Ctrl+,`** para abrir as configurações
3. **Pesquise por "remote.SSH.configFile"**
4. **Defina o valor como:** `C:\Users\SEU_USUARIO\.ssh\config`
   - Substitua `SEU_USUARIO` pelo seu nome de usuário do Windows
   - Ou use o caminho completo que apareceu no Passo 1

### Passo 4: Testar a Conexão

#### Opção A: Testar pelo PowerShell

```powershell
# Testar conexão SSH diretamente
ssh -v vps-ubuntu

# Se funcionar, você verá mensagens de debug e será conectado
```

#### Opção B: Testar pelo VS Code

1. **Reinicie o VS Code** (importante!)
2. **Clique no ícone do Remote-SSH** na barra lateral esquerda
3. **Clique em "Connect to Host..."**
4. **Selecione "vps-ubuntu"** da lista
5. **A conexão deve funcionar agora**

## 🔍 Verificação de Problemas Comuns

### Problema 1: Chave SSH não está no servidor

Se ainda pedir senha, a chave pública pode não estar no servidor. Siga as instruções em `CONFIGURAR_CHAVE_SSH.md`.

### Problema 2: IP da VPS mudou

Verifique se o IP `179.0.178.106` ainda está correto. Você pode testar:

```powershell
ping 179.0.178.106
```

### Problema 3: Firewall bloqueando

Verifique se o firewall do Windows não está bloqueando:

```powershell
# Verificar se a porta 22 está acessível
Test-NetConnection -ComputerName 179.0.178.106 -Port 22
```

## 📋 Script de Verificação Completa

Execute este script para verificar tudo de uma vez:

```powershell
Write-Host "=== Verificação Completa SSH ===" -ForegroundColor Cyan

# 1. Verificar arquivo config
Write-Host "`n1. Verificando arquivo de configuração SSH..." -ForegroundColor Yellow
if (Test-Path "$env:USERPROFILE\.ssh\config") {
    Write-Host "✓ Arquivo config existe" -ForegroundColor Green
    Write-Host "Conteúdo:" -ForegroundColor Gray
    Get-Content "$env:USERPROFILE\.ssh\config" | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
} else {
    Write-Host "✗ Arquivo config não encontrado" -ForegroundColor Red
}

# 2. Verificar chave SSH
Write-Host "`n2. Verificando chave SSH..." -ForegroundColor Yellow
if (Test-Path "d:\photoapp_v2\toni@photum.com.br") {
    Write-Host "✓ Chave privada existe" -ForegroundColor Green
} else {
    Write-Host "✗ Chave privada não encontrada" -ForegroundColor Red
}

if (Test-Path "d:\photoapp_v2\toni@photum.com.br.pub") {
    Write-Host "✓ Chave pública existe" -ForegroundColor Green
} else {
    Write-Host "✗ Chave pública não encontrada" -ForegroundColor Red
}

# 3. Verificar OpenSSH
Write-Host "`n3. Verificando OpenSSH..." -ForegroundColor Yellow
$sshVersion = ssh -V 2>&1
if ($sshVersion) {
    Write-Host "✓ OpenSSH instalado: $sshVersion" -ForegroundColor Green
} else {
    Write-Host "✗ OpenSSH não encontrado" -ForegroundColor Red
}

# 4. Testar conectividade
Write-Host "`n4. Testando conectividade com a VPS..." -ForegroundColor Yellow
$connectionTest = Test-NetConnection -ComputerName 179.0.178.106 -Port 22 -WarningAction SilentlyContinue
if ($connectionTest.TcpTestSucceeded) {
    Write-Host "✓ Porta 22 está acessível" -ForegroundColor Green
} else {
    Write-Host "✗ Não foi possível conectar à porta 22" -ForegroundColor Red
}

Write-Host "`n=== Verificação Concluída ===" -ForegroundColor Cyan
```

## 🎯 Resumo da Solução

1. **Copie o arquivo `ssh-config-corrigido` para `C:\Users\SEU_USUARIO\.ssh\config`**
2. **Configure o VS Code para usar esse arquivo** (remote.SSH.configFile)
3. **Reinicie o VS Code**
4. **Teste a conexão**

## ⚠️ Se Ainda Não Funcionar

Se após seguir todos os passos ainda não conseguir conectar:

1. **Verifique os logs completos do VS Code:**
   - Abra o Output do VS Code (`Ctrl+Shift+U`)
   - Selecione "Remote-SSH" no dropdown
   - Copie os logs e analise os erros

2. **Tente conectar manualmente pelo PowerShell:**
   ```powershell
   ssh -v -i "d:\photoapp_v2\toni@photum.com.br" root@179.0.178.106
   ```

3. **Use o PuTTY como alternativa** (veja `SOLUCOES_SSH.md`)

## 📞 Suporte

Se precisar de mais ajuda, forneça:
- Output do script de verificação
- Logs completos do VS Code (Remote-SSH)
- Resultado do teste de conexão manual