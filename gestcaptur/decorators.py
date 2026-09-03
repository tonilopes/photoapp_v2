# gestcaptur/decorators.py (VERSÃO MELHORADA)

from django.contrib.auth.decorators import user_passes_test, login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from gestcaptur.models import Evento
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# NOTA ANTI-LOOP:
# Quando um usuário AUTENTICADO falha em role_required/group_required,
# NÃO redirecionamos para o login. O login_view devolve o usuário autenticado
# de volta para a URL de origem via ?next=, o que criaria um loop infinito
# de redirecionamento ("Redirecionamento em excesso" no navegador).
# Nesses casos levantamos PermissionDenied (página 403), que nunca redireciona.

def role_required(allowed_roles):
    """
    Decorator para verificar se o usuário tem a role necessária.
    Aceita uma string (single role) ou uma lista de strings (múltiplas roles).

    ✅ Anti-loop: usuário autenticado sem a role recebe 403.
    """
    if not isinstance(allowed_roles, (list, tuple)):
        allowed_roles = [allowed_roles]

    def check_role(user):
        if not user.is_authenticated:
            return False  # anônimo -> tela de login (com ?next=)
        
        if user.role in allowed_roles:
            return True
            
        logger.warning(f"Acesso negado para {user.username}. Role: {user.role}, Permitidas: {allowed_roles}")
        raise PermissionDenied(
            f"Acesso negado: esta área exige role '{allowed_roles}' "
            f"(usuário '{user.username}' tem role '{user.role}')."
        )
        
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
            logger.warning(f"Acesso negado (raise) para {user.username}. Grupos: {user_groups}, Role: {user.role}")
        
        # ✅ Anti-loop: autenticado sem acesso -> 403 (nunca redirecionar ao login)
        logger.warning(f"Acesso negado para {user.username}. Grupos: {user_groups}, Role: {user.role}")
        raise PermissionDenied(
            f"Acesso negado para {user.username}. Grupos: {user_groups}, Role: {user.role}. "
            f"Grupos ou roles necessários: {group_names}"
        )
        
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
        if any(user.has_perm(f'gestcaptur.{p}') for p in TAB_PERMS):
            return True
        # ✅ Anti-loop: autenticado sem acesso ao dashboard -> 403
        logger.warning(f"Dashboard negado para {user.username} (sem view_evento nem guias).")
        raise PermissionDenied(
            f"Acesso negado: usuário '{user.username}' não tem permissão para acessar o dashboard."
        )

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
            # ✅ Anti-loop: autenticado sem acesso -> 403
            raise PermissionDenied(
                f"Acesso negado: usuário '{user.username}' não pertence ao grupo Coordenador."
            )
            
        atua_como_fotografo = Evento.objects.filter(
            coordenador=user,
            coordenador_tambem_fotografo=True
        ).exists()
        
        if atua_como_fotografo:
            return True
        # ✅ Anti-loop: autenticado sem acesso -> 403
        raise PermissionDenied(
            f"Acesso negado: coordenador '{user.username}' não atua como fotógrafo em nenhum evento."
        )
    
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