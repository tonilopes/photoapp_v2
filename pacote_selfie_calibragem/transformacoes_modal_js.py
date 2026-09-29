# -*- coding: utf-8 -*-
"""Agrega as transformacoes do modal publico (ordem de aplicacao)."""

from transf_modal_a import TRANSFORMACOES as _A   # GUIA, estado, retomada
from transf_modal_b import TRANSFORMACOES as _B   # MediaPipe GPU->CPU
from transf_modal_c import TRANSFORMACOES as _C   # wrapper do loop
from transf_modal_e import TRANSFORMACOES as _E   # mensagens de distancia
from transf_modal_f import TRANSFORMACOES as _F   # reagendamento + gate
from transf_modal_g import TRANSFORMACOES as _G   # captura (cover)
from transf_modal_h import TRANSFORMACOES as _H   # preview + avisos
from transf_modal_i import TRANSFORMACOES as _I   # plano B (camara do celular)
from transf_modal_j import TRANSFORMACOES as _J   # retry/erro final/fechamento

TRANSFORMACOES = list(_A) + list(_B) + list(_C) + list(_E) + list(_F) + \
    list(_G) + list(_H) + list(_I) + list(_J)
