// gestcaptur/static/gestcaptur/js/selfie_validacao.js
// Validação de selfie (expressão/pose) a partir dos 478 pontos do
// MediaPipe FaceLandmarker. Usado via window.SelfieValidacao.
//   olhos: 33/133/159/145 + íris 468 | 263/362/386/374 + íris 473
//   boca : 61/291 cantos, 13 topo, 14 base
// HOTFIX salvamento (25/09/2026): limiares calibrados para uso real e
// blindagem contra landmarks ausentes — NUNCA lança erro e, em caso de
// dúvida técnica, devolve [] (não bloqueia o aluno de salvar).
// REVERSÃO: arquivo isolado; basta remover o <script src="selfie_validacao.js">
// dos templates para voltar ao fluxo anterior.
(function (global) {
  'use strict';

  // Limiares centralizados — calibráveis sem mexer na lógica
  var LIM = {
    proxPerto: 0.42,    // distância entre cantos externos dos olhos / largura da imagem
    proxLonge: 0.09,
    anguloMax: 18,      // graus de inclinação lateral da cabeça
    earAberto: 0.42,    // EAR alto = olho arregalado (careta)
    earFechado: 0.13,   // EAR baixo = olho fechado/piscando
    earDiferenca: 0.15, // piscada de um olho só
    gazeDesvio: 0.30,   // diferenca de posicao das iris entre os dois olhos (vesgo)
    gazeMin: 0.15,
    gazeMax: 0.85,
    bocaAberta: 0.42,
    bocaAssim: 0.16
  };

  function pt(pontos, i, W, H) {
    var p = pontos && pontos[i];
    if (!p || typeof p.x !== 'number' || typeof p.y !== 'number') return null;
    return { x: p.x * W, y: p.y * H };
  }
  function dist(a, b) {
    if (!a || !b) return NaN;
    return Math.hypot(a.x - b.x, a.y - b.y);
  }
  function ok(v) { return typeof v === 'number' && isFinite(v); }

  // Retorna array de alertas (vazio = rosto aceitável).
  function validarExpressao(pontos, W, H) {
    var alertas = [];
    try {
      W = W || 640;
      H = H || 480;
      if (!pontos || !pontos.length) return alertas;

      var oE = { out: pt(pontos, 33, W, H), inn: pt(pontos, 133, W, H), top: pt(pontos, 159, W, H), bot: pt(pontos, 145, W, H), iris: pt(pontos, 468, W, H) };
      var oD = { out: pt(pontos, 263, W, H), inn: pt(pontos, 362, W, H), top: pt(pontos, 386, W, H), bot: pt(pontos, 374, W, H), iris: pt(pontos, 473, W, H) };
      var bEsq = pt(pontos, 61, W, H), bDir = pt(pontos, 291, W, H);
      var bTop = pt(pontos, 13, W, H), bBot = pt(pontos, 14, W, H);

      var distOlhos = dist(oE.out, oD.out);
      if (!ok(distOlhos) || distOlhos <= 0) return alertas; // sem base confiável: não bloqueia

      // 1. Distância (foto colada distorce e quebra o reconhecimento facial)
      var prox = distOlhos / W;
      if (prox > LIM.proxPerto) alertas.push('Muito perto — afaste o rosto (~um braço).');
      else if (prox < LIM.proxLonge) alertas.push('Aproxime-se um pouco mais.');

      // 2. Cabeça torta/inclinada
      if (oE.out && oD.out) {
        var ang = Math.abs(Math.atan2(oD.out.y - oE.out.y, oD.out.x - oE.out.x) * 180 / Math.PI);
        if (ang > 90) ang = 180 - ang;
        if (ang > LIM.anguloMax) alertas.push('Cabeça torta — centralize a cabeça.');
      }

      // 3. EAR: olho arregalado (careta), fechado/piscando ou piscada de um olho
      var earE = dist(oE.top, oE.bot) / (dist(oE.out, oE.inn) || 1);
      var earD = dist(oD.top, oD.bot) / (dist(oD.out, oD.inn) || 1);
      if (ok(earE) && ok(earD)) {
        if (earE > LIM.earAberto || earD > LIM.earAberto) alertas.push('Olhos arregalados — olhe natural para a câmera.');
        else if (earE < LIM.earFechado || earD < LIM.earFechado) alertas.push('Olhos fechados ou piscando — abra os olhos.');
        else if (Math.abs(earE - earD) > LIM.earDiferenca) alertas.push('Piscada de um olho só — abra os dois olhos.');
      }

      // 4. Gaze: vesgo/estrabismo (só roda quando as íris existem)
      var rE = NaN, rD = NaN;
      if (oE.iris && oD.iris && oE.out && oE.inn && oD.out && oD.inn) {
        rE = (oE.iris.x - oE.out.x) / ((oE.inn.x - oE.out.x) || 1);
        rD = (oD.iris.x - oD.out.x) / ((oD.inn.x - oD.out.x) || 1);
      }
      if (ok(rE) && ok(rD)) {
        // Metrica simetrica: olhos alinhados tem rE ~ rD. Vesgo de um olho (o caso do
        // aluno fazendo graca) abre uma diferenca grande entre os dois.
        if (Math.abs(rE - rD) > LIM.gazeDesvio) alertas.push('Sem fazer vesgo/olhar desviado — olhe para a câmera.');
        else if (rE < LIM.gazeMin || rE > LIM.gazeMax || rD < LIM.gazeMin || rD > LIM.gazeMax) alertas.push('Olhe direto para a câmera.');
      }

      // 5. Boca: muito aberta ou torta
      var abertura = dist(bTop, bBot) / distOlhos;
      if (ok(abertura) && abertura > LIM.bocaAberta) alertas.push('Boca muito aberta — faça expressão neutra.');
      if (bEsq && bDir && oE.out && oD.out) {
        var assim = Math.abs((bEsq.y - oE.out.y) - (bDir.y - oD.out.y)) / distOlhos;
        if (ok(assim) && assim > LIM.bocaAssim) alertas.push('Boca torta — faça expressão neutra.');
      }
    } catch (e) {
      console.warn('[selfie_validacao] erro ignorado (não bloqueia):', e);
    }
    return alertas;
  }

  global.SelfieValidacao = global.SelfieValidacao || {};
  global.SelfieValidacao.validarExpressao = validarExpressao;
  global.SelfieValidacao.LIM = LIM;
})(window);
