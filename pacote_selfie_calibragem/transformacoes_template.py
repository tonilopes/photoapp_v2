# -*- coding: utf-8 -*-
"""Agrega as transformacoes do fluxo do formando (ordem de aplicacao)."""

from transf_form_a import TRANSFORMACOES as _A    # GUIA e flags
from transf_form_b import TRANSFORMACOES as _B    # MediaPipe GPU->CPU
from transf_form_c import TRANSFORMACOES as _C    # loop que nao morre
from transf_form_d import TRANSFORMACOES as _D    # distancia + mensagens
from transf_form_e import TRANSFORMACOES as _E    # captura manual
from transf_form_f1 import TRANSFORMACOES as _F1  # getUserMedia com fallback
from transf_form_f2 import TRANSFORMACOES as _F2  # plano B + botao manual
from transf_form_g import TRANSFORMACOES as _G    # fechamento + texto do oval

TRANSFORMACOES = list(_A) + list(_B) + list(_C) + list(_D) + list(_E) + \
    list(_F1) + list(_F2) + list(_G)
