# 📊 RELATÓRIO DE ANÁLISE DO PROJETO PHOTOAPP - VPS
**Data da Análise:** 12 de Maio de 2026  
**Responsável:** Claude Code (Assistente IA)  
**Status do Servidor:** ✅ Online e Operacional  
**Última Atualização:** Melhorias de segurança implementadas (13/05/2026)

---

## 🎯 RESUMO EXECUTIVO

O projeto PhotoApp está **funcionando em produção** na VPS, mas apresenta **problemas críticos de segurança e arquitetura** que precisam de atenção imediata.

### ✅ Pontos Positivos
- Serviço rodando estável há 5 dias
- DEBUG=False configurado corretamente
- SSL/HTTPS configurado com Let's Encrypt
- Redis instalado e operacional
- Nginx configurado como proxy reverso
- SQLite como banco de dados (adequado para carga atual)

### 🔴 Pontos Críticos
- **Views.py com 2592 linhas** (deveria ter no máximo 200-300)
- **Sem testes automatizados** (apenas arquivo vazio)
- **Configurações CSRF inseguras** em produção
- **Ataques de scanners** constantes (PHP, .env, WordPress)
- **Falta de rate limiting** contra brute force
- **Logs mostram problemas de CSRF** frequentes

---

## 🔍 ANÁLISE DETALHADA

### 1. INFRAESTRUTURA E SERVIÇOS

#### ✅ Serviços Rodando
```
● photoapp.service - Gunicorn instance (3 workers)
● nginx.service - Reverse proxy
● redis-server.service - Cache
● celery-worker.service - Tarefas assíncronas
```

#### Configuração Gunicorn
- **Workers:** 3 (adequado)
- **Bind:** 127.0.0.1:8001
- **Socket Unix:** /var/www/photoapp/gunicorn.sock
- **Memória:** 6.2MB (leve)

#### Configuração Nginx
- **SSL:** Let's Encrypt (válido)
- **Proxy:** Unix socket → Gunicorn
- **Headers:** X-Forwarded-Proto configurado
- **Redirecionamento:** HTTP → HTTPS

---

### 2. SEGURANÇA - PROBLEMAS CRÍTICOS

#### 🔴 CRÍTICO: Configurações CSRF Inseguras
**Arquivo:** `photoapp/settings.py` (linhas 68-77)

```python
# ❌ PROBLEMA: Em produção (DEBUG=False), estas configurações estão inseguras
CSRF_COOKIE_SECURE = False              # Deve ser TRUE
CSRF_COOKIE_HTTPONLY = False            # Deve ser TRUE
CSRF_USE_SESSIONS = False               # Considerar TRUE
```

**Impacto:** Logs mostram múltiplos erros de CSRF:
```
Forbidden (Referer checking failed - Referer is insecure while host is secure.)
```

**Solução Imediata:**
```python
if not DEBUG:
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True
    CSRF_USE_SESSIONS = True
    SESSION_COOKIE_SECURE = True
```

#### 🔴 CRÍTICO: Ataques de Scanners
**Logs mostram ataques constantes:**
- Busca por arquivos `.env` (20+ tentativas)
- Scan por vulnerabilidades PHP (phpunit, eval-stdin.php)
- Tentativas de acesso WordPress (wp-admin, wp-login.php, xmlrpc.php)
- Scan por Docker API (/containers/json)

**Exemplo dos logs:**
```
WARNING: Not Found: /.env
WARNING: Not Found: /vendor/phpunit/phpunit/src/Util/PHP/eval-stdin.php
WARNING: Not Found: /wp-admin
WARNING: Not Found: /xmlrpc.php
```

**Solução Necessária:**
1. **Fail2Ban** para bloquear IPs após tentativas falhas
2. **Rate limiting** no Nginx
3. **WAF (Web Application Firewall)** como ModSecurity

#### 🟡 IMPORTANTE: Falta de Rate Limiting
**Problema:** Não há proteção contra brute force no login

**Solução Recomendada:**
```python
# requirements.txt
django-ratelimit==4.1.0

# settings.py
RATELIMIT_ENABLE = True
RATELIMIT_VIEW = 'gestcaptur.views.rate_limited'

# views.py (no login)
from ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='5/m', block=True)
def login_view(request):
    # ...
```

---

### 3. ARQUITETURA DO CÓDIGO - PROBLEMAS GRAVES

#### 🔴 CRÍTICO: Views.py Monstruoso
**Arquivo:** `gestcaptur/views.py`
- **2592 linhas** (deveria ter 200-300)
- **Dificulta manutenção**
- **Impossível testar**
- **Viola princípios SOLID**

**Estrutura Atual (exemplo do que deve ser separado):**
```
gestcaptur/views/
├── __init__.py
├── auth.py           # Login, logout, register (~300 linhas)
├── eventos.py        # CRUD eventos (~400 linhas)
├── alunos.py         # CRUD alunos (~400 linhas)
├── fotos.py          # Upload, download (~500 linhas)
├── dashboard.py      # Dashboard, estatísticas (~300 linhas)
├── admin.py          # Funções admin (~200 linhas)
└── api.py            # Endpoints API (~500 linhas)
```

#### 🟡 IMPORTANTE: Falta de Camada de Services
**Problema:** Lógica de negócio misturada nas views

**Exemplo Atual (ruim):**
```python
def upload_foto(request, evento_id):
    # Validação de permissões
    # Processamento de imagem
    # Cálculo de estatísticas
    # Envio de email
    # ... tudo junto!
```

**Solução (criar gestcaptur/services/):**
```python
# gestcaptur/services/foto_service.py
class FotoService:
    @staticmethod
    def processar_upload(aluno, arquivo, fotografo):
        # Validar permissões
        # Processar imagem
        # Atualizar estatísticas
        # Retornar resultado
        pass
```

#### 🟡 IMPORTANTE: Models.py com Duplicação
**Arquivo:** `gestcaptur/models.py` (274 linhas)

**Problema:** Sistema de roles duplicado
```python
# ❌ ATUAL: Duplicado
role = models.CharField(max_length=20, choices=ROLE_CHOICES)
groups = ManyToManyField(Group)  # Do Django

def is_gestor(self):
    return self.groups.filter(name='Gestor').exists() or self.role == 'gestor'
```

**Solução:** Usar apenas Django Groups
```python
# ✅ MELHORADO
def has_role(self, role_name):
    return self.groups.filter(name=role_name).exists()
```

---

### 4. QUALIDADE DE CÓDIGO

#### 🔴 CRÍTICO: Ausência de Testes
**Arquivo:** `gestcaptur/tests.py` (apenas 60 bytes - vazio!)

**Cobertura atual:** 0%

**Estrutura necessária:**
```
gestcaptur/tests/
├── __init__.py
├── test_models.py      # Testar todos os models
├── test_views.py       # Testar todas as views
├── test_forms.py       # Testar formulários
├── test_services.py    # Testar services
├── test_decorators.py  # Testar decorators
└── factories.py        # Factory Boy para dados de teste
```

**Recomendação:** Mínimo 70% de cobertura

#### 🟡 IMPORTANTE: Forms.py Grande
**Arquivo:** `gestcaptur/forms.py` (681 linhas)

**Recomendação:** Separar por funcionalidade
```
gestcaptur/forms/
├── __init__.py
├── auth_forms.py       # Login, registro
├── evento_forms.py     # Formulários de eventos
├── aluno_forms.py      # Formulários de alunos
└── foto_forms.py       # Formulários de fotos
```

---

### 5. BANCO DE DADOS E PERFORMANCE

#### ✅ OK: SQLite em Produção
- **Adequado** para carga atual
- **Simples** de fazer backup
- **Sem configuração** complexa

**Recomendação futura:** Migrar para PostgreSQL quando escalar

#### 🟡 IMPORTANTE: Possíveis N+1 Queries
**Problema:** Não foi possível verificar queries específicas, mas é comum em views grandes

**Solução:**
```python
# ❌ RUIM: N+1 queries
for evento in Evento.objects.all():
    print(evento.fotografos.all())  # Query para cada evento

# ✅ BOM: 2 queries no total
eventos = Evento.objects.prefetch_related('fotografos')
for evento in eventos:
    print(evento.fotografos.all())
```

#### ✅ OK: Redis Instalado
- **Cache** configurado
- **Celery** usando Redis como broker

---

### 6. CONFIGURAÇÕES DJANGO

#### ✅ OK: Settings.py
- **DEBUG=False** ✅
- **ALLOWED_HOSTS** configurado ✅
- **Logging** configurado ✅
- **Middleware** adequado ✅

#### 🔴 PROBLEMA: Settings Misturados
**Arquivo único** para desenvolvimento e produção

**Solução recomendada:**
```
photoapp/settings/
├── __init__.py
├── base.py      # Configurações comuns
├── dev.py       # Desenvolvimento
└── prod.py      # Produção
```

---

### 7. DEPLOY E INFRAESTRUTURA

#### ✅ OK: Systemd Service
- **Service name:** photoapp.service
- **Auto-restart:** configurado
- **User:** root (deveria ser usuário dedicado)

#### 🟡 IMPORTANTE: Permissões
**Problema:** Rodando como root

**Solução:**
```ini
# /etc/systemd/system/photoapp.service
[Service]
User=photoapp
Group=photoapp
WorkingDirectory=/var/www/photoapp
```

#### ✅ OK: Nginx + Gunicorn
- **Proxy reverso** configurado
- **SSL** com Let's Encrypt
- **Headers** de proxy configurados

---

## 📋 PLANO DE AÇÃO PRIORITÁRIO

### 🔴 URGENTE (Esta semana)

1. **Corrigir Configurações CSRF**
   ```python
   # settings.py
   if not DEBUG:
       CSRF_COOKIE_SECURE = True
       CSRF_COOKIE_HTTPONLY = True
       SESSION_COOKIE_SECURE = True
   ```

2. **Implementar Fail2Ban**
   ```bash
   sudo apt install fail2ban
   sudo systemctl enable fail2ban
   ```

3. **Criar Jail para Nginx**
   ```
   # /etc/fail2ban/jail.local
   [nginx-http-auth]
   enabled = true
   port = http,https
   filter = nginx-http-auth
   logpath = /var/log/nginx/error.log
   maxretry = 3
   bantime = 3600
   ```

### 🟡 IMPORTANTE (Próximas 2 semanas)

4. **Refatorar Views.py**
   - Separar em múltiplos arquivos
   - Criar estrutura `gestcaptur/views/`
   - Manter cada view com no máximo 100 linhas

5. **Criar Camada de Services**
   - Extrair lógica de negócio das views
   - Criar `gestcaptur/services/`
   - Services para: Foto, Evento, Aluno, Email

6. **Implementar Testes**
   - Configurar pytest
   - Criar testes para models
   - Criar testes para views principais
   - Meta: 50% de cobertura inicial

7. **Adicionar Rate Limiting**
   - Instalar django-ratelimit
   - Proteger login (5 tentativas/minuto)
   - Proteger uploads

### 🟢 RECOMENDADO (Próximo mês)

8. **Otimizar Queries**
   - Adicionar select_related/prefetch_related
   - Analisar queries com Django Debug Toolbar (dev)

9. **Melhorar Logging**
   - Log de ações importantes
   - Log de erros de negócio
   - Log de acessos admin

10. **Configurar Monitoramento**
    - Sentry para erros
    - Health checks
    - Monitoramento de performance

---

## 🛡️ CHECKLIST DE SEGURANÇA

### Crítico
- [ ] CSRF_COOKIE_SECURE = True em produção
- [ ] CSRF_COOKIE_HTTPONLY = True em produção
- [ ] SESSION_COOKIE_SECURE = True em produção
- [ ] Implementar Fail2Ban
- [ ] Rate limiting no login

### Importante
- [ ] Validar upload de arquivos (tipo, tamanho)
- [ ] Sanitizar inputs de busca
- [ ] Usar Django Groups em vez de role customizado
- [ ] Adicionar headers de segurança no Nginx
- [ ] Configurar CSP (Content Security Policy)

### Recomendado
- [ ] WAF (ModSecurity)
- [ ] Monitoramento de tentativas de login
- [ ] Log de todas as ações administrativas
- [ ] Backup automático do banco
- [ ] SSL/TLS scanning periódico

---

## 📈 MÉTRICAS ATUAIS

| Métrica | Valor | Status |
|---------|-------|--------|
| **Uptime** | 5 dias | ✅ Bom |
| **Memória** | 6.2MB | ✅ Leve |
| **Workers** | 3 | ✅ Adequado |
| **Linhas views.py** | 2592 | 🔴 Crítico |
| **Cobertura testes** | 0% | 🔴 Crítico |
| **Tamanho forms.py** | 681 linhas | 🟡 Atenção |
| **Tamanho models.py** | 274 linhas | ✅ OK |

---

## 🎯 PRÓXIMOS PASSOS IMEDIATOS

1. **Hoje:** Corrigir configurações CSRF no settings.py
2. **Amanhã:** Instalar e configurar Fail2Ban
3. **Esta semana:** Começar refatoração do views.py
4. **Próxima semana:** Implementar testes básicos

---

## 📞 SUPORTE

Para dúvidas sobre esta análise ou implementação das melhorias, consulte:
- **ANALISE_E_MELHORIAS.md** - Análise detalhada original
- **DEPLOY_UBUNTU_GUIDE.md** - Guia de deploy
- **Documentação Django** - https://docs.djangoproject.com/

---

**Relatório gerado em:** 12/05/2026 às 15:58  
**Próxima revisão recomendada:** 19/05/2026