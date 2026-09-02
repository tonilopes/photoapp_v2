# eventos/forms.py

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from .models import Aluno, Usuario, Evento
import datetime
import re
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
  

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Usuário",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Usuário'})
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Senha'})
    )


class RoleForm(forms.ModelForm):
    permissoes_evento = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Permissões de Eventos',
        help_text='Defina quais operações este role pode executar em eventos.'
    )
    permissoes_dashboard = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Guias do Dashboard (Ver Eventos)',
        help_text='Selecione quais guias do dashboard este role poderá ver. Sem nenhuma guia marcada, o grupo não acessa o dashboard.'
    )
    permissoes_usuarios = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Permissões de Usuários (menu Usuários)',
        help_text='Controla os itens do menu "Usuários" no topo. Sem nenhuma marcada, o menu não aparece.'
    )
    permissoes_botoes_formandos = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Botões do Painel de Formandos',
        help_text='Controla quais botões superiores aparecem no painel de controle de formandos.'
    )

    class Meta:
        model = Group
        fields = ['name']
        labels = {'name': 'Nome do Role'}
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control', 'autofocus': True})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        content_type_evento = ContentType.objects.get_for_model(Evento)
        self.fields['permissoes_evento'].queryset = Permission.objects.filter(
            content_type=content_type_evento,
            codename__in=[
                'add_evento', 'change_evento', 'delete_evento', 'view_evento',
                'download_fotos_evento', 'download_cadastros_evento',
                'finalizar_captura_evento',
            ]
        ).order_by('name')

        content_type_usuario = ContentType.objects.get_for_model(Usuario)
        self.fields['permissoes_dashboard'].queryset = Permission.objects.filter(
            content_type=content_type_usuario,
            codename__in=[
                'ver_guia_grade', 'ver_guia_andamento', 'ver_guia_finalizados',
                'ver_guia_fichas_fotos', 'ver_guia_resumo',
            ]
        ).order_by('name')
        self.fields['permissoes_usuarios'].queryset = Permission.objects.filter(
            content_type=content_type_usuario,
            codename__in=[
                'add_usuario', 'change_usuario', 'delete_usuario', 'view_usuario',
                'gerenciar_roles',
            ]
        ).order_by('name')
        self.fields['permissoes_botoes_formandos'].queryset = Permission.objects.filter(
            content_type=content_type_usuario,
            codename__in=[
                'ver_botao_compartilhar_formandos', 'ver_botao_parceiros_formandos',
            ]
        ).order_by('name')

        if self.instance and self.instance.pk:
            self.fields['permissoes_evento'].initial = self.instance.permissions.filter(
                content_type=content_type_evento
            )
            self.fields['permissoes_dashboard'].initial = self.instance.permissions.filter(
                content_type=content_type_usuario, codename__in=[
                    'ver_guia_grade', 'ver_guia_andamento', 'ver_guia_finalizados',
                    'ver_guia_fichas_fotos', 'ver_guia_resumo',
                ]
            )
            self.fields['permissoes_usuarios'].initial = self.instance.permissions.filter(
                content_type=content_type_usuario, codename__in=[
                    'add_usuario', 'change_usuario', 'delete_usuario', 'view_usuario',
                    'gerenciar_roles',
                ]
            )
            self.fields['permissoes_botoes_formandos'].initial = self.instance.permissions.filter(
                content_type=content_type_usuario, codename__in=[
                    'ver_botao_compartilhar_formandos', 'ver_botao_parceiros_formandos',
                ]
            )

    def save(self, commit=True):
        role = super().save(commit=commit)
        if commit:
            permissoes = (
                list(self.cleaned_data['permissoes_evento']) +
                list(self.cleaned_data['permissoes_dashboard']) +
                list(self.cleaned_data['permissoes_usuarios']) +
                list(self.cleaned_data['permissoes_botoes_formandos'])
            )
            role.permissions.set(permissoes)
        return role

class CriarUsuarioForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}), 
        label='Senha'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}), 
        label='Confirmar Senha'
    )

    # ✅ Campo para grupos
    grupos = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Grupos de Acesso',
        help_text='Selecione os grupos que o usuário deve pertencer. Um usuário pode ter múltiplos grupos.'
    )

    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'grupos', 'password', 'confirm_password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'username': 'Nome de usuário',
            'first_name': 'Nome',
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm_password")
        
        if password and confirm and password != confirm:
            self.add_error('confirm_password', "As senhas não coincidem.")
        
        # Validação adicional de senha
        if password and len(password) < 6:
            self.add_error('password', "A senha deve ter pelo menos 6 caracteres.")
            
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        # ✅ Role derivada dos Grupos de Acesso (o campo Role não existe mais no form)
        user.role = self._role_from_groups(self.cleaned_data.get('grupos', []))
        # ✅ CRÍTICO: Usar set_password para hash correto
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            # ✅ Salvar grupos selecionados (fonte de verdade do acesso)
            grupos_selecionados = self.cleaned_data.get('grupos')
            user.groups.set(grupos_selecionados)
        return user

    def _role_from_groups(self, grupos):
        """Define a role com base nos grupos selecionados.
        Um único grupo mapeável -> role correspondente (gestor, coordenador...).
        Múltiplos grupos ou grupo personalizado -> 'personalizado' (acesso via permissões do grupo).
        """
        group_roles = {
            'Gestor': 'gestor',
            'Coordenador': 'coordenador',
            'Fotógrafo': 'fotografo',
            'Pesquisa': 'pesquisa',
            'Parceiro': 'parceiro',
        }
        nomes = [g.name for g in grupos]
        if len(nomes) == 1 and nomes[0] in group_roles:
            return group_roles[nomes[0]]
        return 'personalizado'


class EditarUsuarioForm(forms.ModelForm):
    password = forms.CharField(
        label='Nova Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )
    confirm_password = forms.CharField(
        label='Confirmar Nova Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )

    # ✅ Campo para grupos na edição
    grupos = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Grupos de Acesso'
    )

    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active', 'grupos']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ✅ Pré-selecionar grupos atuais do usuário
        if self.instance and self.instance.pk:
            self.fields['grupos'].initial = self.instance.groups.all()

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm_password")

        if password or confirm:
            if password != confirm:
                self.add_error('confirm_password', "As senhas não coincidem.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Só altera a senha se foi fornecida
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        
        # ✅ A role NÃO é alterada na edição — o acesso é controlado pelos Grupos de Acesso
        # (a role foi derivada dos grupos na criação; aqui só atualizamos os grupos)
        
        if commit:
            user.save()
            # ✅ Atualizar grupos (fonte de verdade do acesso)
            grupos_selecionados = self.cleaned_data.get('grupos', [])
            user.groups.set(grupos_selecionados)
        
        return user


class UploadFotoForm(forms.ModelForm):
    class Meta:
        model = Aluno
        fields = ['foto']
        widgets = {
            'foto': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class ImportXLSXForm(forms.Form):
    arquivo = forms.FileField(
        label="Selecionar arquivo .xlsx",
        widget=forms.ClearableFileInput(attrs={'accept': '.xlsx', 'class': 'form-control'})
    )

class EventoForm(forms.ModelForm):
    # Campo para selecionar UM coordenador
    coordenador = forms.ModelChoiceField(
        queryset=Usuario.objects.filter(role='coordenador'),  # ✅ Correto: Usuario
        required=False,
        empty_label="-- Selecionar Coordenador --",
        label="Coordenador Responsável",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Campo para múltiplos fotógrafos
    fotografos = forms.ModelMultipleChoiceField(
        queryset=Usuario.objects.filter(role='fotografo'),  # ✅ Correto: Usuario
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label='Fotógrafos Atribuídos'
    )

    class Meta:
        model = Evento
        fields = [
            'fot', 'data', 'instituicao', 'curso', 'empresa', 'tipo_evento',
            'observacoes', 'local', 'endereco', 'horario', 'fotografos',
            'coordenador', 'coordenador_tambem_fotografo', 'para_selfie',
            'codigo_turma', 'permite_importacao_nomes'
        ]
        widgets = {
            'data': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control'
            }),
            'horario': forms.TimeInput(attrs={
                'type': 'time', 
                'class': 'form-control'
            }),
            'fot': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: FOT001'
            }),
            'instituicao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da Instituição'
            }),
            'curso': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do Curso'
            }),
            'empresa': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da Empresa (opcional)'
            }),
            'tipo_evento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Formatura, Colação de Grau'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4,
                'placeholder': 'Observações adicionais sobre o evento...'
            }),
            'local': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Local do evento'
            }),
            'endereco': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Endereço completo'
            }),
            'codigo_turma': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 2024-A, EM-001'
                , 'maxlength': 100
            }),
            'coordenador_tambem_fotografo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'para_selfie': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'permite_importacao_nomes': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'fot': 'Código FOT',
            'data': 'Data do Evento',
            'instituicao': 'Instituição',
            'curso': 'Curso',
            'empresa': 'Empresa',
            'tipo_evento': 'Tipo de Evento',
            'observacoes': 'Observações',
            'local': 'Local',
            'endereco': 'Endereço',
            'horario': 'Horário',
            'fotografos': 'Fotógrafos Atribuídos',
            'coordenador': 'Coordenador Responsável',
            'coordenador_tambem_fotografo': 'Coordenador também fotografa neste evento',
            'para_selfie': 'Evento para selfie?'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Adicionar classes required para campos obrigatórios
        required_fields = ['fot', 'data', 'instituicao', 'tipo_evento', 'local']
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True
                if 'class' in self.fields[field_name].widget.attrs:
                    self.fields[field_name].widget.attrs['class'] += ' required'
                else:
                    self.fields[field_name].widget.attrs['class'] = 'form-control required'

    
    def clean_fotografos(self):
        """Tratar string vazia como lista vazia para ModelMultipleChoiceField"""
        fotografos = self.cleaned_data.get('fotografos')
        
        # ✅ CORREÇÃO: Se vier string vazia ou None, retornar lista vazia
        if not fotografos or fotografos == '':
            print("🔍 DEBUG: Fotografos veio vazio, retornando lista vazia")
            return []
        
        print(f"🔍 DEBUG: Fotografos válidos: {fotografos}")
        return fotografos        

    def clean_codigo_turma(self):
        codigo_turma = (self.cleaned_data.get('codigo_turma') or '').strip()
        if any(caractere in codigo_turma for caractere in ('/', '\\')):
            raise forms.ValidationError('O Código da Turma não pode conter barras ou subpastas.')
        return codigo_turma or None


    def clean(self):
        cleaned_data = super().clean()
        
        try:
            coordenador = cleaned_data.get('coordenador')
            fotografos = cleaned_data.get('fotografos')
            coordenador_tambem_fotografo = cleaned_data.get('coordenador_tambem_fotografo', False)
            
            # Debug: Log dos valores para verificar
            print(f"DEBUG - coordenador: {coordenador}")
            print(f"DEBUG - fotografos: {fotografos}")
            print(f"DEBUG - coordenador_tambem_fotografo: {coordenador_tambem_fotografo}")
            print(f"🔍 DEBUG FORM - cleaned_data: {cleaned_data}")            

            # Se coordenador também é fotógrafo
            if coordenador_tambem_fotografo and coordenador:
                # Converter fotografos para lista segura
                if fotografos is None:
                    fotografos_list = []
                elif hasattr(fotografos, '__iter__'):
                    fotografos_list = list(fotografos)
                else:
                    fotografos_list = [fotografos]
                
                # Adicionar coordenador se não estiver presente
                if coordenador not in fotografos_list:
                    fotografos_list.append(coordenador)
                    cleaned_data['fotografos'] = fotografos_list
                    print(f"DEBUG - Adicionado coordenador à lista de fotógrafos: {fotografos_list}")
            
            # Validação: coordenador obrigatório se marcado como fotógrafo
            if coordenador_tambem_fotografo and not coordenador:
                raise forms.ValidationError(
                    'Selecione um coordenador se ele também for fotógrafo neste evento.'
                )
                
        except Exception as e:
            print(f"ERRO na validação do form: {e}")
            # Em caso de erro, não bloquear o salvamento
            pass
        
        return cleaned_data

class AlunoCadastroForm(forms.ModelForm):
    class Meta:
        model = Aluno
        fields = [
            'nome', 'cpf', 'cep', 'endereco', 'numero', 'complemento', 'bairro',
            'cidade', 'estado', 'data_nascimento', 'telefone_fixo', 'whatsapp', 'email', 'instagram',
            'nome_pai', 'whatsapp_pai', 'nome_mae', 'whatsapp_mae',
            'nome_parente', 'grau_parentesco', 'whatsapp_parente'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome completo'
            }),
            'cpf': forms.TextInput(attrs={
                'class': 'form-control cpf-mask',
                'placeholder': '000.000.000-00',
                'maxlength': '14'
            }),
            'cep': forms.TextInput(attrs={
                'class': 'form-control cep-mask',
                'placeholder': '00000-000',
                'maxlength': '9'
            }),
            'endereco': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Rua, Avenida, etc.'
            }),
            'numero': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número'
            }),
            'complemento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apartamento, Bloco, etc. (opcional)'
            }),
            'bairro': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Bairro'
            }),
            'cidade': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cidade'
            }),
            'estado': forms.Select(attrs={
                'class': 'form-control'
            }, choices=[
                ('', 'Selecione o Estado'),
                ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'),
                ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'),
                ('ES', 'Espírito Santo'), ('GO', 'Goiás'), ('MA', 'Maranhão'),
                ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'), ('MG', 'Minas Gerais'),
                ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'), ('PE', 'Pernambuco'),
                ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
                ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'),
                ('SC', 'Santa Catarina'), ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantins')
            ]),
            'data_nascimento': forms.TextInput(attrs={
                'class': 'form-control data-nascimento-mask',
                'placeholder': 'DD/MM/AAAA',
                'maxlength': '10',
                'inputmode': 'numeric',
                'autocomplete': 'bday',
                'max': (datetime.date.today().replace(year=datetime.date.today().year - 8)).strftime('%d/%m/%Y')
            }),
            'telefone_fixo': forms.TextInput(attrs={
                'class': 'form-control telefone-fixo-mask',
                'placeholder': '(00) 0000-0000 (opcional)',
                'maxlength': '14' # máximo com máscara de 14 caracteres
            }),
            'whatsapp': forms.TextInput(attrs={
                'class': 'form-control whatsapp-mask',
                'placeholder': '(00) 00000-0000',
                'maxlength': '15' # máximo com máscara de 15 caracteres
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@exemplo.com'
            }),
            'instagram': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '@usuario (opcional)'
            }),
            'nome_pai': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do pai (opcional)'
            }),
            'whatsapp_pai': forms.TextInput(attrs={
                'class': 'form-control whatsapp-mask',
                'placeholder': '(00) 00000-0000 (opcional)'
            }),
            'nome_mae': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da mãe'
            }),
            'whatsapp_mae': forms.TextInput(attrs={
                'class': 'form-control whatsapp-mask',
                'placeholder': '(00) 00000-0000'
            }),
            'nome_parente': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do parente (opcional)'
            }),
            'grau_parentesco': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Tio, Avô, etc. (opcional)'
            }),
            'whatsapp_parente': forms.TextInput(attrs={
                'class': 'form-control whatsapp-mask',
                'placeholder': '(00) 00000-0000 (opcional)'
            }),
        }

    def __init__(self, *args, evento=None, **kwargs):
        self.evento = evento  # Armazenar evento para validações
        self.aluno_cpf_duplicado_id = None  # Armazenar ID do aluno com CPF duplicado
        super().__init__(*args, **kwargs)
        
        # 🔧 DEFINIR CAMPOS OBRIGATÓRIOS
        # Dados Pessoais
        self.fields['nome'].required = True
        self.fields['cpf'].required = True  # 🔒 CPF AGORA OBRIGATÓRIO
        self.fields['data_nascimento'].required = True
        
        # Contatos
        self.fields['email'].required = True
        self.fields['whatsapp'].required = True
        self.fields['telefone_fixo'].required = True
        
        # Endereço
        self.fields['cep'].required = True
        self.fields['endereco'].required = True
        self.fields['numero'].required = True
        self.fields['bairro'].required = True
        self.fields['cidade'].required = True
        self.fields['estado'].required = True
        
        # Familiares - Mãe é obrigatória
        self.fields['nome_mae'].required = True
        self.fields['whatsapp_mae'].required = True
        
        # Opcionais
        self.fields['complemento'].required = False
        self.fields['instagram'].required = False
        self.fields['telefone_fixo'].required = False
        self.fields['nome_pai'].required = False
        self.fields['whatsapp_pai'].required = False
        self.fields['nome_parente'].required = False
        self.fields['grau_parentesco'].required = False
        self.fields['whatsapp_parente'].required = False

        # 🔧 LABELS PERSONALIZADOS
        self.fields['nome'].label = 'Nome Completo *'
        self.fields['cpf'].label = 'CPF *'
        self.fields['cep'].label = 'CEP *'
        self.fields['endereco'].label = 'Endereço *'
        self.fields['numero'].label = 'Número *'
        self.fields['complemento'].label = 'Complemento'
        self.fields['bairro'].label = 'Bairro *'
        self.fields['cidade'].label = 'Cidade *'
        self.fields['estado'].label = 'Estado *'
        self.fields['data_nascimento'].label = 'Data de Nascimento *'
        self.fields['telefone_fixo'].label = 'Telefone Fixo'
        self.fields['whatsapp'].label = 'WhatsApp *'
        self.fields['email'].label = 'E-mail *'
        self.fields['instagram'].label = 'Instagram'
        self.fields['nome_pai'].label = 'Nome do Pai'
        self.fields['whatsapp_pai'].label = 'WhatsApp do Pai'
        self.fields['nome_mae'].label = 'Nome da Mãe *'
        self.fields['whatsapp_mae'].label = 'WhatsApp da Mãe *'
        self.fields['nome_parente'].label = 'Nome do Parente'
        self.fields['grau_parentesco'].label = 'Grau de Parentesco'
        self.fields['whatsapp_parente'].label = 'WhatsApp do Parente'

    def clean_data_nascimento(self):
        data = self.cleaned_data.get('data_nascimento')
        if data:
            # Se for string (formato DD/MM/AAAA), converter
            if isinstance(data, str):
                try:
                    # Formato DD/MM/AAAA
                    if '/' in data and len(data) == 10:
                        dia, mes, ano = data.split('/')
                        data_obj = datetime.date(int(ano), int(mes), int(dia))
                        data = data_obj
                    else:
                        raise ValidationError("Use o formato DD/MM/AAAA")
                except (ValueError, IndexError):
                    raise ValidationError("Data inválida. Use o formato DD/MM/AAAA.")

            data_limite = datetime.date.today().replace(
                year=datetime.date.today().year - 8
            )
            if data > data_limite:
                raise ValidationError(
                    "A pessoa precisa ter pelo menos 8 anos completos."
                )
        return data

    # 🔧 VALIDAÇÃO DE CPF
    def _validar_cpf(self, cpf):
        """Valida CPF brasileiro"""
        # Remove caracteres não numéricos
        cpf = re.sub(r'\D', '', cpf)
        
        # Verifica se tem 11 dígitos
        if len(cpf) != 11:
            return False
        
        # Verifica se todos os dígitos são iguais
        if cpf == cpf[0] * 11:
            return False
        
        # Calcula primeiro dígito verificador
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto
        
        # Calcula segundo dígito verificador
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto
        
        # Verifica se os dígitos calculados conferem
        return cpf[-2:] == f"{digito1}{digito2}"
    
       # 🔧 VALIDAÇÃO SIMPLIFICADA PARA TESTE

    # 🔧 VALIDAÇÃO SIMPLIFICADA PARA CORRIGIR O PROBLEMA
    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')
        if cpf:
            # Remove formatação
            cpf_limpo = re.sub(r'\D', '', cpf)
            if cpf_limpo:
                # APLICAR VALIDAÇÃO AQUI
                if not self._validar_cpf(cpf_limpo):
                    raise ValidationError("CPF inválido.")
            return cpf_limpo
        return cpf

    def clean_telefone_fixo(self):
        telefone = self.cleaned_data.get('telefone_fixo')
        if telefone:
            # Remove formatação e limita a 10 dígitos
            telefone_limpo = re.sub(r'\D', '', telefone)
            if len(telefone_limpo) > 10:
                telefone_limpo = telefone_limpo[:10]
            return telefone_limpo
        return telefone

    def clean_whatsapp(self):
        whatsapp = self.cleaned_data.get('whatsapp')
        if whatsapp:
            # Remove formatação e limita a 11 dígitos
            whatsapp_limpo = re.sub(r'\D', '', whatsapp)
            if len(whatsapp_limpo) > 11:
                whatsapp_limpo = whatsapp_limpo[:11]
            return whatsapp_limpo
        return whatsapp

    def clean_whatsapp_mae(self):
        whatsapp = self.cleaned_data.get('whatsapp_mae')
        if whatsapp:
            whatsapp_limpo = re.sub(r'\D', '', whatsapp)
            if len(whatsapp_limpo) > 11:
                whatsapp_limpo = whatsapp_limpo[:11]
            return whatsapp_limpo
        return whatsapp

    def clean_whatsapp_pai(self):
        whatsapp = self.cleaned_data.get('whatsapp_pai')
        if whatsapp:
            whatsapp_limpo = re.sub(r'\D', '', whatsapp)
            if len(whatsapp_limpo) > 11:
                whatsapp_limpo = whatsapp_limpo[:11]
            return whatsapp_limpo
        return whatsapp

    def clean_whatsapp_parente(self):
        whatsapp = self.cleaned_data.get('whatsapp_parente')
        if whatsapp:
            whatsapp_limpo = re.sub(r'\D', '', whatsapp)
            if len(whatsapp_limpo) > 11:
                whatsapp_limpo = whatsapp_limpo[:11]
            return whatsapp_limpo
        return whatsapp    
 

    # 🔧 VALIDAÇÃO DE CEP
    def clean_cep(self):
        cep = self.cleaned_data.get('cep')
        if cep:
            numbers = re.sub(r'[^0-9]', '', cep)
            if len(numbers) == 8:
                return f"{numbers[:5]}-{numbers[5:]}"
            else:
                raise ValidationError('CEP deve ter 8 dígitos: 00000-000')
        return cep

   # 🔧 VALIDAÇÃO PARA CADASTRO PARCIAL
    def validar_campos_obrigatorios_completos(self):
        """Retorna lista de campos obrigatórios que estão vazios"""
        campos_obrigatorios = [
            'nome',
            'cpf',
            'data_nascimento',
            'cep', 'endereco', 'numero', 'bairro', 'cidade', 'estado',
            'email',
            'whatsapp',
            'nome_mae',
            'whatsapp_mae']
        campos_vazios = []
        
        for campo in campos_obrigatorios:
            valor = self.cleaned_data.get(campo)
            if not valor or (isinstance(valor, str) and not valor.strip()):
                label = self.fields[campo].label or campo.replace('_', ' ').title()
                campos_vazios.append(label)
        
        return campos_vazios
    
    def tem_email_valido(self):
        """Verifica se tem email válido para envio"""
        email = self.cleaned_data.get('email')
        return email and '@' in email and '.' in email

    def clean(self):
        """Validação customizada do formulário"""
        cleaned_data = super().clean()
        
        # ========================================
        # 0️⃣ NORMALIZAR NOME PARA MAIÚSCULAS
        # ========================================
        nome = cleaned_data.get('nome')
        if nome:
            # Transformar nome para MAIÚSCULAS (caixa alta)
            cleaned_data['nome'] = nome.strip().upper()
        
        # ========================================
        # 1️⃣ VALIDAR CPFS DUPLICADOS (dentro do mesmo evento)
        # ========================================
        cpf = cleaned_data.get('cpf')
        if cpf and self.evento:
            # Remove formatação
            cpf_limpo = re.sub(r'\D', '', cpf)
            
            # Verificar se já existe outro aluno com este CPF no mesmo evento
            alunos_com_cpf = Aluno.objects.filter(
                evento=self.evento,
                cpf=cpf_limpo
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if alunos_com_cpf.exists():
                aluno_existente = alunos_com_cpf.first()
                # Armazenar ID do aluno duplicado para a view acessar
                self.aluno_cpf_duplicado_id = aluno_existente.id
                # Erro no campo CPF (aparece diretamente no campo)
                self.add_error('cpf', 'CPF já cadastrado neste evento. Insira outro ou fale com nossa equipe.')
        
        # ========================================
        # 2️⃣ VALIDAR CELULARES NÃO-DUPLICADOS
        # ========================================
        whatsapp = cleaned_data.get('whatsapp')
        whatsapp_mae = cleaned_data.get('whatsapp_mae')
        whatsapp_pai = cleaned_data.get('whatsapp_pai')
        whatsapp_parente = cleaned_data.get('whatsapp_parente')
        
        # Limpar e normalizar celulares
        def limpar_celular(celular):
            if celular:
                return re.sub(r'\D', '', celular)
            return None
        
        whatsapp_limpo = limpar_celular(whatsapp)
        whatsapp_mae_limpo = limpar_celular(whatsapp_mae)
        whatsapp_pai_limpo = limpar_celular(whatsapp_pai)
        whatsapp_parente_limpo = limpar_celular(whatsapp_parente)
        
        # Verificar duplicatas
        celulares = [
            ('whatsapp', whatsapp_limpo),
            ('whatsapp_mae', whatsapp_mae_limpo),
            ('whatsapp_pai', whatsapp_pai_limpo),
            ('whatsapp_parente', whatsapp_parente_limpo)
        ]
        
        # Filtrar apenas os preenchidos
        celulares_preenchidos = [(nome, valor) for nome, valor in celulares if valor]
        
        # Verificar se há duplicatas
        celulares_unicos = set()
        for nome_campo, valor_celular in celulares_preenchidos:
            if valor_celular in celulares_unicos:
                # Encontrou duplicata - exibir erro no campo especifico
                self.add_error(nome_campo, 'Este numero de WhatsApp ja foi informado em outro campo. Use numeros diferentes.')
            celulares_unicos.add(valor_celular)
        
        return cleaned_data
