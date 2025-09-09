from datetime import datetime, time, date
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Cajas, Usuarioxsucursales
from .forms import AperturaCajaForm
from nombredeapp.decorators import permiso_requerido

# Función para obtener la sucursal asignada al usuario
def obtener_sucursal_del_usuario(usuario_id):
    rel = Usuarioxsucursales.objects.filter(idusuarios_id=usuario_id).select_related('idsucursal').first()
    return rel.idsucursal if rel else None

# Vista del menú de caja
@permiso_requerido("caja:menu_caja")
def menu_caja_view(request):
    usuario_id = request.session.get('usuario_id')
    usuario_nombre = request.session.get('nombre_usuario')

    # Intentamos obtener el id de caja abierta de la sesión (si existe)
    id_caja_abierta = request.session.get('id_caja')
    caja_abierta = None
    if id_caja_abierta:
        try:
            caja_abierta = Cajas.objects.get(idcaja=id_caja_abierta)
        except Cajas.DoesNotExist:
            # Si no existe, limpiamos la sesión
            request.session.pop('caja_abierta', None)
            request.session.pop('id_caja', None)

    return render(request, "menucaja.html", {
        "usuario_nombre": usuario_nombre,
        "open_caja": caja_abierta,
    })

# Vista de apertura de caja
@permiso_requerido("caja:menu_caja")
def apertura_caja_view(request):
    usuario_id = request.session.get('usuario_id')
    usuario_nombre = request.session.get('nombre_usuario')

    # Revisar si ya hay caja abierta en esta sesión
    if request.session.get('caja_abierta'):
        messages.warning(request, "Ya existe una apertura activa en esta sesión.")
        return redirect("caja:menu_caja")

    sucursal = obtener_sucursal_del_usuario(usuario_id)
    if not sucursal:
        messages.error(request, "No tienes una sucursal asignada. Contacta al administrador.")
        return redirect("caja:menu_caja")

    if request.method == "POST":
        form = AperturaCajaForm(request.POST)
        if form.is_valid():
            apertura = form.save(commit=False)
            ahora = datetime.now()
            apertura.fechaaperturacaja = ahora.date()
            apertura.horaaperturacaja = ahora.time()
            apertura.idusuarios_id = usuario_id
            apertura.idsucursal_id = sucursal.idsucursal
            apertura.montofinalcaja = 0.0
            apertura.horacierrecaja = time(0,0,0)
            apertura.fechacierrecaja = apertura.fechaaperturacaja
            apertura.nombrecaja = f"Caja {sucursal.nombresucursal} - {usuario_nombre} - {ahora.strftime('%d/%m %H:%M')}"
            apertura.save()

            # Marcar en la sesión que esta caja está abierta
            request.session['caja_abierta'] = True
            request.session['id_caja'] = apertura.idcaja

            messages.success(request, "✅ Apertura registrada correctamente.")
            return redirect("caja:menu_caja")
        else:
            messages.error(request, "❌ Error en los datos. Revise el formulario.")
    else:
        form = AperturaCajaForm()

    return render(request, "aperturadecaja.html", {
        "usuario_nombre": usuario_nombre,
        "fecha_actual": datetime.now().strftime("%d/%m/%Y"),
        "form": form,
    })

# Vista de cierre de caja (opcional)
@permiso_requerido("caja:menu_caja")
def cierre_caja_view(request):
    usuario_id = request.session.get('usuario_id')
    id_caja = request.session.get('id_caja')

    if not id_caja:
        messages.warning(request, "No hay una caja abierta en esta sesión.")
        return redirect("caja:menu_caja")

    try:
        caja = Cajas.objects.get(idcaja=id_caja)
        caja.horacierrecaja = datetime.now().time()
        caja.fechacierrecaja = datetime.now().date()
        caja.save()

        # Limpiar la sesión
        request.session.pop('caja_abierta', None)
        request.session.pop('id_caja', None)

        messages.success(request, "✅ Caja cerrada correctamente.")
    except Cajas.DoesNotExist:
        messages.error(request, "No se encontró la caja abierta.")
        request.session.pop('caja_abierta', None)
        request.session.pop('id_caja', None)

    return redirect("caja:menu_caja")
