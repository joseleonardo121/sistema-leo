from ventas.models import Caja


def get_caja_abierta(ubicacion):
    """
    Retorna la caja abierta de una ubicación.
    Si no existe, retorna None.
    """
    return Caja.objects.filter(
        ubicacion=ubicacion,
        abierta=True
    ).first()
