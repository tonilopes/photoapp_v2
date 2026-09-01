# 📊 Fluxo Visual - Sistema de Selfie

```
┌─────────────────────────────────────────────────────────────────┐
│                   CLIENTE ACESSA LINK PÚBLICO                    │
│  https://cliente.photum.com.br:2543/evento/{evento_id}/selfie/   │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
        ┌─────────────────────────────────┐
        │ PÁGINA DE CAPTURA DE SELFIE     │
        │ ✅ Webcam carregada             │
        │ ✅ Instruções em destaque       │
        │ ✅ Análise de iluminação        │
        └──────────┬──────────────────────┘
                   │
        ┌──────────▼──────────┐
        │ ANÁLISE EM TEMPO    │
        │ REAL DA ILUMINAÇÃO  │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────────────────┐
        │  BRILHO DETECTADO               │
        └──────────┬──────────────────────┘
                   │
        ┌──────────┴──────────────────────┐
        │                                 │
        ▼                                 ▼
    ┌────────────┐                  ┌────────────┐
    │MUITO CLARO │                  │ MUITO      │
    │ (> 230)    │                  │ ESCURO     │
    └────┬───────┘                  │ (< 80)     │
         │                          └────┬───────┘
         ▼                               ▼
    ┌──────────────────┐        ┌──────────────────┐
    │⚠️ "Reduza        │        │⚠️ "Aumente       │
    │iluminação"      │        │iluminação"      │
    │❌ Btn desabilitado│        │❌ Btn desabilitado│
    └──────────────────┘        └──────────────────┘
                                        
        ┌──────────────────────┐
        │ ILUMINAÇÃO OK        │
        │ (80 < Brilho < 230)  │
        │ ✅ "Pronto para      │
        │    capturar!"        │
        │ ✅ Btn habilitado    │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ USUÁRIO CLICA EM     │
        │ "CAPTURAR FOTO"      │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ FOTO CAPTURADA       │
        │ ✅ Canvas com imagem │
        │ ✅ Preview mostrado  │
        │ ✅ Video parado      │
        └──────────┬───────────┘
                   │
        ┌──────────▼──────────────────┐
        │ OPÇÕES:                     │
        │ 🔄 Recapturar (reinicia)   │
        │ ✅ Confirmar (envia)        │
        └──────────┬──────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
    ┌─────────┐           ┌──────────────┐
    │RECAPTURAR│           │CONFIRMAR     │
    └────┬────┘           └────┬─────────┘
         │                     │
         ▼                     ▼
    ┌──────────┐        ┌────────────────────┐
    │Volta para│        │ENVIO PARA SERVIDOR │
    │captura   │        │POST /selfie/salvar/│
    │          │        └────┬───────────────┘
    └──────────┘             │
                    ┌────────▼────────┐
                    │ VALIDAÇÕES:     │
                    │ 1. Base64 válido│
                    │ 2. Resolução OK │
                    │ 3. Iluminação OK│
                    │ 4. Tamanho OK   │
                    └────────┬────────┘
                             │
                ┌────────────┴──────────────┐
                │                          │
                ▼                          ▼
        ┌──────────────────┐      ┌──────────────────┐
        │ VALIDAÇÃO OK     │      │ VALIDAÇÃO FALHOU │
        │ ✅ Foto salva    │      │ ❌ Erro retornado│
        └────────┬─────────┘      └────────┬─────────┘
                 │                         │
                 ▼                         ▼
        ┌──────────────────────┐  ┌──────────────────┐
        │ REDIRECT PARA        │  │ MENSAGEM DE ERRO │
        │ CADASTRO DO ALUNO:   │  │ "Tente novamente"│
        │                      │  │ com dicas        │
        │ /aluno/cadastro/     │  └──────────────────┘
        │ ?evento_id={id}      │
        │ &aluno_id={id}       │  (Usuário pode)
        │ &token={token}       │  recapturar
        └────────┬─────────────┘
                 │
                 ▼
        ┌──────────────────────────────┐
        │ CADASTRO DO ALUNO             │
        │ ✅ Selfie pré-preenchida     │
        │ ✅ Formulário vazio           │
        │ ✅ Pronto para preencher      │
        └────────┬─────────────────────┘
                 │
                 ▼
        ┌──────────────────────────────┐
        │ ALUNO PREENCHE DADOS:        │
        │ • Nome                        │
        │ • Email                       │
        │ • Telefone                    │
        │ • Endereço                    │
        │ • Contatos de emergência      │
        └────────┬─────────────────────┘
                 │
                 ▼
        ┌──────────────────────────────┐
        │ ALUNO CLICA EM "SALVAR"      │
        └────────┬─────────────────────┘
                 │
                 ▼
        ┌──────────────────────────────┐
        │ VALIDAÇÃO DE FORMULÁRIO      │
        │ ✅ Campos obrigatórios OK     │
        │ ✅ Selfie vinculada          │
        └────────┬─────────────────────┘
                 │
                 ▼
        ┌──────────────────────────────┐
        │ ALUNO SALVO COM SUCESSO     │
        │ ✅ Banco de dados atualizado │
        │ ✅ Selfie armazenada         │
        └────────┬─────────────────────┘
                 │
                 ▼
        ┌──────────────────────────────┐
        │ PÁGINA DE SUCESSO            │
        │ ✅ Cadastro confirmado       │
        │ ✅ Aguardando evento         │
        │ ✅ QR Code para evento       │
        └──────────────────────────────┘
```

---

## 🔄 Fluxo Alternativo: Aluno Existente

```
ALUNO ABRE LINK COM ALUNO_ID
       ↓
VERIFICA SE JÁ TEM SELFIE
       │
       ├─ SIM → REDIRECIONA PARA CADASTRO
       │         (Pula captura)
       │
       └─ NÃO → CAPTURA SELFIE NORMALMENTE
              ↓
         SELFIE SALVA NO BD
              ↓
         REDIRECIONA PARA EDIÇÃO DE CADASTRO
```

---

## 🎯 Estados da Interface

### Estado 1: Carregando
```
┌─────────────────────────────────┐
│         📸 CAPTURE SELFIE       │
│                                 │
│         [Loading...]            │
│                                 │
│     Aguardando acesso à câmera  │
└─────────────────────────────────┘
```

### Estado 2: Webcam Ativa
```
┌─────────────────────────────────┐
│         📸 CAPTURE SELFIE       │
│                                 │
│  ┌───────────────────────────┐  │
│  │    VIDEO DA CÂMERA        │  │
│  │    (ao vivo)              │  │
│  └───────────────────────────┘  │
│                                 │
│  ✅ Iluminação OK              │
│  [    📸 CAPTURAR FOTO    ]     │
└─────────────────────────────────┘
```

### Estado 3: Foto Capturada
```
┌─────────────────────────────────┐
│         📸 CAPTURE SELFIE       │
│                                 │
│  ┌───────────────────────────┐  │
│  │    PREVIEW DA FOTO        │  │
│  │    (imagem congelada)     │  │
│  └───────────────────────────┘  │
│                                 │
│  [  🔄 RECAPTURAR  ]            │
│  [  ✅ CONFIRMAR E CONTINUAR  ] │
└─────────────────────────────────┘
```

### Estado 4: Enviando
```
┌─────────────────────────────────┐
│         📸 CAPTURE SELFIE       │
│                                 │
│  ⏳ Enviando selfie...          │
│                                 │
│     [Spinner animado]           │
│                                 │
└─────────────────────────────────┘
```

### Estado 5: Sucesso
```
┌─────────────────────────────────┐
│         📸 CAPTURE SELFIE       │
│                                 │
│  ✅ Selfie enviada com sucesso!│
│                                 │
│  Redirecionando para cadastro...│
│                                 │
└─────────────────────────────────┘
```

---

## 📊 Validações de Iluminação

```
Eixo X: Brilho (0-255)

0 ├─────────────┬────────────────────┬──────────┤ 255
  │  ESCURO     │    IDEAL           │  CLARO   │
  │  (< 80)     │  (80-230)          │ (> 230)  │
  │  ❌ Rejeita │  ✅ Aceita         │ ❌ Rejeita
  │
Mensagens:
  ❌ Muito escuro: "Mude-se para local mais iluminado"
  ✅ OK: "Pronto para capturar!"
  ⚠️ Muito claro: "Reduza iluminação ou mude de posição"
```

---

## 🔐 Fluxo de Segurança

```
┌──────────────────────────┐
│ ALUNO SUBMETE SELFIE    │
└────────────┬─────────────┘
             │
             ▼
┌────────────────────────────────┐
│ VALIDAÇÃO NO FRONTEND:        │
│ ✅ Arquivo é imagem           │
│ ✅ Tamanho razoável           │
└────────────┬───────────────────┘
             │
             ▼
┌────────────────────────────────┐
│ ENVIO PARA SERVIDOR:           │
│ 📤 POST /selfie/salvar/        │
│ 🔐 HTTPS (produção)            │
│ 🔏 Sem validação CSRF (público)│
└────────────┬───────────────────┘
             │
             ▼
┌────────────────────────────────┐
│ VALIDAÇÃO NO BACKEND:         │
│ ✅ JSON válido                 │
│ ✅ Base64 decodificável       │
│ ✅ Imagem real                │
│ ✅ Resolução OK               │
│ ✅ Iluminação OK              │
│ ✅ Aspecto correto            │
└────────────┬───────────────────┘
             │
             ▼
┌────────────────────────────────┐
│ ARMAZENAMENTO:                │
│ 💾 Django FileField           │
│ 📂 /media/event_photos/       │
│ 🏷️ Nome: selfie_<id>_<uuid>  │
└────────────┬───────────────────┘
             │
             ▼
┌────────────────────────────────┐
│ LOGGING:                      │
│ 📝 Ação registrada no logger   │
│ 📝 Aluno ID registrado         │
│ 📝 Evento ID registrado        │
│ 📝 Timestamp registrado        │
└────────────────────────────────┘
```

---

**Diagrama criado:** 19 de fevereiro de 2026

