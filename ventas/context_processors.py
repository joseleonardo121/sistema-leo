from ventas.services.caja import get_caja_abierta

def caja_actual(request):
    if not request.user.is_authenticated:
        return {}

    user = request.user

    # Admin no tiene tienda fija → no mostramos caja
    if user.is_staff:
        return {'caja_actual': None}

    perfil = getattr(user, 'perfil', None)
    if not perfil or not perfil.ubicacion:
        return {'caja_actual': None}

    caja = get_caja_abierta(perfil.ubicacion)

    return {
        'caja_actual': caja,
        'ubicacion_actual': perfil.ubicacion
    }
