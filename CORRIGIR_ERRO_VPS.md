# 🚨 Guia de Emergência - Corrigir Erro na VPS

## ❌ Problema Identificado

O arquivo `settings.py` na VPS está com **conflitos de merge** não resolvidos:
```python
<<<<<<< HEAD
^
```

Isso impede o Django de funcionar.

## 🔧 Solução Imediata

### Passo 1: Acessar a VPS
Conecte-se via SSH (use PuTTY ou terminal):
```bash
ssh toni@photum.com.br
# ou
ssh -i /caminho/da/chave toni@photum.com.br
```

### Passo 2: Navegar até o projeto
```bash
cd /var/www/photoapp
```

### Passo 3: Verificar status do git
```bash
git status
```

Provavelmente mostrará algo como:
```
both modified: photoapp/settings.py
```

### Passo 4: Resolver o conflito (Método Rápido)

Como queremos a versão mais recente do GitHub, execute:

```bash
# 1. Cancelar qualquer merge em andamento
git merge --abort

# 2. Forçar atualização para a versão do GitHub
git fetch origin
git reset --hard origin/main

# 3. Verificar se o arquivo está correto
head -20 photoapp/settings.py
```

O arquivo `settings.py` não deve mais ter os marcadores `<<<<<<< HEAD`.

### Passo 5: Método Automático (Recomendado)

**Use este método se o rápido não funcionar ou se houver muitos conflitos:**

1. **Copie o script de limpeza para a VPS:**
   ```bash
   # No seu computador Windows (PowerShell):
   scp -i "d:\photoapp_v2\toni@photum.com.br" d:\photoapp_v2\limpar_vps.sh toni@photum.com.br:~/
   ```

2. **Na VPS, execute o script:**
   ```bash
   # Acesse a VPS
   ssh toni@photum.com.br
   
   # Navegue até o projeto
   cd /var/www/photoapp
   
   # Copie o script para o diretório do projeto
   cp ~/limpar_vps.sh .
   
   # Dê permissão de execução
   chmod +x limpar_vps.sh
   
   # Execute o script
   sudo ./limpar_vps.sh
   ```

O script fará tudo automaticamente:
- ✅ Parar o serviço
- ✅ Backup do banco
- ✅ Remover repositório com conflitos
- ✅ Clonar versão limpa do GitHub
- ✅ Verificar e remover conflitos restantes
- ✅ Recriar ambiente virtual
- ✅ Instalar dependências
- ✅ Aplicar migrações
- ✅ Coletar estáticos
- ✅ Reiniciar serviço

### Passo 6: Verificar se funcionou

```bash
# Testar se o Django funciona
python manage.py check

# Ver logs do Gunicorn
sudo journalctl -u gunicorn-photoapp.service -n 50

# Acessar o sistema no navegador
# https://cliente.photum.com.br:2543
```

---

## 🛡️ Prevenção para o Futuro

Sempre que for atualizar a VPS, use este fluxo seguro:

```bash
#!/bin/bash
# atualizar_seguro.sh

echo "🔄 Iniciando atualização segura..."

# 1. Parar serviço
sudo systemctl stop gunicorn-photoapp.service

# 2. Backup
cp db.sqlite3 db.sqlite3.backup.$(date +%Y%m%d_%H%M%S)

# 3. Atualizar
git fetch origin
git reset --hard origin/main  # Isso evita conflitos!

# 4. Dependências
source venv/bin/activate
pip install -r requirements.txt

# 5. Migrações
python manage.py migrate

# 6. Estáticos
python manage.py collectstatic --noinput

# 7. Reiniciar
sudo systemctl start gunicorn-photoapp.service

echo "✅ Atualização concluída!"
```

---

## ⚠️ Importante

- **NUNCA** use `git pull` direto na VPS se houver possibilidade de conflitos
- **SEMPRE** use `git fetch` + `git reset --hard origin/main` para garantir versão limpa
- **SEMPRE** faça backup do banco antes de atualizar
- **TESTE** sempre após a atualização

---

## 📞 Se Nada Funcionar

Se você não conseguir corrigir, podemos:

1. **Restaurar backup anterior** (se tiver)
2. **Reinstalar do zero** usando o script de deploy
3. **Pedir ajuda** com o log completo de erros

---

**Execute os passos na ordem e reporte qualquer erro!**