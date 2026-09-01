# gestcaptur/views/autenticacao.py
# Views do domínio 'autenticacao' (extraídas do antigo views.py monolítico).

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from gestcaptur.models import Evento, Aluno, Usuario, SessaoFotografica
from gestcaptur.forms import LoginForm, UploadFotoForm, ImportXLSXForm, CriarUsuarioForm, EditarUsuarioForm, EventoForm, AlunoCadastroForm, RoleForm
import logging

logger = logging.getLogger(__name__)

def login_view(request):
    # ✅ CORRIGIDO: Verificar se já está autenticado ANTES de processar o form
    print(f"🔑 LOGIN_VIEW chamado")
    print(f"🔑 Method: {request.method}")
    print(f"🔑 User authenticated: {request.user.is_authenticated}")
    
    if request.user.is_authenticated:
        try:
            # Se há um ?next=, respeitar ele para todos os usuários (inclusive parceiros)
            next_url = request.GET.get('next')
            if next_url:
                print(f"🔄 Usuário {request.user.username} já autenticado com ?next=, redirecionando para: {next_url}")
                return redirect(next_url)
            
            dashboard_url = get_dashboard_redirect(request.user)
            print(f"🔄 Usuário {request.user.username} já autenticado, redirecionando para: {dashboard_url}")
            return redirect(dashboard_url)
        except Exception as e:
            print(f"❌ Erro no redirecionamento: {e}")
            # Se der erro, fazer logout e tentar novamente
            from django.contrib.auth import logout
            logout(request)
            return redirect('login')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Bem-vindo(a), {user.username}!")
            
            try:
                # Se há um ?next=, respeitar ele para todos os usuários (inclusive parceiros)
                next_url = request.GET.get('next')
                if next_url:
                    print(f"✅ Login realizado, redirecionando {user.username} para ?next=: {next_url}")
                    return redirect(next_url)
                
                dashboard_url = get_dashboard_redirect(user)
                print(f"✅ Login realizado, redirecionando {user.username} para: {dashboard_url}")
                return redirect(dashboard_url)
            except Exception as e:
                print(f"❌ Erro no redirecionamento pós-login: {e}")
                messages.error(request, "Erro ao redirecionar. Tente novamente.")
                return redirect('login')
        else:
            messages.error(request, "Nome de usuário ou senha inválidos.")
    else:
        form = LoginForm()
    
    return render(request, 'gestcaptur/login.html', {'form': form})


def get_dashboard_redirect(user):
    """
    Retorna a URL do dashboard apropriado baseado no role e situação do usuário.
    
    IMPORTANTE: Esta função NUNCA deve retornar 'login' pois isso causaria
    um loop infinito se o usuário já está autenticado.
    
    **NOTA PARA PARCEIROS:** Parceiros devem ser redirecionados via ?next= na URL
    de login para irem diretamente ao evento que desejam visualizar. Se não houver
    ?next=, vão para um dashboard genérico (ainda não implementado - usar fotografo_dashboard temporariamente).
    """
    print(f"🔍 Verificando redirecionamento para usuário: {user.username}")
    print(f"🔍 Role: {user.role}")
    print(f"🔍 Grupos: {[g.name for g in user.groups.all()]}")
    
    try:
        # Ordem de prioridade: Gestor > Coordenador > Fotógrafo > Pesquisa > Parceiro > Fallback
        
        if user.is_gestor():
            print("✅ Redirecionando para dashboard gestor")
            return 'dashboard'
            
        if user.is_coordenador():
            from gestcaptur.models import Evento
            atua_como_fotografo = Evento.objects.filter(
                coordenador=user,
                coordenador_tambem_fotografo=True
            ).exists()
            
            if atua_como_fotografo:
                print("✅ Redirecionando para dashboard coordenador-fotógrafo")
                return 'dashboard_coordenador_fotografo'
            else:
                print("✅ Redirecionando para dashboard coordenador")
                return 'dashboard_coordenador'
                
        if user.is_fotografo():
            print("✅ Redirecionando para dashboard fotógrafo")
            return 'fotografo_dashboard'
            
        if user.is_pesquisa():
            print("✅ Redirecionando para dashboard pesquisa")
            return 'dashboard_pesquisa'
        
        # ✅ NOVO: Suporte para Parceiros
        if user.is_parceiro():
            print(f"✅ Redirecionando parceiro '{user.username}' para dashboard de parceiro")
            return 'parceiro_dashboard'

        # ✅ NOVO: Grupos personalizados (ex.: 'Separação') com acesso via permissões
        # de guias do dashboard (ver_guia_*) ou permissão de ver eventos.
        # IMPORTANTE: só redireciona pra cá se houver ao menos 1 guia liberada,
        # senão cairia num loop de redirecionamento (dashboard nega -> volta pro login).
        if user.guias_dashboard_permitidas():
            print(f"✅ Redirecionando '{user.username}' para dashboard (acesso via permissões)")
            return 'dashboard'
        
        # FALLBACK: Se nenhum role foi detectado, redirecionar para fotografo_dashboard
        # (nunca retornar 'login' aqui, pois causaria loop infinito)
        print(f"⚠️ Usuário {user.username} não tem nenhuma role definida. Redirecionando para fotografo_dashboard como fallback")
        logger.warning(f"Usuário {user.username} (ID: {user.id}) sem role definida. Redirecionando para fotografo_dashboard")
        return 'fotografo_dashboard'
            
    except Exception as e:
        print(f"❌ Erro em get_dashboard_redirect: {e}")
        logger.exception(f"Erro ao redirecionar usuário {user.username}: {e}")
        # Fallback: redirecionar para fotografo_dashboard ao invés de login
        return 'fotografo_dashboard'


def debug_user(request):
    """View temporária para debug"""
    if request.user.is_authenticated:
        user_info = {
            'username': request.user.username,
            'role': request.user.role,
            'groups': [g.name for g in request.user.groups.all()],
            'is_gestor': request.user.is_gestor(),
            'is_coordenador': request.user.is_coordenador(),
            'is_fotografo': request.user.is_fotografo(),
            'is_pesquisa': request.user.is_pesquisa(),
        }
        return JsonResponse(user_info)
    else:
        return JsonResponse({'error': 'Usuário não autenticado'})


def logout_view(request):
    logout(request)
    messages.info(request, "Você foi desconectado.")
    return redirect('login')


def home_redirect(request):
    """View para redirecionar da home para o dashboard apropriado"""

    logger.info(f"🏠 HOME_REDIRECT: User={request.user}, Authenticated={request.user.is_authenticated}")
    print(f"🏠 HOME_REDIRECT: User={request.user}, Authenticated={request.user.is_authenticated}")

    print(f"🏠 HOME_REDIRECT chamado")
    print(f"🏠 User authenticated: {request.user.is_authenticated}")
    print(f"🏠 User: {request.user}")
    
    if request.user.is_authenticated:
        try:
            dashboard_url = get_dashboard_redirect(request.user)

            logger.info(f"🏠 Redirecionando para: {dashboard_url}")
            print(f"🏠 Redirecionando para: {dashboard_url}")

            print(f"🏠 Home redirect: {request.user.username} -> {dashboard_url}")
            return redirect(dashboard_url)
        except Exception as e:
            print(f"❌ Erro no home_redirect: {e}")
            messages.error(request, "Erro ao acessar dashboard. Contate o administrador.")
            return redirect('login')
    else:
        return redirect('login')
