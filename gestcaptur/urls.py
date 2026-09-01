# gestcaptur/urls.py
from django.urls import path
from . import views
from . import views_selfie
from . import views_formandos
from . import views_parceiros

urlpatterns = [
    # Autenticação Legacy
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('debug_user/', views.debug_user, name='debug_user'),  # TEMPORÁRIO

    # Dashboards
    path('dashboard/', views.dashboard, name='dashboard'),
    path('fotografo/', views.fotografo_dashboard, name='fotografo_dashboard'),
    path('parceiro-dashboard/', views.parceiro_dashboard, name='parceiro_dashboard'),
    path('api/dashboard/coordenador/', views.api_dashboard_coordenador, name='api_dashboard_coordenador'),
    path('dashboard_coordenador/', views.dashboard_coordenador, name='dashboard_coordenador'),
    path('dashboard_pesquisa/', views.dashboard_pesquisa, name='dashboard_pesquisa'), 
    
    # Dashboard híbrido para coordenador-fotógrafo
    path('dashboard-coordenador-fotografo/', views.dashboard_coordenador_fotografo, name='dashboard_coordenador_fotografo'),
    path('dashboard-inteligente/', views.dashboard_inteligente, name='dashboard_inteligente'),

    path('dashboard-coordenador-fotografo/', views.teste_dashboard_hibrido, name='teste_dashboard_hibrido'),


    # Fichas cadastradas por QRCode
    path('fichas_cadastradas/', views.fichas_cadastradas, name='fichas_cadastradas'),
    path('exportar_fichas/', views.exportar_fichas, name='exportar_fichas'),
    path('gerar-novo-token/<int:aluno_id>/', views.gerar_novo_token, name='gerar_novo_token'),

    # Usuários
    path('criar-usuario/', views.criar_usuario, name='criar_usuario'),
    path('editar-usuario/<int:user_id>/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/', views.listar_usuarios, name='listar_usuarios'), # Confirmado com listar_usuarios
    path('usuarios/desativar/<int:user_id>/', views.desativar_usuario, name='desativar_usuario'), # Nova
    path('usuarios/ativar/<int:user_id>/', views.ativar_usuario, name='ativar_usuario'), # Nova
    path('roles/', views.listar_roles, name='listar_roles'),
    path('roles/criar/', views.criar_role, name='criar_role'),
    path('roles/<int:role_id>/editar/', views.editar_role, name='editar_role'),

    # Parceiros
    path('parceiros/', views_parceiros.listar_parceiros, name='listar_parceiros'),
    path('parceiros/criar/', views_parceiros.criar_parceiro, name='criar_parceiro'),
    path('parceiros/<int:parceiro_id>/editar/', views_parceiros.editar_parceiro, name='editar_parceiro'),
    path('parceiros/<int:parceiro_id>/excluir/', views_parceiros.excluir_parceiro, name='excluir_parceiro'),
    path('parceiros/<int:parceiro_id>/desativar/', views_parceiros.desativar_parceiro, name='desativar_parceiro'),
    path('parceiros/<int:parceiro_id>/ativar/', views_parceiros.ativar_parceiro, name='ativar_parceiro'),

    # Eventos
    path('evento/<int:evento_id>/alterar_status/', views.alterar_status_evento, name='alterar_status_evento'),
    path('evento/<int:evento_id>/finalizar-captura/', views.finalizar_captura_gestor, name='finalizar_captura_gestor'),
    
    path('importar/eventos/', views.importar_eventos, name='importar_eventos'),
    path('exportar-eventos/', views.exportar_eventos, name='exportar_eventos'),
    
    path('evento/criar/', views.criar_evento, name='criar_evento'),
    path('eventos/', views.listar_eventos, name='listar_eventos'),
    path('evento/<int:evento_id>/editar/', views.editar_evento, name='editar_evento'),
    path('evento/<int:evento_id>/excluir/', views.deletar_evento, name='deletar_evento'),
    
    path('evento/<int:evento_id>/atribuir-fotografo/', views.atribuir_fotografo, name='atribuir_fotografo'),
    
    path('evento_andamento/', views.eventos_andamento, name='eventos_andamento'),
    path('evento_historico/', views.eventos_historico, name='eventos_historico'),
    path('finalizar-cartao-sd/<int:evento_id>/', views.finalizar_cartao_sd, name='finalizar_cartao_sd'),
    path('iniciar-evento-coordenador/<int:evento_id>/', views.iniciar_evento_coordenador, name='iniciar_evento_coordenador'),
    path('encerrar-evento/<int:evento_id>/', views.encerrar_evento_coordenador, name='encerrar_evento_coordenador'),
    path('encerrar-evento/<int:evento_id>/confirmar/', views.confirmar_encerrar_evento, name='confirmar_encerrar_evento'),
    path('eventos_finalizados/', views.eventos_finalizados, name='eventos_finalizados'),
    path('exportar-fotos-evento/', views.exportar_fotos_evento, name='exportar_fotos_evento'),

    # Alunos
    path('evento/<int:evento_id>/alunos/', views.evento_alunos, name='evento_alunos'),
    path('upload-foto/<int:aluno_id>/', views.upload_foto, name='upload_foto'),
    path('finalizar-sessao/<int:evento_id>/', views.finalizar_sessao, name='finalizar_sessao'),
    path('aluno/<int:aluno_id>/marcar_faltoso/', views.marcar_aluno_faltoso, name='marcar_aluno_faltoso'), 
    
    # Importação de alunos (fluxo em etapas)
    path('importar/alunos/<int:evento_id>/', views.importar_alunos, name='importar_alunos'),
    path('importar/alunos/selecionar/', views.selecionar_evento_para_importar, name='selecionar_evento_para_importar'),
    path('importar/alunos/confirmar/<int:evento_id>/', views.confirmar_importacao_alunos, name='confirmar_importacao_alunos'),
    path('importar/alunos/salvar/', views.salvar_importacao_alunos, name='salvar_importacao_alunos'),

    # Cadastro de alunos por qrcode
    path('alunos/', views.alunos_crud, name='alunos_crud'),
    path('aluno/novo/', views.aluno_novo, name='aluno_novo'),
    path('aluno/<int:aluno_id>/editar/', views.aluno_editar, name='aluno_editar'),
    path('aluno/<int:aluno_id>/visualizar/', views.aluno_visualizar, name='aluno_visualizar'),
    path('aluno/<int:aluno_id>/excluir/', views.aluno_excluir, name='aluno_excluir'),

    # Cadastro público (novo e edição)
    path('aluno/cadastro/', views.aluno_cadastro_publico, name='aluno_cadastro_publico'),  # Novo aluno
    path('aluno/cadastro/<int:aluno_id>/<str:token>/', views.aluno_cadastro_publico, name='aluno_cadastro_publico_editar'),  # Editar aluno
    
    # ✅ NOVO: Captura de Selfie Pública
    path('evento/<int:evento_id>/selfie/', views_selfie.captura_selfie_publico, name='captura_selfie_publico'),
    path('selfie/salvar/', views_selfie.salvar_selfie_publico, name='salvar_selfie_publico'),
    
    # 🔒 NOVO FLUXO: Selfie Obrigatória (após cadastro completo)
    path('aluno/selfie/<int:aluno_id>/<str:token>/', views_selfie.aluno_selfie_obrigatoria, name='aluno_selfie_obrigatoria'),
    path('aluno/selfie/salvar/', views_selfie.salvar_selfie_obrigatoria, name='salvar_selfie_obrigatoria'),

    # ✅ NOVO: Fluxo de Autoatendimento de Formandos
    # Rotas com UUID (SEGURO - recomendado)
    path('evento/<uuid:evento_uuid>/selfie-cadastro/', views_formandos.formando_selfie_cadastro, name='formando_selfie_cadastro_uuid'),
    path('evento/<uuid:evento_uuid>/formandos-status/', views_formandos.formandos_status, name='formandos_status_uuid'),
    path('evento/<uuid:evento_uuid>/formandos-link/', views_formandos.formandos_link_compartilhamento, name='formandos_link_compartilhamento_uuid'),
    path('evento/<uuid:evento_uuid>/importar-nomes/', views_formandos.importar_nomes_formandos, name='importar_nomes_formandos_uuid'),
    path('evento/<uuid:evento_uuid>/exportar-formandos/', views_formandos.exportar_formandos, name='exportar_formandos_uuid'),
    path('evento/<uuid:evento_uuid>/formandos-download/', views_formandos.baixar_tudo_formandos, name='baixar_tudo_formandos_uuid'),
    path('evento/<uuid:evento_uuid>/parceiros/', views_parceiros.gerenciar_parceiros_evento, name='gerenciar_parceiros_evento_uuid'),
    path('evento/<uuid:evento_uuid>/parceiros/link/', views_parceiros.gerar_link_compartilhamento_parceiro, name='gerar_link_parceiro_uuid'),
    path('evento/<uuid:evento_uuid>/formando/<int:aluno_id>/ver-cadastro/', views_formandos.formando_ver_cadastro, name='formando_ver_cadastro_uuid'),
    
    # Rotas com ID numérico (LEGADO - será descontinuado)
    path('evento/<int:evento_id>/selfie-cadastro/', views_formandos.formando_selfie_cadastro, name='formando_selfie_cadastro'),
    path('evento/<int:evento_id>/formandos-status/', views_formandos.formandos_status, name='formandos_status'),
    path('evento/<int:evento_id>/formandos-link/', views_formandos.formandos_link_compartilhamento, name='formandos_link_compartilhamento'),
    path('evento/<int:evento_id>/importar-nomes/', views_formandos.importar_nomes_formandos, name='importar_nomes_formandos'),
    path('evento/<int:evento_id>/exportar-formandos/', views_formandos.exportar_formandos, name='exportar_formandos'),
    path('evento/<int:evento_id>/formandos-download/', views_formandos.baixar_tudo_formandos, name='baixar_tudo_formandos'),
    path('evento/<int:evento_id>/parceiros/', views_parceiros.gerenciar_parceiros_evento, name='gerenciar_parceiros_evento'),
    path('evento/<int:evento_id>/parceiros/link/', views_parceiros.gerar_link_compartilhamento_parceiro, name='gerar_link_parceiro'),
    path('evento/<int:evento_id>/formando/<int:aluno_id>/ver-cadastro/', views_formandos.formando_ver_cadastro, name='formando_ver_cadastro'),

    path('aluno-cadastro-sucesso/', views.aluno_cadastro_sucesso, name='aluno_cadastro_sucesso'),
    path('api/verificar-cpf/', views.verificar_cpf_evento, name='verificar_cpf_evento'),

]
