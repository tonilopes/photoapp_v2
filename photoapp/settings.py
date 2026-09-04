import os
from pathlib import Path
from decouple import config, Csv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Configurações de Segurança e Ambiente ---
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)

# ALLOWED_HOSTS: Corrigido o erro de .split() em Csv()
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv(), default=[])

# Lista COMPLETA de origens confiáveis
CSRF_TRUSTED_ORIGINS = [
    # Local/Desenvolvimento
    'http://192.168.0.25:2580',
    'http://192.168.0.25',
    'http://127.0.0.1:8000',
    'http://localhost:8000',
    'http://localhost:2580',
    'http://photoapp.local',
    
    # Produção/Externo - HTTP
    'http://externo.photum.com.br',
    'http://externo.photum.com.br:2543',
    'http://cliente.photum.com.br',
    'http://cliente.photum.com.br:2543',
    
    # Produção/Externo - HTTPS
    'https://externo.photum.com.br',
    'https://externo.photum.com.br:2543',
    'https://cliente.photum.com.br',
    'https://cliente.photum.com.br:2543',

    # Painel v2 (fotoid)
    'https://fotoid.photum.com.br',
    'http://fotoid.photum.com.br',
]

# ============================================
# CONFIGURAÇÕES DE SEGURANÇA CSRF E SESSÃO
# ============================================

# ============================================
# CONFIGURAÇÕES DE RATE LIMITING
# ============================================
# Proteção contra brute force e abuso
RATELIMIT_ENABLE = not DEBUG  # Habilitado em produção
RATELIMIT_VIEW = 'gestcaptur.views.rate_limited'  # View para quando exceder limite
RATELIMIT_STORAGE_URL = 'memory://'  # Usar memória (pode mudar para Redis em produção)
RATELIMIT_FAIL_OPENLY = False  # Não permitir acesso se rate limiter falhar

# Para produção (DEBUG=False), usamos True para SECURE (HTTPS) e HTTP-only para segurança
# Para desenvolvimento (DEBUG=True), usamos False para compatibilidade local

CSRF_COOKIE_SECURE = not DEBUG  # True em produção, False em desenvolvimento
CSRF_COOKIE_HTTPONLY = not DEBUG  # True em produção, False em desenvolvimento
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = not DEBUG  # True em produção, False em desenvolvimento
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'
CSRF_COOKIE_NAME = 'csrftoken'

# Configurações de Sessão
SESSION_COOKIE_SECURE = not DEBUG  # True em produção, False em desenvolvimento
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_DOMAIN = None

# Headers de proxy
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_PORT = True


# --- Apps Instalados ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'widget_tweaks',
    'gestcaptur',
]


# --- Middlewares ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'gestcaptur.middleware.DisableClientSideCacheMiddleware',
]


# --- Configuração de URLs e Templates ---
ROOT_URLCONF = 'photoapp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'photoapp.wsgi.application'


# --- Configuração de Banco de Dados (MariaDB) ---
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL', default='sqlite:///db.sqlite3'),
        conn_max_age=600
    )
}

# Se o MariaDB for o padrão, adicione as opções específicas aqui
if 'default' in DATABASES and DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
    # Garante que a porta seja definida se não estiver na URL ou se for preciso sobrescrever
    if not DATABASES['default'].get('PORT'):
        DATABASES['default']['PORT'] = '3306'  # Define a porta padrão do MariaDB

    # Atualiza ou adiciona as OPTIONS
    db_options = DATABASES['default'].get('OPTIONS', {})
    db_options.update({
        'charset': 'utf8mb4',
        'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        'autocommit': True,
    })
    DATABASES['default']['OPTIONS'] = db_options


# --- Autenticação e Usuário Customizado ---
AUTH_USER_MODEL = 'gestcaptur.Usuario'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# --- Internacionalização ---
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True


# --- Arquivos Estáticos e de Mídia ---
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'mediafiles')


# --- URLs de Login ---
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# --- Configurações de E-mail (REMOVIDAS CONFORME SOLICITADO) ---
# Se o app não usa e-mail, estas configurações não são necessárias.
# Qualquer código relacionado a EmailBackend, EmailHost, etc. foi removido.


# --- URLs Base do Site e QR Code ---
SITE_URL = config('SITE_URL', default='http://localhost:8002')
QR_CODE_BASE_URL = config('QR_CODE_BASE_URL', default='http://localhost:8002')


# Define os handlers de log que serão ativados com base no modo DEBUG
LOGGING_HANDLERS_FOR_DEBUG = {
    'console': {
        'class': 'logging.StreamHandler',
        'formatter': 'simple',
        'level': 'DEBUG',  # Console ainda mostra DEBUG para feedback imediato
    },
    'file_dev': {
        'level': 'ERROR',  # Apenas ERROS e mensagens CRÍTICAS no debug.log
        'class': 'logging.FileHandler',
        'filename': BASE_DIR / 'debug.log',
        'formatter': 'verbose',
    },
}

LOGGING_HANDLERS_FOR_PROD = {
    'file_prod': {
        'level': 'INFO',  # Em produção, ainda queremos INFO para monitoramento
        'class': 'logging.FileHandler',
        'filename': config('LOG_FILE_PATH', default='/var/log/django/photoapp.log'),
        'formatter': 'verbose',
    },
}

# Escolhe os handlers e níveis de log baseados em DEBUG
if DEBUG:
    # Para DEBUG=True, queremos console verboso e file_dev apenas para erros
    ACTIVE_LOG_HANDLERS = ['console', 'file_dev']
    LOG_LEVEL_DJANGO_CONSOLE = 'DEBUG'
    LOG_LEVEL_APP_CONSOLE = 'DEBUG'
    LOG_LEVEL_DJANGO_FILE = 'INFO'  # Nível do logger 'django' para o arquivo
    LOG_LEVEL_APP_FILE = 'INFO'     # Nível do logger 'gestcaptur' para o arquivo
    LOG_LEVEL_ROOT_CONSOLE = 'WARNING'  # Nível root para console
    LOG_LEVEL_ROOT_FILE = 'WARNING'  # Nível root para arquivo
    ALL_DEFINED_HANDLERS = LOGGING_HANDLERS_FOR_DEBUG
else:  # Produção
    ACTIVE_LOG_HANDLERS = ['file_prod']
    LOG_LEVEL_DJANGO_CONSOLE = 'INFO'  # N/A se console não está ativo em prod
    LOG_LEVEL_APP_CONSOLE = 'INFO'     # N/A
    LOG_LEVEL_DJANGO_FILE = 'INFO'
    LOG_LEVEL_APP_FILE = 'INFO'
    LOG_LEVEL_ROOT_CONSOLE = 'ERROR'  # N/A
    LOG_LEVEL_ROOT_FILE = 'ERROR'
    ALL_DEFINED_HANDLERS = LOGGING_HANDLERS_FOR_PROD

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file_prod': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/photoapp.log',
            'maxBytes': 1024*1024*5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file_prod'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file_prod'],
            'level': 'INFO',
            'propagate': False,
        },
        'gestcaptur': {
            'handlers': ['console', 'file_prod'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}