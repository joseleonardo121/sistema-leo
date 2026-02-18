from django.db import models

# Create your models here.
from django.db import models

class ConfiguracionWeb(models.Model):
    nombre_tienda = models.CharField(max_length=100, default="Sistema LEO")
    logo = models.ImageField(upload_to='web/logo/', null=True, blank=True)
    
    # Sección Hero (Banner Principal)
    banner_titulo = models.CharField(max_length=200, default="¡Bienvenidos a nuestra tienda!")
    banner_subtitulo = models.TextField(default="Las mejores ofertas de la temporada.")
    banner_imagen = models.ImageField(upload_to='web/banners/', null=True, blank=True)
    
    # Colores
    color_primario = models.CharField(max_length=7, default="#0d6efd", help_text="Código Hexadecimal (ej: #0d6efd)")
    
    # Contacto e Información (AQUÍ ESTÁN LOS CAMBIOS)
    whatsapp = models.CharField(max_length=20, default="+51999888777")
    email = models.EmailField(max_length=100, default="contacto@tu-tienda.com")
    direccion = models.CharField(max_length=255, default="Av. Ejemplo 123, Ciudad")
    horario_atencion = models.CharField(max_length=100, default="Lunes a Sábado: 9am - 8pm")
    
    # Redes Sociales
    facebook_url = models.URLField(blank=True, null=True)
    instagram_url = models.URLField(blank=True, null=True)
    tiktok_url = models.URLField(blank=True, null=True)

    class Meta:
        verbose_name = "Configuración General de la Web"

    def __str__(self):
        return self.nombre_tienda
    
class Banner(models.Model):
    titulo = models.CharField(max_length=100, verbose_name="Título (Opcional)", blank=True)
    subtitulo = models.CharField(max_length=200, verbose_name="Subtítulo (Opcional)", blank=True)
    imagen = models.ImageField(upload_to='banners/', verbose_name="Imagen del Banner")
    orden = models.PositiveIntegerField(default=1, verbose_name="Orden de aparición")
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Banner"
        verbose_name_plural = "Banners"
        ordering = ['orden']

    def __str__(self):
        return self.titulo if self.titulo else f"Banner {self.id}"