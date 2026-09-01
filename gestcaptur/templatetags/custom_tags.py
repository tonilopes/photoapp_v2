from django import template
from gestcaptur.models import Evento

register = template.Library()

@register.filter
def tem_eventos_hibridos(user):
    """Verifica se o usuário tem eventos onde é coordenador e fotógrafo"""
    if not user or not hasattr(user, 'role') or user.role != 'coordenador':
        return False
    
    return Evento.objects.filter(
        coordenador=user,
        coordenador_tambem_fotografo=True
    ).exists()

@register.filter
def count_eventos_hibridos(user):
    """Conta quantos eventos híbridos o usuário tem"""
    if not user or not hasattr(user, 'role') or user.role != 'coordenador':
        return 0
    
    return Evento.objects.filter(
        coordenador=user,
        coordenador_tambem_fotografo=True
    ).count()