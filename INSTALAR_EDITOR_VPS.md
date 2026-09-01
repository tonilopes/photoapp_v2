# 📝 Instalar Editor Moderno na VPS

## 🎯 Opções de Editores Melhores que Nano

### Opção 1: Micro (Recomendado - Mais Fácil)

O **micro** é um editor moderno, intuitivo e com recursos como:
- Syntax highlighting
- Mouse support
- Ctrl+C para copiar, Ctrl+V para colar
- Busca e substituição fácil
- Auto-indentação

**Para instalar:**

```bash
# 1. Baixe e instale o micro
cd /tmp
curl -L https://github.com/zyedidia/micro/releases/download/v2.0.13/micro-2.0.13-linux-amd64.tar.gz | tar xz
sudo mv micro-2.0.13/micro /usr/local/bin/
sudo chmod +x /usr/local/bin/micro
rm -rf micro-2.0.13*

# 2. Teste
micro --version

# 3. Use para editar arquivos
micro gestcaptur/views.py
```

**Atalhos do Micro:**
- `Ctrl+S` - Salvar
- `Ctrl+Q` - Sair
- `Ctrl+C` - Copiar
- `Ctrl+V` - Colar
- `Ctrl+F` - Buscar
- `Ctrl+H` - Substituir
- Setas - Mover cursor
- Mouse - Clicar para posicionar

---

### Opção 2: Vim (Clássico e Poderoso)

O **vim** é mais complexo mas muito poderoso:

```bash
# 1. Instale o vim
sudo apt update
sudo apt install vim -y

# 2. Teste
vim --version

# 3. Use para editar
vim gestcaptur/views.py
```

**Atalhos Básicos do Vim:**
- `i` - Entrar no modo de inserção
- `Esc` - Sair do mode de inserção
- `:w` - Salvar
- `:q` - Sair
- `:wq` ou `:x` - Salvar e sair
- `:q!` - Sair sem salvar
- `dd` - Deletar linha
- `yy` - Copiar linha
- `p` - Colar

---

### Opção 3: VS Code Remote SSH (Do Seu Computador)

Se preferir editar no VS Code do seu computador:

1. **Instale a extensão "Remote - SSH" no VS Code**
2. **Configure a conexão SSH** (se conseguir resolver o problema de SSH)
3. **Edite os arquivos diretamente da VPS pelo VS Code**

---

## 🔧 Instalação Rápida (Micro)

Execute estes comandos na VPS:

```bash
# 1. Atualize o sistema
sudo apt update

# 2. Instale dependências
sudo apt install curl -y

# 3. Baixe e instale o micro
cd /tmp
curl -L https://github.com/zyedidia/micro/releases/download/v2.0.13/micro-2.0.13-linux-amd64.tar.gz | tar xz
sudo mv micro-2.0.13/micro /usr/local/bin/
sudo chmod +x /usr/local/bin/micro
rm -rf micro-2.0.13*

# 4. Teste
micro --version

# 5. Use para corrigir o erro de indentação
cd /var/www/photoapp
micro gestcaptur/views.py
```

---

## 📋 Resumo

| Editor | Dificuldade | Vantagens |
|--------|-------------|-----------|
| **Micro** | Fácil | Moderno, intuitivo, atalhos simples |
| **Vim** | Médio | Poderoso, padrão em servidores |
| **VS Code Remote** | Fácil | Interface gráfica, do seu computador |

---

## 🎯 Recomendação

**Use o Micro** - é o mais fácil e tem todos os recursos que você precisa!

---

**Instale e me avise se funcionar!**