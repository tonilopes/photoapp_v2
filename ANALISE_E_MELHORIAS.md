# 📊 Análise Detalhada do Projeto PhotoApp

## 1. 🔴 PROBLEMAS CRÍTICOS (Segurança & Performance)

### 1.1 Configurações de Segurança Inadequadas
**Arquivo:** `photoapp/settings.py`

```python
# ❌ PROBLEMAS ENCONTRADOS:
CSRF_COOKIE_SECURE = False              # DEVE SER TRUE em produção
CSRF_COOKIE_HTTPONLY = False            # DEVE SER TRUE
DEBUG = config('DEBUG', default=False)  # OK, mas verificar em .env
CSRF_USE_SESSIONS = False               # Considerar True para maior segurança
```

**Recomendação:**
- Use `django-environ` para gerenciar configurações por ambiente
- Crie arquivos de configuração separados: `settings/base.py`, `settings/development.py`, `settings/production.py`

---

### 1.2 Falta de Limitação de Requisições
**Problema:** Não há proteção contra brute force ou DDoS
- Adicionar `django-ratelimit` ou `djangorestframework-throttling`
- Implementar rate limiting no login

---

### 1.3 Upload de Arquivos sem Validação Adequada
**Arquivo:** `gestcaptur/views.py` (formulário de upload)

**Problema:** Possível upload de arquivos maliciosos
```python
# ❌ Risco: Sem validação de tipo MIME, tamanho, etc.
foto = models.ImageField(upload_to='event_photos/', blank=True, null=True)
```

**Solução:**
```python
from django.core.files.base import ContentFile
from PIL import Image

def validate_image_file(file):
    if file.size > 5 * 1024 * 1024:  # 5MB max
        raise ValidationError("Arquivo muito grande (máx. 5MB)")
    
    try:
        img = Image.open(file)
        img.verify()
    except Exception:
        raise ValidationError("Arquivo não é uma imagem válida")
```

---

### 1.4 SQL Injection Risk em Buscas
**Arquivo:** `gestcaptur/views.py`

Se há buscas com `filter()` usando entrada do usuário, validar sempre!

**Verificar:** Implementar `Q` objects corretamente:
```python
# ✅ SEGURO:
Aluno.objects.filter(
    Q(nome__icontains=search_term) |
    Q(email__icontains=search_term)
)

# ❌ INSEGURO (se search_term não for sanitizado):
# Usar raw queries sem escape
```

---

## 2. 🟡 PROBLEMAS MODERADOS (Arquitetura & Manutenibilidade)

### 2.1 Views Muito Grandes
**Arquivo:** `gestcaptur/views.py` (2260 linhas!)

**Problema:** Difícil manutenção, testabilidade reduzida

**Solução:** Separar em múltiplos arquivos:
```
gestcaptur/
├── views/
│   ├── __init__.py
│   ├── auth.py          # login, logout, register
│   ├── eventos.py       # CRUD de eventos
│   ├── alunos.py        # CRUD de alunos
│   ├── fotos.py         # Upload, download de fotos
│   ├── dashboard.py     # Dashboards
│   └── admin.py         # Funcionalidades admin
```

---

### 2.2 Lógica de Negócio em Views
**Problema:** Regras de negócio devem estar em services/managers

**Exemplo:**
```python
# ❌ EM VIEWS (ruim)
def upload_foto(request, evento_id):
    # Validação de permissões
    # Processamento de imagem
    # Cálculo de estatísticas
    # Envio de email
    # ... tudo junto!

# ✅ EM SERVICES (bom)
# gestcaptur/services/foto_service.py
class FotoService:
    @staticmethod
    def processar_upload(aluno, arquivo, fotografo):
        # Validar permissões
        # Processar imagem
        # Atualizar estatísticas
        # Retornar resultado
```

---

### 2.3 Falta de Testes
**Problema:** Nenhum arquivo `tests.py` com testes automatizados

**Solução:** Criar cobertura de testes:
```
gestcaptur/
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_views.py
│   ├── test_forms.py
│   ├── test_decorators.py
│   └── factories.py (test data)
```

---

### 2.4 Redundância no Sistema de Roles
**Arquivo:** `gestcaptur/models.py`

```python
# ❌ ATUAL: Duplicado - Role + Groups
role = models.CharField(max_length=20, choices=ROLE_CHOICES)  # Em Usuario
groups = ManyToManyField(Group)  # Do Django

def is_gestor(self):
    return self.groups.filter(name='Gestor').exists() or self.role == 'gestor'
```

**Solução:** Use apenas Django Groups
```python
# ✅ MELHORADO: Usar apenas Groups
def is_gestor(self):
    return self.groups.filter(name='Gestor').exists()

# Em models:
def has_role(self, role_name):
    return self.groups.filter(name=role_name).exists()
```

---

### 2.5 Falta de Logging Estruturado
**Problema:** Logs espalhados sem padrão

**Solução:**
```python
# gestcaptur/utils/logging.py
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

def log_action(user, action, resource, status='success', details=None):
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'user': user.username if user else 'anonymous',
        'action': action,
        'resource': resource,
        'status': status,
        'details': details or {}
    }
    logger.info(json.dumps(log_data))

# USO:
log_action(request.user, 'upload_foto', f'aluno_{aluno.id}', 'success')
```

---

## 3. 🟢 MELHORIAS RECOMENDADAS (Performance & UX)

### 3.1 Otimização de Queries
**Problema:** Possíveis N+1 queries

**Solução:**
```python
# ❌ RUIM:
for evento in Evento.objects.all():
    print(evento.fotografos.all())  # N queries!

# ✅ BOM:
eventos = Evento.objects.prefetch_related('fotografos')
for evento in eventos:
    print(evento.fotografos.all())  # 2 queries no total
```

---

### 3.2 Cache de Dados
**Recomendação:** Adicionar Redis para cache

```python
from django.core.cache import cache

def get_statistics(evento_id):
    cache_key = f'evento_{evento_id}_stats'
    stats = cache.get(cache_key)
    
    if stats is None:
        stats = compute_statistics(evento_id)
        cache.set(cache_key, stats, 3600)  # 1 hora
    
    return stats
```

---

### 3.3 Paginação
**Recomendação:** Implementar em todas as listagens

```python
from django.core.paginator import Paginator

def lista_alunos(request, evento_id):
    alunos = Aluno.objects.filter(evento_id=evento_id)
    paginator = Paginator(alunos, 50)  # 50 por página
    page = request.GET.get('page', 1)
    alunos_page = paginator.get_page(page)
    return render(request, 'lista_alunos.html', {'alunos': alunos_page})
```

---

### 3.4 Processamento Assíncrono
**Problema:** Processamento de imagens bloqueia a requisição

**Solução:** Usar Celery + Redis
```python
# gestcaptur/tasks.py
from celery import shared_task
from PIL import Image

@shared_task
def processar_imagem(aluno_id, foto_path):
    # Redimensionar
    # Aplicar filtros
    # Gerar thumbnail
    # Atualizar banco de dados
    pass

# Na view:
processar_imagem.delay(aluno.id, foto.path)
return JsonResponse({'status': 'processando'})
```

---

## 4. 📋 PADRÕES DE CÓDIGO

### 4.1 Estrutura de Resposta API
Padronizar respostas:
```python
def json_response(success, message, data=None, status_code=200):
    return JsonResponse({
        'success': success,
        'message': message,
        'data': data or {}
    }, status=status_code)

# USO:
return json_response(True, 'Foto enviada', {'foto_id': 123})
```

---

### 4.2 Validação de Permissões
Criar decorator genérico:
```python
# gestcaptur/decorators.py
def permission_required(permission_name):
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not request.user.has_perm(permission_name):
                raise PermissionDenied()
            return func(request, *args, **kwargs)
        return wrapper
    return decorator

# USO:
@permission_required('gestcaptur.add_evento')
def criar_evento(request):
    pass
```

---

## 5. 🗂️ ESTRUTURA RECOMENDADA

```
photoapp/
├── photoapp/               # Configurações Django
│   ├── settings/
│   │   ├── base.py        # Configurações comuns
│   │   ├── dev.py         # Desenvolvimento
│   │   └── prod.py        # Produção
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── gestcaptur/            # App principal
│   ├── models/
│   │   ├── __init__.py
│   │   ├── usuario.py
│   │   ├── evento.py
│   │   ├── aluno.py
│   │   └── sessao.py
│   │
│   ├── views/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── eventos.py
│   │   ├── alunos.py
│   │   ├── fotos.py
│   │   └── dashboard.py
│   │
│   ├── services/          # Lógica de negócio
│   │   ├── __init__.py
│   │   ├── foto_service.py
│   │   ├── evento_service.py
│   │   └── email_service.py
│   │
│   ├── serializers/       # Para API REST
│   │   ├── __init__.py
│   │   └── *.py
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── decorators.py
│   │   ├── validators.py
│   │   ├── logging.py
│   │   └── pagination.py
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_models.py
│   │   ├── test_views.py
│   │   ├── test_services.py
│   │   └── factories.py
│   │
│   ├── templates/
│   ├── static/
│   ├── forms.py
│   ├── admin.py
│   ├── urls.py
│   └── apps.py
│
├── templates/             # Templates globais
├── static/                # Arquivos estáticos
├── .env.example           # Template de variáveis de ambiente
├── .env.production        # Produção (NÃO commitar)
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── gunicorn.conf.py
├── tests/
│   └── conftest.py        # Configuração pytest
└── manage.py
```

---

## 6. ✅ CHECKLIST DE MELHORIAS POR PRIORIDADE

### 🔴 CRÍTICO (Segurança)
- [ ] Separe `settings` por ambiente
- [ ] Ative `CSRF_COOKIE_SECURE = True` em produção
- [ ] Implemente validação de upload de arquivos
- [ ] Configure rate limiting no login
- [ ] Use variáveis de ambiente para dados sensíveis

### 🟡 IMPORTANTE (Arquitetura)
- [ ] Refatore `views.py` em múltiplos arquivos
- [ ] Crie uma camada de services
- [ ] Implemente logging estruturado
- [ ] Use apenas Django Groups (remova `role` duplicado)
- [ ] Adicione testes unitários

### 🟢 RECOMENDADO (Performance)
- [ ] Implemente prefetch_related nas queries
- [ ] Configure cache com Redis
- [ ] Adicione paginação em listagens
- [ ] Use Celery para processamento assíncrono
- [ ] Otimize imagens automaticamente

---

## 7. 📚 REFERÊNCIAS

- Django Security: https://docs.djangoproject.com/en/stable/topics/security/
- Django Best Practices: https://github.com/HackSoftware/Django-Styleguide
- TwoScoops of Django: https://www.feldroy.com/books/two-scoops-of-django
- OWASP: https://owasp.org/www-project-top-ten/

---

**Desenvolvido em:** 19 de fevereiro de 2026
