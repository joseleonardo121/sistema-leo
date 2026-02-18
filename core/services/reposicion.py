from django.db.models import Sum
from core.models import Producto, Traspaso, DetalleTraspaso, Stock, Ubicacion
from ventas.models import DetalleVenta  # Ajusta según tu proyecto
from django.utils import timezone

def generar_reposicion(user):
    """
    Genera traspasos de reposición para todas las tiendas.
    Solo incluye productos que:
        1️⃣ Están en stock en almacén
        2️⃣ Se vendieron desde la última reposición ejecutada
        3️⃣ No tienen suficiente stock en la tienda
    """

    try:
        almacen = Ubicacion.objects.get(tipo='ALMACEN')
    except Ubicacion.DoesNotExist:
        return

    tiendas = Ubicacion.objects.filter(tipo='TIENDA', activo=True)
    productos_almacen = Stock.objects.filter(ubicacion=almacen, cantidad__gt=0)

    for tienda in tiendas:
        # Última reposición ejecutada para esta tienda
        ultima_reposicion = Traspaso.objects.filter(
            destino=tienda.nombre[:2],
            ejecutado=True
        ).order_by('-fecha').first()

        # Fecha límite para considerar ventas
        fecha_limite = ultima_reposicion.fecha if ultima_reposicion else None

        traspaso = Traspaso.objects.create(
            origen='A',
            destino=tienda.nombre[:2],
            usuario=user
        )

        for stock in productos_almacen:
            # Stock actual en la tienda
            stock_tienda = Stock.objects.filter(producto=stock.producto, ubicacion=tienda).first()
            cantidad_tienda = stock_tienda.cantidad if stock_tienda else 0

            # Cantidad vendida desde la última reposición
            ventas_query = DetalleVenta.objects.filter(
                producto=stock.producto,
                venta__ubicacion=tienda
            )
            if fecha_limite:
                ventas_query = ventas_query.filter(venta__fecha__gt=fecha_limite)

            ventas = ventas_query.aggregate(total_vendido=Sum('cantidad'))['total_vendido'] or 0

            # Cantidad a reponer
            cantidad_a_reponer = max(0, ventas - cantidad_tienda)
            if cantidad_a_reponer > 0:
                DetalleTraspaso.objects.create(
                    traspaso=traspaso,
                    producto=stock.producto,
                    cantidad=min(stock.cantidad, cantidad_a_reponer)
                )


from core.models import Traspaso, DetalleTraspaso, Stock, Ubicacion
from django.db.models import Sum

from core.models import Traspaso, DetalleTraspaso, Stock

from django.utils import timezone
from core.models import (
    Traspaso,
    DetalleTraspaso,
    Producto,
    Stock,
    HistorialTraspaso
)

def generar_traspaso_tienda_a_tienda(user, origen_tienda, destino_tienda, productos_dict):
    traspaso = Traspaso.objects.create(
        origen=origen_tienda.nombre[:2],
        destino=destino_tienda.nombre[:2],
        usuario=user
    )

    for producto_id, cantidad in productos_dict.items():
        producto = Producto.objects.get(id=producto_id)

        stock_origen = Stock.objects.filter(
            producto=producto,
            ubicacion=origen_tienda
        ).first()

        if not stock_origen or stock_origen.cantidad < cantidad:
            continue

        DetalleTraspaso.objects.create(
            traspaso=traspaso,
            producto=producto,
            cantidad=cantidad
        )

        # 🔁 mover stock (igual que antes)
        stock_origen.cantidad -= cantidad
        stock_origen.save()

        stock_destino, _ = Stock.objects.get_or_create(
            producto=producto,
            ubicacion=destino_tienda,
            defaults={'cantidad': 0}
        )
        stock_destino.cantidad += cantidad
        stock_destino.save()

        # ✅ REGISTRAR HISTORIAL (NUEVO, NO ROMPE NADA)
        HistorialTraspaso.objects.create(
            producto=producto,
            origen=origen_tienda,
            destino=destino_tienda,
            cantidad=cantidad,
            usuario=user,
            fecha=timezone.now()
        )

    return traspaso
