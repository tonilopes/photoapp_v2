# gestcaptur/admin.py

from django.contrib import admin
from .models import Usuario, Evento, Aluno, SessaoFotografica
from django.contrib.auth.admin import UserAdmin
from django.forms import CheckboxSelectMultiple

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    model = Usuario
    list_display = ['username', 'email', 'role', 'is_active', 'is_staff', 'get_groups']
    
    # ✅ CORRIGIDO: Sobrescrever fieldsets completamente para evitar duplicação
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informações Pessoais', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissões', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Função Principal', {'fields': ('role',)}),  # Campo personalizado
        ('Datas Importantes', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
        ('Informações Pessoais', {'fields': ('first_name', 'last_name', 'email')}),
        ('Função Principal', {'fields': ('role',)}),
        ('Grupos', {'fields': ('groups',)}),
    )
    
    filter_horizontal = ('groups', 'user_permissions')  # Interface amigável para grupos
    
    def get_groups(self, obj):
        return ", ".join([g.name for g in obj.groups.all()])
    get_groups.short_description = "Grupos"

@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ['id', 'data', 'tipo_evento', 'empresa', 'fot', 'coordenador', 'coordenador_tambem_fotografo', 'status']
    list_filter = ['data', 'empresa', 'status', 'coordenador', 'fotografos']
    search_fields = ['tipo_evento', 'empresa', 'fot', 'instituicao', 'local']
    filter_horizontal = ['fotografos']

@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'evento', 'ident', 'cadastro_completo', 'photographer', 'status_comparecimento']  # ✅ ADICIONADO status_comparecimento
    list_filter = ['ident', 'evento', 'cadastro_completo', 'status_comparecimento']  # ✅ ADICIONADO filtro
    search_fields = ['nome', 'cpf', 'evento__tipo_evento', 'evento__instituicao']

@admin.register(SessaoFotografica)
class SessaoFotograficaAdmin(admin.ModelAdmin):
    list_display = ['fotografo', 'evento', 'qtd_fotos', 'inicio_sessao', 'fim_sessao', 'finalizado_fotografo', 'finalizado_evento']
    list_filter = ['evento', 'fotografo', 'finalizado_fotografo', 'finalizado_evento']
    search_fields = ['fotografo__username', 'evento__tipo_evento', 'evento__instituicao']