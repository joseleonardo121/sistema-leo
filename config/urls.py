from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static

urlpatterns = [
    # 1. PANEL DE CONTROL TOTAL
    path('super-admin/', admin.site.urls),

    # 2. SISTEMA INTERNO (POS, Inventario, Cuentas)
    # Les ponemos un prefijo para que no choquen con la web pública
    path('gestion/ventas/', include('ventas.urls')),
    path('gestion/sistema/', include('core.urls')),
    path('cuentas/', include('accounts.urls')), # Aquí suelen ir login/logout

    # 3. PORTADA PÚBLICA (Lo que ve el cliente)
    # Va al final para que las rutas anteriores tengan prioridad
    path('', include('web.urls')), 
]

# Servir archivos multimedia (fotos de productos)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Esto es vital para cuando lo subas a PythonAnywhere
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)