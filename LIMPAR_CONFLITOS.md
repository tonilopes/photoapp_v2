# 🧹 Limpar Conflitos de Merge dos Arquivos Python

## ❌ Problema

Os arquivos Python ainda têm marcadores de conflito de merge:
```python
<<<<<<< HEAD
...
=======
...
>>>>>>> origin/main
```

Isso causa `SyntaxError: invalid syntax`.

## 🔧 Solução Automática

Execute estes comandos na VPS para remover TODOS os conflitos automaticamente:

```bash
# 1. Navegue até o projeto
cd /var/www/photoapp

# 2. Encontre todos os arquivos Python com conflitos
grep -r "<<<<<<< HEAD" . --include="*.py" -l

# 3. Para cada arquivo com conflito, remova os marcadores
# Este comando remove automaticamente todas as linhas de conflito:
find . -name "*.py" -type f -exec sed -i '/^<<<<<<< /d' {} \;
find . -name "*.py" -type f -exec sed -i '/^=======/d' {} \;
find . -name "*.py" -type f -exec sed -i '/^>>>>>>> /d' {} \;

# 4. Verifique se ainda há conflitos
grep -r "<<<<<<< HEAD" . --include="*.py" | wc -l

# Se retornar 0, está limpo!

# 5. Teste o Django
python manage.py check
```

## 🔧 Solução Manual (Se Preferir)

Se quiser editar manualmente:

```bash
# 1. Veja quais arquivos têm conflitos
grep -r "<<<<<<< HEAD" . --include="*.py" -l

# 2. Edite cada arquivo
nano photoapp/settings.py
# (e outros arquivos listados)

# 3. Em cada arquivo, remova as linhas que contêm:
# <<<<<<< HEAD
# =======
# >>>>>>> origin/main

# 4. Mantenha APENAS o código correto (geralmente a versão mais recente)

# 5. Salve e repita para todos os arquivos
```

## 🎯 Resumo

**Execute os comandos automáticos acima** - eles removerão todos os marcadores de conflito de uma vez.

Depois:
```bash
python manage.py check
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn-photoapp.service
```

---

**Execute e me avise o resultado!**