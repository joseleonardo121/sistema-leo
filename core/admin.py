from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.safestring import mark_safe
from django.utils.html import format_html

from .models import Categoria, Producto, Ubicacion, Stock, PerfilUsuario

# ----------------------
# MODELOS CORE
# ----------------------

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre',)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('ver_miniatura', 'codigo', 'diseno', 'categoria', 'color', 'talla', 'precio',  'activo')
    list_filter = ('categoria', 'marca', 'talla', 'activo')
    search_fields = ('codigo', 'diseno', 'color', 'marca')
    
    # Control de edición en la lista principal
    def get_list_editable(self, request):
        # Si NO es superusuario, quitamos la posibilidad de editar el precio desde la lista
        if not request.user.is_superuser:
            return ()
        return ('precio', 'activo')

    # Control de campos de SÓLO LECTURA en el formulario
    def get_readonly_fields(self, request, obj=None):
        # Si NO es superusuario, todos los campos son fijos excepto la imagen
        if not request.user.is_superuser:
            return ('codigo', 'categoria', 'talla', 'marca', 'diseno', 'color', 'precio', 'activo',)
        return ()

    def get_exclude(self, request, obj=None):
        # Mantenemos oculta la fila de costo para el empleado
        if not request.user.is_superuser:
            return ('costo',)
        return None


    def get_queryset(self, request):
        self.request = request
        return super().get_queryset(request)

    def ver_miniatura(self, obj):
        if obj.imagen:
            return mark_safe(f'<img src="{obj.imagen.url}" width="50" height="50" style="object-fit: cover; border-radius: 5px;" />')
        return mark_safe('<span style="font-size: 20px;">📷</span>')
    
    ver_miniatura.short_description = 'Imagen'
@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'activo')
    list_filter = ('tipo', 'activo')
    search_fields = ('nombre',)

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('producto', 'ubicacion', 'cantidad')
    list_filter = ('ubicacion',)
    search_fields = ('producto__codigo', 'producto__diseno')

# ----------------------
# PERFIL USUARIO Y SEGURIDAD
# ----------------------

class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = 'Perfil Usuario'

class UserAdmin(BaseUserAdmin):
    inlines = (PerfilUsuarioInline,)
    list_display = ('username', 'email', 'is_staff', 'get_ubicacion')
    
    def get_ubicacion(self, obj):
        return obj.perfil.ubicacion if hasattr(obj, 'perfil') else "Sin asignar"
    get_ubicacion.short_description = 'Ubicación'

# Reiniciamos el registro de usuarios
admin.site.unregister(User)
admin.site.register(User, UserAdmin)