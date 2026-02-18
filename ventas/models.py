from django.db import models
from django.contrib.auth.models import User
from core.models import Producto, Ubicacion

from django.db import models
from django.conf import settings
from core.models import Ubicacion

User = settings.AUTH_USER_MODEL

class Venta(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='ventas'
    )
    ubicacion = models.ForeignKey(
        Ubicacion,
        on_delete=models.PROTECT
    )
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    descuento = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    total = models.DecimalField(max_digits=10, decimal_places=2)
    anulada = models.BooleanField(default=False)
    venta_origen = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='cambios'
    )

    # 🔹 NUEVO CAMPO: Asociación con Caja
    caja = models.ForeignKey(
        'Caja',
        on_delete=models.PROTECT,
        related_name='ventas',
        null=True,
        blank=True
    )

    def __str__(self):
        return f"Venta #{self.id} - {self.fecha.strftime('%d/%m/%Y')}"

class DetalleVenta(models.Model):
    venta = models.ForeignKey(
        Venta,
        on_delete=models.CASCADE,
        related_name='detalles'
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT
    )
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    def __str__(self):
        return f"{self.producto} x{self.cantidad}"
    
class PagoVenta(models.Model):
    METODOS = (
        ('EFECTIVO', 'Efectivo'),
        ('YAPE', 'Yape'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('VISA', 'Visa'),
    )

    venta = models.ForeignKey(
        Venta,
        on_delete=models.CASCADE,
        related_name='pagos'
    )
    metodo = models.CharField(max_length=20, choices=METODOS)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.metodo} - S/ {self.monto}"
    

from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL

class Caja(models.Model):
    ubicacion = models.ForeignKey(
        'core.Ubicacion',
        on_delete=models.PROTECT,
        related_name='cajas'
    )
    fecha_apertura = models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    monto_apertura = models.DecimalField(max_digits=10, decimal_places=2)
    monto_cierre = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_ventas = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    diferencia = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    abierta = models.BooleanField(default=True)
    usuario_apertura = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='cajas_abiertas'
    )
    usuario_cierre = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='cajas_cerradas',
        null=True,
        blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['ubicacion'],
                condition=models.Q(abierta=True),
                name='unica_caja_abierta_por_ubicacion'
            )
        ]

    def __str__(self):
        estado = "ABIERTA" if self.abierta else "CERRADA"
        return f"Caja {self.ubicacion} - {estado}"
