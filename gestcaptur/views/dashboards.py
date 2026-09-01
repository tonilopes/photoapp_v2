# gestcaptur/views/dashboards.py
# Views do domínio 'dashboards' (extraídas do antigo views.py monolítico).

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.cache import never_cache
from django.utils import timezone
from django.db.models import F, Sum, Count, Q, Avg, ExpressionWrapper, DurationField
from gestcaptur.utils.dashboard import get_eventos_data_coordenador
from django.middleware.csrf import get_token, CsrfViewMiddleware
from gestcaptur.models import Evento, Aluno, Usuario, SessaoFotografica
from gestcaptur.decorators import role_required, group_required, dashboard_gestor_required, coordenador_fotografo_required, evento_permission_required
from datetime import datetime, timedelta
from django.utils.timezone import now
from django.utils.dateparse import parse_date
import logging

logger = logging.getLogger(__name__)

def dashboard(request):

    logger.info(f"📊 DASHBOARD: User={request.user}")
    print(f"📊 DASHBOARD: User={request.user}")   

    tipo_evento_filtro = request.GET.get('tipo_evento')
    empresa_filtro = request.GET.get('empresa')
    data = request.GET.get('data')
    if data:
        try:
            if '/' in data:
                data = datetime.strptime(data, '%d/%m/%Y').date()
            else:
                data = datetime.strptime(data, '%Y-%m-%d').date()
        except ValueError:
            data = None

    data_filtro = request.GET.get('data')
    eventos_cadastrados_query = Evento.objects.all()

    if tipo_evento_filtro:
        eventos_cadastrados_query = eventos_cadastrados_query.filter(tipo_evento__icontains=tipo_evento_filtro)
    if empresa_filtro:
        eventos_cadastrados_query = eventos_cadastrados_query.filter(instituicao__icontains=empresa_filtro)
    if data_filtro:
        eventos_cadastrados_query = eventos_cadastrados_query.filter(data=data_filtro)

    eventos_cadastrados = eventos_cadastrados_query.exclude(
        Q(status='iniciado') | Q(status='finalizado')
    ).order_by('-data', '-hora_inicio')

    # sugestão ChatGPT: Filtrar eventos em andamento
    eventos_andamento = Evento.objects.filter(status='iniciado')\
        .prefetch_related('sessoes_fotograficas', 'alunos', 'fotografos', 'coordenador')
    
    # somente eventos finalizados
    eventos_finalizados = Evento.objects.filter(status='finalizado').order_by('-data')
    for evento in eventos_finalizados:
        evento.total_alunos = evento.alunos.count()
        evento.total_fotos_count = evento.alunos.exclude(Q(foto='') | Q(foto__icontains='semfoto.png')).count()

    # fichas_cadastradas
    # Importa o código de agrupamento de fichas cadastradas
    alunos = Aluno.objects.filter(token__isnull=False)
    # (aplique os filtros se quiser)
    eventos = {}
    for aluno in alunos.select_related('evento'):
        evento = aluno.evento
        key = (evento.id, evento.instituicao, evento.tipo_evento)
        if key not in eventos:
            eventos[key] = []
        eventos[key].append(aluno)

    # CORRIGIDO: Preencher total_alunos para cada evento da grade
    for evento in eventos_cadastrados:
        evento.total_alunos = evento.alunos.count()
        # NOVO: Adicionar informação se pode iniciar captura
        evento.pode_iniciar_captura = (
            evento.status == 'pendente' and 
            not SessaoFotografica.objects.filter(evento=evento, finalizado_fotografo=False).exists()
        )
    
    # Estatísticas gerais (mantém como já estava)
    todos_eventos = Evento.objects.prefetch_related('alunos', 'sessoes_fotograficas', 'fotografos').all()
    for evento in todos_eventos:
        alunos_qs = evento.alunos.all()
        evento.total_alunos = alunos_qs.count()
        evento.total_com_foto = alunos_qs.exclude(Q(foto='') | Q(foto__icontains='semfoto.png')).count()
        evento.total_sem_foto = alunos_qs.filter(Q(foto='') | Q(foto__icontains='semfoto.png')).count()
        evento.total_identificados = alunos_qs.filter(ident=True).count()
        evento.total_nao_identificados = alunos_qs.filter(ident=False).count()
        evento.tempo_decorrido = now() - evento.hora_inicio if evento.hora_inicio else None
        sessoes_qs = evento.sessoes_fotograficas.all()
        sessoes_com_fim = sessoes_qs.exclude(fim_sessao=None)
        
        if sessoes_com_fim.exists():
            media_duracao = sessoes_com_fim.annotate(
                duracao=ExpressionWrapper(
                    F('fim_sessao') - F('inicio_sessao'), output_field=DurationField()
                )
            ).aggregate(media=Avg('duracao'))['media']
            evento.media_tempo_sd = media_duracao
        else:
            evento.media_tempo_sd = None

    # NOVO: Eventos com Formandos (Selfie + Cadastro)
    eventos_com_formandos = Evento.objects.filter(para_selfie=True).prefetch_related('alunos', 'parceiros')
    for evento in eventos_com_formandos:
        evento.alunos_com_selfie = evento.alunos.filter(selfie_realizada=True).count()

    # NOVO: Adicionar estatísticas de status para o dashboard
    eventos_pendentes_count = Evento.objects.filter(status='pendente').count()
    eventos_iniciados_count = eventos_andamento.count()
    eventos_finalizados_count = eventos_finalizados.count()

    # Guias do dashboard que este usuário pode ver (Gestor vê todas; grupos personalizados
    # veem apenas as guias liberadas via permissão 'ver_guia_*')
    guias_permitidas = request.user.guias_dashboard_permitidas()

    context = {
        'eventos_cadastrados': eventos_cadastrados,
        'eventos': todos_eventos,
        'tipo_evento': tipo_evento_filtro,
        'empresa': empresa_filtro,
        'data': data_filtro,
        'total_eventos': Evento.objects.count(),
        'total_alunos': Aluno.objects.count(),
        'total_fotos': Aluno.objects.exclude(Q(foto='') | Q(foto__icontains='semfoto.png')).count(),
        'total_fotografos': Usuario.objects.filter(groups__name='Fotógrafo').count(), # Ajustado para grupo
        'eventos_andamento': eventos_andamento,
        'eventos_finalizados': eventos_finalizados,
        'eventos_com_formandos': eventos_com_formandos,  # NOVO: eventos com selfie+cadastro
        'can_finalizar_captura': request.user.has_perm('gestcaptur.finalizar_captura_evento'),
        'filtros': {'fot': '', 'empresa': '', 'tipo_evento': '', 'data': ''},  # ou pegue dos GETs
        
        # NOVO: Estatísticas de status
        'eventos_pendentes': eventos_pendentes_count,
        'eventos_iniciados': eventos_iniciados_count,
        'eventos_finalizados_count': eventos_finalizados_count,

        # NOVO: controle de guias vis\u00edveis por permiss\u00e3o
        'guias_permitidas': guias_permitidas,
        'guia_ativa': guias_permitidas[0] if guias_permitidas else None,
    }
    return render(request, 'gestcaptur/gestor_dashboard.html', context)


def dashboard_coordenador(request):
    logger.info(f"Usuário logado: {request.user} (ID: {request.user.id})")
    # AQUI ESTÁ O FILTRO PRINCIPAL para eventos do coordenador logado
    eventos_do_coordenador = Evento.objects.filter(coordenador=request.user).order_by('-data', '-hora_inicio')
    logger.info(f"Eventos encontrados para {request.user.username}: {eventos_do_coordenador.count()}")
    # Lógica para criar sessões se o evento foi iniciado e ainda não tem sessão para fotógrafos
    # Esta lógica é executada para todas as requisições, seja HTML ou AJAX.
    for evento in eventos_do_coordenador:
        if evento.status == 'iniciado':
            for fotografo in evento.fotografos.all():
                sessao_existente = SessaoFotografica.objects.filter(evento=evento, fotografo=fotografo).exists()
                if not sessao_existente:
                    logger.info(f"Criando sessão para {fotografo.username} no evento {evento.id}")
                    SessaoFotografica.objects.create(
                        fotografo=fotografo,
                        evento=evento,
                        inicio_sessao=timezone.now(),
                        finalizado_fotografo=False,
                        finalizado_evento=False,
                        qtd_fotos=0,
                    )
    # Aplica os filtros de frontend e coleta os dados formatados
    filtros = {
        'fot': request.GET.get('fot'),
        'empresa': request.GET.get('empresa'),
    }
    eventos_data = get_eventos_data_coordenador(request.user, filtros)

    # --- INÍCIO DA CORREÇÃO CRÍTICA ---
    # Se a requisição for AJAX (detectada pelo cabeçalho 'X-Requested-With'),
    # retorne um JsonResponse.
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        logger.info("Requisição AJAX detectada. Retornando JsonResponse.")
        return JsonResponse({'eventos': eventos_data})
    # --- FIM DA CORREÇÃO CRÍTICA ---
    # Se NÃO for uma requisição AJAX (ou seja, carregamento inicial da página),
    # renderize o template HTML completo.
    logger.info("Requisição HTML detectada. Renderizando template.")
    context = {
        'eventos_data': eventos_data,   # Pode ser usado para pré-popular, mas o JS vai sobrescrever
        'eventos_finalizados': Evento.objects.filter(status='finalizado').order_by('-data'),
        # Você pode adicionar mais contexto HTML aqui se necessário
    }
    return render(request, 'gestcaptur/dashboard_coordenador.html', context)


def dashboard_coordenador_fotografo(request):
    """
    Dashboard híbrido para coordenadores que também atuam como fotógrafos
    """
    print("🚀 DASHBOARD HÍBRIDO CHAMADO!")
    print(f"🚀 Usuário: {request.user}")
    print(f"🚀 Autenticado: {request.user.is_authenticated}")
    print(f"🚀 Role: {getattr(request.user, 'role', 'N/A')}")
    
    usuario = request.user
    
    print(f"DEBUG - Usuario: {usuario}")
    print(f"DEBUG - Role: {usuario.role}")
    
    # Buscar eventos onde o usuário é coordenador E fotógrafo
    eventos_hibridos = Evento.objects.filter(
        coordenador=usuario,
        coordenador_tambem_fotografo=True
    ).order_by('-data', '-horario')
    
    print(f"DEBUG - Eventos híbridos encontrados: {eventos_hibridos.count()}")
    for evento in eventos_hibridos:
        print(f"DEBUG - Evento: {evento}, Coordenador: {evento.coordenador}, Coord+Foto: {evento.coordenador_tambem_fotografo}")
    # ✅ CORRIGIDO: Não usar 'coordenadores' - usar apenas eventos onde é fotógrafo mas NÃO coordenador híbrido
    eventos_coordenacao = Evento.objects.filter(
        coordenador=usuario,
        coordenador_tambem_fotografo=False  # Apenas coordenação, sem fotografia
    ).order_by('-data', '-horario')
    
    print(f"DEBUG - Eventos só coordenação: {eventos_coordenacao.count()}")
    
    # Buscar eventos onde é apenas fotógrafo (não é coordenador)
    eventos_fotografia = Evento.objects.filter(
        fotografos=usuario
    ).exclude(
        coordenador=usuario  # Excluir onde também é coordenador
    ).order_by('-data', '-horario')
    
    print(f"DEBUG - Eventos só fotografia: {eventos_fotografia.count()}")
    
    # Estatísticas - CORRIGIDO
    total_fotos_capturadas = 0
    total_sessoes = 0
    
    try:
        # Método 1: Contar através do campo photographer no modelo Aluno
        for evento in eventos_hibridos:
            fotos_evento = Aluno.objects.filter(
                evento=evento,
                photographer=usuario,
                foto__isnull=False
            ).exclude(foto='').count()
            total_fotos_capturadas += fotos_evento
            print(f"DEBUG - Evento {evento.id}: {fotos_evento} fotos")
        
        # Método 2: Contar através das SessoesFotograficas
        total_sessoes = SessaoFotografica.objects.filter(
            fotografo=usuario,
            evento__in=eventos_hibridos
        ).count()
        
        print(f"DEBUG - Total fotos: {total_fotos_capturadas}")
        print(f"DEBUG - Total sessões: {total_sessoes}")
        
        # Se não houver fotos pelo photographer, usar qtd_fotos das sessões
        if total_fotos_capturadas == 0:
            from django.db.models import Sum
            total_fotos_sessoes = SessaoFotografica.objects.filter(
                fotografo=usuario,
                evento__in=eventos_hibridos
            ).aggregate(
                total=Sum('qtd_fotos')
            )['total'] or 0
            
            print(f"DEBUG - Total fotos das sessões: {total_fotos_sessoes}")
            total_fotos_capturadas = total_fotos_sessoes
            
    except Exception as e:
        print(f"ERRO ao calcular estatísticas: {e}")
        total_fotos_capturadas = 0
        total_sessoes = 0
    
    # Adicionar informações extras para cada evento híbrido
    eventos_hibridos_info = []
    for evento in eventos_hibridos:
        # Contar fotos deste evento específico
        fotos_evento = Aluno.objects.filter(
            evento=evento,
            photographer=usuario,
            foto__isnull=False
        ).exclude(foto='').count()
        
        # Verificar se tem sessão ativa
        sessao_ativa = SessaoFotografica.objects.filter(
            fotografo=usuario,
            evento=evento,
            fim_sessao__isnull=True
        ).exists()
        
        eventos_hibridos_info.append({
            'evento': evento,
            'fotos_capturadas': fotos_evento,
            'sessao_ativa': sessao_ativa,
        })
    
    # Garantir que as variáveis não sejam None
    total_fotos_capturadas = total_fotos_capturadas or 0
    total_sessoes = total_sessoes or 0
    
    print(f"DEBUG - Valores finais - Fotos: {total_fotos_capturadas}, Sessões: {total_sessoes}")
    
    context = {
        'eventos_hibridos': eventos_hibridos,
        'eventos_hibridos_info': eventos_hibridos_info,
        'eventos_coordenacao': eventos_coordenacao,
        'eventos_fotografia': eventos_fotografia,
        'total_fotos_capturadas': total_fotos_capturadas,
        'total_sessoes': total_sessoes,
        'usuario': usuario,
    }
    
    print(f"DEBUG - Context: {context}")
    
    return render(request, 'gestcaptur/dashboard_coordenador_fotografo.html', context)


def teste_dashboard_hibrido(request):
    """View de teste para debug"""
    from django.http import JsonResponse
    
    usuario = request.user
    
    # Dados básicos
    dados = {
        'usuario': str(usuario),
        'role': getattr(usuario, 'role', 'N/A'),
        'autenticado': usuario.is_authenticated,
        'groups': [g.name for g in usuario.groups.all()]
    }
    
    # Eventos como coordenador
    eventos_coord = Evento.objects.filter(coordenador=usuario)
    dados['eventos_como_coordenador'] = eventos_coord.count()
    
    # Eventos híbridos
    eventos_hibridos = Evento.objects.filter(
        coordenador=usuario,
        coordenador_tambem_fotografo=True
    )
    dados['eventos_hibridos'] = eventos_hibridos.count()
    dados['lista_eventos_hibridos'] = [
        {
            'id': e.id,
            'tipo': e.tipo_evento,
            'coordenador': str(e.coordenador),
            'coord_tambem_foto': e.coordenador_tambem_fotografo,
            'fotografos': [str(f) for f in e.fotografos.all()]
        }
        for e in eventos_hibridos
    ]
    
    # Eventos como fotógrafo
    eventos_foto = Evento.objects.filter(fotografos=usuario)
    dados['eventos_como_fotografo'] = eventos_foto.count()
    
    return JsonResponse(dados, indent=2)


def dashboard_inteligente(request):
    """
    Dashboard inteligente que redireciona baseado no role e situação do usuário
    """
    usuario = request.user
    
    if usuario.is_gestor():
        return redirect('dashboard')
    
    elif usuario.is_fotografo():
        return redirect('fotografo_dashboard')
    
    elif usuario.is_coordenador():
        # Verificar se o coordenador também atua como fotógrafo
        atua_como_fotografo = Evento.objects.filter(
            coordenador=usuario,
            coordenador_tambem_fotografo=True
        ).exists()
        
        if atua_como_fotografo:
            return redirect('dashboard_coordenador_fotografo')
        else:
            return redirect('dashboard_coordenador')
    
    elif usuario.is_pesquisa():
        return redirect('dashboard_pesquisa') # NOVO
    
    else:
        messages.error(request, 'Role ou grupo não reconhecido.')
        return redirect('login')


def api_dashboard_coordenador(request):
    filtros = {
        'fot': request.GET.get('fot'),
        'empresa': request.GET.get('empresa'),
    }
    eventos_data = get_eventos_data_coordenador(request.user, filtros)
    return JsonResponse({'eventos': eventos_data})


def fichas_cadastradas(request):
    fot = request.GET.get('fot', '')
    empresa = request.GET.get('empresa', '')
    tipo_evento = request.GET.get('tipo_evento', '')
    data = request.GET.get('data', '')
    # Inclui alunos de eventos finalizados também
    alunos = Aluno.objects.filter(token__isnull=False)
    if fot:
        alunos = alunos.filter(evento__fot__icontains=fot)
    if empresa:
        alunos = alunos.filter(evento__instituicao__icontains=empresa)
    if tipo_evento:
        alunos = alunos.filter(evento__tipo_evento__icontains=tipo_evento)
    if data:
        alunos = alunos.filter(evento__data=data)

    # Agrupa alunos por evento, incluindo eventos finalizados
    eventos = {}
    for aluno in alunos.select_related('evento'):
        evento = aluno.evento
        key = (evento.id, evento.instituicao, evento.tipo_evento)
        if key not in eventos:
            eventos[key] = []
        eventos[key].append(aluno)

    return render(request, 'gestcaptur/fichas_cadastradas.html', {
        'eventos': eventos,
        'filtros': {'fot': fot, 'empresa': empresa, 'tipo_evento': tipo_evento, 'data': data}
    })


def fotografo_dashboard(request):
    fotografo = request.user
    
    get_token(request)
    
    eventos = Evento.objects.filter(
        fotografos=fotografo,
        status__in=['pendente', 'iniciado']
    ).order_by('data', 'horario')

    for evento in eventos:
        # Sessão ativa: sessão não finalizada para este fotógrafo e evento
        evento.sessao_ativa = SessaoFotografica.objects.filter(
            fotografo=fotografo,
            evento=evento,
            finalizado_fotografo=False,
            finalizado_evento=False
        ).order_by('-inicio_sessao').first()

        evento.total_alunos = evento.alunos.count()

        # Sessões finalizadas desse fotógrafo no evento
        evento.sessoes_finalizadas_fotografo = SessaoFotografica.objects.filter(
            fotografo=fotografo,
            evento=evento,
            finalizado_fotografo=True
        ).order_by('-fim_sessao')
        # Total de fotos desse fotógrafo no evento
        evento.total_fotos_capturadas_fotografo = Aluno.objects.filter(
            evento=evento,
            photographer=fotografo,
            ).exclude(Q(foto='') | Q(foto__isnull=True) | Q(foto__icontains='semfoto.png')).count()

    context = {
        'eventos': eventos,
    }
    return render(request, 'gestcaptur/fotografo_dashboard.html', context)


def parceiro_dashboard(request):
    """Dashboard simplificado para parceiros - mostra apenas eventos aos quais têm acesso"""
    parceiro = request.user
    
    # Verificar se o usuário é realmente um parceiro
    if not parceiro.is_parceiro():
        messages.error(request, "Acesso restrito a parceiros.")
        return redirect('login')
    
    # Buscar eventos aos quais este parceiro tem acesso
    eventos_list = []
    eventos_qs = parceiro.eventos_como_parceiro.filter(
        status__in=['pendente', 'iniciado']
    ).order_by('-data')
    
    # Adicionar informações úteis a cada evento
    for evento in eventos_qs:
        total_alunos = evento.alunos.count()
        total_fotos = Aluno.objects.filter(
            evento=evento
        ).exclude(Q(foto='') | Q(foto__isnull=True) | Q(foto__icontains='semfoto.png')).count()
        
        # Criar um dicionário com os dados do evento
        evento_data = {
            'id': evento.id,
            'uuid': evento.uuid,
            'fot': evento.fot,
            'instituicao': evento.instituicao,
            'data': evento.data,
            'status': evento.status,
            'observacoes': evento.observacoes,
            'total_alunos': total_alunos,
            'total_fotos': total_fotos,
        }
        eventos_list.append(evento_data)
    
    context = {
        'eventos': eventos_list,
        'parceiro_nome': parceiro.get_full_name() or parceiro.username,
    }
    return render(request, 'gestcaptur/parceiro_dashboard.html', context)


def eventos_gestor(request):
    """
    Página principal de gerenciamento de eventos para o gestor
    Combina listagem, filtros e ações em uma só página
    """
    # Filtros
    tipo_evento_filter = request.GET.get('tipo_evento')
    empresa_filter = request.GET.get('empresa')
    status_filter = request.GET.get('status')
    data_inicio_filter = request.GET.get('data_inicio')
    data_fim_filter = request.GET.get('data_fim')
    instituicao_filter = request.GET.get('instituicao')

    # Query base
    eventos = Evento.objects.all().order_by('-data')

    # Aplicar filtros
    if tipo_evento_filter:
        eventos = eventos.filter(tipo_evento__icontains=tipo_evento_filter)
    if empresa_filter:
        eventos = eventos.filter(empresa__icontains=empresa_filter)
    if status_filter:
        eventos = eventos.filter(status=status_filter)
    if data_inicio_filter:
        eventos = eventos.filter(data__gte=data_inicio_filter)
    if data_fim_filter:
        eventos = eventos.filter(data__lte=data_fim_filter)
    if instituicao_filter:
        eventos = eventos.filter(instituicao__icontains=instituicao_filter)
    # Adicionar estatísticas para cada evento
    for evento in eventos:
        evento.total_alunos = Aluno.objects.filter(evento=evento).count()
        evento.alunos_com_foto = Aluno.objects.filter(evento=evento, foto__isnull=False).exclude(foto='').count()
        evento.percentual_fotos = round((evento.alunos_com_foto / evento.total_alunos * 100) if evento.total_alunos > 0 else 0, 1)

    # Estatísticas gerais
    total_eventos = eventos.count()
    eventos_pendentes = eventos.filter(status='pendente').count()
    eventos_iniciados = eventos.filter(status='iniciado').count()
    eventos_finalizados = eventos.filter(status='finalizado').count()
    context = {
        'eventos': eventos,
        'total_eventos': total_eventos,
        'eventos_pendentes': eventos_pendentes,
        'eventos_iniciados': eventos_iniciados,
        'eventos_finalizados': eventos_finalizados,
        'filtros': {
            'tipo_evento': tipo_evento_filter,
            'empresa': empresa_filter,
            'status': status_filter,
            'data_inicio': data_inicio_filter,
            'data_fim': data_fim_filter,
            'instituicao': instituicao_filter,
        }
    }
    
    return render(request, 'gestcaptur/eventos_gestor.html', context)


def eventos_andamento(request):
    eventos = Evento.objects.filter(status='iniciado') # Alterado de 'andamento' para 'iniciado'

    context = {'eventos': eventos}
    return render(request, 'gestcaptur/eventos_andamento.html', context)


def eventos_finalizados(request):
    eventos = Evento.objects.filter(status='finalizado').order_by('-data')
    for evento in eventos:
        evento.total_alunos = evento.alunos.count()
        evento.total_fotos = evento.alunos.exclude(Q(foto='') | Q(foto__icontains='semfoto.png')).count()
    return render(request, 'gestcaptur/eventos_finalizados.html', {'eventos': eventos})


def eventos_historico(request):
    eventos = Evento.objects.filter(status='finalizado').order_by('-data')

    # Filtros GET
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    instituicao = request.GET.get('instituicao')
    if data_inicio:
        eventos = eventos.filter(data__gte=parse_date(data_inicio))
    if data_fim:
        eventos = eventos.filter(data__lte=parse_date(data_fim))
    if instituicao:
        eventos = eventos.filter(instituicao__icontains=instituicao)

    # Contagem de fotos
    for evento in eventos:
        evento.total_fotos = evento.alunos.exclude(Q(foto='') | Q(foto__icontains='semfoto.png')).count()
    return render(request, 'gestcaptur/eventos_historico.html', {
        'eventos': eventos,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'instituicao': instituicao,
    })


def dashboard_pesquisa(request):
    eventos = Evento.objects.all().order_by('-data')
    # Adicionar contagens de fotos, alunos, etc. para cada evento
    for evento in eventos:
        evento.total_alunos_cadastrados = evento.alunos.count()
        evento.total_fotos_capturadas = evento.alunos.exclude(Q(foto='') | Q(foto__isnull=True)).count()

    context = {
        'eventos': eventos,
        'total_eventos': eventos.count(),
        'total_alunos': Aluno.objects.count(),
        'total_fotos_geral': Aluno.objects.exclude(Q(foto='') | Q(foto__isnull=True)).count(),
    }
    return render(request, 'gestcaptur/dashboard_pesquisa.html', context)
