# 📋 Guia de Uso - Comparador Local vs GitHub

Este guia explica como usar as ferramentas de comparação entre seu ambiente local e o repositório GitHub.

## 🎯 Objetivo

Comparar o que está no seu computador (`d:\photoapp_v2`) com o repositório GitHub (`anlorone/photoapp_v2`) e com a VPS de produção.

---

## 🖥️ No Seu Computador (Windows)

### Método 1: Usando o arquivo batch (mais fácil)

1. Abra o Explorador de Arquivos
2. Navegue até `d:\photoapp_v2`
3. Dê dois cliques em **`comparar.bat`**

### Método 2: Usando Python diretamente

1. Abra o PowerShell ou Prompt de Comando
2. Execute:
```cmd
cd d:\photoapp_v2
python comparar_com_github.py
```

### O que o script mostra:

- **📊 COMPARAÇÃO DE COMMITS**: Mostra quais commits estão no local mas não no GitHub, e vice-versa
- **📁 COMPARAÇÃO DE ARQUIVOS**: Lista arquivos modificados, adicionados ou deletados
- **📂 STATUS LOCAL**: Mostra arquivos não versionados no seu diretório
- **📋 RESUMO**: Visão geral da situação

---

## 🖥️ Na VPS (Ubuntu/Linux)

### Passo 1: Copiar o script para a VPS

Você precisa copiar o arquivo `comparar_vps.sh` para a VPS. Use um destes métodos:

#### Método A: Usando SCP (recomendado)
No seu computador Windows, abra o PowerShell:
```powershell
scp -i "d:\photoapp_v2\toni@photum.com.br" d:\photoapp_v2\comparar_vps.sh toni@photum.com.br:~/
```

#### Método B: Usando WinSCP ou FileZilla
1. Conecte-se à VPS usando WinSCP ou FileZilla
2. Navegue até `d:\photoapp_v2`
3. Arraste o arquivo `comparar_vps.sh` para a pasta home do usuário na VPS

### Passo 2: Acessar a VPS via SSH

Use o terminal ou PuTTY para conectar:
```bash
ssh -i "d:\photoapp_v2\toni@photum.com.br" toni@photum.com.br
```

### Passo 3: Executar o script na VPS

Uma vez conectado à VPS:

```bash
# 1. Navegue até o diretório do projeto
cd /home/admsuporte/photoapp

# 2. Copie o script para o diretório do projeto (se estiver na home)
cp ~/comparar_vps.sh .

# 3. Dê permissão de execução
chmod +x comparar_vps.sh

# 4. Execute o script
./comparar_vps.sh
```

### O que o script da VPS mostra:

O script na VPS fará a mesma comparação que o script local, mostrando:
- Diferenças entre a VPS e o GitHub
- Commits que precisam ser atualizados
- Arquivos modificados
- Recomendações de ações necessárias

---

## 🔍 Interpretando os Resultados

### Cenário 1: Tudo sincronizado ✅
```
✅ Local e remoto estão SYNCRONIZADOS!
```
**Significado**: Sua versão local/VPS está igual ao GitHub. Nenhuma ação necessária.

### Cenário 2: VPS atrasada em relação ao GitHub ⚠️
```
📥 Seu local está X commit(s) ATRASADO
```
**Significado**: Existem atualizações no GitHub que não estão na VPS.

**Ação recomendada na VPS**:
```bash
cd /home/admsuporte/photoapp
git pull origin main
```

### Cenário 3: Local adiantado em relação ao GitHub 📤
```
📤 Seu local está X commit(s) À FRENTE
```
**Significado**: Você tem commits no seu computador que ainda não foram enviados para o GitHub.

**Ação recomendada no seu computador**:
```cmd
cd d:\photoapp_v2
git push origin main
```

---

## 📊 Situação Atual (Baseado na última comparação)

No momento, a comparação mostrou:

### No seu computador (d:\photoapp_v2):
- **6 commits À FRENTE** do GitHub
- **4 commits ATRASADO** em relação ao GitHub
- **Muitas diferenças** nos arquivos

Isso significa que:
1. Você tem trabalho local que ainda não foi enviado para o GitHub
2. O GitHub tem atualizações que você ainda não baixou

### Próximos passos recomendados:

1. **No seu computador**:
   ```cmd
   cd d:\photoapp_v2
   git fetch origin
   git merge origin/main  # ou git pull
   ```

2. **Depois de sincronizar localmente**, envie suas alterações:
   ```cmd
   git push origin main
   ```

3. **Na VPS**, execute o script para verificar se precisa atualizar:
   ```bash
   cd /home/admsuporte/photoapp
   ./comparar_vps.sh
   ```

4. **Se a VPS estiver atrasada**, atualize:
   ```bash
   git pull origin main
   ```

---

## 🛠️ Solução de Problemas

### Problema: Erro de chave SSH
Se você receber erros como "Corrupted MAC on input", tente:
```bash
ssh -o MACs=hmac-sha2-256 -i "caminho/da/chave" usuario@servidor
```

### Problema: Permissão negada no script da VPS
Execute:
```bash
chmod +x comparar_vps.sh
```

### Problema: Git não encontrado na VPS
Instale o git:
```bash
sudo apt update
sudo apt install git
```

---

## 📞 Precisa de Ajuda?

Se tiver dúvidas ou problemas, execute os scripts e compartilhe o output completo para análise.

---

**Última atualização**: 11/05/2026