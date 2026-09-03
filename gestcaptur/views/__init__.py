# gestcaptur/views/__init__.py
# Pacote de views por domínio (substitui o antigo views.py monolítico).
# Re-exporta todas as views para compatibilidade com urls.py.

from .autenticacao import (debug_user,
    get_dashboard_redirect,
    home_redirect,
    login_view,
    logout_view)

from .dashboards import (api_dashboard_coordenador,
    dashboard,
    dashboard_coordenador,
    dashboard_coordenador_fotografo,
    dashboard_inteligente,
    dashboard_pesquisa,
    eventos_andamento,
    eventos_finalizados,
    eventos_gestor,
    eventos_historico,
    fichas_cadastradas,
    fotografo_dashboard,
    parceiro_dashboard,
    teste_dashboard_hibrido)

from .eventos import (alterar_status_evento,
    atribuir_fotografo,
    confirmar_encerrar_evento,
    criar_evento,
    criar_evento_modal,
    deletar_evento,
    editar_evento,
    encerrar_evento_coordenador,
    exportar_eventos,
    exportar_fotos_evento,
    finalizar_captura_gestor,
    importar_eventos,
    iniciar_evento_coordenador,
    listar_eventos,
    selecionar_evento_para_importar)

from .upload import (finalizar_cartao_sd,
    finalizar_sessao,
    upload_foto)

from .alunos import (aluno_editar,
    aluno_excluir,
    aluno_novo,
    aluno_visualizar,
    alunos_crud,
    confirmar_importacao_alunos,
    evento_alunos,
    exportar_fichas,
    gerar_novo_token,
    importar_alunos,
    marcar_aluno_faltoso,
    salvar_importacao_alunos,
    verificar_cpf_evento)

from .publico import (aluno_cadastro_publico,
    aluno_cadastro_sucesso,
    salvar_info_cadastro_incompleto)

from .usuarios import (ativar_usuario,
    criar_role,
    criar_usuario,
    desativar_usuario,
    editar_role,
    editar_usuario,
    listar_roles,
    listar_usuarios)

__all__ = ['alterar_status_evento', 'aluno_cadastro_publico', 'aluno_cadastro_sucesso', 'aluno_editar', 'aluno_excluir', 'aluno_novo', 'aluno_visualizar', 'alunos_crud', 'api_dashboard_coordenador', 'ativar_usuario', 'atribuir_fotografo', 'confirmar_encerrar_evento', 'confirmar_importacao_alunos', 'criar_evento', 'criar_evento_modal', 'criar_role', 'criar_usuario', 'dashboard', 'dashboard_coordenador', 'dashboard_coordenador_fotografo', 'dashboard_inteligente', 'dashboard_pesquisa', 'debug_user', 'deletar_evento', 'desativar_usuario', 'editar_evento', 'editar_role', 'editar_usuario', 'encerrar_evento_coordenador', 'evento_alunos', 'eventos_andamento', 'eventos_finalizados', 'eventos_gestor', 'eventos_historico', 'exportar_eventos', 'exportar_fichas', 'exportar_fotos_evento', 'fichas_cadastradas', 'finalizar_captura_gestor', 'finalizar_cartao_sd', 'finalizar_sessao', 'fotografo_dashboard', 'gerar_novo_token', 'get_dashboard_redirect', 'home_redirect', 'importar_alunos', 'importar_eventos', 'iniciar_evento_coordenador', 'listar_eventos', 'listar_roles', 'listar_usuarios', 'login_view', 'logout_view', 'marcar_aluno_faltoso', 'parceiro_dashboard', 'salvar_importacao_alunos', 'salvar_info_cadastro_incompleto', 'selecionar_evento_para_importar', 'teste_dashboard_hibrido', 'upload_foto', 'verificar_cpf_evento']
