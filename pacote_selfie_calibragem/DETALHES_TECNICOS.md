# Detalhes técnicos — pacote de calibragem da selfie (25/09/2026)

## 1. Arquivos do pacote

| Arquivo do pacote | Arquivo do app que ele gera/atualiza |
|---|---|
| `arquivos/captura_selfie_modal.js` | `gestcaptur/static/gestcaptur/js/captura_selfie_modal.js` (fluxo público `/selfie/`) |
| `arquivos/formando_selfie_cadastro.html` | `templates/gestcaptur/formando_selfie_cadastro.html` (fluxo do formando) |
| `transf_modal_*.py` / `transf_form_*.py` | definições das transformações (âncora → substituto), aplicadas por `aplicar_transformacoes.py` |

```powershell
python pacote_selfie_calibragem/aplicar_transformacoes.py            # gera em arquivos/
python pacote_selfie_calibragem/aplicar_transformacoes.py --diff     # lista as transformações
python pacote_selfie_calibragem/aplicar_transformacoes.py --aplicar  # aplica no app (com backup)
python pacote_selfie_calibragem/aplicar_transformacoes.py --reverter # restaura o backup recente
python pacote_selfie_calibragem/validar_pacote.py                    # node --check + Django compile
```

Garantia: em modo `--aplicar`, se qualquer âncora não aparecer exatamente 1 vez o script **aborta antes
de escrever** (sem alteração parcial). Backups ficam como `<arquivo>.bak_pacote_<YYYYmmdd_HHMMSS>`.

## 2. Calibração — bloco `GUIA` (topo de cada arquivo)

| Chave | Novo | Antigo | Efeito de ajustar |
|---|---|---|---|
| `faceMin` | 0.16 | 0.28 | menor largura de rosto aceita. Baixe se ainda pedir para chegar muito perto |
| `faceMax` | 0.50 | 0.55 | maior largura aceita. Baixe para forçar mais distância (menos distorção grande-angular) |
| `confiancaDeteccao` | 0.45 (modal) / 0.35 (formando) | 0.65 / 0.5 | baixe se o rosto "não for reconhecido" a distância; suba se detectar outras pessoas ao fundo |
| `gracaManualMs` | 12000 | — | tempo até liberar a captura manual (nunca travar) |
| `retryLeituraMs` | 800 | — | espera antes de tentar abrir a câmera de novo (câmera ocupada) |
| `toleranciaCentroX/Y` | 0.20 / 0.22 | 0.15 / 0.18 | tolerância de centralização do rosto no enquadramento |

O oval visual (`.selfie-oval` / `.face-guide`, `inset: 26% 28%`) **não** foi alterado — a faixa de
aceitação passou a ser compatível com ele e com câmeras de FOV largo.


## 3. Fluxo público — `captura_selfie_modal.js` (20 transformações)

1. Bloco `GUIA` + `console.log` de versão; `retryLeituraFeito` reiniciado a cada abertura.
2. `faceGuidance` ganhou `deteccoes`, `erros`, `inicio` (mede se o detector realmente avaliou o rosto).
3. `retomarDeteccaoFacial()` reinicia os contadores.
4. Helper `criarComDelegateFallback()`: MediaPipe tenta `GPU` e cai para `CPU` (landmarker anti-careta e FaceDetector).
5. FaceDetector usa `GUIA.confiancaDeteccao` (0.45) em vez de 0.65.
6. Se o FaceDetector não subir: `deteccoes = 0` → **sem gate**, captura manual livre.
7. `orientarEnquadramento()` virou wrapper (`try/catch/finally`) + `orientarEnquadramentoInterno()`: o
   `requestAnimationFrame` é reagendado **sempre** (inclusive com vídeo aquecendo e depois de erro).
8. Mensagens de distância corrigidas ("Afaste" com rosto pequeno virou "Aproxime um pouco…").
9. Gate do Capturar: `guiaAtiva = available && deteccoes > 0`, com escape após 12 s (`liberarCapturaManual`).
10. Captura: verifica `videoWidth` (evita foto preta) e recorta centralizado (cover) em vez de esticar.
11. `mostrarTelaPreview(espelhar)`: para o loop de orientação e não espelha foto vinda de arquivo.
12. `oferecerCapturaPorArquivo()`: plano B com a câmera nativa (`<input capture="user">`) + botão
    "Usar a câmera do celular" no mesmo fluxo de preview/confirmar/salvar (JPEG base64, view intacta).
13. `NotReadableError`: espera `retryLeituraMs` e repete a tentativa antes de desistir.
14. Sem `navigator.mediaDevices` (webview) ou erro final: aviso claro + plano B.
15. Fechar o modal encerra o loop de orientação (sem `requestAnimationFrame` órfão).

## 4. Fluxo do formando — `formando_selfie_cadastro.html` (19 transformações)

1. Bloco `GUIA` + `guiaDeteccoes`, `guiaErros`, `capturaManual`, `temporizadorManual`.
2. `loadFaceLandmarker()`: tenta `GPU` e cai para `CPU`; usa `GUIA.confiancaDeteccao`.
3. `updateGuidance()` virou wrapper (`try/catch`) + `agendarGuia()` + `updateGuidanceInterno()`: o loop
   **nunca** morre (vídeo aquecendo, detector ausente ou exceção).
4. Aviso amigável quando a verificação facial fica instável (3 erros) + mostra o botão "Capturar Foto".
5. Faixa de distância realista (0.16–0.50), tolerância de centralização maior e **mensagens invertidas corrigidas**.
6. `capturaManual`: o botão manual funciona mesmo sem `faceOk` (countdown e `dispararCaptura` não barram mais).
7. `getUserMedia` com 3 combinações de constraints, retry de `NotReadableError` e mensagens por `err.name`
   (`NotAllowedError`, `NotReadableError`, `NotFoundError`).
8. `oferecerCameraDoCelular()`: plano B com a câmera nativa; o arquivo entra como `blobCapturado` e usa o
   **mesmo** `POST multipart 'foto'` + "Confirmar e Continuar" já existente (view intacta).
9. `agendarLiberacaoManual()`: mostra o botão manual após 12 s se a captura automática não disparar.
10. Fechar o modal limpa os novos estados; texto de apoio do oval ficou neutro ("Ajuste a distância…").

## 5. Verificação

```bash
python manage.py check
python manage.py test gestcaptur            # limpe DATABASE_URL e use PYTHONIOENCODING=utf-8 se preciso
python pacote_selfie_calibragem/validar_pacote.py       # node --check + Django compile
curl -s https://fotoid.photum.com.br/static/gestcaptur/js/captura_selfie_modal.js | grep -c "PACOTE CALIBRAGEM"
```

No navegador do aparelho (cache limpo) o console deve mostrar
`PACOTE CALIBRAGEM SELFIE ativo (25/09/2026)`.

## 6. O que NÃO foi alterado

- Models, migrations, views, URLs, formulários e banco — nenhuma mudança de servidor.
- `aluno_selfie_obrigatoria.html`, `captura_selfie.html` (CSS/HTML), `fotografar.js` e o cadastro.
- O oval/guia visual e os limiares do `selfie_validacao.js` (anti-careta).
- Pendência conhecida: `aluno_selfie_obrigatoria.html` continua sem plano B para webview/permissão
  negada (dá para aplicar o mesmo padrão depois, se quiser).
