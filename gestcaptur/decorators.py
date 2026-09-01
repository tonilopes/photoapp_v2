# gestcaptur/decorators.py (VERSÃO MELHORADA)

from django.contrib.auth.decorators import user_passes_test, login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden
from gestcaptur.models import Evento
from functools import wraps
import logging

logger = logging.getLogger(__name__)

def role_required(allowed_roles):
    """
    Decorator para verificar se o usuário tem a role necessária.
    Aceita uma string (single role) ou uma lista de strings (múltiplas roles).
    """
    if not isinstance(allowed_roles, (list, tuple)):
        allowed_roles = [allowed_roles]

    def check_role(user):
        if not user.is_authenticated:
            return False
        
        if user.role in allowed_roles:
            return True
            
        logger.warning(f"Acesso negado para {user.username}. Role: {user.role}, Permitidas: {allowed_roles}")
        return False
        
    return user_passes_test(check_role, login_url='login')

def group_required(group_names, login_url='login', raise_exception=False):
    """
    Decorator para verificar se o usuário pertence a pelo menos um dos grupos especificados
    OU tem a role correspondente no modelo.
    Aceita uma string (single group name) ou uma lista de strings (múltiplos group names).
    
    Exemplos:
    - @group_required('Fotógrafo') -> verifica grupo 'Fotógrafo' OU role='fotografo'
    - @group_required(['Gestor', 'Admin']) -> verifica grupos OU roles correspondentes
    """
    if not isinstance(group_names, (list, tuple)):
        group_names = [group_names]

    def check_group(user):
        if not user.is_authenticated:
            return False
        
        # Mapeamento de grupo para método role
        role_map = {
            'Gestor': 'is_gestor',
            'Coordenador': 'is_coordenador',
            'Fotógrafo': 'is_fotografo',
            'Pesquisa': 'is_pesquisa',
        }
        
        user_groups = [g.name for g in user.groups.all()]
        
        # Verificar grupos primeiro
        if any(group in user_groups for group in group_names):
            return True
        
        # Se não tiver grupo, verificar role correspondente
        for group_name in group_names:
            role_method = role_map.get(group_name)
            if role_method and hasattr(user, role_method):
                if getattr(user, role_method)():
                    logger.info(f"Acesso concedido para {user.username} via role (não via grupo)")
                    return True
        
        if raise_exception:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied(f"Acesso negado. Grupos ou roles necessários: {group_names}")
            
        logger.warning(f"Acesso negado para {user.username}. Grupos: {user_groups}, Role: {user.role}")
        return False
        
    return user_passes_test(check_group, login_url=login_url)


def dashboard_gestor_required(view_func):
    """
    Permite acesso ao dashboard do Gestor para: Gestores, ou qualquer usuário
    (ex.: grupos personalizados como 'Separação') que tenha ao menos uma
    permissão de guia do dashboard ou a permissão de ver eventos.
    """
    TAB_PERMS = [
        'ver_guia_grade', 'ver_guia_andamento', 'ver_guia_finalizados',
        'ver_guia_fichas_fotos', 'ver_guia_resumo',
    ]

    def check(user):
        if not user.is_authenticated:
            return False
        if user.is_gestor():
            return True
        if user.has_perm('gestcaptur.view_evento'):
            return True
        return any(user.has_perm(f'gestcaptur.{p}') for p in TAB_PERMS)

    return login_required(user_passes_test(check, login_url='login')(view_func))

def coordenador_fotografo_required(function=None, login_url='login'):
    """
    Decorator para garantir que o usuário é um coordenador E está marcado como
    'coordenador_tambem_fotografo' para algum evento.
    """
    def check_coordenador_fotografo(user):
        if not user.is_authenticated:
            return False
            
        is_coordenador = user.groups.filter(name='Coordenador').exists()
        if not is_coordenador:
            return False
            
        atua_como_fotografo = Evento.objects.filter(
            coordenador=user,
            coordenador_tambem_fotografo=True
        ).exists()
        
        return atua_como_fotografo
    
    actual_decorator = user_passes_test(check_coordenador_fotografo, login_url=login_url)
    
    if function:
        return actual_decorator(function)
    return actual_decorator


def evento_permission_required(permission_codename, login_url='login'):
    """Garante a permissão CRUD solicitada para o modelo Evento."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f'{login_url}?next={request.get_full_path()}')

            permission_name = f'gestcaptur.{permission_codename}'
            if request.user.is_superuser or request.user.has_perm(permission_name):
                return view_func(request, *args, **kwargs)

            messages.error(request, 'Você não possui permissão para executar esta ação em eventos.')
            return redirect('dashboard')
        return wrapped_view
    return decorator