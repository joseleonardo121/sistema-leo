import datetime
from pyexpat.errors import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Case, When, IntegerField, Sum
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from accounts import models

from .models import HistorialTraspaso, Producto, Stock, Ubicacion, Categoria, Traspaso
from core.services.reposicion import generar_reposicion
from core.models import DetalleTraspaso       # tu modelo de traspasos sigue igual
from ventas.models import DetalleVenta       # importa de donde esté tu modelo de ventas

##################################
# PRODUCTOS
##################################
from django.shortcuts import render
from django.db.models import Sum, Q
from .models import Producto, Categoria

def productos(request):
    # Capturamos todos los filtros
    codigo = request.GET.get('codigo')
    categoria = request.GET.get('categoria')
    talla = request.GET.get('talla')
    diseno = request.GET.get('diseno')
    color = request.GET.get('color')
    marca = request.GET.get('marca')

    # Base QuerySet con la suma de stock
    productos = Producto.objects.annotate(total_stock=Sum('stocks__cantidad'))

    # Aplicamos filtros si existen
    if codigo:
        productos = productos.filter(codigo__icontains=codigo)
    if categoria:
        productos = productos.filter(categoria_id=categoria)
        
    # --- CAMBIO AQUÍ: Filtro de talla EXACTO (Evita que L traiga XL) ---
    if talla:
        productos = productos.filter(talla__iexact=talla)
        
    if diseno:
        productos = productos.filter(diseno__icontains=diseno)
    if color:
        productos = productos.filter(color__icontains=color)
    if marca:
        productos = productos.filter(marca__icontains=marca)

    productos = productos.order_by('-id')
    
    return render(request, 'core/productos.html', {
        'productos': productos,
        # --- CAMBIO AQUÍ: Categorías ordenadas de A a Z ---
        'categorias': Categoria.objects.filter(activo=True).order_by('nombre'),
        'codigo': codigo 
    })

from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages  # Añadimos esto
from .models import Categoria, Producto
import urllib.parse

def crear_producto(request):
    categorias = Categoria.objects.all()
    
    if request.method == 'POST':
        try:
            # Intentamos crear el producto
            Producto.objects.create(
                codigo=request.POST['codigo'],
                categoria_id=request.POST['categoria'],
                talla=request.POST['talla'],
                marca=request.POST['marca'],
                diseno=request.POST['diseno'],
                color=request.POST['color'],
                costo=request.POST['costo'],
                precio=request.POST['precio'],
            )

            # Si se presionó "Guardar y clonar"
            if request.POST.get('clonar') == 'true':
                params = urllib.parse.urlencode({
                    'cat': request.POST['categoria'],
                    't': request.POST['talla'],
                    'm': request.POST['marca'],
                    'd': request.POST['diseno'],
                    'c': request.POST['color'],
                    'cos': request.POST['costo'],
                    'pre': request.POST['precio'],
                })
                return redirect(f"{reverse('crear_producto')}?{params}")

            return redirect('productos')

        except Exception as e:
            # Si el código ya existe o hay otro error, enviamos un mensaje
            messages.error(request, f"Error: El código '{request.POST['codigo']}' ya está registrado o los datos son inválidos.")
            # Mantenemos los datos que el usuario ya escribió para que no los pierda
            datos_error = request.POST 
            return render(request, 'core/crear_producto.html', {
                'categorias': categorias,
                'datos': {
                    'categoria': datos_error.get('categoria'),
                    'talla': datos_error.get('talla'),
                    'marca': datos_error.get('marca'),
                    'diseno': datos_error.get('diseno'),
                    'color': datos_error.get('color'),
                    'costo': datos_error.get('costo'),
                    'precio': datos_error.get('precio'),
                }
            })

    # Lógica GET normal
    datos_previos = {
        'categoria': request.GET.get('cat'),
        'talla': request.GET.get('t'),
        'marca': request.GET.get('m'),
        'diseno': request.GET.get('d'),
        'color': request.GET.get('c'),
        'costo': request.GET.get('cos'),
        'precio': request.GET.get('pre'),
    }

    return render(request, 'core/crear_producto.html', {
        'categorias': categorias,
        'datos': datos_previos
    })

@login_required
def eliminar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    producto.activo = False
    producto.save()
    messages.success(request, f'El producto "{producto.codigo}" fue eliminado correctamente.')
    return redirect('productos')

def desactivar_producto(request, producto_id):
    producto = Producto.objects.get(id=producto_id)
    producto.activo = False
    producto.save()
    return redirect('productos')

def toggle_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    producto.activo = not producto.activo
    producto.save()
    return redirect('productos')

def productos_inactivos(request):
    productos = Producto.objects.filter(activo=False).order_by('-id')
    return render(request, 'core/productos_inactivos.html', {
        'productos': productos
    })

def editar_producto(request, pk):
    producto = Producto.objects.get(pk=pk)
    if request.method == 'POST':
        producto.codigo = request.POST['codigo']
        producto.categoria_id = request.POST['categoria']
        producto.marca = request.POST['marca']
        producto.diseno = request.POST['diseno']
        producto.color = request.POST['color']
        producto.talla = request.POST['talla']
        producto.costo = request.POST['costo']
        producto.precio = request.POST['precio']
        producto.save()
        return redirect('productos')
    categorias = Categoria.objects.all()
    return render(request, 'core/editar_producto.html', {
        'producto': producto,
        'categorias': categorias
    })


##################################
# STOCK
##################################

from django.shortcuts import render
from django.db.models import Case, When, IntegerField
from .models import Ubicacion, Producto, Stock, Categoria

def stock(request):
    ubicaciones = Ubicacion.objects.filter(activo=True).annotate(
        orden_tipo=Case(
            When(tipo='TIENDA', then=1),
            When(tipo='ALMACEN', then=2),
            output_field=IntegerField()
        )
    ).order_by('orden_tipo', 'nombre')

    productos = Producto.objects.filter(activo=True)

    # Captura de filtros
    codigo = request.GET.get('codigo')
    categoria = request.GET.get('categoria')
    talla = request.GET.get('talla')
    diseno = request.GET.get('diseno')
    color = request.GET.get('color')
    marca = request.GET.get('marca')

    # Aplicación de filtros
    if codigo:
        productos = productos.filter(codigo__icontains=codigo)
    if categoria:
        productos = productos.filter(categoria_id=categoria)
    
    # --- CAMBIO 1: Filtro de talla exacto ---
    if talla:
        # Cambiamos __icontains por __iexact para que "L" no traiga "XL"
        productos = productos.filter(talla__iexact=talla)
    
    if diseno:
        productos = productos.filter(diseno__icontains=diseno)
    if color:
        productos = productos.filter(color__icontains=color)
    if marca:
        productos = productos.filter(marca__icontains=marca)

    stock_data = []
    for producto in productos:
        fila = {
            'producto': producto,
            'cantidades': {},
            'total': 0
        }
        for ubicacion in ubicaciones:
            stock_obj = Stock.objects.filter(producto=producto, ubicacion=ubicacion).first()
            cantidad = stock_obj.cantidad if stock_obj else 0
            fila['cantidades'][ubicacion.id] = cantidad
            fila['total'] += cantidad
        stock_data.append(fila)

    return render(request, 'core/stock.html', {
        'ubicaciones': ubicaciones,
        'stock_data': stock_data,
        # --- CAMBIO 2: Categorías ordenadas de A a Z ---
        'categorias': Categoria.objects.filter(activo=True).order_by('nombre'),
    })

def crear_stock(request):
    producto = None
    codigo = request.GET.get('codigo')
    ubicaciones = Ubicacion.objects.all()
    if codigo:
        producto = Producto.objects.filter(codigo=codigo).first()
    if request.method == 'POST':
        producto_id = request.POST['producto']
        for u in ubicaciones:
            cantidad = int(request.POST.get(f'cantidad_{u.id}', 0))
            if cantidad > 0:
                Stock.objects.update_or_create(
                    producto_id=producto_id,
                    ubicacion=u,
                    defaults={'cantidad': cantidad}
                )
        return redirect('stock')
    return render(request, 'core/crear_stock.html', {
        'producto': producto,
        'codigo': codigo,
        'ubicaciones': ubicaciones
    })


def stock_masivo_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    ubicaciones = Ubicacion.objects.filter(activo=True)
    
    if request.method == 'POST':
        for ubicacion in ubicaciones:
            cantidad = request.POST.get(f'ubicacion_{ubicacion.id}')
            cantidad = int(cantidad) if cantidad else 0
            
            stock, created = Stock.objects.get_or_create(
                producto=producto,
                ubicacion=ubicacion,
                defaults={'cantidad': cantidad}
            )
            if not created:
                stock.cantidad = cantidad
                stock.save()
        
        # Redirección al catálogo de productos como solicitaste
        return redirect('productos')
        
    stock_actual = {s.ubicacion_id: s.cantidad for s in Stock.objects.filter(producto=producto)}
    
    return render(request, 'core/stock_masivo.html', {
        'producto': producto,
        'ubicaciones': ubicaciones,
        'stock_actual': stock_actual
    })

##################################
# UBICACIONES
##################################

def crear_ubicacion(request):
    if request.method == 'POST':
        Ubicacion.objects.create(
            nombre=request.POST['nombre'],
            tipo=request.POST['tipo']
        )
        return redirect('ubicaciones')
    return render(request, 'core/crear_ubicacion.html')


def ubicaciones(request):
    ubicaciones = Ubicacion.objects.all()
    return render(request, 'core/ubicaciones.html', {
        'ubicaciones': ubicaciones
    })


def eliminar_ubicacion(request, id):
    ubicacion = get_object_or_404(Ubicacion, id=id)
    ubicacion.delete()
    return redirect('ubicaciones')


##################################
# CATEGORIAS
##################################

def categorias(request):
    categorias = Categoria.objects.all()
    q = request.GET.get('q')
    if q:
        categorias = categorias.filter(nombre__icontains=q)
    return render(request, 'core/categorias.html', {
        'categorias': categorias
    })


def crear_categoria(request):
    if request.method == 'POST':
        Categoria.objects.create(
            nombre=request.POST['nombre']
        )
        return redirect('categorias')
    return render(request, 'core/crear_categoria.html')


def eliminar_categoria(request, id):
    categoria = get_object_or_404(Categoria, id=id)
    if request.method == 'POST':
        categoria.delete()
    return redirect('categorias')


@csrf_exempt
def crear_categoria_ajax(request):
    import json
    data = json.loads(request.body)
    categoria = Categoria.objects.create(nombre=data['nombre'])
    return JsonResponse({
        'id': categoria.id,
        'nombre': categoria.nombre
    })


##################################
# REPOSICIÓN / TRASPASOS
##################################

@login_required
def generar_reposicion_view(request):
    # 1️⃣ Eliminar reposiciones pendientes antiguas
    Traspaso.objects.filter(ejecutado=False).delete()

    # 2️⃣ Generar reposición según el stock actual y ventas
    generar_reposicion(request.user)  # Esta función ahora filtra solo productos vendidos

    # 3️⃣ Redirigir a pendientes
    return redirect('traspasos_pendientes')


@login_required
def traspasos_pendientes(request):
    traspasos = Traspaso.objects.filter(ejecutado=False).order_by('destino', 'fecha')
    tiendas = Ubicacion.objects.filter(tipo='TIENDA', activo=True).order_by('nombre')
    return render(request, 'core/reposicion/pendientes.html', {
        'traspasos': traspasos,
        'tiendas': tiendas
    })
from django.utils import timezone

@login_required
def ejecutar_traspaso(request, traspaso_id):
    # 1. Traer el traspaso
    traspaso = get_object_or_404(Traspaso, id=traspaso_id, ejecutado=False)

    # 2. Obtener las ubicaciones por nombre (limpiando espacios)
    nombre_destino = traspaso.nombre_tienda.strip()
    
    try:
        # Buscamos la tienda destino por nombre
        tienda_destino = Ubicacion.objects.get(nombre__icontains=nombre_destino)
        # Buscamos el almacén (asumiendo que tienes uno creado con tipo 'ALMACEN')
        tienda_origen = Ubicacion.objects.filter(tipo='ALMACEN').first()
        
        if not tienda_origen:
            messages.error(request, "No se encontró una ubicación de tipo ALMACÉN.")
            return redirect('traspasos_pendientes')

    except Ubicacion.DoesNotExist:
        messages.error(request, f"No existe la ubicación: {nombre_destino}")
        return redirect('traspasos_pendientes')

    # 3. Procesar productos
    detalles = traspaso.detalles.all()
    for detalle in detalles:
        stock_origen, _ = Stock.objects.get_or_create(
            producto=detalle.producto, 
            ubicacion=tienda_origen, 
            defaults={'cantidad': 0}
        )

        stock_destino, _ = Stock.objects.get_or_create(
            producto=detalle.producto,
            ubicacion=tienda_destino,
            defaults={'cantidad': 0}
        )

        # Mover stock
        if stock_origen.cantidad >= detalle.cantidad:
            stock_origen.cantidad -= detalle.cantidad
            stock_destino.cantidad += detalle.cantidad
            stock_origen.save()
            stock_destino.save()
            
            # Crear historial
            HistorialTraspaso.objects.create(
                producto=detalle.producto,
                origen=tienda_origen,
                destino=tienda_destino,
                cantidad=detalle.cantidad,
                usuario=request.user,
                traspaso=traspaso
            )
        else:
            messages.warning(request, f"Stock insuficiente para {detalle.producto.codigo}")
            # Opcional: podrías decidir si cancelar todo el traspaso o solo este producto

    # 4. Marcar como finalizado
    traspaso.ejecutado = True
    traspaso.save()

    messages.success(request, f"¡Reposición #{traspaso.id} completada con éxito!")
    return redirect('traspasos_pendientes')

# views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from core.models import Ubicacion, Producto, Stock
from core.services.reposicion import generar_traspaso_tienda_a_tienda

@login_required
def traspaso_tienda_a_tienda_view(request):
    # 1. Traemos las tiendas activas
    tiendas = Ubicacion.objects.filter(tipo='TIENDA', activo=True)
    
    # 2. TRAEMOS LAS CATEGORÍAS (Esto es lo que te falta)
    categorias = Categoria.objects.filter(activo=True).order_by('nombre')
    
    # 3. Traemos los productos (opcional, si los usas al cargar la página)
    productos = Producto.objects.filter(activo=True)

    if request.method == 'POST':
        origen_id = request.POST.get('origen')
        destino_id = request.POST.get('destino')

        origen = get_object_or_404(Ubicacion, id=origen_id)
        destino = get_object_or_404(Ubicacion, id=destino_id)

        productos_dict = {}
        # Recorremos los productos para ver cuáles tienen cantidad > 0
        for producto in productos:
            cantidad_str = request.POST.get(f'cantidad_{producto.id}', '0')
            if cantidad_str and int(cantidad_str) > 0:
                productos_dict[producto.id] = int(cantidad_str)

        if not productos_dict:
            messages.error(request, "Debes seleccionar al menos un producto y cantidad.")
            return redirect('traspaso_tienda_a_tienda')

        # Llamamos a tu servicio de traspaso
        generar_traspaso_tienda_a_tienda(request.user, origen, destino, productos_dict)
        messages.success(request, f"Traspaso creado de {origen.nombre} → {destino.nombre}")
        return redirect('traspaso_tienda_a_tienda')

    # 4. PASAMOS LAS CATEGORÍAS AL CONTEXTO
    return render(request, 'core/traspaso_tienda_a_tienda.html', {
        'tiendas': tiendas,
        'categorias': categorias,  # <-- ESTO HACE QUE APAREZCAN EN EL SELECT
        'productos': productos
    })
from django.http import JsonResponse
from django.db.models import F

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from core.models import Producto, Stock

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from core.models import Producto, Stock, Ubicacion
from django.db.models import Q

@login_required
def buscar_producto_ajax(request):
    # 1. Capturamos todos los parámetros enviados desde el JS
    q = request.GET.get('q', '').strip()  # Mantenemos 'q' por compatibilidad
    origen_id = request.GET.get('origen')
    
    # Nuevos filtros individuales
    codigo = request.GET.get('codigo')
    categoria_id = request.GET.get('categoria')
    diseno = request.GET.get('diseno')
    color = request.GET.get('color')
    talla = request.GET.get('talla')
    marca = request.GET.get('marca')

    # Validación básica
    if not origen_id:
        return JsonResponse([], safe=False)

    try:
        origen = Ubicacion.objects.get(id=origen_id)
    except Ubicacion.DoesNotExist:
        return JsonResponse([], safe=False)

    # 2. Base QuerySet: Productos activos con stock mayor a 0 en la tienda origen
    productos = Producto.objects.filter(
        activo=True,
        stocks__ubicacion=origen,
        stocks__cantidad__gt=0
    )

    # 3. Aplicación de filtros multicriterio (Lógica acumulativa)
    if q:
        # Si se usa el buscador general antiguo
        productos = productos.filter(Q(codigo__icontains=q) | Q(diseno__icontains=q))
    
    if codigo:
        productos = productos.filter(codigo__icontains=codigo)
    
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
        
    if diseno:
        productos = productos.filter(diseno__icontains=diseno)
        
    if color:
        productos = productos.filter(color__icontains=color)
        
    if talla:
        productos = productos.filter(talla__icontains=talla)
        
    if marca:
        productos = productos.filter(marca__icontains=marca)

    # Distinct para evitar duplicados por el join de stocks y límite de 50 para velocidad
    productos = productos.distinct()[:50]

    # 4. Obtener todas las tiendas activas para el encabezado de la tabla
    tiendas = Ubicacion.objects.filter(tipo='TIENDA', activo=True).order_by('id')

    # 5. Construcción de la respuesta JSON
    data = []
    for p in productos:
        # Calculamos el stock de este producto en cada una de las tiendas
        listado_stocks = []
        for t in tiendas:
            stock_obj = Stock.objects.filter(producto=p, ubicacion=t).first()
            listado_stocks.append(stock_obj.cantidad if stock_obj else 0)

        data.append({
            'id': p.id,
            'codigo': p.codigo,
            'diseno': p.diseno,
            'color': p.color,
            'talla': p.talla,
            'marca': str(p.marca), # str() por si marca es un objeto
            'stocks': listado_stocks
        })

    return JsonResponse(data, safe=False)
from django.utils.dateparse import parse_date # Importante agregar este import al inicio

@login_required
def historial_traspasos(request):
    fecha_inicio = request.GET.get('desde')
    fecha_fin = request.GET.get('hasta')

    historiales = HistorialTraspaso.objects.filter(origen__tipo='TIENDA').select_related(
        'producto', 'origen', 'destino', 'usuario'
    )

    if fecha_inicio:
        historiales = historiales.filter(fecha__date__gte=parse_date(fecha_inicio))
    if fecha_fin:
        historiales = historiales.filter(fecha__date__lte=parse_date(fecha_fin))

    historiales = historiales.order_by('-fecha')

    return render(request, 'core/traspasos/historial.html', {
        'historiales': historiales,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    })

@login_required
def historial_reposiciones(request):
    fecha_inicio = request.GET.get('desde')
    fecha_fin = request.GET.get('hasta')
    destino_id = request.GET.get('destino') # <--- Nuevo filtro

    historiales = HistorialTraspaso.objects.filter(origen__tipo='ALMACEN').select_related(
        'producto', 'origen', 'destino', 'usuario'
    )

    # Filtro por Fechas
    if fecha_inicio:
        historiales = historiales.filter(fecha__date__gte=parse_date(fecha_inicio))
    if fecha_fin:
        historiales = historiales.filter(fecha__date__lte=parse_date(fecha_fin))
    
    # Filtro por Tienda Destino
    if destino_id:
        historiales = historiales.filter(destino_id=destino_id)

    historiales = historiales.order_by('-fecha')
    
    # Para el selector de tiendas en el HTML
    tiendas = Ubicacion.objects.filter(tipo='TIENDA', activo=True)

    return render(request, 'core/traspasos/historial_reposiciones.html', {
        'historiales': historiales,
        'tiendas': tiendas, # <--- Enviamos las tiendas al HTML
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'destino_id': destino_id,
    })
from django.db.models import Sum

@login_required
def reporte_pedidos(request):
    # Definimos un umbral por defecto (puedes cambiarlo a tu gusto)
    umbral = int(request.GET.get('umbral', 5))
    categoria_id = request.GET.get('categoria')
    
    # Obtenemos productos activos con la suma total de su stock
    productos_stock = Producto.objects.filter(activo=True).annotate(
        total_stock=Sum('stocks__cantidad')
    )

    # Si un producto no tiene registros en la tabla Stock, total_stock será None. 
    # Lo tratamos como 0 y filtramos por el umbral.
    lista_pedidos = []
    for p in productos_stock:
        cantidad = p.total_stock if p.total_stock is not None else 0
        if cantidad <= umbral:
            lista_pedidos.append({
                'producto': p,
                'cantidad': cantidad
            })

    # Filtro por categoría si se selecciona
    if categoria_id:
        lista_pedidos = [item for item in lista_pedidos if item['producto'].categoria_id == int(categoria_id)]

    categorias = Categoria.objects.filter(activo=True)

    return render(request, 'core/reporte_pedidos.html', {
        'pedidos': lista_pedidos,
        'categorias': categorias,
        'umbral': umbral,
    })

from django.shortcuts import render
from .models import Producto  # Asegúrate de importar tu modelo


from django.db.models import Sum, F
from django.utils import timezone
from .models import Producto, Ubicacion, Stock # Verifica que Stock sea el nombre de tu modelo de inventario

def reporte_inversion(request):
    # 1. Inicializamos la lista de resumen y el total global
    resumen = []
    total_global = 0

    # 2. Obtenemos todas las ubicaciones (Tiendas, Almacenes)
    ubicaciones = Ubicacion.objects.all()

    for u in ubicaciones:
        # Calculamos la inversión por tienda usando el campo 'costo' que confirmaste
        inversion_tienda = Stock.objects.filter(ubicacion=u).aggregate(
            total=Sum(F('cantidad') * F('producto__costo'))
        )['total'] or 0
        
        total_global += inversion_tienda
        
        resumen.append({
            'tienda': u.nombre,
            'inversion': inversion_tienda,
        })

    # 3. Calculamos el porcentaje de participación
    for item in resumen:
        if total_global > 0:
            item['porcentaje'] = round((item['inversion'] / total_global) * 100, 1)
        else:
            item['porcentaje'] = 0

    # 4. Contexto para el template
    context = {
        'resumen': resumen,
        'total_global': total_global,
        'fecha': timezone.now(),
    }
    
    return render(request, 'core/reporte_inversion.html', context)


from django.shortcuts import render, redirect
from .models import Cliente
from django.contrib import messages

def lista_clientes(request):
    clientes = Cliente.objects.all()
    return render(request, 'core/clientes.html', {'clientes': clientes})

def crear_cliente(request):
    if request.method == 'POST':
        dni = request.POST.get('dni')
        nombres = request.POST.get('nombres')
        apellidos = request.POST.get('apellidos')
        celular = request.POST.get('celular')
        correo = request.POST.get('correo')
        
        Cliente.objects.create(
            dni=dni,
            nombres=nombres,
            apellidos=apellidos,
            celular=celular,
            correo=correo
        )
        messages.success(request, "Cliente registrado correctamente.")
        return redirect('lista_clientes')


