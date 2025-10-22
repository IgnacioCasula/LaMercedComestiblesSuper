from datetime import datetime, time, date
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Caja, UsuxSuc
from .forms import AperturaCajaForm
from nombredeapp.decorators import permiso_requerido

def obtener_sucursal_del_usuario(usuario_id):
    rel = UsuxSuc.objects.filter(idusuario_id=usuario_id).select_related('idsucursal').first()
    return rel.idsucursal if rel else None

@permiso_requerido(roles_permitidos=['Supervisor de Caja'])
def menu_caja_view(request):
    usuario_id = request.session.get('usuario_id')
    usuario_nombre = request.session.get('nombre_usuario')
    id_caja_abierta = request.session.get('id_caja')
    caja_abierta = None
    if id_caja_abierta:
        try:
            caja_abierta = Caja.objects.get(idcaja=id_caja_abierta)
        except Caja.DoesNotExist:
            request.session.pop('caja_abierta', None)
            request.session.pop('id_caja', None)
    return render(request, "menucaja.html", {"usuario_nombre": usuario_nombre, "open_caja": caja_abierta})

@permiso_requerido(roles_permitidos=['Supervisor de Caja'])
def apertura_caja_view(request):
    usuario_id = request.session.get('usuario_id')
    usuario_nombre = request.session.get('nombre_usuario')
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
            apertura.horacierrecaja = time(0, 0, 0)
            apertura.fechacierrecaja = apertura.fechaaperturacaja
            apertura.nombrecaja = f"Caja {sucursal.nombresucursal} - {usuario_nombre} - {ahora.strftime('%d/%m %H:%M')}"
            apertura.save()
            request.session['caja_abierta'] = True
            request.session['id_caja'] = apertura.idcaja
            messages.success(request, "✅ Apertura registrada correctamente.")
            return redirect("caja:menu_caja")
        else:
            messages.error(request, "❌ Error en los datos. Revise el formulario.")
    else:
        form = AperturaCajaForm()
    return render(request, "aperturadecaja.html", {"usuario_nombre": usuario_nombre, "fecha_actual": datetime.now().strftime("%d/%m/%Y"), "form": form})

@permiso_requerido(roles_permitidos=['Supervisor de Caja'])
def cierre_caja_view(request):
    id_caja = request.session.get('id_caja')
    if not id_caja:
        messages.warning(request, "No hay una caja abierta en esta sesión.")
        return redirect("caja:menu_caja")
    try:
        caja = Caja.objects.get(idcaja=id_caja)
        caja.horacierrecaja = datetime.now().time()
        caja.fechacierrecaja = datetime.now().date()
        caja.save()
        request.session.pop('caja_abierta', None)
        request.session.pop('id_caja', None)
        messages.success(request, "✅ Caja cerrada correctamente.")
    except Caja.DoesNotExist:
        messages.error(request, "No se encontró la caja abierta.")
        request.session.pop('caja_abierta', None)
        request.session.pop('id_caja', None)
        print(f"DEBUG - Usuario: {usuario_id}, Caja ID: {id_caja_abierta}, Caja objeto: {caja_abierta}")
    return redirect("caja:menu_caja")