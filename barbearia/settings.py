from pathlib import Path
from datetime import timedelta
import os
import dj_database_url

# Caminho base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# Configuração da chave secreta
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'chave-de-desenvolvimento')

# Modo de depuração (Ativa em desenvolvimento, desativa em produção)
DEBUG = os.getenv('DJANGO_DEVELOPMENT', 'False') == 'True'

# Hosts permitidos
ALLOWED_HOSTS = [
    '127.0.0.1', 
    'localhost', 
    'sua-barbearia.com', 
    'www.sua-barbearia.com',
    'barbearia-rd-a3b518df45e1.herokuapp.com'
]

# Aplicações instaladas
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'agendamentos',
    'corsheaders',
    'sslserver',
]

# Middlewares
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Gerenciador de arquivos estáticos no Heroku
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Configuração de URLs
ROOT_URLCONF = 'barbearia.urls'

# Configuração de templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

# Configuração do WSGI
WSGI_APPLICATION = 'barbearia.wsgi.application'

# Configuração do banco de dados
if DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        'default': dj_database_url.config(conn_max_age=600, ssl_require=True)
    }

# Validação de senhas
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Configuração de idioma e fuso horário
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Configuração de arquivos estáticos
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]  # Para dev
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')   # Para produção
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Configuração do CORS (evita bloqueio de requisições entre frontend e backend)
CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:5500",
    "https://sua-barbearia.com",
]

# Configuração de envio de e-mails
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_FAIL_SILENTLY = True  # Evita que erro no e-mail quebre o site

# Configuração de autenticação JWT
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKEN': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# Configurações de segurança para HTTPS (forçado apenas em produção)
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
