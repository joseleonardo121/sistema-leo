from django.urls import path
from . import views

urlpatterns = [
    #TODO SOBRE LA TABLA PRINCIPAL QUE ES PRODUCTOS EN GENERAL
    path('productos/', views.productos, name='productos'),
    path('stock/', views.stock, name='stock'),
    path('productos/nuevo/', views.crear_producto, name='crear_producto'),
    path('stock/nuevo/', views.crear_stock, name='crear_stock'),
    path('stock/masivo/<int:producto_id>/',views.stock_masivo_producto,name='stock_masivo_producto'),
    path('ubicaciones/', views.ubicaciones, name='ubicaciones'),
    path('ubicaciones/nuevo/', views.crear_ubicacion, name='crear_ubicacion'),
    path('categorias/', views.categorias, name='categorias'),
    path('categorias/nuevo/', views.crear_categoria, name='crear_categoria'),
    path('productos/desactivar/<int:producto_id>/', views.desactivar_producto, name='desactivar_producto'),
    path('productos/inactivos/', views.productos_inactivos, name='productos_inactivos'),
    path('productos/toggle/<int:id>/', views.toggle_producto, name='toggle_producto'),
    path('productos/editar/<int:pk>/', views.editar_producto, name='editar_producto'),
    path('categorias/eliminar/<int:id>/', views.eliminar_categoria, name='eliminar_categoria'),
    path('ubicaciones/eliminar/<int:id>/', views.eliminar_ubicacion, name='eliminar_ubicacion'),
    path('productos/eliminar/<int:id>/', views.eliminar_producto, name='eliminar_producto'),
    path('categoria/ajax/', views.crear_categoria_ajax, name='crear_categoria_ajax'),
    path('reposicion/generar/', views.generar_reposicion_view, name='generar_reposicion'),
    path('reposicion/', views.traspasos_pendientes, name='traspasos_pendientes'),
    path('reposicion/ejecutar/<int:traspaso_id>/', views.ejecutar_traspaso, name='ejecutar_traspaso'),
    path('traspaso/tienda-a-tienda/', views.traspaso_tienda_a_tienda_view, name='traspaso_tienda_a_tienda'),
    path('ajax/buscar-producto/', views.buscar_producto_ajax, name='buscar_producto_ajax'),
    path('traspasos/historial/', views.historial_traspasos, name='historial_traspasos'),
    path('reporte-pedidos/', views.reporte_pedidos, name='reporte_pedidos'),
    path('reportes/inversion/', views.reporte_inversion, name='reporte_inversion'),
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/crear/', views.crear_cliente, name='crear_cliente'),
    path('traspasos/historial/', views.historial_traspasos, name='historial_traspasos'),
    path('reposicion/historial/', views.historial_reposiciones, name='historial_reposiciones'),
    
]

