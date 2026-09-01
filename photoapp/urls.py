# projeto/urls.py

from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.views.generic import RedirectView, TemplateView
# Importe staticfiles_urlpatterns para servir arquivos estáticos em desenvolvimento
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
# Não precisamos de django.conf.urls.static.static aqui se usarmos staticfiles_urlpatterns()

urlpatterns = [
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),  # 🔥 Redireciona a raiz para dashboard
    # Service Worker do painel interno servido na raiz para ter escopo '/' (PWA)
    path('sw.js', TemplateView.as_view(template_name='sw.js', content_type='application/javascript'), name='service_worker'),
    path('admin/', admin.site.urls),
    path('', include('gestcaptur.urls')),
]

# Apenas para desenvolvimento: serve arquivos de mídia e estáticos
if settings.DEBUG:
    # Use staticfiles_urlpatterns para servir arquivos estáticos de STATIC_ROOT e STATICFILES_DIRS
    urlpatterns += staticfiles_urlpatterns()
    # E para arquivos de mídia (uploads de usuário)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)    