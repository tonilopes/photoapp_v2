# 🔧 Corrigir Erro de Indentação no views.py

## ❌ Problema

Na linha 1300 do arquivo `gestcaptur/views.py`, há um decorator `@role_required('fotografo')` sem o corpo da função indentado corretamente.

Isso causa:
```
IndentationError: expected an indented block
```

## 🔧 Solução Rápida

### Opção 1: Corrigir Manualmente (Se Souber Qual é a Função)

```bash
# 1. Navegue até o projeto
cd /var/www/photoapp

# 2. Veja o contexto do erro (linhas 1295-1310)
sed -n '1295,1310p' gestcaptur/views.py

# 3. Edite o arquivo
nano gestcaptur/views.py

# 4. Vá até a linha 1300 (Ctrl+_, digite 1300, Enter)

# 5. Verifique se após o decorator há uma função indentada
# Deve ficar assim:
# @role_required('fotografo')
# def nome_da_funcao(request):
#     # corpo da função indentado com 4 espaços
#     ...

# 6. Se não houver função após o decorator, remova o decorator ou adicione a função
```

### Opção 2: Remover o Decorator Problemático

Se não souber o que fazer, remova o decorator:

```bash
# 1. Navegue até o projeto
cd /var/www/photoapp

# 2. Edite o arquivo
nano gestcaptur/views.py

# 3. Vá até a linha 1300 (Ctrl+_, digite 1300, Enter)

# 4. Remova a linha com @role_required('fotografo')
# Use Delete ou Backspace

# 5. Salve (Ctrl+X, Y, Enter)
```

### Opção 3: Verificar se Há Mais Erros de Indentação

```bash
# 1. Verifique a indentação do arquivo inteiro
python -m py_compile gestcaptur/views.py

# Se mostrar erros, corrija cada um
```

## 🎯 Resumo

1. **O erro está na line 1300** de `gestcaptur/views.py`
2. **Há um decorator sem função após ele**
3. **Ou remova o decorator ou adicione a função faltante**

---

**Corrija e me avise se funcionar!**