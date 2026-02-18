from django.urls import path
from .views import pos, buscar_producto, finalizar_venta,historial_ventas,boleta_venta,anular_venta,cambio_venta,abrir_caja,cerrar_caja,panel_cajas,dashboard_tienda,ver_ventas_tienda,mis_ventas_hoy,historial_cajas
from .views import reporte_anual,reporte_mensual,crear_cliente_ajax,traspaso_pos_rapido
urlpatterns = [
    path('pos/', pos, name='pos'),
    path('buscar-producto/', buscar_producto, name='buscar_producto'),
    path('finalizar/', finalizar_venta, name='finalizar_venta'),
    path('historial/', historial_ventas, name='historial_ventas'),
    path('boleta/<int:venta_id>/', boleta_venta, name='boleta_venta'),
    path('anular/<int:venta_id>/', anular_venta, name='anular_venta'),
    path('cambio/<int:venta_id>/', cambio_venta, name='cambio_venta'),
    path('caja/abrir/', abrir_caja, name='abrir_caja'),
    path('caja/cerrar/<int:caja_id>/', cerrar_caja, name='cerrar_caja'),
    path('caja/panel/', panel_cajas, name='panel_cajas'),
    path('dashboard/', dashboard_tienda, name='dashboard_tienda'),
    path('ventas/tienda/<int:ubicacion_id>/', ver_ventas_tienda, name='ver_ventas_tienda'),
    path('ventas/hoy/', mis_ventas_hoy, name='mis_ventas_hoy'),
    path('cajas/historial/', historial_cajas, name='historial_cajas'),
    path('reportes/mensual/', reporte_mensual, name='reporte_mensual'),
    path('reportes/anual/', reporte_anual, name='reporte_anual'),
    path('crear-cliente-ajax/',crear_cliente_ajax, name='crear_cliente_ajax'),
    path('traspaso-pos-rapido/', traspaso_pos_rapido, name='traspaso_pos_rapido'),
]