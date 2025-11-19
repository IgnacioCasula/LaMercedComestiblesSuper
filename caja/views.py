from datetime import datetime, time, date
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Caja, UsuxSuc, Usuarios, Sucursales, Ubicaciones, Codigopostal, Ventas, Movimientosdecaja
from .forms import AperturaCajaForm
from .decorators import permiso_requerido
from django.db import models
from django.db.models import Sum, Q  
from .utils import registrar_actividad
from django.http import JsonResponse

def obtener_o_crear_sucursal_sistema():
    """
    Crea o devuelve la sucursal central para usuarios sin sucursal asignada.
    Esta función se asegura de que siempre exista una sucursal por defecto.
    """
    try:
        # PRIMERO intentar obtener la sucursal "Sucursal Central" (la del comando productos)
        sucursal = Sucursales.objects.filter(nombresucursal='Sucursal Central').first()
        
        if not sucursal:
            # Si no existe, intentar obtener "Sistema" (para compatibilidad con versiones anteriores)
            sucursal = Sucursales.objects.filter(nombresucursal='Sistema').first()
            
        if not sucursal:
            # Si no existe ninguna, crear la sucursal central con los mismos datos del comando productos
            codigo_postal = Codigopostal.objects.filter(codigopostal=5000).first()
            if not codigo_postal:
                codigo_postal = Codigopostal.objects.create(
                    codigopostal=5000,
                    nombrelocalidad='Córdoba Capital'
                )
            
            ubicacion = Ubicaciones.objects.filter(
                ciudad='Córdoba', 
                nombrecalle='Av. Colón 1000'
            ).first()
            if not ubicacion:
                ubicacion = Ubicaciones.objects.create(
                    ciudad='Córdoba',
                    nombrecalle='Av. Colón 1000',
                    barrio='Centro',
                    idcodigopostal=codigo_postal
                )
            
            # Crear sucursal central (igual que en productos.py)
            sucursal = Sucursales.objects.create(
                nombresucursal='Sucursal Central',
                telefonosucursal=3511234567,
                idubicacion=ubicacion
            )
            print(f"✅ Sucursal Central creada: {sucursal.idsucursal}")
        
        return sucursal
    except Exception as e:
        print(f"Error al crear/obtener sucursal central: {e}")
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
            

            try:
                Movimientosdecaja.objects.create(
                    nombreusuariomovcaja=usuario_nombre,
                    fechamovcaja=ahora.date(),
                    horamovcaja=ahora.time(),
                    nombrecajamovcaja=apertura.nombrecaja,
                    tipomovcaja='APERTURA',
                    conceptomovcaja=f'Apertura de caja - {apertura.observacionapertura}',
                    valormovcaja=apertura.montoinicialcaja,
                    saldomovcaja=apertura.montoinicialcaja,
                    idusuarios_id=usuario_id,
                    idcaja=apertura
                )
            except Exception as e:
                print(f"Error registrando movimiento de apertura: {e}")


            # Guardar en sesión
            request.session['caja_abierta'] = True
            request.session['id_caja'] = apertura.idcaja
            
            messages.success(request, "✅ Apertura registrada correctamente.")
            registrar_actividad(
                request,
                'APERTURA_CAJA',
                f'Apertura de caja con monto inicial ${apertura.montoinicialcaja}',
                detalles={
                    'caja_id': apertura.idcaja,
                    'monto_inicial': float(apertura.montoinicialcaja)
                }
            )
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
                
                # Calcular totales por método de pago - CORREGIDO
                ventas_efectivo_result = ventas_dia.filter(
                    models.Q(metodopago='EFECTIVO') | 
                    models.Q(metodopago='Efectivo')
                ).aggregate(total=models.Sum('totalventa'))
                ventas_efectivo = ventas_efectivo_result['total'] or 0.0
                
                # ✅ CORRECCIÓN: Incluir todos los tipos de tarjeta
                ventas_tarjeta_result = ventas_dia.filter(
                    models.Q(metodopago='TARJETA DEBITO') |
                    models.Q(metodopago='TARJETA CREDITO') |
                    models.Q(metodopago='Tarjeta Débito') |
                    models.Q(metodopago='Tarjeta Crédito') |
                    models.Q(metodopago__icontains='TARJETA')
                ).aggregate(total=models.Sum('totalventa'))
                ventas_tarjeta = ventas_tarjeta_result['total'] or 0.0
                
                ventas_transferencia_result = ventas_dia.filter(
                    models.Q(metodopago='TRANSFERENCIA') |
                    models.Q(metodopago='Transferencia')
                ).aggregate(total=models.Sum('totalventa'))
                ventas_transferencia = ventas_transferencia_result['total'] or 0.0
                
                total_sistema = ventas_efectivo + ventas_tarjeta + ventas_transferencia
                total_efectivo_esperado = caja.montoinicialcaja + ventas_efectivo

                # ✅ NUEVO: Obtener movimientos de caja para el resumen
                movimientos_caja = Movimientosdecaja.objects.filter(
                    idcaja=caja,
                    fechamovcaja=hoy
                ).order_by('horamovcaja')

                
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


                ultimo_movimiento = Movimientosdecaja.objects.filter(
                    idcaja=caja
                ).order_by('-idmovcaja').first()
                
                saldo_actual = ultimo_movimiento.saldomovcaja if ultimo_movimiento else caja.montoinicialcaja

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
                registrar_actividad(
                    request,
                    'CIERRE_CAJA',
                    f'Cierre de caja - Diferencia: ${diferencia:.2f}',
                    detalles={
                        'caja_id': caja.idcaja,
                        'diferencia': float(diferencia)
                    },
                    nivel='WARNING' if abs(diferencia) > 100 else 'INFO'
                )
            elif diferencia > 0:
                messages.success(request, f"✅ Caja cerrada. ⚠ SOBRANTE: ${diferencia:.2f}")
                registrar_actividad(
                    request,
                    'CIERRE_CAJA',
                    f'Cierre de caja - Diferencia: ${diferencia:.2f}',
                    detalles={
                        'caja_id': caja.idcaja,
                        'diferencia': float(diferencia)
                    },
                    nivel='WARNING' if abs(diferencia) > 100 else 'INFO'
                )
            else:
                messages.success(request, f"✅ Caja cerrada. ⚠ FALTANTE: ${abs(diferencia):.2f}")
                registrar_actividad(
                    request,
                    'CIERRE_CAJA',
                    f'Cierre de caja - Diferencia: ${diferencia:.2f}',
                    detalles={
                        'caja_id': caja.idcaja,
                        'diferencia': float(diferencia)
                    },
                    nivel='WARNING' if abs(diferencia) > 100 else 'INFO'
                )
                
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
        "total_efectivo_esperado": total_efectivo_esperado,
        "movimientos_caja": movimientos_caja
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




@permiso_requerido(['Administrador', 'Cajero'])
def movimientos_caja_menu_view(request):
    """Vista del menú de movimientos de caja"""
    usuario_id = request.session.get('usuario_id')
    
    # Verificar si el usuario es administrador
    from nombredeapp.models import Roles, UsuxRoles
    roles_usuario = list(
        Roles.objects.filter(usuxroles__idusuarios_id=usuario_id).values_list('nombrerol', flat=True)
    )
    is_admin = 'Administrador' in roles_usuario or 'Recursos Humanos' in roles_usuario
    
    return render(request, "movimientos_caja_menu.html", {
        "usuario_nombre": request.session.get('nombre_usuario', 'Usuario'),
        "is_admin": is_admin
    })

@permiso_requerido(['Administrador'])
def agregar_movimiento_caja_view(request):
    """Vista para agregar movimiento de caja (solo admin)"""
    usuario_id = request.session.get('usuario_id')
    usuario_nombre = request.session.get('nombre_usuario', 'Usuario')
    
    # Obtener caja activa si existe
    id_caja = request.session.get('id_caja')
    caja_activa = None
    if id_caja:
        try:
            caja_activa = Caja.objects.get(idcaja=id_caja)
        except Caja.DoesNotExist:
            pass
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            tipo_movimiento = request.POST.get('tipo')
            concepto = request.POST.get('concepto')
            valor = float(request.POST.get('valor', 0))
            
            if not tipo_movimiento or not concepto:
                messages.error(request, '❌ Tipo y Concepto son obligatorios')
                return redirect('caja:agregar_movimiento_caja')
            
            # Validar que el valor sea positivo
            if valor <= 0:
                messages.error(request, '❌ El valor debe ser mayor a 0')
                return redirect('caja:agregar_movimiento_caja')
            
            # Obtener último movimiento para calcular saldo
            ultimo_movimiento = Movimientosdecaja.objects.filter(
                idcaja=caja_activa
            ).order_by('-idmovcaja').first()
            
            saldo_actual = ultimo_movimiento.saldomovcaja if ultimo_movimiento else (caja_activa.montoinicialcaja if caja_activa else 0)
            
            # Calcular nuevo saldo según el tipo
            if tipo_movimiento == 'INGRESO':
                nuevo_saldo = saldo_actual + valor
            else:  # EGRESO
                if valor > saldo_actual:
                    messages.error(request, '❌ No hay suficiente saldo en la caja para este egreso')
                    return redirect('caja:agregar_movimiento_caja')
                nuevo_saldo = saldo_actual - valor
            
            # Crear movimiento
            ahora = datetime.now()
            movimiento = Movimientosdecaja.objects.create(
                nombreusuariomovcaja=usuario_nombre,
                fechamovcaja=ahora.date(),
                horamovcaja=ahora.time(),
                nombrecajamovcaja=caja_activa.nombrecaja if caja_activa else 'Caja General',
                tipomovcaja=tipo_movimiento,
                conceptomovcaja=concepto,
                valormovcaja=valor,
                saldomovcaja=nuevo_saldo,
                idusuarios_id=usuario_id,
                idcaja=caja_activa
            )
            
            messages.success(request, '✅ Movimiento registrado correctamente')
            registrar_actividad(
                request,
                'MOVIMIENTO_CAJA',
                f'Movimiento de caja: {tipo_movimiento} - {concepto} - ${valor}',
                detalles={
                    'tipo': tipo_movimiento,
                    'concepto': concepto,
                    'valor': float(valor),
                    'saldo': float(nuevo_saldo)
                }
            )
            return redirect('caja:movimientos_caja_menu')
            
        except Exception as e:
            messages.error(request, f'❌ Error al registrar movimiento: {str(e)}')
    
    # Opciones actualizadas para los selects
    tipos_movimiento = [
        ('APERTURA', 'Apertura'),
        ('INGRESO', 'Ingreso'),
        ('EGRESO', 'Egreso'),
        ('CIERRE', 'Cierre'),
    ]
    
    conceptos = [
        'Arqueo final',
        'Venta de Producto', 
        'Pago de sueldos',
        'Fondo Inicial',
        'Pago de servicios',
        'Pago Proveedor',
        'Transf. a Caja',
        'Gastos varios',
        'Ajuste de caja',
        'Otros'
    ]
    
    return render(request, "agregar_movimiento_caja.html", {
        "usuario_nombre": usuario_nombre,
        "fecha_actual": datetime.now().strftime("%d/%m/%Y"),
        "hora_actual": datetime.now().strftime("%H:%M"),
        "caja_activa": caja_activa,
        "tipos_movimiento": tipos_movimiento,
        "conceptos": conceptos
    })

@permiso_requerido(['Administrador', 'Cajero'])
def ver_movimientos_caja_view(request):
    """Vista para ver movimientos de caja con filtros"""
    movimientos = Movimientosdecaja.objects.all().order_by('-fechamovcaja', '-horamovcaja')
    
    # Aplicar filtros
    usuario_filter = request.GET.get('usuario')
    caja_filter = request.GET.get('caja')
    tipo_filter = request.GET.get('tipo')
    concepto_filter = request.GET.get('concepto')
    fecha_filter = request.GET.get('fecha')
    mes_filter = request.GET.get('mes')
    año_filter = request.GET.get('año')
    
    if usuario_filter:
        movimientos = movimientos.filter(nombreusuariomovcaja__icontains=usuario_filter)
    if caja_filter:
        movimientos = movimientos.filter(nombrecajamovcaja__icontains=caja_filter)
    if tipo_filter:
        movimientos = movimientos.filter(tipomovcaja=tipo_filter)
    if concepto_filter:
        movimientos = movimientos.filter(conceptomovcaja__icontains=concepto_filter)
    if fecha_filter:
        movimientos = movimientos.filter(fechamovcaja=fecha_filter)
    if mes_filter:
        movimientos = movimientos.filter(fechamovcaja__month=mes_filter)
    if año_filter:
        movimientos = movimientos.filter(fechamovcaja__year=año_filter)
    
    # Obtener valores únicos para los filtros
    usuarios = Movimientosdecaja.objects.values_list('nombreusuariomovcaja', flat=True).distinct()
    cajas = Movimientosdecaja.objects.values_list('nombrecajamovcaja', flat=True).distinct()
    
    # Opciones actualizadas para los filtros
    tipos = ['APERTURA', 'INGRESO', 'EGRESO', 'CIERRE']
    
    conceptos = [
        'Arqueo final',
        'Venta de Producto', 
        'Pago de sueldos',
        'Fondo Inicial',
        'Pago de servicios',
        'Pago Proveedor',
        'Transf. a Caja',
        'Gastos varios',
        'Ajuste de caja',
        'Otros'
    ]
    
    meses = [
        ('01', 'Enero - 01'),
        ('02', 'Febrero - 02'), 
        ('03', 'Marzo - 03'),
        ('04', 'Abril - 04'),
        ('05', 'Mayo - 05'),
        ('06', 'Junio - 06'),
        ('07', 'Julio - 07'),
        ('08', 'Agosto - 08'),
        ('09', 'Septiembre - 09'),
        ('10', 'Octubre - 10'),
        ('11', 'Noviembre - 11'),
        ('12', 'Diciembre - 12')
    ]
    
    años = ['2022', '2023', '2024', '2025']
    
    return render(request, "ver_movimientos_caja.html", {
        "movimientos": movimientos,
        "usuarios": usuarios,
        "cajas": cajas,
        "tipos": tipos,
        "conceptos": conceptos,
        "meses": meses,
        "años": años,
        "usuario_nombre": request.session.get('nombre_usuario', 'Usuario'),
        "filtros_activos": {
            'usuario': usuario_filter,
            'caja': caja_filter,
            'tipo': tipo_filter,
            'concepto': concepto_filter,
            'fecha': fecha_filter,
            'mes': mes_filter,
            'año': año_filter,
        }
    })

def api_movimientos_caja(request):
    """API para obtener movimientos de caja (para imprimir)"""
    movimientos = Movimientosdecaja.objects.all().order_by('-fechamovcaja', '-horamovcaja')
    
    # Aplicar mismos filtros que en la vista
    usuario_filter = request.GET.get('usuario')
    caja_filter = request.GET.get('caja')
    tipo_filter = request.GET.get('tipo')
    concepto_filter = request.GET.get('concepto')
    fecha_filter = request.GET.get('fecha')
    mes_filter = request.GET.get('mes')
    año_filter = request.GET.get('año')
    
    if usuario_filter:
        movimientos = movimientos.filter(nombreusuariomovcaja__icontains=usuario_filter)
    if caja_filter:
        movimientos = movimientos.filter(nombrecajamovcaja__icontains=caja_filter)
    if tipo_filter:
        movimientos = movimientos.filter(tipomovcaja=tipo_filter)
    if concepto_filter:
        movimientos = movimientos.filter(conceptomovcaja__icontains=concepto_filter)
    if fecha_filter:
        movimientos = movimientos.filter(fechamovcaja=fecha_filter)
    if mes_filter:
        movimientos = movimientos.filter(fechamovcaja__month=mes_filter)
    if año_filter:
        movimientos = movimientos.filter(fechamovcaja__year=año_filter)
    
    data = []
    for mov in movimientos:
        data.append({
            'fecha': mov.fechamovcaja.strftime('%d/%m/%Y'),
            'hora': mov.horamovcaja.strftime('%H:%M'),
            'usuario': mov.nombreusuariomovcaja,
            'caja': mov.nombrecajamovcaja,
            'tipo': mov.tipomovcaja,
            'concepto': mov.conceptomovcaja,
            'valor': f"${mov.valormovcaja:,.2f}",
            'saldo': f"${mov.saldomovcaja:,.2f}",
        })
    
    return JsonResponse(data, safe=False)

def api_filtros_dependientes(request):
    """API para obtener opciones de filtros dependientes"""
    caja_seleccionada = request.GET.get('caja')
    tipo_seleccionado = request.GET.get('tipo')
    
    # Filtrar movimientos
    movimientos = Movimientosdecaja.objects.all()
    
    if caja_seleccionada:
        movimientos = movimientos.filter(nombrecajamovcaja=caja_seleccionada)
    
    if tipo_seleccionado:
        movimientos = movimientos.filter(tipomovcaja=tipo_seleccionado)
    
    # Obtener opciones únicas
    usuarios = movimientos.values_list('nombreusuariomovcaja', flat=True).distinct()
    tipos = movimientos.values_list('tipomovcaja', flat=True).distinct()
    conceptos = movimientos.values_list('conceptomovcaja', flat=True).distinct()
    
    return JsonResponse({
        'usuarios': list(usuarios),
        'tipos': list(tipos),
        'conceptos': list(conceptos),
    })