#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Valida o pacote gerado em pacote_selfie_calibragem/arquivos/ SEM tocar no app:
  1) JS do modal: node --check
  2) JS inline do template do formando (extraido do <script>): node --check
  3) template do formando: compilacao pelo engine do Django
Uso: python pacote_selfie_calibragem/validar_pacote.py
"""

import io
import os
import re
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_ARQUIVOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'arquivos')
sys.path.insert(0, RAIZ)

falhas = []


def checar_node(caminho, rotulo):
    print('-> node --check  %s' % rotulo)
    try:
        r = subprocess.run(['node', '--check', caminho], capture_output=True, text=True)
    except FileNotFoundError:
        print('   (node não encontrado; validação de sintaxe JS ignorada)')
        return
    if r.returncode == 0:
        print('   OK')
    else:
        falhas.append('%s: %s' % (rotulo, (r.stderr or r.stdout).strip().splitlines()[:4]))
        print('   FALHOU:\n%s' % (r.stderr or r.stdout))


def extrair_script_principal(html):
    blocos = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', html, flags=re.S | re.I)
    for bloco in blocos:
        if 'updateGuidance' in bloco:
            return bloco
    return None


def main():
    js = os.path.join(PASTA_ARQUIVOS, 'captura_selfie_modal.js')
    tpl = os.path.join(PASTA_ARQUIVOS, 'formando_selfie_cadastro.html')

    if not os.path.exists(js) or not os.path.exists(tpl):
        print('Rode primeiro: python pacote_selfie_calibragem/aplicar_transformacoes.py')
        return 2

    checar_node(js, 'captura_selfie_modal.js (arquivo publico)')

    with io.open(tpl, encoding='utf-8', newline='') as f:
        html = f.read()

    bloco = extrair_script_principal(html)
    if bloco is None:
        falhas.append('formando_selfie_cadastro.html: <script> principal nao encontrado')
        print('-> script inline do template: NAO ENCONTRADO')
    else:
        # tags do Django dentro do JS viram marcadores neutros (nao afetam a sintaxe JS)
        js_inline = re.sub(r'\{\{.*?\}\}', 'x', bloco, flags=re.S)
        js_inline = re.sub(r'\{%.*?%\}', '', js_inline, flags=re.S)
        tmp = os.path.join(tempfile.gettempdir(), 'pacote_selfie_formando_inline.js')
        with io.open(tmp, 'w', encoding='utf-8') as f:
            f.write(js_inline)
        checar_node(tmp, 'formando_selfie_cadastro.html (script inline)')

    print('-> compilacao do template pelo engine do Django')
    os.environ.pop('DATABASE_URL', None)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'photoapp.settings')
    try:
        import django
        django.setup()
        from django.template import engines
        engines['django'].engine.from_string(html)
        print('   OK')
    except Exception as e:
        falhas.append('template: %s' % e)
        print('   FALHOU: %s' % e)

    print('')
    if falhas:
        print('RESULTADO: FALHAS ->')
        for f in falhas:
            print('   - %s' % f)
        return 1
    print('RESULTADO: TUDO OK — pacote pronto para aplicar quando quiser.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
