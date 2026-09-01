# 📋 Instruções Manuais para VPS (Sem SCP)

## 🚨 Problema de Conexão SSH

Se você está com erros como:
- `Corrupted MAC on input`
- `ssh_dispatch_run_fatal: Connection to ... port 22: message authentication code incorrect`

Siga estas soluções:

---

## 🔧 Solução 1: Copiar Script Manualmente

Como não consegue usar SCP, copie o conteúdo do script manualmente:

### Passo 1: Abrir o arquivo do script
No seu computador, abra o arquivo `d:\photoapp_v2\limpar_vps.sh` com o Bloco de Notas.

### Passo 2: Copiar todo o conteúdo
Selecione todo o texto (Ctrl+A) e copie (Ctrl+C).

### Passo 3: Acessar a VPS
Use um cliente SSH alternativo:

#### Opção A: PuTTY
1. Baixe e instale o PuTTY se não tiver
2. Em "Host Name", coloque: `photum.com.br`
3. Em "Port", coloque: `22`
4. Em "Connection type", selecione: `SSH`
5. Em "Connection" → "Data", coloque o usuário: `toni`
6. Em "Connection" → "SSH" → "Auth", selecione a chave: `d:\photoapp_v2\toni@photum.com.br`
7. Clique em "Open"

#### Opção B: Windows Terminal/PowerShell com opções alternativas
```powershell
# Tente com opções de cipher diferentes
ssh -c aes128-ctr -i "d:\photoapp_v2\toni@photum.com.br" toni@photum.com.br

# Ou com MAC diferente
ssh -o MACs=hmac-sha2-256 -i "d:\photoapp_v2\toni@photum.com.br" toni@photum.com.br
```

### Passo 4: Criar o script na VPS
Uma vez conectado à VPS:

```bash
# 1. Navegue até o projeto
cd /var/www/photoapp

# 2. Crie um arquivo vazio
nano limpar_vps.sh
```

### Passo 5: Colar o conteúdo
No nano:
1. Pressione `Ctrl+Shift+V` (ou botão direito → Paste) para colar o conteúdo
2. Pressione `Ctrl+X` para sair
3. Pressione `Y` para salvar
4. Pressione `Enter` para confirmar

### Passo 6: Dar permissão e executar
```bash
# 1. Dê permissão de execução
chmod +x limpar_vps.sh

# 2. Execute o script
sudo ./limpar_vps.sh
```

---

## 🔧 Solução 2: Método Direto (Sem Script)

Se não conseguir nem copiar o script, execute os comandos manualmente:

```bash
# 1. Acesse a VPS (tente as opções acima)
ssh toni@photum.com.br

# 2. Navegue até o projeto
cd /var/www/photoapp

# 3. Pare o serviço
sudo systemctl stop gunicorn-photoapp.service

# 4. Faça backup do banco
cp db.sqlite3 db.sqlite3.backup.manual.$(date +%Y%m%d_%H%M%S)

# 5. Vá para a pasta pai
cd /var/www

# 6. Remova o projeto atual
rm -rf photoapp

# 7. Clone do GitHub
git clone git@github.com:anlorone/photoapp_v2.git photoapp

# 8. Entre no projeto
cd photoapp

# 9. Crie ambiente virtual
python3 -m venv venv

# 10. Ative o ambiente
source venv/bin/activate

# 11. Instale dependências
pip install -r requirements.txt

# 12. Execute migrações
python manage.py migrate

# 13. Colete estáticos
python manage.py collectstatic --noinput

# 14. Reinicie o serviço
sudo systemctl start gunicorn-photoapp.service

# 15. Teste
python manage.py check
```

---

## 🔧 Solução 3: WinSCP (Interface Gráfica)

Se preferir uma interface visual:

1. **Baixe e instale o WinSCP** (https://winscp.net/)

2. **Configure a conexão:**
   - Protocolo: `SFTP`
   - Hostname: `photum.com.br`
   - Port number: `22`
   - Username: `toni`
   - Password: (deixe vazio)
   - Private key file: `d:\photoapp_v2\toni@photum.com.br`

3. **Conecte-se**

4. **Navegue até `/var/www/photoapp`**

5. **Crie o arquivo `limpar_vps.sh`:**
   - Botão direito → New → File
   - Nome: `limpar_vps.sh`
   - Cole o conteúdo do script
   - Salve

6. **Dê permissão de execução:**
   - Botão direito no arquivo → Properties
   - Em "Permissions", marque "Execute" para todos

7. **Execute via terminal SSH** (o WinSCP tem terminal integrado)

---

## 🔧 Solução 4: Se Nada Funcionar

Se você não conseguir acessar a VPS de forma alguma:

### Opção A: Painel de Controle da Locaweb
1. Acesse o painel da Locaweb
2. Vá até "Servidores" ou "VPS"
3. Procure por "Console" ou "Acesso Remoto"
4. Use o console web para acessar

### Opção B: Contatar Suporte
Se for um servidor gerenciado, peça ajuda ao suporte para:
- Resetar a senha SSH
- Reinstalar o projeto do GitHub
- Verificar problemas de conexão

---

## 📞 Verificação Após Correção

Depois de conseguir corrigir, verifique:

```bash
# 1. Status do serviço
sudo systemctl status gunicorn-photoapp.service

# 2. Logs
sudo journalctl -u gunicorn-photoapp.service -n 50

# 3. Teste o Django
python manage.py check

# 4. Acesse no navegador
# https://cliente.photum.com.br:2543
```

---

## ⚠️ Importante

- **Tente diferentes métodos de conexão** até conseguir
- **Sempre faça backup** antes de remover arquivos
- **Teste após cada etapa** para identificar onde está o problema

**Boa sorte! Se conseguir acessar, siga os passos manualmente.**