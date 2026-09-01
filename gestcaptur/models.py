# gestcaptur/models.py (ou o nome do seu arquivo models.py)

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group
from django.utils import timezone
from django.db.models import Sum
from django.db.models.functions import Coalesce
import uuid
import unicodedata
import re

class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, username, password=None, **extra_fields):
        if not extra_fields.get('role'):
            raise ValueError('O campo "role" é obrigatório.')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'gestor')

        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')
        if not extra_fields.get('role'):
            raise ValueError('O campo "role" é obrigatório para superusuário.')

        return self.create_user(username, password, **extra_fields)

class Usuario(AbstractUser):
    ROLE_CHOICES = (
        ('gestor', 'Gestor'),
        ('fotografo', 'Fotógrafo'),
        ('coordenador', 'Coordenador'),
        ('pesquisa', 'Pesquisa'),
        ('parceiro', 'Parceiro'),
        ('personalizado', 'Personalizado (acesso via permissões do grupo)'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='fotografo')

    objects = UsuarioManager()

    class Meta:
        permissions = (
            ('ver_guia_grade', 'Pode ver a guia Grade do dashboard'),
            ('ver_guia_andamento', 'Pode ver a guia Em Andamento do dashboard'),
            ('ver_guia_finalizados', 'Pode ver a guia Finalizados do dashboard'),
            ('ver_guia_fichas_fotos', 'Pode ver a guia Fichas e Fotos do dashboard'),
            ('ver_guia_resumo', 'Pode ver a guia Resumo do dashboard'),
            ('gerenciar_roles', 'Pode gerenciar roles e permissões (menu Usuários)'),
            ('ver_botao_compartilhar_formandos', 'Pode ver o botão Compartilhar Link/QRCode (painel de formandos)'),
            ('ver_botao_parceiros_formandos', 'Pode ver o botão Parceiros (painel de formandos)'),
        )

    def __str__(self):
        return self.username

  # Métodos auxiliares para verificar grupos OU role
    def is_gestor(self):
        return self.groups.filter(name='Gestor').exists() or self.role == 'gestor'

    def is_coordenador(self):
        return self.groups.filter(name='Coordenador').exists() or self.role == 'coordenador'
    
    def is_fotografo(self):
        return self.groups.filter(name='Fotógrafo').exists() or self.role == 'fotografo'

    def is_pesquisa(self):
        return self.groups.filter(name='Pesquisa').exists() or self.role == 'pesquisa'  # ✅ ADICIONADO

    def is_parceiro(self):
        return self.groups.filter(name='Parceiro').exists() or self.role == 'parceiro'  # ✅ ADICIONADO

    def is_personalizado(self):
        return self.role == 'personalizado'

    # Guias do dashboard que este usuário pode ver (Gestor sempre vê todas)
    def guias_dashboard_permitidas(self):
        if self.is_gestor():
            return ['grade', 'andamento', 'finalizados', 'fichas', 'resumo']
        mapa = {
            'grade': 'ver_guia_grade',
            'andamento': 'ver_guia_andamento',
            'finalizados': 'ver_guia_finalizados',
            'fichas': 'ver_guia_fichas_fotos',
            'resumo': 'ver_guia_resumo',
        }
        return [guia for guia, codename in mapa.items() if self.has_perm(f'gestcaptur.{codename}')]

    def get_full_name(self):
        return self.first_name if self.first_name else self.username

    def get_short_name(self):
        return self.first_name if self.first_name else self.username

class Evento(models.Model):
    fot = models.CharField(verbose_name="FOT", max_length=100)
    data = models.DateField(verbose_name="Data do Evento")
    instituicao = models.CharField(verbose_name="Instituição" ,max_length=200, blank=True)
    curso = models.CharField(verbose_name="Curso",max_length=200, blank=True)
    empresa = models.CharField(verbose_name="Empresa",max_length=200, blank=True)
    tipo_evento = models.CharField(verbose_name="Tipo Evento",max_length=100, blank=True)
    observacoes = models.TextField(verbose_name="Observações",blank=True)
    local = models.CharField(verbose_name="Local",max_length=200, blank=True)
    endereco = models.CharField(verbose_name="Endereço completo",max_length=300, blank=True)
    horario = models.CharField(verbose_name="Horário",max_length=100, blank=True)
    fotografos = models.ManyToManyField(Usuario, related_name='eventos_atribuidos', verbose_name="Fotógrafos", blank=True)
    
    # NOVO: Parceiros com acesso de leitura ao evento
    parceiros = models.ManyToManyField(
        Usuario,
        related_name='eventos_como_parceiro',
        verbose_name="Parceiros com Acesso",
        blank=True,
        limit_choices_to={'role': 'parceiro'},
        help_text="Selecione os parceiros que terão acesso de leitura a este evento"
    )
    
    # NOVO: UUID para URLs seguras (sem expor ID)
    uuid = models.CharField(
        max_length=36,
        unique=True,
        blank=True,
        null=True,
        verbose_name="UUID do Evento",
        help_text="Identificador único para compartilhamento seguro"
    )
    
    created_at = models.DateTimeField(verbose_name="Criado em",auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="Atualizado em",auto_now=True)

    # NOVOS CAMPOS PARA STATUS DO EVENTO
    STATUS_CHOICES = (
        ('pendente', 'Pendente de Início'),
        ('iniciado', 'Em Andamento'),
        ('finalizado', 'Finalizado'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    hora_inicio = models.DateTimeField(null=True, blank=True)
    hora_fim = models.DateTimeField(null=True, blank=True)

    # NOVOS CAMPOS PARA ATRIBUIÇÃO DE COORDENADOR
    coordenador = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='eventos_coordenados', # Eventos que este usuário coordena
        limit_choices_to={'role': 'coordenador'} # Limita as escolhas a usuários com role 'coordenador'
    )
    coordenador_tambem_fotografo = models.BooleanField(
        default=False,
        help_text="Marque se o coordenador deste evento também atuará como fotógrafo."
    )

    # Campo para indicar se o evento permite captura de selfie pública
    para_selfie = models.BooleanField(
        default=False,
        verbose_name="Evento para selfie?",
        help_text="Marque para permitir que alunos capturem selfie pública antes do cadastro."
    )
    
    # NOVO: Código da turma (será aplicado a todos os alunos deste evento)
    codigo_turma = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Código da Turma",
        help_text="Código único da turma (ex: 2024-A, EM-001). Aplicado automaticamente a todos os alunos."
    )
    
    # NOVO: Indica se o evento permite importação de nomes
    permite_importacao_nomes = models.BooleanField(
        default=False,
        verbose_name="Importar nomes?",
        help_text="Marque para permitir importação de lista de nomes via XLSX"
    )

    def __str__(self):
        return f"{self.data} - {self.tipo_evento} - {self.empresa}"
    
    def save(self, *args, **kwargs):
        # Gerar UUID se não existir
        if not self.uuid:
            import uuid
            self.uuid = str(uuid.uuid4())
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-data', '-created_at']
        permissions = (
            ('download_fotos_evento', 'Pode baixar fotos de eventos'),
            ('download_cadastros_evento', 'Pode baixar cadastros de eventos'),
            ('finalizar_captura_evento', 'Pode encerrar captura de eventos'),
        )

    @property
    def total_fotos(self):
        total_por_sessao = self.sessoes_fotograficas.aggregate(total=Sum('qtd_fotos'))['total']
        if total_por_sessao:
            return total_por_sessao
        return self.alunos.exclude(foto='').exclude(foto__isnull=True).count()

class Aluno(models.Model):
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name='alunos')
    nome = models.CharField(max_length=200) # sempre obrigatório
    cpf = models.CharField(
        max_length=14, 
        blank=False, 
        null=False,
        verbose_name="CPF",
        help_text="CPF do formando (obrigatório e único)"
    )
    cep = models.CharField(max_length=9, blank=True, null=True)
    endereco = models.CharField(max_length=300, blank=True, null=True)
    numero = models.CharField(max_length=10, blank=True, null=True)
    bairro = models.CharField(max_length=100, blank=True, null=True)
    complemento = models.CharField(max_length=100, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=2, blank=True, null=True)
    data_nascimento = models.DateField(blank=True, null=True)
    telefone_fixo = models.CharField(max_length=20, blank=True, null=True)
    whatsapp = models.CharField(max_length=20) # sempre obrigatório
    email = models.EmailField(blank=True, null=True)
    instagram = models.CharField(max_length=100, blank=True, null=True)
    nome_pai = models.CharField(max_length=200, blank=True, null=True)
    whatsapp_pai = models.CharField(max_length=20, blank=True, null=True)
    nome_mae = models.CharField(max_length=200, blank=True, null=True)
    whatsapp_mae = models.CharField(max_length=20, blank=True, null=True)
    nome_parente = models.CharField(max_length=200, blank=True, null=True)
    grau_parentesco = models.CharField(max_length=100, blank=True, null=True)
    whatsapp_parente = models.CharField(max_length=20, blank=True, null=True)
    token = models.CharField(max_length=100, unique=True, blank=True, null=True)
    ident = models.BooleanField(default=False)
    foto = models.ImageField(upload_to='event_photos/', blank=True, null=True)
    photographer = models.ForeignKey(
        'Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='photos_taken_by_aluno'
    )
    card_number = models.CharField(max_length=50, null=True, blank=True)
    cadastro_completo = models.BooleanField(default=False, verbose_name="Cadastro Completo")
    
    # NOVOS CAMPOS PARA CONTROLE DE FORMANDOS
    codigo_turma = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="Código da Turma",
        help_text="Código identificador da turma (ex: 2024-A, EM-001)"
    )
    selfie_realizada = models.BooleanField(
        default=False,
        verbose_name="Selfie Realizada",
        help_text="Indica se o formando capturou a selfie obrigatória"
    )
    data_ultimo_email = models.DateTimeField(null=True, blank=True, verbose_name="Último Email Enviado")
    tentativas_email = models.IntegerField(default=0, verbose_name="Tentativas de Email")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # --- CAMPO: Status de Comparecimento ---
    STATUS_COMPARECIMENTO_CHOICES = (
        ('presente', 'Presente'),
        ('faltoso', 'Faltoso'),
    )
    status_comparecimento = models.CharField(
        max_length=10,
        choices=STATUS_COMPARECIMENTO_CHOICES,
        default='presente',
        verbose_name="Status Comparecimento"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['evento', 'cpf'],
                name='unique_cpf_per_evento',
                violation_error_message='Já existe um cadastro com este CPF neste evento.'
            )
        ]

    def __str__(self):
        return f"{self.nome} - {'Completo' if self.cadastro_completo else 'Parcial'}"
    
    def get_nome_arquivo_foto(self):
        """
        Retorna o caminho formatado da foto em estrutura de pastas:
        {código_turma}/{NOME_COMPLETO}.JPG
        
        Exemplo: 25248_SupDiversosCTT8_ESPM - ESPM - 25248/ADRIANO MURAD DE ALCANTARA.JPG
        """
        if not self.evento or not self.nome:
            return None
        
        # Usar código_turma como pasta, ou usar código do evento se não tiver
        pasta = self.codigo_turma if self.codigo_turma else f"{self.evento.id}"
        
        # Nome do arquivo: nome em MAIÚSCULAS com espaços + extensão .JPG
        # Exemplo: "ADRIANO MURAD DE ALCANTARA.JPG"
        nome_arquivo = f"{self.nome.strip().upper()}.JPG"
        
        # Retornar caminho: pasta/NOME COMPLETO.JPG
        return f"{pasta}/{nome_arquivo}"
    
    def save(self, *args, **kwargs):
        # Transformar nome para MAIÚSCULAS (caixa alta) para padronização
        if self.nome:
            self.nome = self.nome.strip().upper()
        
        # Gerar token se não existir
        if not self.token:
            self.token = uuid.uuid4().hex
        
        # Atualizar ident baseado na foto
        if self.foto:
            self.ident = True
            # Renomear apenas para novos uploads (nao commitados no storage)
            # Evita que o prefixo 'event_photos/' seja removido incorretamente do path no DB
            if self.codigo_turma and not getattr(self.foto, '_committed', True):
                novo_nome = self.get_nome_arquivo_foto()
                if novo_nome and self.foto.name != novo_nome:
                    self.foto.name = novo_nome
        else:
            self.ident = False
        
        super().save(*args, **kwargs)


    @property
    def ficha_preenchida(self):
        """
        Verifica se a ficha foi preenchida parcialmente
        - Campos mínimos obrigatórios: nome + whatsapp
        - Se tem esses campos MAS não está completo = ficha_preenchida
        """
        # Verificar se tem os campos mínimos
        tem_minimos = bool(self.nome and str(self.nome).strip() and 
                        self.whatsapp and str(self.whatsapp).strip())
        
        # Se não tem nem os mínimos, retorna False
        if not tem_minimos:
            return False
        
        # Se já está completo, não é "parcialmente preenchida"
        if self.cadastro_completo:
            return False
        
        # Tem os mínimos mas não está completo = parcialmente preenchida
        return True


    def pode_enviar_email(self):
        """Verifica se pode enviar email (máximo 3 por dia)"""
        if not self.data_ultimo_email:
            return True
        
        hoje = timezone.now().date()
        ultimo_email = self.data_ultimo_email.date()
        
        if ultimo_email < hoje:
            self.tentativas_email = 0
            self.save()
            return True
        
        return self.tentativas_email < 3
    
    def registrar_envio_email(self):
        """Registra o envio de email"""
        self.data_ultimo_email = timezone.now()
        self.tentativas_email += 1
        self.save()

class SessaoFotografica(models.Model):
    fotografo = models.ForeignKey('Usuario', on_delete=models.CASCADE, related_name='sessoes')
    evento = models.ForeignKey('Evento', on_delete=models.CASCADE, related_name='sessoes_fotograficas')
    qtd_fotos = models.IntegerField(default=0)
    numero_cartao = models.CharField(max_length=50, null=True, blank=True)
    inicio_sessao = models.DateTimeField(auto_now_add=True)
    fim_sessao = models.DateTimeField(null=True, blank=True)
    finalizado_fotografo = models.BooleanField(default=False)
    finalizado_evento = models.BooleanField(default=False)
    last_activity = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.fotografo.username} - {self.evento.tipo_evento} ({self.qtd_fotos} fotos)"
