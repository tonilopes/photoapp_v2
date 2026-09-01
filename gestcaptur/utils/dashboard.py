# gestcaptur/utils/dashboard.py

from django.utils import timezone
from gestcaptur.models import Evento, SessaoFotografica, Aluno

def get_eventos_data_coordenador(user, filtros=None):
    eventos = Evento.objects.filter(coordenador=user).order_by('-data', '-hora_inicio')

    # Aplicar filtros
    if filtros:
        fot_filter = filtros.get('fot')
        empresa_filter = filtros.get('empresa')
        if fot_filter:
            eventos = eventos.filter(fotografos__username__icontains=fot_filter).distinct()
        if empresa_filter:
            eventos = eventos.filter(instituicao__icontains=empresa_filter)

    eventos_data = []

    for evento in eventos:
        # Criar sessões se ainda não existirem
        if evento.status == 'iniciado':
            for fotografo in evento.fotografos.all():
                if not SessaoFotografica.objects.filter(evento=evento, fotografo=fotografo).exists():
                    SessaoFotografica.objects.create(
                        fotografo=fotografo,
                        evento=evento,
                        inicio_sessao=timezone.now(),
                        finalizado_fotografo=False,
                        finalizado_evento=False,
                        qtd_fotos=0
                    )

        fotografos_status = []
        for fotografo in evento.fotografos.all():
            sessoes = SessaoFotografica.objects.filter(evento=evento, fotografo=fotografo)
            sessoes_info = []
            total_fotos = Aluno.objects.filter(evento=evento, photographer=fotografo)\
                .exclude(foto='').exclude(foto__isnull=True).count()

            for sessao in sessoes:
                sessoes_info.append({
                    'qtd_fotos': sessao.qtd_fotos,
                    'inicio_sessao': sessao.inicio_sessao.strftime('%H:%M') if sessao.inicio_sessao else '—',
                    'fim_sessao': sessao.fim_sessao.strftime('%H:%M') if sessao.fim_sessao else '—',
                    'status_sessao': 'Finalizada' if sessao.finalizado_fotografo else 'Em Andamento'
                })

            fotografos_status.append({
                'id': fotografo.id,
                'username': fotografo.username,
                'sessoes': sessoes_info,
                'total_fotos_fotografo': total_fotos,
            })

        eventos_data.append({
            'evento': {
                'id': evento.id,
                'fot': evento.fot,
                'instituicao': evento.instituicao,
                'tipo_evento': evento.tipo_evento,
                'coordenador': evento.coordenador.username if evento.coordenador else "N/A",
                'status': evento.get_status_display(),
                'total_alunos': evento.alunos.count(),
            },
            'fotografos_status': fotografos_status,
            'pode_iniciar_captura': evento.status == 'pendente' and not SessaoFotografica.objects.filter(evento=evento, finalizado_fotografo=False).exists()
        })

    return eventos_data
