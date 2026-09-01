# 🔑 Soluções para Problemas de SSH

## ❌ Problema Atual

- Erro `Corrupted MAC on input` com a maioria das opções
- Quando funciona, pede senha em vez de usar a chave

## 🔧 Soluções para Testar

### Solução 1: Verificar Permissões da Chave (Windows)

No Windows, as permissões do arquivo de chave devem estar corretas:

1. **Abra o PowerShell como Administrador**

2. **Execute estes comandos:**
   ```powershell
   # Navegue até a pasta da chave
   cd d:\photoapp_v2
   
   # Defina permissões corretas (apenas seu usuário)
   icacls "toni@photum.com.br" /inheritance:r
   icacls "toni@photum.com.br" /grant:r "$($env:USERNAME):R"
   
   # Tente conectar novamente
   ssh -o MACs=hmac-sha2-256 -i "toni@photum.com.br" toni@photum.com.br
   ```

### Solução 2: Usar PuTTY (Recomendado para Windows)

O PuTTY funciona melhor no Windows:

1. **Baixe o PuTTY**: https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html

2. **Converta a chave para formato .ppk:**
   - Abra o PuTTYgen (instalado com PuTTY)
   - Clique em "Load"
   - Selecione `d:\photoapp_v2\toni@photum.com.br`
   - Clique em "Save private key" → salve como `toni@photum.com.br.ppk`

3. **Configure a conexão no PuTTY:**
   - Host Name: `photum.com.br`
   - Port: `22`
   - Connection type: `SSH`
   - Em "Connection" → "Data":
     - Auto-login username: `toni`
   - Em "Connection" → "SSH" → "Auth":
     - Private key file for authentication: `d:\photoapp_v2\toni@photum.com.br.ppk`
   - Clique em "Open"

4. **Se pedir senha**, tente:
   - Usuário: `toni`
   - Senha: (deixe vazio ou tente senhas comuns)

### Solução 3: Verificar se a Chave Está no Servidor

Às vezes a chave não está configurada corretamente no servidor:

1. **Tente conectar com senha** (se souber a senha):
   ```powershell
   ssh toni@photum.com.br
   # Digite a senha quando pedir
   ```

2. **Uma vez conectado, verifique as chaves:**
   ```bash
   # Na VPS, verifique se sua chave está no arquivo authorized_keys
   cat ~/.ssh/authorized_keys
   
   # Se não estiver, adicione sua chave pública
   # Primeiro, no Windows, copie o conteúdo de toni@photum.com.br.pub
   # Depois, na VPS:
   echo "COLE_AQUI_O_CONTEUDO_DA_CHAVE_PUBLICA" >> ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   ```

### Solução 4: Reconfigurar SSH na VPS

Se conseguir acesso por outro método (painel da Locaweb):

```bash
# 1. Verifique as permissões SSH
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys

# 2. Reinicie o serviço SSH
sudo systemctl restart sshd

# 3. Verifique logs
sudo tail -f /var/log/auth.log
```

### Solução 5: Painel da Locaweb (Último Recurso)

Se nada funcionar:

1. **Acesse o painel da Locaweb**: https://www.locaweb.com.br/

2. **Vá para sua VPS**:
   - Produtos → VPS → Sua VPS

3. **Use o Console Web**:
   - Procure por "Console" ou "Acesso Remoto"
   - Isso dá acesso direto à máquina sem SSH

4. **Uma vez no console, execute os comandos de limpeza**:
   ```bash
   cd /var/www/photoapp
   sudo systemctl stop gunicorn-photoapp.service
   cp db.sqlite3 db.sqlite3.backup.$(date +%Y%m%d_%H%M%S)
   cd /var/www && rm -rf photoapp
   git clone git@github.com:anlorone/photoapp_v2.git photoapp
   cd photoapp
   python3 -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py collectstatic --noinput
   sudo systemctl start gunicorn-photoapp.service
   python manage.py check
   ```

---

## 📋 Checklist de Tentativas

- [ ] Testar permissões da chave no Windows (Solução 1)
- [ ] Usar PuTTY com chave convertida (Solução 2)
- [ ] Tentar conectar com senha se souber (Solução 3)
- [ ] Acessar painel da Locaweb (Solução 5)
- [ ] Usar console web da Locaweb (Solução 5)

---

## ⚠️ Se Nada Funcionar

Se você não conseguir acesso de forma alguma:

1. **Contate o suporte da Locaweb** - Eles podem resetar o acesso SSH
2. **Peça ajuda a alguém com acesso** - Alguém que já tenha acessado a VPS antes
3. **Considere reinstalar a VPS** - Como último recurso, reinstale o sistema e configure do zero

---

## 🎯 Prioridade

Tente nesta ordem:
1. **PuTTY** (Solução 2) - Mais provável de funcionar no Windows
2. **Painel da Locaweb** (Solução 5) - Acesso garantido
3. **Console Web** (Solução 5) - Último recurso

**Boa sorte!**