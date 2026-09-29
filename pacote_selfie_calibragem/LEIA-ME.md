# Pacote de calibragem da SELFIE — Galaxy/Samsung (S23 Ultra) e todos os aparelhos

Criado em 25/09/2026. **Nada foi alterado no app**: este pacote fica parado até você mandar aplicar.
Os arquivos prontos estão em `pacote_selfie_calibragem/arquivos/`.

---

## 1. O que o usuário relatou

- "muito perto" quando está **longe** (mensagem invertida);
- "rosto não reconhecido";
- fica no loop afastar/aproximar e **não consegue capturar/salvar**.

Isso bate exatamente com a causa encontrada no código — não é "aparelho não suportado".

## 2. Causas confirmadas no código

| # | Causa | Onde estava | Efeito |
|---|-------|-------------|--------|
| 1 | **Loop de orientação facial morria** (saída sem reagendar o `requestAnimationFrame` quando o vídeo ainda não tinha imagem, ou exceção do MediaPipe) | `captura_selfie_modal.js` (`orientarEnquadramento`) e `formando_selfie_cadastro.html` (`updateGuidance`) | `available=true` + `valid=false` para sempre: no modal público o botão **Capturar ficava bloqueado**; no formando **nenhuma auto-captura** e o botão manual escondido |
| 2 | **Mensagem invertida + faixa de distância irreal** (`FACE_MIN 0.28`): rosto pequeno/longe recebia "**Afaste o rosto**" | mesmas duas funções | Aluno ia para o lado errado e nunca entrava no enquadramento. Com frontal de FOV largo (S23 Ultra ~80°) é praticamente impossível chegar a 28% da largura |
| 3 | **MediaPipe com `delegate: 'GPU'` sem fallback** | 3 pontos (landmarker/FaceDetector) | Falha de WebGL em vários Adreno/One UI → exceção → causa 1 |
| 4 | **`NotReadableError`** ("Could not start video source"), o erro mais comum nos Galaxys | `getUserMedia` do formando tinha 1 tentativa + `alert()` em inglês | Aluno sem nenhuma alternativa |
| 5 | Webview (WhatsApp/Instagram) ou permissão negada sem `navigator.mediaDevices` | formando não checava | Erro técnico, sem plano B |
| 6 | Detector "cego" para rosto mais afastado (`minDetectionConfidence 0.65`) e captura manual barrada pelo `faceOk` | modal e formando | Botão manual não funcionava como saída de emergência |

O S23 Ultra é o aparelho que **mais** cai nas causas 1–3 (frontal mais lenta para aquecer + FOV largo + Adreno/One UI).

## 3. O que o pacote muda

- **Nunca mais trava:** loop de orientação reagenda sempre (`try/finally`); erro de GPU cai para CPU automaticamente.
- **Gate do "Capturar" destravado:** só bloqueia se o detector **realmente avaliou** o rosto (`deteccoes > 0`) e por no máximo 12 s; depois o aluno captura sempre (a validação da foto final continua valendo).
- **Mensagens corretas + faixa realista:** `FACE_MIN 0.28 → 0.16`, `FACE_MAX 0.55 → 0.50`, tolerância de centralização 0.15/0.18 → 0.20/0.22, textos "Aproxime…"/"Afaste um pouco…" no lado certo.
- **Formando sempre tem saída:** botão **"Capturar Foto"** aparece após 12 s sem enquadramento ou se a verificação facial ficar instável; o disparo manual ignora o gate de rosto.
- **Plano B universal — "Usar a câmera do celular"** (`<input capture="user">`) nos dois fluxos: entra no **mesmo** preview/confirmar/salvar (funciona em webview, permissão negada e câmera ocupada). Sem mudança no servidor.
- **Câmera ocupada:** `NotReadableError` espera ~0,8 s e tenta de novo; `getUserMedia` testa 3 combinações de constraints.
- **Sem foto preta/achatada:** espera o vídeo ter quadro e faz recorte central (cover) em vez de esticar 16:9 dentro de 3:4.
- Marco no console para conferir a versão publicada: `PACOTE CALIBRAGEM SELFIE ativo (25/09/2026)`.

## 4. Como aplicar (quando quiser)

### Opção A — pelo script (recomendada, backup automático)

```powershell
# Windows, na raiz do projeto
python pacote_selfie_calibragem/aplicar_transformacoes.py --diff     # lista o que será mudado
python pacote_selfie_calibragem/aplicar_transformacoes.py --aplicar  # aplica (backup .bak_pacote_<data>)
python pacote_selfie_calibragem/validar_pacote.py                    # valida sintaxe JS + template
```

```bash
# VPS / Linux, na raiz do projeto
python3 pacote_selfie_calibragem/aplicar_transformacoes.py --aplicar
```

O script **aborta sem alterar nada** se o arquivo tiver mudado desde 25/09/2026 (cada âncora precisa
aparecer exatamente 1 vez). Nesse caso use a Opção B ou peça para eu ajustar as âncoras.

### Opção B — copiando os arquivos prontos

```bash
bash pacote_selfie_calibragem/aplicar_pacote.sh                 # Linux/VPS
powershell -File pacote_selfie_calibragem/aplicar_pacote.ps1    # Windows
```

### Publicar (obrigatório — o JS é servido via `staticfiles`)

```bash
source venv/bin/activate
python manage.py collectstatic --noinput
sudo /usr/local/bin/reiniciar-fotoid.sh
```

### Voltar atrás (rollback)

```bash
python pacote_selfie_calibragem/aplicar_transformacoes.py --reverter   # ou bash reverter_pacote.sh
python manage.py collectstatic --noinput && sudo /usr/local/bin/reiniciar-fotoid.sh
```

Veja também: `DETALHES_TECNICOS.md` (calibração e lista completa das 39 mudanças),
`CHECKLIST_TESTES.md` (o que testar, aparelho por aparelho).
