from django.shortcuts import render
from .models import ConfiguracionWeb, Banner  # Añadimos Banner
from core.models import Producto, Categoria 
from django.db.models import Q
from django.core.paginator import Paginator 
import operator
from functools import reduce

def inicio(request):
    config = ConfiguracionWeb.objects.first()
    categorias = Categoria.objects.all()
    # Obtenemos solo los banners activos y ordenados
    banners = Banner.objects.filter(activo=True).order_by('orden')
    
    query = request.GET.get('q', '')
    cat_id = request.GET.get('categoria', '')
    precio_max = request.GET.get('precio_max', '')

    productos_list = Producto.objects.filter(
        activo=True, 
        stocks__cantidad__gt=0
    ).exclude(Q(imagen=None) | Q(imagen='')).distinct().order_by('-creado')

    # --- BUSCADOR INTELIGENTE ---
    if query:
        palabras = query.split()
        q_objects = Q()
        for palabra in palabras:
            q_objects &= (
                Q(diseno__icontains=palabra) | 
                Q(color__icontains=palabra) | 
                Q(categoria__nombre__icontains=palabra) |
                Q(codigo__icontains=palabra)
            )
        productos_list = productos_list.filter(q_objects)

    # Filtro de categoría
    if cat_id:
        productos_list = productos_list.filter(categoria_id=cat_id)

    # Filtros de precio
    if precio_max:
        if precio_max == '50':
            productos_list = productos_list.filter(precio__lt=50)
        elif precio_max == '100':
            productos_list = productos_list.filter(precio__gte=50, precio__lte=100)
        elif precio_max == '101':
            productos_list = productos_list.filter(precio__gt=100)

    # Paginación (12 productos por página)
    paginator = Paginator(productos_list, 12) 
    page_number = request.GET.get('page')
    productos = paginator.get_page(page_number)

    return render(request, 'web/inicio.html', {
        'config': config,
        'productos': productos,
        'categorias': categorias,
        'banners': banners, # Pasamos los banners al HTML
        'query': query,
        'precio_max': precio_max
    })