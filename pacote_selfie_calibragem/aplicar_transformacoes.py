#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Pacote de CALIBRAGEM DA SELFIE (25/09/2026) — gerador/aplicador de transformacoes.

Alvos (nada mais e tocado):
  gestcaptur/static/gestcaptur/js/captura_selfie_modal.js   -> fluxo publico (modal /selfie/)
  templates/gestcaptur/formando_selfie_cadastro.html        -> fluxo do formando

Modos (execute na raiz do projeto):
  python pacote_selfie_calibragem/aplicar_transformacoes.py            # so gera em arquivos/
  python pacote_selfie_calibragem/aplicar_transformacoes.py --diff     # lista as mudancas
  python pacote_selfie_calibragem/aplicar_transformacoes.py --copiar   # instala as versoes prontas de arquivos/ (NAO checa ancoras)
  python pacote_selfie_calibragem/aplicar_transformacoes.py --aplicar  # aplica por ancoras (backup .bak_pacote_<selo>)
  python pacote_selfie_calibragem/aplicar_transformacoes.py --reverter # restaura o backup mais recente

IMPORTANTE: --aplicar (ancoras) exige que o arquivo do app seja exatamente a versao base usada
para gerar o pacote. Onde o arquivo for diferente (ex.: servidor/VPS), use --copiar (ou
aplicar_pacote.sh), que simplesmente instala a versao final pronta, com backup.

Seguranca: cada transformacao exige a ancora EXATAMENTE 1 vez. Se algo mudou desde
25/09/2026 o script ABORTA antes de escrever qualquer coisa. Detalhes: LEIA-ME.md
"""

import argparse
import datetime
import os
import shutil
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACOTE = os.path.dirname(os.path.abspath(__file__))
PASTA_ARQUIVOS = os.path.join(PACOTE, 'arquivos')

sys.path.insert(0, PACOTE)
from transformacoes_modal_js import TRANSFORMACOES as TRANSF_MODAL        # noqa: E402
from transformacoes_template import TRANSFORMACOES as TRANSF_TEMPLATE    # noqa: E402

ALVOS = [
    {
        'rotulo': 'Fluxo publico (modal /selfie/)',
        'origem': os.path.join('gestcaptur', 'static', 'gestcaptur', 'js', 'captura_selfie_modal.js'),
        'nome': 'captura_selfie_modal.js',
        'transformacoes': TRANSF_MODAL,
    },
    {
        'rotulo': 'Fluxo do formando',
        'origem': os.path.join('templates', 'gestcaptur', 'formando_selfie_cadastro.html'),
        'nome': 'formando_selfie_cadastro.html',
        'transformacoes': TRANSF_TEMPLATE,
    },
]


def ler(caminho):
    with open(caminho, 'r', encoding='utf-8', newline='') as f:
        return f.read()


def escrever(caminho, texto):
    with open(caminho, 'w', encoding='utf-8', newline='') as f:
        f.write(texto)


MARCADOR = 'PACOTE CALIBRAGEM SELFIE'


def aplicar_um(texto, transformacoes, nome):
    nl = '\r\n' if '\r\n' in texto else '\n'
    linhas_antes = texto.count('\n') + 1
    if MARCADOR in texto:
        raise SystemExit(
            'JA APLICADO: %s já contém o pacote (marcador "%s").\n'
            'Nada foi alterado. Use --copiar para reinstalar a versão final do pacote '
            'ou --reverter para voltar ao backup.' % (nome, MARCADOR))
    for rotulo, antes, depois in transformacoes:
        antes_n = antes.replace('\n', nl)
        depois_n = depois.replace('\n', nl)
        ocorrencias = texto.count(antes_n)
        if ocorrencias != 1:
            raise SystemExit(
                'ABORTADO: em %s a ancora "%s" aparece %d vez(es) (esperado 1).\n'
                'Nada foi alterado. Se o arquivo mudou, ajuste transf_*.py.' % (nome, rotulo, ocorrencias))
        texto = texto.replace(antes_n, depois_n)
    print('   - %s: %d transformacoes (linhas: %d -> %d)' % (
        nome, len(transformacoes), linhas_antes, texto.count('\n') + 1))
    return texto


def gerar(listar=False):
    resultados = []
    for alvo in ALVOS:
        caminho = os.path.join(RAIZ, alvo['origem'])
        if not os.path.exists(caminho):
            raise SystemExit('Arquivo nao encontrado: %s' % caminho)
        if listar:
            print('\n=== %s (%s) ===' % (alvo['rotulo'], alvo['nome']))
            for rotulo, _a, _d in alvo['transformacoes']:
                print('   * %s' % rotulo)
        novo = aplicar_um(ler(caminho), alvo['transformacoes'], alvo['nome'])
        resultados.append((alvo, novo))
    return resultados


def main():
    parser = argparse.ArgumentParser(description='Pacote de calibragem da selfie')
    parser.add_argument('--aplicar', action='store_true', help='aplica nos arquivos do app (com backup)')
    parser.add_argument('--reverter', action='store_true', help='restaura o backup .bak_pacote_* mais recente')
    parser.add_argument('--diff', action='store_true', help='lista as transformacoes que serao aplicadas')
    parser.add_argument('--copiar', action='store_true',
                        help='instala os arquivos prontos de arquivos/ no app (sem checar ancoras)')
    args = parser.parse_args()

    selo = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

    if args.reverter:
        for alvo in ALVOS:
            destino = os.path.join(RAIZ, alvo['origem'])
            pasta = os.path.dirname(destino)
            prefixo = os.path.basename(destino) + '.bak_pacote_'
            backups = sorted(n for n in os.listdir(pasta) if n.startswith(prefixo))
            if not backups:
                print('   - %s: nenhum backup .bak_pacote_* encontrado' % alvo['nome'])
                continue
            shutil.copy2(os.path.join(pasta, backups[-1]), destino)
            print('   - %s restaurado de %s' % (alvo['nome'], backups[-1]))
        print('\nOK: reversao concluida. Publique de novo (collectstatic + restart).')
        return 0

    if args.copiar:
        print('Rota de copia: instalando as versoes prontas de arquivos/ (com backup)...')
        for alvo in ALVOS:
            origem = os.path.join(PASTA_ARQUIVOS, alvo['nome'])
            destino = os.path.join(RAIZ, alvo['origem'])
            if not os.path.exists(origem):
                raise SystemExit('Pacote incompleto: falta %s' % origem)
            backup = destino + '.bak_pacote_' + selo
            shutil.copy2(destino, backup)
            shutil.copy2(origem, destino)
            print('   - %s  (backup: %s)' % (alvo['origem'], os.path.basename(backup)))
        print('\nOK: versoes finais instaladas. Publique com:')
        print('   python manage.py collectstatic --noinput')
        print('   sudo /usr/local/bin/reiniciar-fotoid.sh')
        print('   Reverter: python pacote_selfie_calibragem/aplicar_transformacoes.py --reverter')
        return 0

    print('Pacote de calibragem da selfie - gerando as versoes novas...')
    resultados = gerar(listar=args.diff)

    os.makedirs(PASTA_ARQUIVOS, exist_ok=True)
    for alvo, novo in resultados:
        escrever(os.path.join(PASTA_ARQUIVOS, alvo['nome']), novo)
    print('\nVersoes geradas em: %s' % PASTA_ARQUIVOS)

    if args.aplicar:
        print('\nAplicando nos arquivos do app (backup antes de escrever)...')
        for alvo, novo in resultados:
            destino = os.path.join(RAIZ, alvo['origem'])
            backup = destino + '.bak_pacote_' + selo
            shutil.copy2(destino, backup)
            escrever(destino, novo)
            print('   - %s  (backup: %s)' % (alvo['origem'], os.path.basename(backup)))
        print('\nOK: pacote aplicado. Publique com:')
        print('   python manage.py collectstatic --noinput')
        print('   sudo /usr/local/bin/reiniciar-fotoid.sh')
        print('   Reverter: python pacote_selfie_calibragem/aplicar_transformacoes.py --reverter')
    else:
        print('(nada foi alterado no app — use --aplicar para aplicar)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
