# 📊 Análise Completa do Projeto PhotoApp V2

## Resumo Executivo
O projeto é uma aplicação Django para **gestão de eventos fotográficos** com:
- Diferentes perfis de usuário (Gestor, Fotografo, Coordenador, Pesquisa)
- Cadastro de alunos via QR Code e link público com selfie
- Captura de fotos e gestão de sessões fotográficas
- Autenticação baseada em roles e grupos Django

---

## 1. 📦 ESTRUTURA DE MODELS

### 1.1 **Modelo: Usuario** (Customizado - AbstractUser)
**Localização:** `gestcaptur/models.py`

**Campos principais:**
```python
- username: CharField (único)
- first_name, last_name: CharField
- email: EmailField
- password: Hashed (via set_password)
- role: CharField
  ├─ 'gestor' (Gestor)
  ├─ 'fotografo' (Fotógrafo)
  ├─ 'coordenador' (Coordenador)
  └─ 'pesquisa' (Pesquisa)
- is_active: BooleanField
- is_staff, is_superuser: BooleanField
- groups: ManyToMany (Django Groups)
```

**Métodos de verificação de role:**
- `is_gestor()` - Verifica role='gestor' OU grupo 'Gestor'
- `is_coordenador()` - Verifica role='coordenador' OU grupo 'Coordenador'
- `is_fotografo()` - Verifica role='fotografo' OU grupo 'Fotógrafo'
- `is_pesquisa()` - Verifica role='pesquisa' OU grupo 'Pesquisa'

**Relacionamentos:**
- `eventos_atribuidos`: ManyToMany com Evento (Fotógrafos de um evento)
- `eventos_coordenados`: ForeignKey com Evento (Eventos que coordena)
- `sessoes`: OneToMany com SessaoFotografica (Sessões do fotógrafo)
- `photos_taken_by_aluno`: OneToMany com Aluno (Fotos que tirou)

---

### 1.2 **Modelo: Evento**
**Localização:** `gestcaptur/models.py`

**Campos principais:**
```python
# Identificação
- fot: CharField (FOT - número do evento)
- tipo_evento: CharField (Ex: "Formatura", "Batizado")
- data: DateField
- instituicao: CharField (opcional)
- curso: CharField (opcional)
- empresa: CharField (opcional)

# Localização
- local: CharField
- endereco: CharField (endereço completo)
- horario: CharField

# Status e Timeline
- status: CharField
  ├─ 'pendente' (Pendente de Início)
  ├─ 'iniciado' (Em Andamento)
  └─ 'finalizado' (Finalizado)
- hora_inicio: DateTimeField (nullable)
- hora_fim: DateTimeField (nullable)

# Associações
- fotografos: ManyToMany com Usuario (fotógrafos atribuídos)
- coordenador: ForeignKey para Usuario (role='coordenador')
  └─ related_name='eventos_coordenados'
- coordenador_tambem_fotografo: BooleanField
  └─ Indica se coordenador atua como fotógrafo

# Funcionalidades de Selfie Pública
- para_selfie: BooleanField
  └─ Se True, permite captura pública de selfie antes do cadastro

# Timestamps
- created_at: DateTimeField (auto)
- updated_at: DateTimeField (auto)

# Observações
- observacoes: TextField
```

**Propriedades computadas:**
- `total_fotos`: Soma de fotos de todas as sessões fotograficas do evento

**Relacionamentos:**
- `alunos`: OneToMany com Aluno (Alunos do evento)
- `sessoes_fotograficas`: OneToMany com SessaoFotografica

---

### 1.3 **Modelo: Aluno**
**Localização:** `gestcaptur/models.py`

**Campos de identificação pessoal:**
```python
# Obrigatórios
- evento: ForeignKey com Evento
- nome: CharField (sempre obrigatório)
- whatsapp: CharField (sempre obrigatório)

# Pessoais
- cpf: CharField (opcional)
- data_nascimento: DateField (opcional)
- email: EmailField (opcional)
- instagram: CharField (opcional)
- telefone_fixo: CharField (opcional)
```

**Campos de endereço:**
```python
- cep: CharField
- endereco: CharField
- numero: CharField
- complemento: CharField
- bairro: CharField
- cidade: CharField
- estado: CharField (2 letras)
```

**Contatos familiares:**
```python
- nome_pai, whatsapp_pai, nome_mae, whatsapp_mae
- nome_parente, grau_parentesco, whatsapp_parente
```

**Gestão de cadastro e fotos:**
```python
- foto: ImageField (upload_to='event_photos/')
  └─ Pode ser selfie ou foto tirada pelo fotógrafo
- photographer: ForeignKey para Usuario
  └─ Fotógrafo que tirou a foto
- card_number: CharField (número de cartão SD/dispositivo)
- cadastro_completo: BooleanField
- ident: BooleanField (true se tem foto)
- token: CharField (UUID - único para acesso público)

# Email tracking
- data_ultimo_email: DateTimeField (último envio)
- tentativas_email: IntegerField (máximo 3 por dia)
```

**Status de comparecimento:**
```python
- status_comparecimento: CharField
  ├─ 'presente' (Presente)
  └─ 'faltoso' (Faltoso)
```

**Timestamps:**
```python
- created_at: DateTimeField (auto)
- updated_at: DateTimeField (auto)
```

**Métodos e propriedades:**
- `save()`: Auto-gera token UUID se não tiver
- `ficha_preenchida`: Verifica se tem nome+whatsapp mas não está completo
- `pode_enviar_email()`: Limita 3 emails/dia
- `registrar_envio_email()`: Registra envio

**Relacionamentos:**
- `evento`: ForeignKey com Evento
- `photographer`: ForeignKey com Usuario

---

### 1.4 **Modelo: SessaoFotografica**
**Localização:** `gestcaptur/models.py`

**Campos principais:**
```python
# Associações
- fotografo: ForeignKey com Usuario
- evento: ForeignKey com Evento

# Dados da sessão
- qtd_fotos: IntegerField (quantidade de fotos tiradas)
- numero_cartao: CharField (ID do cartão SD/dispositivo)

# Timeline
- inicio_sessao: DateTimeField (auto_now_add)
- fim_sessao: DateTimeField (nullable)
- last_activity: DateTimeField (auto_now)

# Status
- finalizado_fotografo: BooleanField (fotógrafo finalizou)
- finalizado_evento: BooleanField (coordenador confirmou)
```

**Relacionamentos:**
- `fotografo`: ForeignKey com Usuario
- `evento`: ForeignKey com Evento

---

## 2. 🎯 ROTAS E URLS

### 2.1 Rotas Públicas (SEM autenticação)

| Rota | View | Template | Descrição |
|------|------|----------|-----------|
| `/login/` | `login_view` | `login.html` | Login de usuários |
| `/aluno/cadastro/` | `aluno_cadastro_publico` | `aluno_cadastro_publico.html` | Novo cadastro de aluno (público) |
| `/aluno/cadastro/<aluno_id>/<token>/` | `aluno_cadastro_publico` | `aluno_cadastro_publico.html` | Edição de aluno via link público |
| `/evento/<evento_id>/selfie/` | `captura_selfie_publico` (views_selfie) | `captura_selfie.html` | Captura de selfie pública |
| `/selfie/salvar/` (POST) | `salvar_selfie_publico` (views_selfie) | - | Salva selfie capturada |
| `/aluno-cadastro-sucesso/` | `aluno_cadastro_sucesso` | `aluno_cadastro_sucesso.html` | Página de sucesso |

### 2.2 Rotas Protegidas por Autenticação

#### **Dashboards e Home**
| Rota | Proteção | View | Descrição |
|------|----------|------|-----------|
| `/` | - | `home_redirect` | Redireciona para dashboard apropriado |
| `/dashboard/` | `@group_required('Gestor')` | `dashboard` | Dashboard do Gestor |
| `/fotografo/` | `@login_required` | `fotografo_dashboard` | Dashboard do Fotógrafo |
| `/dashboard_coordenador/` | `@login_required` | `dashboard_coordenador` | Dashboard do Coordenador |
| `/dashboard-coordenador-fotografo/` | `@login_required` | `dashboard_coordenador_fotografo` | Dashboard híbrido |
| `/dashboard_pesquisa/` | `@login_required` | `dashboard_pesquisa` | Dashboard de Pesquisa |
| `/dashboard-inteligente/` | `@login_required` | `dashboard_inteligente` | Dashboard adaptativo |

#### **Gestão de Usuários** (Gestor)
```
/criar-usuario/                    POST  criar_usuario
/editar-usuario/<user_id>/         GET/POST  editar_usuario
/usuarios/                          GET  listar_usuarios
/usuarios/desativar/<user_id>/     POST  desativar_usuario
/usuarios/ativar/<user_id>/        POST  ativar_usuario
```

#### **Gestão de Eventos** (Gestor/Coordenador)
```
/evento/criar/                      GET/POST  criar_evento
/eventos/                           GET  listar_eventos
/evento/<evento_id>/editar/         GET/POST  editar_evento
/evento/<evento_id>/excluir/        POST  deletar_evento
/evento/<evento_id>/alterar_status/ POST  alterar_status_evento
/evento/<evento_id>/atribuir-fotografo/  POST  atribuir_fotografo
/evento_andamento/                  GET  eventos_andamento
/evento_historico/                  GET  eventos_historico
/eventos_finalizados/               GET  eventos_finalizados

/exportar-eventos/                  GET  exportar_eventos
/exportar-fotos-evento/             GET  exportar_fotos_evento

/iniciar-evento-coordenador/<evento_id>/        POST  iniciar_evento_coordenador
/encerrar-evento/<evento_id>/                   GET   encerrar_evento_coordenador
/encerrar-evento/<evento_id>/confirmar/         POST  confirmar_encerrar_evento
```

#### **Gestão de Alunos**
```
# Importação
/importar/alunos/selecionar/                    GET   selecionar_evento_para_importar
/importar/alunos/<evento_id>/                   GET/POST  importar_alunos
/importar/alunos/confirmar/<evento_id>/         GET/POST  confirmar_importacao_alunos
/importar/alunos/salvar/                        POST  salvar_importacao_alunos

# CRUD
/alunos/                                        GET   alunos_crud
/aluno/novo/                                    GET/POST  aluno_novo
/aluno/<aluno_id>/editar/                       GET/POST  aluno_editar
/aluno/<aluno_id>/visualizar/                   GET   aluno_visualizar

# Fotos e Sessões
/evento/<evento_id>/alunos/                     GET   evento_alunos
/upload-foto/<aluno_id>/                        POST  upload_foto
/finalizar-sessao/<evento_id>/                  POST  finalizar_sessao
/aluno/<aluno_id>/marcar_faltoso/               POST  marcar_aluno_faltoso

# Tokens
/gerar-novo-token/<aluno_id>/                   POST  gerar_novo_token
```

#### **Fichas**
```
/fichas_cadastradas/                GET  fichas_cadastradas
/exportar_fichas/                   GET  exportar_fichas
```

---

## 3. 🛡️ DECORADORES E PROTEÇÕES

**Localização:** `gestcaptur/decorators.py`

### 3.1 Decorador: `@role_required`
```python
# Uso:
@role_required('gestor')
@role_required(['gestor', 'coordenador'])  # múltiplas roles
def view_funcao(request):
    pass
```
- Verifica se `user.role` está na lista de roles permitidas
- Redireciona para `login` se falhar
- Funciona com role do modelo Usuario

### 3.2 Decorador: `@group_required`
```python
# Uso:
@group_required('Gestor')
@group_required(['Gestor', 'Coordenador'])  # múltiplos grupos
def view_funcao(request):
    pass
```
- Verifica se usuário pertence ao grupo Django Groups
- Também verifica role correspondente como fallback
- Mapeamento: 'Gestor' → role='gestor', 'Fotografo' → role='fotografo', etc.

### 3.3 Decorador: `@coordenador_fotografo_required`
- Verifica se usuário é coordenador E está marcado como `coordenador_tambem_fotografo` em algum evento

### 3.4 Fluxo de Autenticação
```
user.is_authenticated 
  ↓
get_dashboard_redirect(user)
  ├─ is_gestor() → 'dashboard' (Gestor)
  ├─ is_coordenador() 
  │  ├─ Se coordenador_tambem_fotografo → 'dashboard_coordenador_fotografo'
  │  └─ Senão → 'dashboard_coordenador'
  ├─ is_fotografo() → 'fotografo_dashboard'
  ├─ is_pesquisa() → 'dashboard_pesquisa'
  └─ Fallback → 'fotografo_dashboard'
```

---

## 4. 📝 TEMPLATES EXISTENTES

### 4.1 Templates Base
| Template | Localização | Descrição | Para quem |
|----------|------------|-----------|----------|
| `base.html` | `gestcaptur/templates/gestcaptur/` | Base genérica | Todos |
| `base_gestor.html` | `gestcaptur/templates/gestcaptur/` | Base gestor | Gestores |
| `base_fotografo.html` | `gestcaptur/templates/gestcaptur/` | Base fotógrafo | Fotógrafos |
| `base_coordenador.html` | `gestcaptur/templates/gestcaptur/` | Base coordenador | Coordenadores |
| `base_publico.html` | `gestcaptur/templates/gestcaptur/` | Base pública | Usuários anônimos |

### 4.2 Templates de Cadastro e Selfie
| Template | Descrição | Funcionalidades |
|----------|-----------|-----------------|
| `aluno_cadastro_publico.html` | Cadastro público de aluno | - Formulário com múltiplas seções (Identificação, Endereço, Contatos) |
| | | - Validações Bootstrap 5 |
| | | - Link para captura de selfie |
| | | - Modo edição com token |
| `captura_selfie.html` | Captura de selfie via webcam | - Acesso à câmera (getUserMedia) |
| | | - Validações de qualidade de imagem |
| | | - Preview antes de salvar |
| | | - Suporta portrait/fullscreen |
| `aluno_cadastro_sucesso.html` | Página de confirmação | Mensagem de sucesso |
| `aluno_novo.html` | Novo aluno (administrativo) | Criação manual |
| `aluno_cadastro_publico-old1.html` | Versão antiga (descontinuada) | - |

### 4.3 Templates de Gestão
| Template | Descrição |
|----------|-----------|
| `atribuir_fotografo.html` | Atribuir fotógrafos a eventos |
| `confirmar_importacao_alunos.html` | Confirmação de importação |
| `fichas_cadastradas.html` | Lista de fichas cadastradas |

### 4.4 Estrutura HTML do Formulário de Cadastro Público

**Seções do formulário:**
1. **Identificação Pessoal** (obrigatório)
   - Nome (obrigatório)
   - WhatsApp (obrigatório)
   - CPF
   - Email
   - Data de Nascimento

2. **Contatos** (opcional)
   - Instagram
   - Telefone Fixo

3. **Endereço** (opcional)
   - CEP
   - Endereço
   - Número
   - Complemento
   - Bairro
   - Cidade
   - Estado

4. **Contatos Familiares** (opcional)
   - Pai (nome, WhatsApp)
   - Mãe (nome, WhatsApp)
   - Parente (nome, grau, WhatsApp)

**Características:**
- Responsivo (mobile-first)
- Bootstrap 5
- Campos com validação client-side
- Seções com cores/ícones para melhor UX
- Cálculo de tamanho de fonte relativo (clamp)

---

## 5. 🔐 FLUXO DE CADASTRO PÚBLICO ATUAL

### 5.1 Fluxo Simplificado
```
1. ACESSO INICIAL
   ├─ Link público: /aluno/cadastro/?evento=<evento_id>
   └─ Ou com selfie: /evento/<evento_id>/selfie/

2. [OPCIONAL] CAPTURA DE SELFIE
   ├─ View: captura_selfie_publico
   ├─ Template: captura_selfie.html
   ├─ Acesso à câmera via WebRTC (getUserMedia)
   ├─ Validação de qualidade:
   │  ├─ Resolução mínima 320x320
   │  ├─ Brilho entre 80-230
   │  └─ Salva em Aluno.foto
   └─ Redireciona para cadastro

3. FORMULÁRIO DE CADASTRO
   ├─ View: aluno_cadastro_publico
   ├─ Template: aluno_cadastro_publico.html
   ├─ Modo novo: sem aluno_id
   ├─ Modo edição: com aluno_id + token (verificação de token)
   ├─ Campos obrigatórios: nome, whatsapp
   └─ Campos opcionais: endereço, contatos familiares

4. VALIDAÇÃO E SALVAMENTO
   ├─ Token único gerado automaticamente
   ├─ Marca como ficha_preenchida
   ├─ Envia email de confirmação (com limite 3/dia)
   └─ Redireciona para sucesso

5. CONFIRMAÇÃO
   ├─ Template: aluno_cadastro_sucesso.html
   └─ Mensagem de sucesso
```

### 5.2 Fluxo Detalhado de Autorizações
```
NOVO ALUNO (sem autenticação):
  GET /aluno/cadastro/?evento=<evento_id>
    ↓
  Verificar se evento.para_selfie == True
    ├─ SIM → Oferecer captura de selfie
    └─ NÃO → Ir direto ao formulário
    ↓
  POST /aluno/cadastro/
    ├─ Validar nome + whatsapp
    ├─ Gerar token UUID
    ├─ Salvar como Aluno
    ├─ Enviar email (se possível)
    └─ Sucesso

EDIÇÃO (com token):
  GET /aluno/cadastro/<aluno_id>/<token>/
    ├─ Verificar token válido
    ├─ Carregar dados existentes
    └─ Mostrar formulário pré-preenchido
    ↓
  POST /aluno/cadastro/<aluno_id>/<token>/
    ├─ Verificar token novamente
    ├─ Validar nome + whatsapp
    ├─ Atualizar dados
    └─ Sucesso
```

---

## 6. 🎬 FLUXO DE SELFIE INTEGRADO

**Arquivo:** `gestcaptur/views_selfie.py`

### 6.1 View: `captura_selfie_publico`
```python
GET /evento/<evento_id>/selfie/
  ├─ Verifica se evento existe
  ├─ Se aluno_id fornecido:
  │  ├─ Verifica se aluno já tem foto
  │  ├─ Se sim → Redireciona para cadastro
  │  └─ Se não → Permite capturar nova
  └─ Renderiza template captura_selfie.html
```

### 6.2 View: `salvar_selfie_publico` (AJAX)
```python
POST /selfie/salvar/ (JSON)
  ├─ Decodifica imagem base64
  ├─ Validações:
  │  ├─ Resolução mínima 320x320px
  │  ├─ Brilho: 80-230 (escala 0-255)
  │  ├─ Se falhar → Retorna erro com mensagem
  │  └─ Se passar → Salva em Aluno.foto
  ├─ Retorna JSON com:
  │  ├─ status: 'ok' | 'error' | 'warning'
  │  ├─ message: mensagem ao usuário
  │  ├─ redirect_url: para cadastro
  │  └─ aluno_id, token
  └─ Cliente redireciona para /aluno/cadastro/<aluno_id>/<token>/
```

### 6.3 Características da Selfie
- **Pública:** Sem autenticação
- **Validação de qualidade:** Resolução + brilho
- **Salvamento:** JPEG com UUID no nome
- **Path:** `event_photos/selfie_<aluno_id>_<uuid>.jpg`
- **Reutilização:** Pode capturar novamente dentro do mesmo evento

---

## 7. 📋 FORMULÁRIOS

**Localização:** `gestcaptur/forms.py`

### 7.1 LoginForm
- Campos: username, password
- Bootstrap styling

### 7.2 AlunoCadastroForm
- Validação de CPF (regex)
- Validação de WhatsApp (comprimento)
- Campos obrigatórios: nome, whatsapp
- Campos opcionais: endereço, contatos, familiares

### 7.3 CriarUsuarioForm
- Campos: username, first_name, last_name, email, role, grupos, password
- Validação de senha (mínimo 6 caracteres)
- Confirmação de senha
- Auto-adiciona a grupo baseado na role

### 7.4 EditarUsuarioForm
- Edição de usuário existente
- Senha opcional (se deixar em branco, mantém a atual)
- Gerenciamento de grupos

### 7.5 UploadFotoForm
- Campo: foto (ImageField)

### 7.6 ImportXLSXForm
- Campo: arquivo (.xlsx)

---

## 8. 🎭 ROLES E PERMISSÕES

### 8.1 Matriz de Permissões

| Funcionalidade | Gestor | Fotografo | Coordenador | Pesquisa | Anônimo |
|---|---|---|---|---|---|
| Ver Dashboard | ✅ | ✅ | ✅ | ✅ | ❌ |
| Criar Evento | ✅ | ❌ | ❌ | ❌ | ❌ |
| Editar Evento | ✅ | ❌ | ✅* | ❌ | ❌ |
| Gerenciar Fotógrafos | ✅ | ❌ | ✅ | ❌ | ❌ |
| Iniciar/Finalizar Evento | ❌ | ❌ | ✅ | ❌ | ❌ |
| Tirar Fotos (upload) | ❌ | ✅ | ✅* | ❌ | ❌ |
| Cadastrar Alunos | ✅ | ❌ | ✅ | ❌ | ✅** |
| Ver Relatórios | ✅ | ❌ | ❌ | ✅ | ❌ |
| Captura de Selfie | ❌ | ❌ | ❌ | ❌ | ✅** |

**Legenda:**
- `✅` = Permitido
- `❌` = Não permitido
- `*` = Se marcado como `coordenador_tambem_fotografo`
- `**` = Apenas para eventos com `para_selfie=True`

### 8.2 Fluxo de Autenticação por Role
```
Usuário Autenticado
  ↓
  ├─ Role: gestor
  │  └─ Dashboard: /dashboard/
  ├─ Role: coordenador
  │  ├─ Se coordenador_tambem_fotografo
  │  │  └─ Dashboard: /dashboard-coordenador-fotografo/
  │  └─ Senão
  │     └─ Dashboard: /dashboard_coordenador/
  ├─ Role: fotografo
  │  └─ Dashboard: /fotografo/
  └─ Role: pesquisa
     └─ Dashboard: /dashboard_pesquisa/

Usuário Anônimo
  ├─ POST /aluno/cadastro/
  │  └─ Cria novo Aluno (se nome + whatsapp válidos)
  ├─ GET /evento/<evento_id>/selfie/
  │  └─ Captura selfie (se evento.para_selfie=True)
  └─ GET /aluno/cadastro/<aluno_id>/<token>/
     └─ Edita aluno (com token válido)
```

---

## 9. 🌐 INFORMAÇÕES DE BANCO DE DADOS

### 9.1 Configuração Local (.env)
```
DATABASE_URL=mysql://root:Ph0tuM@fv2018@127.0.0.1:3306/photoapp_db
```

### 9.2 Engine
```python
Engine: django.db.backends.mysql (MariaDB)
Charset: utf8mb4
Port: 3306
```

### 9.3 Modelos no Banco
- `gestcaptur_usuario` (customizado)
- `gestcaptur_evento`
- `gestcaptur_aluno`
- `gestcaptur_sessaofotografica`
- `auth_group` (Django Groups)
- `auth_group_permissions`

### 9.4 Migrações Recentes
- `0001_initial` - Criação inicial
- `0002_aluno_cadastro_completo_aluno_data_ultimo_email_and_more` - Adição de campos
- `0006_aluno_status_comparecimento_alter_aluno_whatsapp` - Status de comparecimento
- `0007_alter_usuario_role` - Alteração de role
- `0008_evento_para_selfie` - Campo para_selfie em eventos

---

## 10. 🚀 INFORMAÇÕES CRÍTICAS PARA AUTOATENDIMENTO DE FORMANDOS

### 10.1 Fluxo Sugerido para Feature
```
1. DESCOBERTA
   - QR Code aponta para /evento/<evento_id>/
   - Verifica se evento.para_selfie == True
   
2. CAPTURA (OPCIONAL)
   - Se para_selfie=True:
     - Redireciona para /evento/<evento_id>/selfie/
     - Captura selfie com validações
     - Salva em Aluno.foto
   
3. CADASTRO (OBRIGATÓRIO)
   - Redireciona para /aluno/cadastro/?evento=<evento_id>
   - Formulário responsivo com validações
   - Seções: Identificação, Endereço, Contatos
   - Campos obrigatórios: nome, whatsapp
   
4. CONFIRMAÇÃO
   - Salva como Aluno.cadastro_completo=True
   - Gera token UUID
   - Envia email de confirmação
   - Mostra página de sucesso
```

### 10.2 Campos-Chave para Formandos
```python
# OBRIGATÓRIOS
- nome: str (sempre)
- whatsapp: str (sempre)
- foto: ImageField (opcional, mas desejável)

# RECOMENDADOS
- email: str (para confirmação)
- cpf: str (identificação)
- data_nascimento: date (para relatórios)

# OPCIONAIS
- Endereço, contatos familiares (coleta extra)
```

### 10.3 Campos no Banco para Rastrear Cadastro
```python
# Status do cadastro
aluno.cadastro_completo: bool
aluno.ficha_preenchida: bool (parcialmente completo)
aluno.ident: bool (tem foto)

# Rastreamento de comunicação
aluno.data_ultimo_email: datetime
aluno.tentativas_email: int (limite 3/dia)

# Edição via link
aluno.token: str (UUID - único)

# Comparecimento
aluno.status_comparecimento: str ('presente' ou 'faltoso')

# Fotos
aluno.foto: ImageField
aluno.photographer: ForeignKey (quem tirou)
```

### 10.4 Pontos de Extensão para Feature
1. **Pré-preenchimento de dados:**
   - QR Code pode passar `nome` e `evento_id`
   - URL: `/aluno/cadastro/?evento=<evento_id>&nome=<nome>`

2. **Validação de CPF/documento:**
   - Adicionar validação de CPF no formulário
   - Integração com APIs de validação

3. **Confirmação por OTP:**
   - Enviar código via WhatsApp
   - Validar antes de confirmar cadastro

4. **Integração com lista oficial:**
   - Importar lista de formandos
   - Marcar como "convidado confirmado"
   - Enviar link apenas para quem está na lista

5. **Relatórios:**
   - % de cadastros completados
   - Tempo médio para completar cadastro
   - Formandos presentes vs faltosos

---

## 11. 📊 RESUMO DE ARQUIVOS PRINCIPAIS

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `gestcaptur/models.py` | ~500 | Definição de modelos |
| `gestcaptur/views.py` | ~3000+ | Lógica de negócios |
| `gestcaptur/views_selfie.py` | ~150 | Fluxo de selfie |
| `gestcaptur/urls.py` | ~80 | Roteamento |
| `gestcaptur/decorators.py` | ~100 | Proteções e permissões |
| `gestcaptur/forms.py` | ~250 | Validação de dados |
| `gestcaptur/templates/` | 58+ templates | Interfaces |
| `gestcaptur/photoapp/settings.py` | ~200 | Configuração Django |

---

## 12. 🔗 PRÓXIMAS ETAPAS RECOMENDADAS

Para implementar **autoatendimento de formandos**, considere:

1. ✅ Criar nova view para fluxo de formando (separado de aluno genérico)
2. ✅ Adicionar modelo `Formando` (herda ou estende Aluno)
3. ✅ Campos adicionais: matrícula, curso, turma, data de conclusão
4. ✅ Fluxo: Descoberta → Selfie → Cadastro → Confirmação
5. ✅ Dashboard para formandos (visualizar status)
6. ✅ Relatório de confirmação de presença
7. ✅ Integração com lista oficial de formandos
8. ✅ Notificações via WhatsApp (confirmação de cadastro)
9. ✅ Exportação de formandos confirmados
10. ✅ Possibilidade de editar cadastro após confirmação

---

**Data da análise:** Maio 20, 2026  
**Versão do projeto:** PhotoApp V2  
**Status:** Documentado e pronto para desenvolvimento
