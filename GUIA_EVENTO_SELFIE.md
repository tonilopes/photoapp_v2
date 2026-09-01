# 🎓 Guia: Criar Evento com Selfie e Cadastro de Formandos

## O que é?
Um **"Evento com Selfie"** permite que formandos:
1. Acessem via **link ou QRCode** (pode ser compartilhado no WhatsApp, e-mail, etc)
2. Capturem uma **selfie em tempo real** via câmera do celular
3. Preencham um **formulário de cadastro online** com dados pessoais
4. Façam **upload automático** da selfie renomeada como `TURMA-NOME.jpg`

## Passo 1: Criar um Evento com Selfie

### Acesso
- Entre como **Gestor**
- Vá para **Dashboard** > **Criar Evento**
- Ou acesse: `https://photoapp.photum.com.br/evento/criar/`

### Preenchimento (Seção "Evento com Selfie e Cadastro de Formandos")

**1️⃣ Ativar Selfie**
- ☑️ Marque: **"Ativar captura de selfie pública para este evento"**
- Isso permite acesso público (sem login) ao formulário de selfie

**2️⃣ Código da Turma** (Opcional)
- Exemplo: `2024-A`, `EM-001`, `3º-Ano-B`
- Este código será usado para renomear as fotos: `TURMA-NOME.jpg`
- Se deixar em branco, será usado apenas o nome

**3️⃣ Permitir Importação de Nomes** (Opcional)
- ☑️ Marque para **importar uma lista de nomes** de um arquivo XLSX
- Útil para pré-validar quem são os formandos

**4️⃣ Salvar Evento**
- Clique em **"Criar Evento"**

---

## Passo 2: Compartilhar com Formandos

### Gerar Link/QRCode
Após criar o evento:
1. Acesse o painel de controle do evento
2. Procure por **"Formandos - Link de Acesso Público"**
3. Você encontrará:
   - **Link direto**: `https://photoapp.photum.com.br/evento/[ID]/selfie-cadastro/`
   - **QRCode**: Para ler com celular

### Compartilhar
- 📱 Enviar link via **WhatsApp** em grupo de formandos
- 📧 Enviar por **e-mail** na convocação
- 🎯 Imprimir **QRCode** em cartazes

---

## Passo 3: Acompanhar Progresso (Painel Gestor)

### Painel de Controle
Acesse: `https://photoapp.photum.com.br/evento/[ID]/formandos-status/`

**Você verá:**
- 📊 **% de Selfies Capturadas**
- 📋 **% de Cadastros Completos**
- 👥 **Lista de Formandos** com status
- ⬇️ **Opção de Exportar** (CSV ou Excel)

### Importar Nomes (Opcional)
Se marcou "Permitir Importação de Nomes":
1. Acesse: `https://photoapp.photum.com.br/evento/[ID]/importar-nomes/`
2. Faça upload de um arquivo XLSX com coluna "nome"
3. Formandos aparecerão pré-cadastrados no painel

---

## Passo 4: O que o Formando Vê?

### Fluxo do Formando

**1. Acessa o Link/QRCode**
- Abre no navegador do celular
- Vê instruções: "Clique para capturar selfie"

**2. Captura Selfie**
- Clica em **"Ativar Câmera"**
- Vê preview em tempo real
- Clica em **"Capturar"** para tirar a foto

**3. Preenche Cadastro**
- **Dados Pessoais**: Nome, CPF, data nascimento
- **Contatos**: E-mail, WhatsApp
- **Endereço**: Rua, número, bairro, cidade
- **Familiares** (opcional)

**4. Sucesso!**
- Recebe mensagem de sucesso
- Selfie é salva como `TURMA-NOME.jpg`
- Link para **editar cadastro** (caso esqueça algo)

---

## Exemplo Prático (Local)

### Scenario: Formatura EM - 2024

**Passo 1: Criar Evento**
```
FOT: FOT001
Data: 15/12/2024
Tipo: Formatura - Ensino Médio
Instituição: Colégio ABC
Código da Turma: 3EM-2024
✅ Ativar Selfie
✅ Permitir Importação de Nomes
```

**Passo 2: Compartilhar Link**
```
Enviar no WhatsApp:
"Formandos! Tirem sua selfie aqui:
https://photoapp.photum.com.br/evento/123/selfie-cadastro/

Leia o QRCode abaixo ou clique no link ☝️"
```

**Passo 3: Acompanhar**
- Gestor acessa painel: vê em tempo real quantos já fizeram selfie
- Exporta lista quando pronto

---

## 🎯 Urls Importantes

### Para Formandos (Acesso Público)
- Selfie + Cadastro: `/evento/{id}/selfie-cadastro/`

### Para Gestor (Requer Login)
- Painel de Controle: `/evento/{id}/formandos-status/`
- Importar Nomes: `/evento/{id}/importar-nomes/`
- Exportar Dados: `/evento/{id}/exportar-formandos/`

---

## ❓ Dúvidas Comuns

### P: Preciso ter todos os nomes antes de criar o evento?
**R:** Não. Você pode deixar vazio e formandos auto-cadastram. Ou importar lista depois.

### P: A selfie é obrigatória?
**R:** Sim, para completar o cadastro. Sem selfie, o formulário não envia.

### P: Como formandos editam o cadastro?
**R:** Na página de sucesso, recebem um link para editar (com hash de segurança).

### P: As fotos ficam onde?
**R:** Em `/media/fotos/` da VPS, com nome: `TURMA-NOME.jpg`

### P: Posso deletar um evento com selfies?
**R:** Sim, mas as fotos no disco também são deletadas. Faça backup se necessário.

---

## 📱 Teste Local

**URL Local:**
```
http://localhost:8000/evento/criar/
```

**Após criar, teste:**
```
http://localhost:8000/evento/[ID]/selfie-cadastro/
```

**Painel Gestor (após login):**
```
http://localhost:8000/evento/[ID]/formandos-status/
```
