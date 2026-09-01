# 🚀 Guia de Atualização da VPS

## ✅ Status Atual

**GitHub**: ✅ Atualizado com todas as melhorias (commit `fba7bb8`)
- Seu trabalho local foi enviado com sucesso
- Todas as funcionalidades novas estão no GitHub
- Local e GitHub estão sincronizados

**VPS**: ⚠️ Precisa ser atualizada

---

## 📋 O Que Será Atualizado na VPS

Baseado nas diferenças entre o GitHub e a VPS, a atualização incluirá:

### 🎯 Principais Melhorias
1. **Funcionalidade de Selfie** - Cadastro público com captura de selfie
2. **PWA (Progressive Web App)** - Service worker e recursos offline
3. **Melhorias de Responsividade** - Dashboard e botões otimizados para mobile
4. **Novos Templates** - Interface de coordenador e captura de selfie
5. **Migrações de Banco** - Novos campos e tabelas
6. **Correções de Bugs** - Configuração de câmera e crop inteligente

### 📁 Arquivos que Serão Atualizados
- `gestcaptur/views.py` - Novas views de selfie
- `gestcaptur/urls.py` - Novas rotas
- `gestcaptur/models.py` - Novos modelos
- `gestcaptur/templates/` - Templates atualizados
- `staticfiles/` - Arquivos estáticos atualizados
- `photoapp/settings.py` - Configurações atualizadas

---

## 🔧 Passo a Passo para Atualizar a VPS

### Método 1: Atualização Automática (Recomendado)

#### 1. Acessar a VPS via SSH
```bash
ssh -i "d:\photoapp_v2\toni@photum.com.br" toni@photum.com.br
```

#### 2. Navegar até o diretório do projeto
```bash
cd /home/admsuporte/photoapp
```

#### 3. Parar o serviço Gunicorn
```bash
sudo systemctl stop gunicorn-photoapp.service
```

#### 4. Fazer backup do banco de dados (IMPORTANTE!)
```bash
# Se estiver usando SQLite
cp db.sqlite3 db.sqlite3.backup.$(date +%Y%m%d_%H%M%S)

# Se estiver usando MySQL/PostgreSQL
# mysqldump -u usuario -p nome_banco > backup_$(date +%Y%m%d_%H%M%S).sql
```

#### 5. Atualizar o código do GitHub
```bash
git fetch origin
git reset --hard origin/main
```

#### 6. Atualizar dependências Python
```bash
source venv/bin/activate
pip install -r requirements.txt
```

#### 7. Aplicar migrações do Django
```bash
python manage.py migrate
```

#### 8. Coletar arquivos estáticos
```bash
python manage.py collectstatic --noinput
```

#### 9. Reiniciar o serviço Gunicorn
```bash
sudo systemctl start gunicorn-photoapp.service
```

#### 10. Verificar status do serviço
```bash
sudo systemctl status gunicorn-photoapp.service
```

#### 11. Verificar logs (opcional)
```bash
sudo journalctl -u gunicorn-photoapp.service -f
```

Pressione `Ctrl+C` para sair dos logs.

---

### Método 2: Script Automático

Crie um script de atualização na VPS:

#### 1. Criar o script
```bash
cd /home/admsuporte/photoapp
nano atualizar_vps.sh
```

#### 2. Cole o seguinte conteúdo:
```bash
#!/bin/bash

echo "🚀 Iniciando atualização do PhotoApp VPS..."
echo "============================================"

# Parar serviço
echo "🛑 Parando Gunicorn..."
sudo systemctl stop gunicorn-photoapp.service

# Backup
DATA=$(date +%Y%m%d_%H%M%S)
echo "💾 Criando backup do banco de dados..."
if [ -f "db.sqlite3" ]; then
    cp db.sqlite3 db.sqlite3.backup.$DATA
    echo "   Backup criado: db.sqlite3.backup.$DATA"
fi

# Atualizar código
echo "📥 Atualizando código do GitHub..."
git fetch origin
git reset --hard origin/main

# Atualizar dependências
echo "📦 Atualizando dependências Python..."
source venv/bin/activate
pip install -r requirements.txt

# Migrações
echo "🗄️  Aplicando migrações..."
python manage.py migrate

# Coletar estáticos
echo "🎨 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

# Reiniciar serviço
echo "🔄 Reiniciando Gunicorn..."
sudo systemctl start gunicorn-photoapp.service

# Verificar status
echo "✅ Verificando status..."
sudo systemctl status gunicorn-photoapp.service --no-pager

echo ""
echo "🎉 Atualização concluída!"
echo "   Commit atual: $(git log -1 --oneline)"
```

#### 3. Salvar e sair
Pressione `Ctrl+X`, depois `Y` e `Enter`.

#### 4. Dar permissão de execução
```bash
chmod +x atualizar_vps.sh
```

#### 5. Executar o script
```bash
./atualizar_vps.sh
```

---

## 🧪 Testar Após Atualização

### 1. Acessar o sistema
- Abra o navegador e acesse: `https://cliente.photum.com.br:2543`
- Teste o login no dashboard

### 2. Testar nova funcionalidade de selfie
- Acesse um evento com captura de selfie
- Teste o cadastro público com selfie

### 3. Verificar PWA
- Acesse pelo celular
- Verifique se aparece opção de "Adicionar à tela inicial"

### 4. Testar responsividade
- Redimensione a janela do navegador
- Teste em diferentes dispositivos

---

## ⚠️ Solução de Problemas

### Problema: Erro nas migrações
```bash
# Se houver conflito de migrações
python manage.py migrate --fake-initial
```

### Problema: Serviço não inicia
```bash
# Verificar logs detalhados
sudo journalctl -u gunicorn-photoapp.service -n 100 --no-pager

# Reiniciar serviço
sudo systemctl restart gunicorn-photoapp.service
```

### Problema: Erro de permissão
```bash
# Corrigir permissões
sudo chown -R admsuporte:admsuporte /home/admsuporte/photoapp
sudo chmod -R 755 /home/admsuporte/photoapp
```

### Problema: Arquivos estáticos não carregam
```bash
# Recriar symbolic links do Nginx se necessário
sudo systemctl restart nginx
```

---

## 📞 Rollback (Voltar Versão Anterior)

Se algo der errado, você pode voltar para a versão anterior:

```bash
cd /home/admsuporte/photoapp

# Listar commits anteriores
git log --oneline -10

# Voltar para o commit anterior (substitua HASH pelo hash desejado)
git reset --hard HASH_ANTERIOR

# Reiniciar serviço
sudo systemctl restart gunicorn-photoapp.service
```

---

## 📊 Resumo da Atualização

| Item | Status |
|------|--------|
| **GitHub** | ✅ Atualizado (commit `fba7bb8`) |
| **Local (Windows)** | ✅ Sincronizado com GitHub |
| **VPS** | ⚠️ Aguardando atualização |
| **Backup** | ⚠️ Fazer antes de atualizar |
| **Tempo estimado** | 5-10 minutos |

---

## 🎯 Checklist de Atualização

- [ ] Acessar VPS via SSH
- [ ] Parar serviço Gunicorn
- [ ] Fazer backup do banco de dados
- [ ] Atualizar código do GitHub
- [ ] Atualizar dependências Python
- [ ] Aplicar migrações
- [ ] Coletar arquivos estáticos
- [ ] Reiniciar serviço Gunicorn
- [ ] Testar acesso ao sistema
- [ ] Testar nova funcionalidade de selfie
- [ ] Verificar logs em caso de erro

---

**Dúvidas?** Execute o script `comparar_vps.sh` antes e depois da atualização para ver as diferenças.

**Última atualização**: 11/05/2026 - 11:48