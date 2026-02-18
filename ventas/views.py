from datetime import timezone
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db.models import Sum
from core.models import Producto, Stock
from core.models import Ubicacion
from ventas.services.caja import get_caja_abierta
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Venta, DetalleVenta  # Estos sí están en ventas
from core.models import Ubicacion
from .models import Caja

def es_admin(user):
    return user.is_superuser

from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from core.models import Ubicacion
from .models import Caja

# ventas/views.py
from core.models import Ubicacion
from ventas.models import Caja

def abrir_caja_admin(request):
    ubicaciones = Ubicacion.objects.all()
    # Preparamos un diccionario con tiendas que ya tienen caja abierta
    cajas_abiertas = {c.ubicacion.id for c in Caja.objects.filter(abierta=True)}

    return render(request, 'ventas/abrir_caja.html', {
        'ubicaciones': ubicaciones,
        'cajas_abiertas': cajas_abiertas,
    })


def get_caja_abierta(ubicacion):
    if not ubicacion:
        return None
    return Caja.objects.filter(
        ubicacion=ubicacion,
        abierta=True
    ).first()




from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

from ventas.models import Ubicacion


@login_required
def pos(request):
    usuario = request.user

    # Si es admin → no necesita ubicación fija
    if usuario.is_staff:
        ubicacion = None
    else:
        perfil = getattr(usuario, 'perfil', None)
        if not perfil or not perfil.ubicacion:
            messages.error(
                request,
                'Tu usuario no tiene una tienda asignada. Contacta al administrador.'
            )
            return redirect('logout')
        ubicacion = perfil.ubicacion

    ubicaciones = Ubicacion.objects.all()
    # ✅ AGREGAMOS ESTO:
    categorias = Categoria.objects.filter(activo=True) # O solo Categoria.objects.all()

    return render(
        request,
        'ventas/pos.html',
        {
            'ubicaciones': ubicaciones,
            'categorias': categorias, # ✅ AHORA SÍ LLEGAN AL HTML
        }
    )
@require_GET
def buscar_producto(request):
    # 1. Capturamos todos los posibles parámetros
    codigo = request.GET.get('codigo')
    categoria_id = request.GET.get('categoria')
    diseno = request.GET.get('diseno')
    color = request.GET.get('color')
    talla = request.GET.get('talla')
    
    # Obtenemos la ubicación del usuario para priorizar stock
    user_ubicacion_id = request.user.perfil.ubicacion.id

    # 2. Base de la búsqueda
    query = Producto.objects.filter(activo=True)

    # 3. Aplicamos filtros dinámicos
    if codigo:
        # Búsqueda por pistola o Enter (un solo resultado)
        try:
            producto = query.get(codigo=codigo)
            stocks = Stock.objects.filter(producto=producto).select_related('ubicacion')
            stock_total = 0
            detalles_stock = []
            for s in stocks:
                stock_total += s.cantidad
                if s.cantidad > 0:
                    detalles_stock.append({
                        'ubicacion_id': s.ubicacion.id,
                        'ubicacion_nombre': s.ubicacion.nombre,
                        'cantidad': s.cantidad
                    })
            return JsonResponse({
                'success': True,
                'producto': {
                    'id': producto.id,
                    'nombre': f"{producto.diseno} - {producto.color} ({producto.talla})",
                    'precio': float(producto.precio),
                    'stock_total': stock_total,
                    'detalles_stock': detalles_stock
                }
            })
        except Producto.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Producto no encontrado'})

    # 4. Si no hay código, es búsqueda por filtros (devuelve lista)
    if categoria_id:
        query = query.filter(categoria_id=categoria_id)
    if diseno:
        query = query.filter(diseno__icontains=diseno)
    if color:
        query = query.filter(color__icontains=color)
    if talla:
        query = query.filter(talla__icontains=talla)

    # Limitamos y obtenemos resultados
    productos = query.distinct()[:15]
    resultados = []

    for p in productos:
        # Stock en la tienda actual para la lista de resultados
        stock_local = Stock.objects.filter(producto=p, ubicacion_id=user_ubicacion_id).first()
        cant_local = stock_local.cantidad if stock_local else 0
        
        resultados.append({
            'id': p.id,
            'codigo': p.codigo,
            'diseno': p.diseno,
            'color': p.color,
            'talla': p.talla,
            'precio': float(p.precio),
            'stocks': [cant_local] # Para que el JS lo lea correctamente
        })

    return JsonResponse(resultados, safe=False)
from decimal import Decimal
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db import transaction

from core.models import Producto, Stock
from .models import Venta, DetalleVenta, PagoVenta, Caja
from ventas.services.caja import get_caja_abierta


@require_POST
@login_required
@transaction.atomic
def finalizar_venta(request):
    try:
        data = json.loads(request.body)
        usuario = request.user
        perfil = getattr(usuario, 'perfil', None)

        if not perfil or not perfil.ubicacion:
            return JsonResponse({'success': False, 'message': 'Usuario sin tienda asignada'})

        ubicacion = perfil.ubicacion
        caja_abierta = get_caja_abierta(ubicacion)
        if not caja_abierta:
            return JsonResponse({'success': False, 'message': 'No hay caja abierta en esta tienda'})

        productos = data.get('productos', [])
        pagos = data.get('pagos', [])
        venta_origen_id = data.get('venta_origen')
        # Ahora recibimos una lista de objetos: [{'detalle_id': 1, 'cantidad': 1}, ...]
        devoluciones = data.get('devoluciones', []) 

        if not productos:
            raise Exception('Carrito vacío')
        if not pagos:
            raise Exception('Debe registrar un método de pago')

        # ===== 1. CARGAR VENTA ORIGEN Y DEVOLVER STOCK PARCIAL =====
        venta_origen = None
        if venta_origen_id:
            venta_origen = Venta.objects.select_for_update().get(id=venta_origen_id)
            
            if not devoluciones:
                raise Exception('No se seleccionaron productos para devolver de la boleta anterior.')

            for dev in devoluciones:
                # Buscamos el detalle específico de la boleta anterior
                detalle_antiguo = DetalleVenta.objects.get(id=dev['detalle_id'])
                cantidad_a_devolver = int(dev['cantidad'])

                # Devolvemos al stock solo la cantidad seleccionada
                stock_reingreso = Stock.objects.select_for_update().get(
                    producto=detalle_antiguo.producto,
                    ubicacion=ubicacion
                )
                stock_reingreso.cantidad += cantidad_a_devolver
                stock_reingreso.save()

            # Nota de auditoría (opcional)
            if hasattr(venta_origen, 'observaciones'):
                venta_origen.observaciones = f"Se realizó un cambio parcial/total en esta boleta."
                venta_origen.save()

        # ===== 2. VALIDAR STOCK DE NUEVOS PRODUCTOS + CALCULAR TOTAL =====
        total_nuevo_carrito = Decimal('0.00')
        for item in productos:
            producto = Producto.objects.select_for_update().get(id=item['id'])
            cantidad = Decimal(str(item['cantidad']))
            precio = Decimal(str(item['precio']))

            stock = Stock.objects.select_for_update().get(
                producto=producto,
                ubicacion=ubicacion
            )
            if stock.cantidad < cantidad:
                raise Exception(f'Stock insuficiente para {producto}.')

            total_nuevo_carrito += cantidad * precio

        # ===== 3. CREAR NUEVA VENTA =====
        venta = Venta.objects.create(
            usuario=usuario,
            ubicacion=ubicacion,
            subtotal=total_nuevo_carrito,
            descuento=0,
            total=total_nuevo_carrito,
            venta_origen=venta_origen,
            caja=caja_abierta
        )

        # ===== 4. DESCONTAR STOCK FINAL + DETALLE =====
        for item in productos:
            producto = Producto.objects.get(id=item['id'])
            cantidad = int(item['cantidad'])
            precio = Decimal(str(item['precio']))

            stock = Stock.objects.get(producto=producto, ubicacion=ubicacion)
            stock.cantidad -= cantidad
            stock.save()

            DetalleVenta.objects.create(
                venta=venta,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=precio,
                subtotal=Decimal(str(cantidad)) * precio
            )

        # ===== 5. REGISTRAR PAGOS (Solo el monto real recibido) =====
        total_pagos_efectivos = sum(Decimal(str(p['monto'])) for p in pagos)
        for p in pagos:
            monto_pago = Decimal(str(p['monto']))
            PagoVenta.objects.create(
                venta=venta,
                metodo=p['metodo'],
                monto=monto_pago
            )

        # ===== 6. ACTUALIZAR CAJA =====
        caja_abierta.total_ventas += total_pagos_efectivos
        caja_abierta.save()

        return JsonResponse({
            'success': True, 
            'venta_id': venta.id,
            'message': 'Cambio/Venta parcial registrada con éxito'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
from django.shortcuts import render, get_object_or_404
from .models import Venta

def historial_ventas(request):

    ventas = Venta.objects.all().order_by('-fecha')

    boleta = request.GET.get('boleta')

    if boleta:
        ventas = ventas.filter(id=boleta)

    return render(request, 'ventas/historial.html', {
        'ventas': ventas
    })

def boleta_venta(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id)
    return render(request, 'ventas/boleta.html', {
        'venta': venta
    })


from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

@transaction.atomic
def anular_venta(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id)

    if venta.anulada:
        messages.warning(request, 'La venta ya está anulada')
        return redirect('historial_ventas')

    # 1. Devolver Stock
    for detalle in venta.detalles.all():
        stock = Stock.objects.select_for_update().get(
            producto=detalle.producto,
            ubicacion=venta.ubicacion
        )
        stock.cantidad += detalle.cantidad
        stock.save()

    # 2. Descontar dinero de la Caja (Solo si la caja sigue abierta)
    # Importante: Restamos la suma de sus PAGOS, no el venta.total
    caja = get_caja_abierta(venta.ubicacion)
    if caja:
        # Sumamos cuánto dinero real entró en esta boleta
        total_pagado = venta.pagos.aggregate(Sum('monto'))['monto__sum'] or 0
        caja.total_ventas -= total_pagado
        caja.save()

    # 3. Marcar como anulada
    venta.anulada = True
    venta.save()

    messages.success(request, f'Venta #{venta.id} anulada. S/ {total_pagado} restados de caja.')
    return redirect('historial_ventas')

def cambio_venta(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id)

    if venta.anulada:
        messages.warning(request, 'No se puede cambiar una venta anulada')
        return redirect('historial_ventas')

    # Detalles de la venta original
    detalles = venta.detalles.all()

    productos = []
    for d in detalles:
        productos.append({
            'detalle_id': d.id,  # <--- CRUCIAL: Para saber qué línea devolver
            'id': d.producto.id,
            'nombre': str(d.producto),
            'precio': float(d.precio_unitario),
            'cantidad': d.cantidad
        })

    return render(request, 'ventas/pos.html', {
        'ubicaciones': Ubicacion.objects.all(),
        'cambio': True,
        'venta_origen': venta.id,
        'productos_cambio': productos,
        'total_origen': float(venta.total)
    })

from django.utils import timezone

@user_passes_test(es_admin)
def abrir_caja(request):
    if request.method == 'POST':
        ubicacion_id = request.POST.get('ubicacion')
        monto_apertura = request.POST.get('monto_apertura')

        if not ubicacion_id or not monto_apertura:
            return render(request, 'ventas/abrir_caja.html', {
                'error': 'Todos los campos son obligatorios'
            })

        ubicacion = Ubicacion.objects.get(id=ubicacion_id)

        hoy = timezone.localdate()

        # 🔒 VALIDAR: solo 1 caja por día por tienda
        existe_caja_hoy = Caja.objects.filter(
            ubicacion=ubicacion,
            fecha_apertura__date=hoy
        ).exists()

        if existe_caja_hoy:
            return render(request, 'ventas/abrir_caja.html', {
                'error': 'Ya se abrió una caja hoy para esta tienda. No se puede abrir otra.'
            })

        # 🔒 VALIDAR: si hay caja abierta (doble protección)
        if get_caja_abierta(ubicacion):
            return render(request, 'ventas/abrir_caja.html', {
                'error': 'Ya existe una caja abierta para esta tienda.'
            })

        Caja.objects.create(
            ubicacion=ubicacion,
            monto_apertura=monto_apertura,
            usuario_apertura=request.user
        )

        return redirect('pos')

    ubicaciones = Ubicacion.objects.filter(activo=True)

    return render(request, 'ventas/abrir_caja.html', {
        'ubicaciones': ubicaciones
    })


@user_passes_test(es_admin)
def cerrar_caja(request, caja_id):
    caja = Caja.objects.get(id=caja_id, abierta=True)

    # --- 🔹 CORRECCIÓN CRÍTICA PARA EL ARQUEO 🔹 ---
    # Sumamos solo el dinero real que entró por ventas asociadas a esta caja
    total_ventas = PagoVenta.objects.filter(
        venta__caja=caja,
        venta__anulada=False
    ).aggregate(
        total_real=Sum('monto')
    )['total_real'] or Decimal('0.00')
    # -----------------------------------------------

    # El sistema sugiere: Monto con el que abrió + Dinero real que entró
    total_general = Decimal(str(caja.monto_apertura)) + Decimal(str(total_ventas))

    if request.method == 'POST':
        monto_cierre = request.POST.get('monto_cierre')

        if not monto_cierre:
            return render(request, 'ventas/cerrar_caja.html', {
                'caja': caja,
                'total_ventas': total_ventas,
                'total_general': total_general,
                'error': 'Debe ingresar el monto de cierre'
            })

        monto_cierre = Decimal(str(monto_cierre))

        # Calculamos la diferencia sobre el total real
        diferencia = monto_cierre - total_general

        caja.monto_cierre = monto_cierre
        caja.total_ventas = total_ventas # Guardamos el valor real en la caja
        caja.diferencia = diferencia
        caja.fecha_cierre = timezone.now()
        caja.abierta = False
        caja.usuario_cierre = request.user
        caja.save()

        return redirect('pos')

    return render(request, 'ventas/cerrar_caja.html', {
        'caja': caja,
        'total_ventas': total_ventas,
        'total_general': total_general
    })

@user_passes_test(es_admin)
def historial_cajas(request):

    cajas = Caja.objects.all().order_by('-fecha_apertura')

    # Filtros
    ubicacion_id = request.GET.get('ubicacion')
    fecha_inicio = request.GET.get('inicio')
    fecha_fin = request.GET.get('fin')

    if ubicacion_id:
        cajas = cajas.filter(ubicacion_id=ubicacion_id)

    if fecha_inicio and fecha_fin:
        cajas = cajas.filter(
            fecha_apertura__date__range=[fecha_inicio, fecha_fin]
        )

    ubicaciones = Ubicacion.objects.filter(tipo='TIENDA')

    return render(request, 'ventas/historial_cajas.html', {
        'cajas': cajas,
        'ubicaciones': ubicaciones
    })






from django.db.models import Sum
from .models import Caja, Venta
from core.models import Ubicacion

@login_required
def panel_cajas(request):
    # Solo mostramos ubicaciones tipo TIENDA
    ubicaciones = Ubicacion.objects.filter(tipo='TIENDA')
    data = []

    for u in ubicaciones:
        caja = Caja.objects.filter(
            ubicacion=u,
            abierta=True
        ).first()

        total_ventas = 0

        if caja:
            # --- 🔹 CORRECCIÓN AQUÍ 🔹 ---
            # En lugar de sumar Venta.objects... Sum('total')
            # Sumamos los montos de PagoVenta asociados a esa caja y tienda
            total_ventas = PagoVenta.objects.filter(
                venta__caja=caja,
                venta__ubicacion=u,
                venta__anulada=False
            ).aggregate(
                total_real=Sum('monto')
            )['total_real'] or 0
            # -----------------------------

        data.append({
            'ubicacion': u,
            'caja': caja,
            'total_ventas': total_ventas  # Ahora este monto será el dinero real (ej. 110)
        })

    return render(request, 'ventas/panel_cajas.html', {
        'data': data
    })
from django.utils import timezone
from django.db.models import Sum, Count

@login_required
def dashboard_tienda(request):
    usuario = request.user

    perfil = getattr(usuario, 'perfil', None)
    if not perfil or not perfil.ubicacion:
        messages.error(request, 'No tienes tienda asignada')
        return redirect('pos')

    ubicacion = perfil.ubicacion
    hoy = timezone.now().date()

    # Filtramos las ventas no anuladas de hoy
    ventas_query = Venta.objects.filter(
        ubicacion=ubicacion,
        fecha__date=hoy,
        anulada=False
    )

    # --- 🔹 CORRECCIÓN DE TOTAL (PAGOS REALES) 🔹 ---
    # Sumamos los montos de la tabla PagoVenta asociados a las ventas de hoy
    total = PagoVenta.objects.filter(
        venta__in=ventas_query
    ).aggregate(total_pagos=Sum('monto'))['total_pagos'] or 0
    # -----------------------------------------------

    cantidad = ventas_query.count()
    ultimas = ventas_query.order_by('-fecha')[:10]

    return render(request, 'ventas/dashboard_tienda.html', {
        'ubicacion': ubicacion,
        'total': total,      # Ahora mostrará 110 (100 de la original + 10 del cambio)
        'cantidad': cantidad,
        'ventas': ultimas
    })


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.db.models import Sum, Count
from core.models import Ubicacion
from .models import Venta, Caja, PagoVenta

from django.db.models import Sum
from django.utils import timezone

@login_required
def ver_ventas_tienda(request, ubicacion_id):
    hoy = timezone.localdate()
    ubicacion = get_object_or_404(Ubicacion, id=ubicacion_id)

    caja = Caja.objects.filter(
        ubicacion=ubicacion,
        abierta=True
    ).first()

    ventas = Venta.objects.filter(
        ubicacion=ubicacion,
        fecha__date=hoy,
        anulada=False
    ).order_by('-fecha')

    # --- 🔹 CORRECCIÓN AQUÍ 🔹 ---
    # En lugar de sumar el "total" de las ventas, sumamos los pagos reales 
    # de esas ventas para obtener el Total Vendido real del día.
    pagos = PagoVenta.objects.filter(venta__in=ventas)
    total_vendido = pagos.aggregate(Sum('monto'))['monto__sum'] or 0
    # -----------------------------

    cantidad_ventas = ventas.count()

    # Desglose por método de pago
    total_efectivo = pagos.filter(metodo='EFECTIVO').aggregate(Sum('monto'))['monto__sum'] or 0
    total_yape = pagos.filter(metodo__in=['YAPE', 'PLIN']).aggregate(Sum('monto'))['monto__sum'] or 0
    total_transferencia = pagos.filter(metodo='TRANSFERENCIA').aggregate(Sum('monto'))['monto__sum'] or 0
    total_tarjeta = pagos.filter(metodo='TARJETA').aggregate(Sum('monto'))['monto__sum'] or 0

    monto_apertura = caja.monto_apertura if caja else 0
    total_en_caja = monto_apertura + total_efectivo 

    return render(request, 'ventas/ver_ventas_tienda.html', {
        'ubicacion': ubicacion,
        'ventas': ventas,
        'total_vendido': total_vendido, # Ahora sumará 100 + 10 = 110
        'cantidad_ventas': cantidad_ventas,
        'monto_apertura': monto_apertura,
        'total_en_caja': total_en_caja,
        'caja': caja,
        'total_efectivo': total_efectivo,
        'total_yape': total_yape,
        'total_transferencia': total_transferencia,
        'total_tarjeta': total_tarjeta,
    })
@login_required
def mis_ventas_hoy(request):
    ubicacion = request.user.perfil.ubicacion
    return redirect('ver_ventas_tienda', ubicacion.id)


from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from ventas.models import Caja

@user_passes_test(lambda u: u.is_superuser)
def reporte_mensual(request):
    mes = int(request.GET.get('mes', timezone.now().month))
    anio = int(request.GET.get('anio', timezone.now().year))

    # Obtenemos las cajas cerradas del periodo
    cajas = Caja.objects.filter(
        fecha_cierre__year=anio,
        fecha_cierre__month=mes,
        abierta=False
    )

    # Agrupamos por tienda sumando el total_ventas (que ya es el valor real neto)
    resumen_raw = cajas.values(
        'ubicacion__nombre'
    ).annotate(
        total=Sum('total_ventas') # Este campo ya fue corregido en cerrar_caja
    ).order_by('ubicacion__nombre')

    resumen = []
    total_general = Decimal('0.00')
    total_ganancia = Decimal('0.00')

    for r in resumen_raw:
        total = r['total'] or Decimal('0.00')
        # Calculamos la utilidad sobre el dinero real que entró
        ganancia = (total * Decimal('0.60')).quantize(Decimal('0.01'))

        resumen.append({
            'tienda': r['ubicacion__nombre'],
            'total': total,
            'ganancia': ganancia
        })

        total_general += total
        total_ganancia += ganancia

    return render(request, 'ventas/reporte_mensual.html', {
        'resumen': resumen,
        'total_general': total_general,
        'total_ganancia': total_ganancia,
        'mes': mes,
        'anio': anio
    })
from django.db.models import Sum
from django.db.models.functions import ExtractMonth

from decimal import Decimal
from django.db.models import Sum
from django.db.models.functions import ExtractMonth
from django.utils import timezone
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from ventas.models import Caja


@user_passes_test(lambda u: u.is_superuser)
def reporte_anual(request):
    anio = int(request.GET.get('anio', timezone.now().year))

    # Filtramos cajas cerradas del año
    cajas = Caja.objects.filter(
        fecha_cierre__year=anio,
        abierta=False
    )

    resumen = {}
    tiendas = Ubicacion.objects.filter(tipo='TIENDA', activo=True)

    for tienda in tiendas:
        cajas_tienda = cajas.filter(ubicacion=tienda)
        
        # --- 🔹 LA CLAVE ESTÁ AQUÍ 🔹 ---
        # Agrupamos por mes y sumamos total_ventas (que ya es el valor neto real)
        meses_raw = cajas_tienda.annotate(
            mes_num=ExtractMonth('fecha_cierre')
        ).values('mes_num').annotate(
            total=Sum('total_ventas') # Usamos el monto real guardado al cerrar caja
        ).order_by('mes_num')

        meses = []
        total_general = Decimal('0.00')
        total_ganancia = Decimal('0.00')

        # Diccionario para nombres de meses (opcional pero ayuda al HTML)
        nombres_meses = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto', 
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }

        for m in meses_raw:
            total = m['total'] or Decimal('0.00')
            # La ganancia del 60% se calcula sobre el ingreso real neto
            ganancia = (total * Decimal('0.60')).quantize(Decimal('0.01'))

            meses.append({
                'mes': nombres_meses.get(m['mes_num'], f"Mes {m['mes_num']}"),
                'total': total,
                'ganancia': ganancia
            })

            total_general += total
            total_ganancia += ganancia

        resumen[tienda.nombre] = {
            'meses': meses,
            'total_general': total_general,
            'total_ganancia': total_ganancia
        }

    return render(request, 'ventas/reporte_anual.html', {
        'resumen': resumen,
        'anio': anio
    })
import json
from django.http import JsonResponse
from core.models import Cliente # Importamos Cliente desde core

def crear_cliente_ajax(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nuevo_c = Cliente.objects.create(
                dni=data.get('dni'),
                nombres=data.get('nombres'),
                apellidos='', # Dejamos apellidos vacío o lo puedes separar después
                celular=data.get('celular'),
            )
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

from django.db.models import Count, Sum
from datetime import timedelta
from django.utils import timezone
from core.models import Producto, Stock, Categoria
from ventas.models import DetalleVenta

@login_required
def sugerido_compras(request):
    # 1. Obtener el umbral del navegador (por defecto 2)
    umbral = int(request.GET.get('umbral', 2))
    
    # 2. Traer todas las ubicaciones tipo TIENDA para las columnas S1, S2...
    tiendas = Ubicacion.objects.filter(tipo='TIENDA').order_by('id')
    
    # 3. Filtrar productos con stock bajo en CUALQUIERA de las tiendas
    # Usamos distinct para no repetir el mismo producto varias veces
    productos_id = Stock.objects.filter(
        cantidad__lte=umbral, 
        ubicacion__tipo='TIENDA'
    ).values_list('producto_id', flat=True).distinct()

    pedidos = []
    
    # 4. Construir la data detallada para cada producto
    for p_id in productos_id:
        # Obtenemos el objeto producto con su marca
        from .models import Producto # Asegúrate de importar tu modelo
        prod = Producto.objects.select_related('marca', 'categoria').get(id=p_id)
        
        # --- BUSCAR STOCK EN ALMACÉN ---
        alm = Stock.objects.filter(producto=prod, ubicacion__tipo='ALMACEN').first()
        cant_almacen = alm.cantidad if alm else 0
        
        # --- BUSCAR STOCK EN CADA TIENDA (S1, S2, S3...) ---
        lista_stocks_sedes = []
        for t in tiendas:
            st_tienda = Stock.objects.filter(producto=prod, ubicacion=t).first()
            cant_t = st_tienda.cantidad if st_tienda else 0
            lista_stocks_sedes.append({
                'nombre': t.nombre,
                'cantidad': cant_t
            })

        # 5. Agregamos todo al diccionario que lee el HTML
        pedidos.append({
            'producto': prod,
            'stock_almacen': cant_almacen,
            'stocks_por_tienda': lista_stocks_sedes,
            # Forzamos que 'cantidad' sea la suma de tiendas para las cards de arriba
            'cantidad': sum(item['cantidad'] for item in lista_stocks_sedes) 
        })

    return render(request, 'ventas/planificador_compras.html', {
        'pedidos': pedidos,
        'tiendas_lista': tiendas,
        'umbral': umbral
    })


from django.http import JsonResponse
from core.models import Stock, Ubicacion, Producto, HistorialTraspaso

@login_required
def traspaso_pos_rapido(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        
        producto_id = data.get('producto_id')
        origen_id = data.get('origen_id')
        # La tienda destino es la del usuario actual
        destino = request.user.perfil.ubicacion 
        cantidad = int(data.get('cantidad', 1))

        if not destino:
            return JsonResponse({'success': False, 'message': 'Tu usuario no tiene una tienda asignada.'})

        try:
            producto = Producto.objects.get(id=producto_id)
            stock_origen = Stock.objects.get(producto_id=producto_id, ubicacion_id=origen_id)

            if stock_origen.cantidad < cantidad:
                return JsonResponse({'success': False, 'message': 'La tienda origen ya no tiene stock suficiente.'})

            # 1. Restar origen
            stock_origen.cantidad -= cantidad
            stock_origen.save()

            # 2. Sumar destino
            stock_destino, _ = Stock.objects.get_or_create(
                producto=producto, 
                ubicacion=destino, 
                defaults={'cantidad': 0}
            )
            stock_destino.cantidad += cantidad
            stock_destino.save()

            # 3. Registrar en historial
            HistorialTraspaso.objects.create(
                producto=producto,
                origen_id=origen_id,
                destino=destino,
                cantidad=cantidad,
                usuario=request.user
            )

            return JsonResponse({'success': True, 'nuevo_stock': stock_destino.cantidad})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})