from datetime import datetime, time, date
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Cajas, Usuarioxsucursales
from .forms import AperturaCajaForm
# Create your views here.
#def rol_requerido(rol_requerido):
#    def decorator(view_func):
#        def wrapper(request, *args, **kwargs):
#            if not request.session.get('usuario_id'):
#                return redirect('login')
#            if request.session.get('rol_nombre') != rol_requerido:
#                return redirect('inicio')
#            return view_func(request, *args, **kwargs)
#        return wrapper
#    return decorator

def obtener_sucursal_del_usuario(usuario_id):
    """
    Busca la relación Usuarioxsucursales para el usuario y devuelve la sucursal.
    Retorna None si no tiene sucursal.
    """
    rel = Usuarioxsucursales.objects.filter(idusuarios_id=usuario_id).select_related('idsucursal').first()
    return rel.idsucursal if rel else None

def get_caja_abierta_para_usuario(usuario_id):
    """
    Define una apertura 'abierta' si:
      - fechaaperturacaja == hoy
      - horacierrecaja == 00:00:00 (marcador de 'no cerrado' en tu esquema)
    Devuelve la instancia o None.
    """
    hoy = date.today()
    caja_abierta = Cajas.objects.filter(
        idusuarios_id=usuario_id,
        fechaaperturacaja=hoy,
        horacierrecaja=time(0, 0, 0)
    ).order_by('-idcaja').first()
    return caja_abierta

#@rol_requerido("Cajero")
def menu_caja_view(request):
    """
    Renderiza el menú y pasa 'open_caja' para que la plantilla muestre monto inicial o 'Sin apertura'.
    """
    usuario_id = request.session.get('usuario_id', None)
    usuario_nombre = request.session.get('nombre_usuario', "Invitado")

    open_caja = None
    if usuario_id:
        open_caja = get_caja_abierta_para_usuario(usuario_id)

    return render(request, "menucaja.html", {
        "usuario_nombre": usuario_nombre,
        "open_caja": open_caja,
    })

#@rol_requerido("Cajero")
def apertura_caja_view(request):
    """
    Procesa formulario de apertura:
      - Verifica que no exista ya una apertura hoy (get_caja_abierta_para_usuario).
      - Valida form (AperturaCajaForm).
      - Completa campos automáticos y guarda con apertura.save().
    """
    usuario_id = request.session.get('usuario_id', None)
    usuario_nombre = request.session.get('nombre_usuario', "Invitado")

    if usuario_id and get_caja_abierta_para_usuario(usuario_id):
        messages.warning(request, "Ya existe una apertura activa para hoy. Debe cerrar antes de abrir otra.")
        return redirect("menu_caja")

    sucursal = obtener_sucursal_del_usuario(usuario_id) if usuario_id else None
    if not sucursal:
        messages.warning(request, "No tienes una sucursal asignada, se usará sucursal genérica.")

    if request.method == "POST":
        form = AperturaCajaForm(request.POST)
        if form.is_valid():
            apertura = form.save(commit=False)

            ahora = datetime.now()
            apertura.fechaaperturacaja = ahora.date()
            apertura.horaaperturacaja = ahora.time()

            # FK assignment (nombres según tus modelos autogenerados)
            apertura.idusuarios_id = usuario_id if usuario_id else None
            apertura.idsucursal_id = sucursal.idsucursal if sucursal else None

            # Inicializamos campos de cierre para indicar "no cerrado" (tu esquema actual lo requiere)
            apertura.montofinalcaja = 0.0
            apertura.horacierrecaja = time(0, 0, 0)
            apertura.fechacierrecaja = apertura.fechaaperturacaja
            
            if sucursal:
                sucursal_nombre = sucursal.nombresucursal
            else:
                sucursal_nombre = "Sucursal genérica"

            apertura.nombrecaja = f"Caja {sucursal_nombre} - {usuario_nombre} - {ahora.strftime('%d/%m %H:%M')}"
            apertura.save()  # <-- aquí se inserta el registro en la tabla 'cajas'
            messages.success(request, "✅ Apertura registrada correctamente.")
            return redirect("menu_caja")
        else:
            messages.error(request, "❌ Error en los datos. Revise el formulario.")
    else:
        form = AperturaCajaForm()

    return render(request, "aperturadecaja.html", {
        "usuario_nombre": usuario_nombre,
        "fecha_actual": datetime.now().strftime("%d/%m/%Y"),
        "form": form,
    })
