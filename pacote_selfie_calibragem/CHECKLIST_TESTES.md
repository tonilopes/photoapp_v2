# Checklist de testes — pacote de calibragem da selfie

Faça **depois** de aplicar e publicar (`collectstatic` + `reiniciar-fotoid.sh`).
Use uma aba anônima ou limpe o cache (o JS fica em `/static/` e é agressivamente cacheado).

## 0. Conferir que a versão nova está no ar

1. Abrir a página da selfie, F12 → Console → deve aparecer `PACOTE CALIBRAGEM SELFIE ativo (25/09/2026)`.
2. `curl -s https://fotoid.photum.com.br/static/gestcaptur/js/captura_selfie_modal.js | grep -c "PACOTE CALIBRAGEM"` → `1`.

## 1. Formando — caminho feliz (celular no Wi-Fi)

- [ ] Abrir `/formando/<evento>/` (link de selfie do formando) → modal abre, vídeo aparece.
- [ ] Aproximar/distanciar: a mensagem alterna **corretamente** ("Aproxime um pouco…" quando longe, "Afaste um pouco…" quando muito perto). O oval fica verde quando enquadrado.
- [ ] Auto-captura dispara após ~1 s de enquadramento (não mais que 2 fotos) → preview aparece.
- [ ] "Confirmar e Continuar" → salva e avança para o cadastro (sem erro no console).
- [ ] "Tirar Novamente" → volta ao vídeo e permite nova captura.

## 2. Formando — nunca travar (o bug relatado)

- [ ] Abrir o modal e **imediatamente** cobrir a câmera / sair da frente: depois de ~12 s o status muda e o botão **"Capturar Foto"** aparece.
- [ ] Tocar em "Capturar Foto" → contagem 2-1 → foto entra no preview (mesmo sem o rosto "detectado").
- [ ] Recarregar a página e abrir o modal: em nenhum momento a tela deve ficar parada em "Analise do rosto iniciando…" sem nenhuma saída.

## 3. Formando — erros de câmera

- [ ] Negar a permissão da câmera → aparece mensagem clara + botão **"Usar a câmera do celular"**.
- [ ] Tocar nele → câmera nativa abre → tirar foto → preview + "Confirmar e Continuar" salva normalmente.
- [ ] Com a câmera ocupada (ex.: app de câmera/chamada aberto em segundo plano) → status "Liberando a câmera…" e a câmera sobe sozinha depois.

## 4. Fluxo público `/selfie/`

- [ ] Abrir o link público pelo **Chrome do celular** → câmera sobe e o oval mostra as mensagens certas.
- [ ] Tocar em "Capturar" mesmo antes de o oval ficar verde: **deve capturar** (e avisar para ajustar) — não pode ficar bloqueado.
- [ ] Esperar ~12 s sem enquadrar e tocar em Capturar: captura normalmente.
- [ ] Preview → "Confirmar" → salva e redireciona ao cadastro.
- [ ] "Fazer Outra" → volta para a câmera.

## 5. Samsung / S23 Ultra (o alvo do problema)

- [ ] Repetir o teste 3 (formando) e 4 (público) **duas vezes seguidas** (fechar e reabrir o modal): a segunda abertura usa o modelo em cache e era o cenário do travamento.
- [ ] Conferir no console que aparece `Detector facial criado (delegate=GPU)` ou `(delegate=CPU)` (o CPU é o fallback — funciona igual).
- [ ] Verificar que a foto salva não está preta e nem achatada (recorte cover).
- [ ] Testar com o celular na vertical e na horizontal.

## 6. Regressão nos outros aparelhos

- [ ] 1 Android comum (Chrome), 1 iPhone (Safari), 1 desktop com webcam.
- [ ] Conferir que a selfie salva abre corretamente na tela do parceiro/administração (mesmo formato de antes).
- [ ] `python manage.py test gestcaptur` continua verde.

## 7. Se algo der errado em produção

```bash
python3 pacote_selfie_calibragem/aplicar_transformacoes.py --reverter
python manage.py collectstatic --noinput && sudo /usr/local/bin/reiniciar-fotoid.sh
```

(ou `bash pacote_selfie_calibragem/reverter_pacote.sh`) — volta ao estado anterior em ~1 minuto.
