from django.contrib import admin
from django.urls import path, include

# --- PASO 1: AÑADIR ESTAS DOS LÍNEAS DE IMPORTACIÓN ---
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('caja/', include('caja.urls')),
    path('', include('nombredeapp.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)