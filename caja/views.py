from datetime import datetime, time, date
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Caja, UsuxSuc, Usuarios, Sucursales, Ubicaciones, Codigopostal
from .forms import AperturaCajaForm
from .decorators import permiso_requerido

def obtener_o_crear_sucursal_sistema():
    """
    Crea o devuelve una sucursal del sistema para usuarios sin sucursal asignada.
    Esta función se asegura de que siempre exista una sucursal por defecto.
    """
    try:
        # Intentar obtener la sucursal del sistema
        sucursal = Sucursales.objects.filter(nombresucursal='Sistema').first()
        
        if not sucursal:
            # Crear ubicación por defecto si no existe
            codigo_postal = Codigopostal.objects.first()
            if not codigo_postal:
                codigo_postal = Codigopostal.objects.create(
                    codigopostal=0,
                    nombrelocalidad='Sistema'
                )
            
            ubicacion = Ubicaciones.objects.first()
            if not ubicacion:
                ubicacion = Ubicaciones.objects.create(
                    ciudad='Sistema',
                    nombrecalle='Sistema',
                    barrio='Sistema',
                    idcodigopostal=codigo_postal
                )
            
            # Crear sucursal del sistema
            sucursal = Sucursales.objects.create(
                nombresucursal='Sistema',
                telefonosucursal=0,
                idubicacion=ubicacion
            )
        
        return sucursal
    except Exception as e:
        print(f"Error al crear/obtener sucursal del sistema: {e}")
        # Si todo falla, intentar devolver cualquier sucursal existente
        return Sucursales.objects.first()

def menu_caja_view(request):
    """Vista del menú principal de caja"""
    usuario_id = request.session.get('usuario_id')
    usuario_nombre = request.session.get('nombre_usuario')
    
    # Buscar caja abierta para este usuario
    id_caja_abierta = request.session.get('id_caja')
    caja_abierta = None
    
    if id_caja_abierta:
        try:
            caja_abierta = Caja.objects.get(idcaja=id_caja_abierta)
            # Verificar que la caja realmente esté abierta (hora de cierre = 00:00:00)
            if caja_abierta.horacierrecaja and caja_abierta.horacierrecaja != time(0, 0, 0):
                caja_abierta = None
                request.session.pop('caja_abierta', None)
                request.session.pop('id_caja', None)
        except Caja.DoesNotExist:
            request.session.pop('caja_abierta', None)
            request.session.pop('id_caja', None)
    
    # Si no hay caja en sesión, buscar si hay alguna caja abierta del usuario
    if not caja_abierta:
        caja_abierta = Caja.objects.filter(
            idusuarios_id=usuario_id,
            horacierrecaja=time(0, 0, 0)  # Caja abierta
        ).order_by('-fechaaperturacaja', '-horaaperturacaja').first()
        
        if caja_abierta:
            request.session['caja_abierta'] = True
            request.session['id_caja'] = caja_abierta.idcaja
    
    return render(request, "menucaja.html", {
        "usuario_nombre": usuario_nombre,
        "open_caja": caja_abierta
    })

def apertura_caja_view(request):
    """Vista para apertura de caja - SIN RESTRICCIÓN DE SUCURSAL"""
    usuario_id = request.session.get('usuario_id')
    usuario_nombre = request.session.get('nombre_usuario')
    
    # Verificar si ya hay una caja abierta
    caja_abierta_existente = Caja.objects.filter(
        idusuarios_id=usuario_id,
        horacierrecaja=time(0, 0, 0)
    ).first()
    
    if caja_abierta_existente:
        messages.warning(request, "Ya tienes una caja abierta. Debes cerrarla antes de abrir una nueva.")
        request.session['caja_abierta'] = True
        request.session['id_caja'] = caja_abierta_existente.idcaja
        return redirect("caja:menu_caja")
    
    # AQUÍ ES DONDE QUITAMOS LA RESTRICCIÓN:
    # Ya no verificamos si el usuario tiene sucursal ni mostramos error
    # Simplemente obtenemos o creamos una sucursal del sistema
    sucursal = obtener_o_crear_sucursal_sistema()
    
    if request.method == "POST":
        form = AperturaCajaForm(request.POST)
        if form.is_valid():
            apertura = form.save(commit=False)
            ahora = datetime.now()
            
            # Configurar campos de apertura
            apertura.fechaaperturacaja = ahora.date()
            apertura.horaaperturacaja = ahora.time()
            apertura.idusuarios_id = usuario_id
            apertura.idsucursal = sucursal  # Asignar la sucursal del sistema
            apertura.montofinalcaja = 0.0
            apertura.horacierrecaja = time(0, 0, 0)  # Indicador de caja abierta
            apertura.fechacierrecaja = apertura.fechaaperturacaja
            apertura.nombrecaja = f"Caja {usuario_nombre} - {ahora.strftime('%d/%m %H:%M')}"
            
            apertura.save()
            
            # Guardar en sesión
            request.session['caja_abierta'] = True
            request.session['id_caja'] = apertura.idcaja
            
            messages.success(request, "✅ Apertura registrada correctamente.")
            return redirect("inicio")
        else:
            messages.error(request, "❌ Error en los datos. Revise el formulario.")
    else:
        form = AperturaCajaForm()
    
    return render(request, "aperturadecaja.html", {
        "usuario_nombre": usuario_nombre,
        "fecha_actual": datetime.now().strftime("%d/%m/%Y"),
        "form": form
    })

def cierre_caja_view(request):
    """Vista para cierre de caja"""
    usuario_id = request.session.get('usuario_id')
    usuario_nombre = request.session.get('nombre_usuario')
    id_caja = request.session.get('id_caja')
    
    caja = None
    
    # Intentar obtener la caja
    if id_caja:
        try:
            caja = Caja.objects.get(idcaja=id_caja, idusuarios_id=usuario_id)
            
            # Verificar que la caja esté abierta
            if caja.horacierrecaja != time(0, 0, 0):
                messages.warning(request, "Esta caja ya está cerrada.")
                request.session.pop('caja_abierta', None)
                request.session.pop('id_caja', None)
                caja = None
        except Caja.DoesNotExist:
            messages.error(request, "No se encontró la caja.")
            request.session.pop('caja_abierta', None)
            request.session.pop('id_caja', None)
    
    # Si es POST, procesar el cierre
    if request.method == "POST" and caja:
        monto_final = request.POST.get('monto_final', 0)
        observacion_cierre = request.POST.get('observacion_cierre', '')
        
        try:
            # Cerrar caja
            ahora = datetime.now()
            caja.horacierrecaja = ahora.time()
            caja.fechacierrecaja = ahora.date()
            caja.montofinalcaja = float(monto_final)
            
            # Agregar observación de cierre si existe el campo
            if hasattr(caja, 'observacioncierre'):
                caja.observacioncierre = observacion_cierre
            
            caja.save()
            
            # Limpiar sesión
            request.session.pop('caja_abierta', None)
            request.session.pop('id_caja', None)
            
            messages.success(request, "✅ Caja cerrada correctamente.")
            return redirect("inicio")
        except Exception as e:
            messages.error(request, f"❌ Error al cerrar la caja: {str(e)}")
    
    # Renderizar el template
    return render(request, "cierredecaja.html", {
        "usuario_nombre": usuario_nombre,
        "fecha_actual": datetime.now().strftime("%d/%m/%Y"),
        "caja": caja
    })