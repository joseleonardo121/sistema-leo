from django.db import models



class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre
    
from django.db import models
from simple_history.models import HistoricalRecords  # <--- ASEGÚRATE DE IMPORTAR ESTO ARRIBA

class Producto(models.Model):
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)
    codigo = models.CharField(max_length=50, unique=True)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name='productos'
    )
    talla = models.CharField(max_length=10)
    marca = models.CharField(max_length=50)
    diseno = models.CharField(max_length=100)
    color = models.CharField(max_length=50)

    costo = models.DecimalField(max_digits=10, decimal_places=2)
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.codigo} - {self.diseno} ({self.color})"

class Ubicacion(models.Model):
    TIPO_CHOICES = (
        ('TIENDA', 'Tienda'),
        ('ALMACEN', 'Almacén'),
    )

    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} ({self.tipo})"


class Stock(models.Model):
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='stocks'
    )
    ubicacion = models.ForeignKey(
        Ubicacion,
        on_delete=models.CASCADE,
        related_name='stocks'
    )
    cantidad = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('producto', 'ubicacion')

    def __str__(self):
        return f"{self.producto} - {self.ubicacion}: {self.cantidad}"


from django.db import models
from django.contrib.auth.models import User

class Traspaso(models.Model):
    ORIGEN_CHOICES = [
        ('A', 'Almacén'),
    ]

    DESTINO_CHOICES = [
        ('S1', 'Tienda S1'),
        ('S2', 'Tienda S2'),
        ('S3', 'Tienda S3'),
    ]

    fecha = models.DateTimeField(auto_now_add=True)
    origen = models.CharField(max_length=2, choices=ORIGEN_CHOICES, default='A')
    destino = models.CharField(max_length=2, choices=DESTINO_CHOICES)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    ejecutado = models.BooleanField(default=False)

    def __str__(self):
        return f"Traspaso {self.id} → {self.destino}"
    
    @property
    def nombre_tienda(self):
        # Retorna el nombre legible de la tienda
        return dict(self.DESTINO_CHOICES).get(self.destino, self.destino)
    
class DetalleTraspaso(models.Model):
    traspaso = models.ForeignKey(Traspaso, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey('Producto', on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.producto} x {self.cantidad}"
    
    
class HistorialTraspaso(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)

    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT
    )

    origen = models.ForeignKey(
        Ubicacion,
        on_delete=models.PROTECT,
        related_name='traspasos_origen'
    )

    destino = models.ForeignKey(
        Ubicacion,
        on_delete=models.PROTECT,
        related_name='traspasos_destino'
    )

    cantidad = models.PositiveIntegerField()

    usuario = models.ForeignKey(
        User,
        on_delete=models.PROTECT
    )

    traspaso = models.ForeignKey(
        Traspaso,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.fecha} | {self.producto.codigo} | {self.origen} → {self.destino}"

from django.conf import settings

User = settings.AUTH_USER_MODEL


class PerfilUsuario(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='perfil'
    )

    ubicacion = models.ForeignKey(
        Ubicacion,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.user} - {self.ubicacion}"

class Cliente(models.Model):
    dni = models.CharField(max_length=15, blank=True, null=True, verbose_name="DNI/RUC")
    nombres = models.CharField(max_length=100, verbose_name="Nombres")
    apellidos = models.CharField(max_length=100, verbose_name="Apellidos")
    celular = models.CharField(max_length=20, verbose_name="Celular")
    correo = models.EmailField(blank=True, null=True, verbose_name="Correo Electrónico")
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['-creado']