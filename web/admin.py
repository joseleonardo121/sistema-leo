from django.contrib import admin
from .models import ConfiguracionWeb

@admin.register(ConfiguracionWeb)
class ConfiguracionWebAdmin(admin.ModelAdmin):
    # Evita que el usuario cree más de una configuración
    def has_add_permission(self, request):
        return not ConfiguracionWeb.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
    
from .models import Banner

@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('id', 'titulo', 'orden', 'activo')
    list_editable = ('orden', 'activo')