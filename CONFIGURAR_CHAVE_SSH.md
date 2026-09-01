# 🔑 Como Configurar a Chave SSH na VPS

## ❌ Problema Identificado

O SSH está pedindo senha em vez de usar a chave, o que indica que:
- A chave pública **NÃO** está no arquivo `authorized_keys` do servidor
- OU as permissões do arquivo `authorized_keys` estão incorretas

## 🔧 Solução: Adicionar a Chave Pública ao Servidor

### Passo 1: Pegar o Conteúdo da Chave Pública

No seu computador Windows:

1. **Abra o arquivo da chave pública:**
   - Vá até `d:\photoapp_v2`
   - Abra o arquivo `toni@photum.com.br.pub` com o Bloco de Notas
   - **Copie TODO o conteúdo** (deve começar com `ssh-rsa` ou `ssh-ed25519`)

2. **O conteúdo deve ser algo assim:**
   ```
   ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC7... (muito texto) ...== toni@photum.com.br
   ```

### Passo 2: Acessar a VPS Pelo Painel da Locaweb

Como o SSH não está funcionando, use o **Console Web**:

1. **Acesse o painel da Locaweb:**
   - Vá para https://www.locaweb.com.br/
   - Faça login na sua conta

2. **Navegue até sua VPS:**
   - Clique em "Produtos" ou "Meus Produtos"
   - Encontre "VPS" ou "Servidor Virtual"
   - Clique na sua VPS (deve aparecer o IP `179.188.11.96`)

3. **Acesse o Console Web:**
   - Procure por "Console", "Acesso Remoto" ou "VNC"
   - Clique para abrir o console
   - Isso dará acesso direto à máquina, sem precisar de SSH

### Passo 3: Adicionar a Chave ao Servidor

Uma vez no console da VPS:

```bash
# 1. Faça login (se pedir usuário/senha, use as credenciais da VPS)
# Normalmente: usuário = toni, senha = (a que você configurou)

# 2. Crie a pasta .ssh se não existir
mkdir -p ~/.ssh

# 3. Defina permissões corretas
chmod 700 ~/.ssh

# 4. Edite o arquivo authorized_keys
nano ~/.ssh/authorized_keys

# 5. Cole a chave pública que você copiou no Passo 1
# No nano:
# - Pressione Ctrl+Shift+V para colar
# - Ou clique com botão direito → Paste

# 6. Salve e saia do nano:
# - Pressione Ctrl+X
# - Pressione Y para salvar
# - Pressione Enter

# 7. Defina permissões corretas no arquivo
chmod 600 ~/.ssh/authorized_keys

# 8. Verifique se a chave foi adicionada
cat ~/.ssh/authorized_keys

# 9. Reinicie o serviço SSH
sudo systemctl restart sshd

# 10. Teste a conexão (se conseguir sair do console)
# exit
```

### Passo 4: Testar Conexão SSH

Depois de adicionar a chave, tente conectar novamente:

```powershell
# No PowerShell do Windows:
ssh -i "d:\photoapp_v2\toni@photum.com.br" toni@photum.com.br
```

**Se funcionar**, você estará conectado à VPS!

---

## 🔧 Método Alternativo: Usar Senha (Se Souber)

Se você **sabe a senha** do usuário `toni` na VPS:

```powershell
# Tente conectar com senha:
ssh toni@photum.com.br
# Digite a senha quando pedir

# Uma vez conectado, adicione sua chave pública:
mkdir -p ~/.ssh
echo "COLE_AQUI_SUA_CHAVE_PUBLICA" >> ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
exit
```

Depois disso, o SSH com chave deve funcionar.

---

## 🔧 Método Alternativo: Criar Nova Chave SSH

Se a chave atual estiver corrompida, crie uma nova:

### No Windows (PowerShell):

```powershell
# 1. Crie uma nova chave
ssh-keygen -t ed25519 -C "toni@photum.com.br" -f "d:\photoapp_v2\nova_chave"

# 2. Vai pedir uma senha (pode deixar vazio pressionando Enter)

# 3. Isso criará dois arquivos:
#    - d:\photoapp_v2\nova_chave (chave privada)
#    - d:\photoapp_v2\nova_chave.pub (chave pública)

# 4. Siga os passos acima para adicionar a NOVA chave pública ao servidor
```

---

## 📋 Resumo dos Passos

1. **Copie o conteúdo de `toni@photum.com.br.pub`**
2. **Acesse a VPS pelo Console Web da Locaweb**
3. **Adicione a chave pública em `~/.ssh/authorized_keys`**
4. **Defina permissões corretas (`chmod 600`)**
5. **Reinicie o SSH (`sudo systemctl restart sshd`)**
6. **Teste a conexão SSH**

---

## ⚠️ Se Não Conseguir Acessar o Console Web

Se não encontrar o console web no painel da Locaweb:

1. **Contate o suporte da Locaweb** - Eles podem:
   - Resetar a senha do usuário
   - Adicionar sua chave pública manualmente
   - Fornecer acesso ao console

2. **Peça ajuda a alguém** que já tenha acesso à VPS

3. **Considere reinstalar a VPS** - Como último recurso

---

## 🎯 Próximos Passos Após Resolver o SSH

Uma vez conectado à VPS, execute:

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

**Boa sorte! O problema é apenas configurar a chave SSH corretamente.**