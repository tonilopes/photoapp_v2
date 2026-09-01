# 📝 Como Criar o Arquivo .env na VPS

## 🔧 Passo a Passo

### 1. No console da VPS, navegue até o projeto:
```bash
cd /var/www/photoapp
```

### 2. Crie o arquivo .env:
```bash
nano .env
```

### 3. Cole o seguinte conteúdo (ajuste os valores):

```bash
# =====================================================
# CONFIGURAÇÕES DJANGO - PhotoApp VPS
# =====================================================

# Segurança
SECRET_KEY=sua-secret-key-aqui-gerar-uma-nova
DEBUG=False

# Hosts permitidos (IPs/domínios do seu servidor)
ALLOWED_HOSTS=179.188.11.96,cliente.photum.com.br,localhost,127.0.0.1

# Banco de Dados (se usar SQLite)
DB_NAME=db.sqlite3
DB_ENGINE=django.db.backends.sqlite3

# Se usar PostgreSQL/MySQL, descomente e ajuste:
# DB_NAME=nome_do_banco
# DB_USER=usuario
# DB_PASSWORD=senha
# DB_HOST=localhost
# DB_PORT=5432
# DB_ENGINE=django.db.backends.postgresql

# Email (configure com seus dados)
EMAIL_HOST=smtp.seuprovedor.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seu_email@seudominio.com
EMAIL_HOST_PASSWORD=sua_senha_email
DEFAULT_FROM_EMAIL=noreply@seudominio.com

# URLs
SITE_URL=https://cliente.photum.com.br:2543
CSRF_TRUSTED_ORIGINS=https://cliente.photum.com.br:2543,https://179.188.11.96:2543

# Segurança CSRF
CSRF_TRUSTED_ORIGINS=https://cliente.photum.com.br:2543

# Configurações de Mídia
MEDIA_URL=/media/
MEDIA_ROOT=/var/www/photoapp/media

# Arquivos Estáticos
STATIC_URL=/static/
STATIC_ROOT=/var/www/photoapp/staticfiles

# Timezone
TIME_ZONE=America/Sao_Paulo
LANGUAGE_CODE=pt-br

# =====================================================
# FIM DAS CONFIGURAÇÕES
# =====================================================
```

### 4. Salve e saia:
- Pressione `Ctrl+X`
- Pressione `Y` para salvar
- Pressione `Enter`

### 5. Defina permissões seguras:
```bash
chmod 600 .env
```

### 6. Teste o Django:
```bash
source venv/bin/activate
python manage.py check
```

---

## 🎯 Valores Importantes para Ajustar

| Variável | Valor Sugerido | Onde Obter |
|----------|---------------|------------|
| `SECRET_KEY` | Gere uma nova | Execute: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `ALLOWED_HOSTS` | `179.188.11.96,cliente.photum.com.br,localhost` | IP da sua VPS e domínio |
| `EMAIL_HOST` | `smtp.seu provedor.com` | Seu provedor de email |
| `EMAIL_HOST_USER` | `seu_email@seudominio.com` | Seu email |
| `EMAIL_HOST_PASSWORD` | `sua_senha` | Senha do email |

---

## 📋 Resumo

1. **Crie o arquivo `.env`** com `nano .env`
2. **Cole o modelo acima**
3. **Ajuste os valores** (especialmente SECRET_KEY e EMAIL)
4. **Defina permissões** com `chmod 600 .env`
5. **Teste** com `python manage.py check`

---

**Crie o arquivo e me avise se funcionar!**