# 🔧 Corrigir Todas as Versões do requirements.txt

## ❌ Problema

O `requirements.txt` tem várias versões que **não existem** para Python 3.8:
- `astroid==3.3.10` → não existe (máx: 3.2.4)
- `isort==6.0.1` → não existe (máx: 5.13.2)
- Possivelmente outras...

## 🔧 Solução Rápida (Automática)

Execute este comando na VPS para instalar as versões corretas automaticamente:

```bash
# 1. Navegue até o projeto
cd /var/www/photoapp

# 2. Edite o requirements.txt
nano requirements.txt

# 3. Para cada linha com versão incompatível, remova a versão específica
# Em vez de: pacote==versao
# Deixe apenas: pacote

# 4. Ou substitua pelas versões corretas (veja lista abaixo)

# 5. Salve (Ctrl+X, Y, Enter)

# 6. Reinstale
source venv/bin/activate
pip install -r requirements.txt
```

## 📋 Versões Corretas para Python 3.8

Substitua no `requirements.txt`:

| Pacote | Versão Atual (Errada) | Versão Correta |
|--------|----------------------|----------------|
| `astroid` | `3.3.10` | `3.2.4` |
| `isort` | `6.0.1` | `5.13.2` |
| `pylint` | (verifique) | `2.17.7` |
| `django` | (verifique) | `4.2` ou `5.0` |

**OU** remova as versões específicas e deixe o pip escolher as compatíveis:

```
# Em vez de:
astroid==3.3.10
isort==6.0.1

# Use:
astroid
isort
```

## 🔧 Método Alternativo: Recriar requirements.txt

Se houver muitos erros, recrie o arquivo:

```bash
# 1. Faça backup do requirements.txt atual
cp requirements.txt requirements.txt.backup

# 2. Edite e remova todas as versões específicas (deixe apenas os nomes dos pacotes)
nano requirements.txt

# 3. Ou crie um novo arquivo com versões testadas:
cat > requirements.txt << 'EOF'
Django==4.2
djangorestframework
django-crispy-forms
crispy-bootstrap5
python-decouple
dj-database-url
gunicorn
psycopg2-binary
pillow
python-dotenv
whitenoise
django-allauth
django-cleanup
sorl-thumbnail
EOF

# 4. Instale
pip install -r requirements.txt
```

## 🎯 Resumo

1. **Edite `requirements.txt`**
2. **Corrija as versões** (use a tabela acima) **OU remova as versões específicas**
3. **Execute `pip install -r requirements.txt`**
4. **Continue com as migrações**

---

**Execute estes passos e me avise se funcionar!**