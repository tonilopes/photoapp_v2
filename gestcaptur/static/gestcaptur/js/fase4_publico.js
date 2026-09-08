/* ==========================================================================
   FASE 4 — JS público (flujo de formandos · fotoid)
   - Tema claro/escuro OPZIONAL: decisão do usuário, persistida em localStorage.
     Default: preferencia do sistema (prefers-color-scheme).
   - Registra o Service Worker público (network-first, escopo raíz).
   ========================================================================== */
(function () {
    'use strict';

    var KEY = 'photum_tema';

    function aplicar(tema) {
        if (tema === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark');
        } else {
            document.documentElement.removeAttribute('data-theme');
        }
    }

    function guardar(tema) {
        try { localStorage.setItem(KEY, tema); } catch (e) { /* ignore */ }
    }

    var guardado = null;
    try { guardado = localStorage.getItem(KEY); } catch (e) { /* ignore */ }

    var oscuro;
    if (guardado === 'dark') oscuro = true;
    else if (guardado === 'light') oscuro = false;
    else {
        var mq = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;
        oscuro = mq ? mq.matches : false;
    }
    aplicar(oscuro ? 'dark' : 'light');

    var btn = document.getElementById('f4ThemeBtn');
    if (btn) {
        btn.textContent = oscuro ? '☀️' : '🌙';
        btn.setAttribute('aria-label', oscuro ? 'Ativar tema claro' : 'Ativar tema escuro');
        btn.addEventListener('click', function () {
            oscuro = !oscuro;
            aplicar(oscuro ? 'dark' : 'light');
            guardar(oscuro ? 'dark' : 'light');
            btn.textContent = oscuro ? '☀️' : '🌙';
            btn.setAttribute('aria-label', oscuro ? 'Ativar tema claro' : 'Ativar tema escuro');
        });
    }

    // Service Worker público (solo en HTTPS, nunca rompe si falla)
    if ('serviceWorker' in navigator && window.location.protocol === 'https:') {
        navigator.serviceWorker.register('/sw_fotoid.js').catch(function () { /* ignore */ });
    }
})();