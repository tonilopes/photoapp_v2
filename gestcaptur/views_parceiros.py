# gestcaptur/views_parceiros.py
# Views para gerenciamento de usuários parceiros

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import Usuario, Evento
from .decorators import group_required
from django import forms


class FormularioParceiro(forms.ModelForm):
    """Formulário para criar/editar parceiro"""
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(),
        required=False,
        help_text='Deixe em branco para manter a senha atual'
    )
    password_confirm = forms.CharField(
        label='Confirmar Senha',
        widget=forms.PasswordInput(),
        required=False,
        help_text='Confirme a nova senha'
    )
    
    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']
        labels = {
            'username': 'Nome de Usuário',
            'first_name': 'Primeiro Nome',
            'last_name': 'Último Nome',
            'email': 'Email',
            'is_active': 'Ativo',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # Para edição, deixar password opcional
            self.fields['password'].required = False
            self.fields['password_confirm'].required = False
        else:
            # Para criação, password é obrigatório
            self.fields['password'].required = True
            self.fields['password_confirm'].required = True
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password != password_confirm:
            raise forms.ValidationError("As senhas não coincidem.")
        
        if not self.instance.pk and not password:
            raise forms.ValidationError("Senha é obrigatória para novos parceiros.")
        
        return cleaned_data


@login_required
@group_required('Gestor')
def listar_parceiros(request):
    """
    Lista todos os usuários com role 'parceiro'
    """
    parceiros = Usuario.objects.filter(role='parceiro').order_by('username')
    
    context = {
        'parceiros': parceiros,
        'total_parceiros': parceiros.count(),
    }
    
    return render(request, 'gestcaptur/listar_parceiros.html', context)


@login_required
@group_required('Gestor')
def criar_parceiro(request):
    """
    Cria um novo usuário com role 'parceiro'
    """
    if request.method == 'POST':
        form = FormularioParceiro(request.POST)
        if form.is_valid():
            with transaction.atomic():
                parceiro = form.save(commit=False)
                parceiro.role = 'parceiro'  # Definir role como parceiro
                parceiro.set_password(form.cleaned_data['password'])
                parceiro.save()
                
                messages.success(
                    request,
                    f'Parceiro "{parceiro.username}" criado com sucesso! '
                    f'Ele pode fazer login com sua conta para acessar o painel de formandos em leitura.'
                )
            return redirect('listar_parceiros')
    else:
        form = FormularioParceiro()
    
    return render(request, 'gestcaptur/criar_parceiro.html', {'form': form})


@login_required
@group_required('Gestor')
def editar_parceiro(request, parceiro_id):
    """
    Edita um usuário parceiro existente
    """
    parceiro = get_object_or_404(Usuario, id=parceiro_id, role='parceiro')
    
    if request.method == 'POST':
        form = FormularioParceiro(request.POST, instance=parceiro)
        if form.is_valid():
            with transaction.atomic():
                parceiro = form.save(commit=False)
                
                # Se houver nova senha, atualizar
                if form.cleaned_data['password']:
                    parceiro.set_password(form.cleaned_data['password'])
                
                parceiro.save()
                messages.success(request, f'Parceiro "{parceiro.username}" atualizado com sucesso!')
            return redirect('listar_parceiros')
    else:
        form = FormularioParceiro(instance=parceiro)
    
    return render(request, 'gestcaptur/editar_parceiro.html', {
        'form': form,
        'parceiro': parceiro,
    })


@login_required
@group_required('Gestor')
def excluir_parceiro(request, parceiro_id):
    """
    Exclui um usuário parceiro
    """
    parceiro = get_object_or_404(Usuario, id=parceiro_id, role='parceiro')
    
    if request.method == 'POST':
        nome_parceiro = parceiro.username
        parceiro.delete()
        messages.success(request, f'Parceiro "{nome_parceiro}" excluído com sucesso!')
        return redirect('listar_parceiros')
    
    return render(request, 'gestcaptur/confirmar_excluir_parceiro.html', {
        'parceiro': parceiro,
    })


@login_required
@group_required('Gestor')
def desativar_parceiro(request, parceiro_id):
    """
    Desativa um usuário parceiro (sem acesso ao sistema)
    """
    parceiro = get_object_or_404(Usuario, id=parceiro_id, role='parceiro')
    
    if request.method == 'POST':
        parceiro.is_active = False
        parceiro.save()
        messages.success(request, f'Parceiro "{parceiro.username}" desativado com sucesso!')
        return redirect('listar_parceiros')
    
    return render(request, 'gestcaptur/confirmar_desativar_parceiro.html', {
        'parceiro': parceiro,
    })


@login_required
@group_required('Gestor')
def ativar_parceiro(request, parceiro_id):
    """
    Ativa um usuário parceiro (restaura acesso)
    """
    parceiro = get_object_or_404(Usuario, id=parceiro_id, role='parceiro')
    
    if request.method == 'POST':
        parceiro.is_active = True
        parceiro.save()
        messages.success(request, f'Parceiro "{parceiro.username}" ativado com sucesso!')
        return redirect('listar_parceiros')
    
    return render(request, 'gestcaptur/confirmar_ativar_parceiro.html', {
        'parceiro': parceiro,
    })


# ============================================================================
# GERENCIAMENTO DE PARCEIROS POR EVENTO
# ============================================================================

@login_required
def gerenciar_parceiros_evento(request, evento_id=None, evento_uuid=None):
    """
    Gerencia quais parceiros têm acesso a um evento específico.
    Permite adicionar e remover parceiros do evento.
    
    ✅ Mesma regra do botão 'Parceiros' no painel: gestor, coordenador do
    evento, ou perm. 'ver_botao_parceiros_formandos'.
    (Antes exigia grupo 'Gestor' -> loop/403 para outros usuários.)
    """
    from .views_formandos import _obter_evento, _pode_usar_botao_formandos
    
    evento = _obter_evento(evento_id=evento_id, evento_uuid=evento_uuid)
    
    # Verificar permissão (idêntica à regra que exibe o botão no painel)
    if not _pode_usar_botao_formandos(request.user, evento, 'ver_botao_parceiros_formandos'):
        messages.error(request, "Você não tem permissão para gerenciar parceiros deste evento.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        parceiro_id = request.POST.get('parceiro_id')
        acao = request.POST.get('acao')  # 'adicionar' ou 'remover'
        
        parceiro = get_object_or_404(Usuario, id=parceiro_id, role='parceiro')
        
        if acao == 'adicionar':
            evento.parceiros.add(parceiro)
            messages.success(
                request,
                f'Parceiro "{parceiro.username}" agora tem acesso ao evento "{evento.fot}". '
                f'Clique no botão "Compartilhar Link" para gerar as instruções de acesso.'
            )
        elif acao == 'remover':
            evento.parceiros.remove(parceiro)
            messages.warning(
                request,
                f'Parceiro "{parceiro.username}" foi removido do evento "{evento.fot}"'
            )
        
        return redirect('gerenciar_parceiros_evento_uuid', evento_uuid=evento.uuid)
    
    # Listar parceiros disponíveis (ativos) e os já vinculados
    parceiros_disponiveis = Usuario.objects.filter(
        role='parceiro',
        is_active=True
    ).exclude(id__in=evento.parceiros.all()).order_by('username')
    
    parceiros_vinculados = evento.parceiros.all().order_by('username')
    
    context = {
        'evento': evento,
        'parceiros_vinculados': parceiros_vinculados,
        'parceiros_disponiveis': parceiros_disponiveis,
        'total_vinculados': parceiros_vinculados.count(),
    }
    
    return render(request, 'gestcaptur/gerenciar_parceiros_evento.html', context)


@login_required
def gerar_link_compartilhamento_parceiro(request, evento_id=None, evento_uuid=None):
    """
    Gera instruções de acesso para compartilhar com um parceiro.
    Mostra:
    - Link seguro do painel de formandos (requer login)
    - Username do parceiro
    - Instruções para o parceiro fazer login
    
    ✅ Mesma regra do botão 'Parceiros' no painel: gestor, coordenador do
    evento, ou perm. 'ver_botao_parceiros_formandos'.
    """
    from .views_formandos import _obter_evento, _pode_usar_botao_formandos
    
    evento = _obter_evento(evento_id=evento_id, evento_uuid=evento_uuid)
    
    # Verificar permissão (idêntica à regra que exibe o botão no painel)
    if not _pode_usar_botao_formandos(request.user, evento, 'ver_botao_parceiros_formandos'):
        messages.error(request, "Você não tem permissão.")
        return redirect('dashboard')
    
    # Listar parceiros vinculados
    parceiros = evento.parceiros.all().order_by('username')
    
    if not parceiros.exists():
        messages.info(
            request,
            f'Nenhum parceiro vinculado ao evento "{evento.fot}". '
            f'Vá para "Gerenciar Parceiros" e adicione pelo menos um.'
        )
        return redirect('gerenciar_parceiros_evento_uuid', evento_uuid=evento.uuid)
    
    # Preparar dados para compartilhamento
    # ✅ Links gerados dinamicamente a partir do host usado no acesso
    # (antes eram hardcoded para https://photoapp.photum.com.br — errado no v2/fotoid)
    from django.urls import reverse
    path_painel = reverse('formandos_status_uuid', kwargs={'evento_uuid': evento.uuid})
    link_painel = request.build_absolute_uri(path_painel)
    link_login = request.build_absolute_uri('/login/') + '?next=' + path_painel
    
    context = {
        'evento': evento,
        'parceiros': parceiros,
        'link_painel': link_painel,
        'link_login': link_login,
    }
    
    return render(request, 'gestcaptur/gerar_link_parceiro.html', context)

