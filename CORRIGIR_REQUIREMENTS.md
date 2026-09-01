# 🔧 Corrigir Erro do astroid no requirements.txt

## ❌ Problema

O arquivo `requirements.txt` tem:
```
astroid==3.3.10
```

Mas essa versão **não existe** para Python 3.8. A versão máxima disponível é `3.2.4`.

## 🔧 Solução

### Passo 1: Editar o requirements.txt

No console da VPS, execute:

```bash
# 1. Navegue até o projeto
cd /var/www/photoapp

# 2. Edite o arquivo requirements.txt
nano requirements.txt
```

### Passo 2: Alterar a Versão do astroid

No nano:

1. **Procure pela linha do astroid** (pressione `Ctrl+W` e digite `astroid`)
2. **Mude de:**
   ```
   astroid==3.3.10
   ```
   **Para:**
   ```
   astroid==3.2.4
   ```

3. **Salve e saia:**
   - Pressione `Ctrl+X`
   - Pressione `Y` para salvar
   - Pressione `Enter`

### Passo 3: Reinstalar as Dependências

```bash
# 1. Certifique-se de que está no ambiente virtual
source venv/bin/activate

# 2. Reinstale as dependências
pip install -r requirements.txt
```

### Passo 4: Continuar a Migração

```bash
# 1. Execute as migrações
python manage.py migrate

# 2. Colete os estáticos
python manage.py collectstatic --noinput

# 3. Reinicie o Gunicorn
sudo systemctl start gunicorn-photoapp.service

# 4. Teste
python manage.py check
```

---

## 🎯 Resumo

1. **Edite `requirements.txt`**
2. **Mude `astroid==3.3.10` para `astroid==3.2.4`**
3. **Execute `pip install -r requirements.txt`**
4. **Continue com as migrações**

---

**Execute estes passos e me avise o resultado!**