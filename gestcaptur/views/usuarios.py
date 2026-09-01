# gestcaptur/views/usuarios.py
# Views do domínio 'usuarios' (extraídas do antigo views.py monolítico).

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib import messages
from gestcaptur.models import Evento, Aluno, Usuario, SessaoFotografica
from gestcaptur.forms import LoginForm, UploadFotoForm, ImportXLSXForm, CriarUsuarioForm, EditarUsuarioForm, EventoForm, AlunoCadastroForm, RoleForm
from gestcaptur.decorators import role_required, group_required, dashboard_gestor_required, coordenador_fotografo_required, evento_permission_required

import logging

logger = logging.getLogger(__name__)

def listar_usuarios(request):
    usuarios = Usuario.objects.all().order_by('username')
    return render(request, 'gestcaptur/listar_usuarios.html', {'usuarios': usuarios})


def criar_usuario(request):
    if request.method == 'POST':
        form = CriarUsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuário criado com sucesso!')
            return redirect('listar_usuarios')
    else:
        form = CriarUsuarioForm()
    
    return render(request, 'gestcaptur/criar_usuario.html', {'form': form})


def editar_usuario(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)
    if request.method == 'POST':
        form = EditarUsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data.get('password')
            if password:
                user.set_password(password)  # Define a nova senha
            user.save()
            messages.success(request, "Usuário atualizado com sucesso!")
            return redirect('listar_usuarios')
    else:
        form = EditarUsuarioForm(instance=usuario)

    return render(request, 'gestcaptur/editar_usuario.html', {
        'form': form,
        'usuario': usuario
    })


def desativar_usuario(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)
    if request.method == 'POST':
        if str(usuario.id) == str(request.user.id):
            messages.error(request, "Você não pode desativar seu próprio usuário.")
            return redirect('listar_usuarios')
        usuario.is_active = False
        usuario.save()
        messages.success(request, f"Usuário {usuario.username} desativado com sucesso.")
        return redirect('listar_usuarios')
    return render(request, 'gestcaptur/confirmar_desativar_usuario.html', {'usuario': usuario})


def ativar_usuario(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)
    if request.method == 'POST':
        usuario.is_active = True
        usuario.save()
        messages.success(request, f"Usuário {usuario.username} ativado com sucesso.")
        return redirect('listar_usuarios')
    return render(request, 'gestcaptur/confirmar_ativar_usuario.html', {'usuario': usuario})


def listar_roles(request):
    roles = Group.objects.prefetch_related('permissions').order_by('name')
    return render(request, 'gestcaptur/listar_roles.html', {'roles': roles})


def criar_role(request):
    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Role criado com sucesso.')
            return redirect('listar_roles')
    else:
        form = RoleForm()
    return render(request, 'gestcaptur/role_form.html', {'form': form, 'titulo': 'Criar Role'})


def editar_role(request, role_id):
    role = get_object_or_404(Group, id=role_id)
    if request.method == 'POST':
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            form.save()
            messages.success(request, 'Role atualizado com sucesso.')
            return redirect('listar_roles')
    else:
        form = RoleForm(instance=role)
    return render(request, 'gestcaptur/role_form.html', {'form': form, 'role': role, 'titulo': 'Editar Role'})
