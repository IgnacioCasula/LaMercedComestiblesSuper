from datetime import datetime, time, date
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Caja, UsuxSuc, Usuarios, Sucursales, Ubicaciones, Codigopostal, Ventas, Movimientosdecaja
from .forms import AperturaCajaForm
from .decorators import permiso_requerido
from django.db import models
from django.db.models import Sum  


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
    #"""Vista para apertura de caja - CON INFORMACIÓN REAL DEL ÚLTIMO CIERRE"""
    usuario_id = request.session.get('usuario_id')
    usuario_nombre = request.session.get('nombre_usuario')
    
    # Obtener información REAL del último cierre
    ultimo_cierre_info = None
    try:
        # Buscar el último cierre del usuario (cajas cerradas)
        ultimo_cierre = Caja.objects.filter(
            idusuarios_id=usuario_id
        ).exclude(
            horacierrecaja=time(0, 0, 0)  # Excluir cajas abiertas
        ).order_by('-fechacierrecaja', '-horacierrecaja').first()
        
        if ultimo_cierre:
            # Calcular diferencia REAL del último cierre
            # Buscar ventas de ese día para calcular diferencia precisa
            ventas_ultimo_cierre = Ventas.objects.filter(
                idcaja=ultimo_cierre,
                fechaventa=ultimo_cierre.fechacierrecaja
            )
            
            ventas_efectivo = ventas_ultimo_cierre.filter(metodopago='Efectivo').aggregate(
                total=Sum('totalventa')
            )['total'] or 0.0
            
            # Calcular diferencia: Efectivo real - (Fondo inicial + Ventas efectivo)
            efectivo_esperado = ultimo_cierre.montoinicialcaja + ventas_efectivo
            diferencia = ultimo_cierre.montofinalcaja - efectivo_esperado
            
            # Obtener nombre del usuario que cerró la caja
            usuario_cierre = ultimo_cierre.idusuarios.nombreusuario
            
            ultimo_cierre_info = {
                'hora': ultimo_cierre.horacierrecaja.strftime('%H:%M'),
                'fecha': ultimo_cierre.fechacierrecaja.strftime('%d/%m/%Y'),
                'usuario': usuario_cierre,
                'diferencia': f"{diferencia:.2f}",
                'monto_final': ultimo_cierre.montofinalcaja,
                'monto_inicial': ultimo_cierre.montoinicialcaja,
                'ventas_efectivo': ventas_efectivo
            }
            
    except Exception as e:
        print(f"Error obteniendo último cierre: {e}")
        # En caso de error, mostrar información básica
        try:
            ultimo_cierre = Caja.objects.filter(
                idusuarios_id=usuario_id
            ).exclude(
                horacierrecaja=time(0, 0, 0)
            ).order_by('-fechacierrecaja', '-horacierrecaja').first()
            
            if ultimo_cierre:
                # Información básica sin cálculo de diferencia
                ultimo_cierre_info = {
                    'hora': ultimo_cierre.horacierrecaja.strftime('%H:%M'),
                    'fecha': ultimo_cierre.fechacierrecaja.strftime('%d/%m/%Y'),
                    'usuario': ultimo_cierre.idusuarios.nombreusuario,
                    'diferencia': '0.00',  # Valor por defecto
                    'monto_final': ultimo_cierre.montofinalcaja,
                    'basico': True  # Indicador de que es info básica
                }
        except Exception as e2:
            print(f"Error obteniendo info básica: {e2}")





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
        "form": form,
        "ultimo_cierre": ultimo_cierre_info  # Pasar la info REAL al template
    })

def cierre_caja_view(request):
    """Vista mejorada para cierre de caja con cálculo automático"""
    usuario_id = request.session.get('usuario_id')
    usuario_nombre = request.session.get('nombre_usuario')
    id_caja = request.session.get('id_caja')
    
    caja = None
    ventas_efectivo = 0
    ventas_tarjeta = 0
    ventas_transferencia = 0
    total_sistema = 0
    total_efectivo_esperado = 0
    
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
            else:
                # CALCULAR VENTAS DEL DÍA para esta caja
                hoy = date.today()
                
                ventas_dia = Ventas.objects.filter(
                    idcaja=caja,
                    fechaventa=hoy
                )
                
                # Calcular totales por método de pago
                ventas_efectivo_result = ventas_dia.filter(metodopago='Efectivo').aggregate(
                    total=models.Sum('totalventa')
                )
                ventas_efectivo = ventas_efectivo_result['total'] or 0.0
                
                ventas_tarjeta_result = ventas_dia.filter(metodopago='Tarjeta').aggregate(
                    total=models.Sum('totalventa')
                )
                ventas_tarjeta = ventas_tarjeta_result['total'] or 0.0
                
                ventas_transferencia_result = ventas_dia.filter(metodopago='Transferencia').aggregate(
                    total=models.Sum('totalventa')
                )
                ventas_transferencia = ventas_transferencia_result['total'] or 0.0
                
                total_sistema = ventas_efectivo + ventas_tarjeta + ventas_transferencia
                total_efectivo_esperado = caja.montoinicialcaja + ventas_efectivo
                
        except Caja.DoesNotExist:
            messages.error(request, "No se encontró la caja.")
            request.session.pop('caja_abierta', None)
            request.session.pop('id_caja', None)
    
    # Si es POST, procesar el cierre
    if request.method == "POST" and caja:
        monto_final_efectivo = request.POST.get('monto_final_efectivo', 0)
        observacion_cierre = request.POST.get('observacion_cierre', '')
        
        try:
            # Calcular diferencia
            monto_final_efectivo = float(monto_final_efectivo)
            diferencia = monto_final_efectivo - total_efectivo_esperado
            
            # Cerrar caja
            ahora = datetime.now()
            caja.horacierrecaja = ahora.time()
            caja.fechacierrecaja = ahora.date()
            caja.montofinalcaja = monto_final_efectivo
            
            # Si tienes el campo observacioncierre en tu modelo, descomenta:
            # if hasattr(caja, 'observacioncierre'):
            #     caja.observacioncierre = observacion_cierre
            
            caja.save()
            
            # Registrar movimiento de caja si tienes el modelo
            try:
                Movimientosdecaja.objects.create(
                    nombreusuariomovcaja=usuario_nombre,
                    fechamovcaja=ahora.date(),
                    horamovcaja=ahora.time(),
                    nombrecajamovcaja=caja.nombrecaja,
                    tipomovcaja='CIERRE',
                    conceptomovcaja=f'Cierre de caja - Diferencia: ${diferencia:.2f}',
                    valormovcaja=0,
                    saldomovcaja=monto_final_efectivo,
                    idusuarios_id=usuario_id,
                    idcaja=caja
                )
            except Exception as e:
                print(f"Error registrando movimiento: {e}")
            
            # Limpiar sesión
            request.session.pop('caja_abierta', None)
            request.session.pop('id_caja', None)
            
            if diferencia == 0:
                messages.success(request, "✅ Caja cerrada correctamente. Sin diferencias.")
            elif diferencia > 0:
                messages.success(request, f"✅ Caja cerrada. ⚠ SOBRANTE: ${diferencia:.2f}")
            else:
                messages.success(request, f"✅ Caja cerrada. ⚠ FALTANTE: ${abs(diferencia):.2f}")
                
            return redirect("inicio")
        except Exception as e:
            messages.error(request, f"❌ Error al cerrar la caja: {str(e)}")
    
    # Renderizar el template
    return render(request, "cierredecaja.html", {
        "usuario_nombre": usuario_nombre,
        "fecha_actual": datetime.now().strftime("%d/%m/%Y"),
        "caja": caja,
        "ventas_efectivo": ventas_efectivo,
        "ventas_tarjeta": ventas_tarjeta,
        "ventas_transferencia": ventas_transferencia,
        "total_sistema": total_sistema,
        "total_efectivo_esperado": total_efectivo_esperado
    })

def obtener_ultimo_cierre(request):
    """Obtiene información del último cierre para mostrar en apertura"""
    usuario_id = request.session.get('usuario_id')
    if usuario_id:
        try:
            ultimo_cierre = Caja.objects.filter(
                idusuarios_id=usuario_id
            ).exclude(
                horacierrecaja=time(0, 0, 0)  # Excluir cajas abiertas
            ).order_by('-fechacierrecaja', '-horacierrecaja').first()
            
            if ultimo_cierre:
                # Calcular diferencia del último cierre (simplificado)
                diferencia = ultimo_cierre.montofinalcaja - ultimo_cierre.montoinicialcaja
                
                request.session['ultimo_cierre'] = {
                    'hora': ultimo_cierre.horacierrecaja.strftime('%H:%M'),
                    'usuario': request.session.get('nombre_usuario', 'Usuario'),
                    'diferencia': f"{diferencia:.2f}"
                }
        except Exception as e:
            print(f"Error obteniendo último cierre: {e}")
    
    return redirect('caja:apertura_caja')