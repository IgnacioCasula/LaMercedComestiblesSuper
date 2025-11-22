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
    
    # Obtener información del último cierre CORREGIDA
    ultimo_cierre_info = None
    try:
        ultimo_cierre = Caja.objects.filter(
            idusuarios_id=usuario_id
        ).exclude(
            horacierrecaja=time(0, 0, 0)
        ).order_by('-fechacierrecaja', '-horacierrecaja').first()
        
        if ultimo_cierre:
            # Calcular diferencia CORRECTA: Efectivo físico vs Efectivo sistema
            diferencia = ultimo_cierre.montofinalcaja - ultimo_cierre.efectivo_actual
            
            ultimo_cierre_info = {
                'hora': ultimo_cierre.horacierrecaja.strftime('%H:%M'),
                'fecha': ultimo_cierre.fechacierrecaja.strftime('%d/%m/%Y'),
                'usuario': ultimo_cierre.idusuarios.nombreusuario,
                'diferencia': f"{diferencia:.2f}",
                'monto_final': ultimo_cierre.montofinalcaja,
                'saldo_sistema': ultimo_cierre.saldo_actual,
                'efectivo_sistema': ultimo_cierre.efectivo_actual
            }
            
    except Exception as e:
        print(f"Error obteniendo último cierre: {e}")
    
    # Resto del código igual...
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
            apertura.idsucursal = sucursal
            apertura.montofinalcaja = 0.0
            apertura.horacierrecaja = time(0, 0, 0)
            apertura.fechacierrecaja = apertura.fechaaperturacaja
            apertura.nombrecaja = f"Caja {usuario_nombre}"
            # INICIALIZAR EL SALDO ACTUAL CON EL MONTO INICIAL
            apertura.saldo_actual = apertura.montoinicialcaja
            apertura.efectivo_actual = apertura.montoinicialcaja
            
            apertura.save()
            

            try:
                Movimientosdecaja.objects.create(
                    nombreusuariomovcaja=usuario_nombre,
                    fechamovcaja=ahora.date(),
                    horamovcaja=ahora.time(),
                    nombrecajamovcaja=apertura.nombrecaja,
                    tipomovcaja='APERTURA',
                    conceptomovcaja='Apertura de caja',
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
                    'monto_inicial': float(apertura.montoinicialcaja),
                    'saldo_inicial': float(apertura.saldo_actual),
                    'efectivo_inicial': float(apertura.efectivo_actual)
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
    """Vista mejorada para cierre de caja - MOSTRAR AMBOS SALDOS"""
    usuario_id = request.session.get('usuario_id')
    usuario_nombre = request.session.get('usuario_nombre')
    id_caja = request.session.get('id_caja')
    
    caja = None
    ventas_efectivo = 0
    ventas_tarjeta = 0
    ventas_transferencia = 0
    total_sistema = 0
    efectivo_esperado = 0
    movimientos_caja = []
    
    if id_caja:
        try:
            caja = Caja.objects.get(idcaja=id_caja, idusuarios_id=usuario_id)
            
            if caja.horacierrecaja != time(0, 0, 0):
                messages.warning(request, "Esta caja ya está cerrada.")
                request.session.pop('caja_abierta', None)
                request.session.pop('id_caja', None)
                caja = None
            else:
                hoy = date.today()
                
                # Calcular ventas por método de pago
                ventas_dia = Ventas.objects.filter(
                    idcaja=caja,
                    fechaventa=hoy
                )
                
                ventas_efectivo = ventas_dia.filter(
                    models.Q(metodopago='EFECTIVO') | 
                    models.Q(metodopago='Efectivo')
                ).aggregate(total=models.Sum('totalventa'))['total'] or 0.0
                
                ventas_tarjeta = ventas_dia.filter(
                    models.Q(metodopago='TARJETA DEBITO') |
                    models.Q(metodopago='TARJETA CREDITO') |
                    models.Q(metodopago__icontains='TARJETA')
                ).aggregate(total=models.Sum('totalventa'))['total'] or 0.0
                
                ventas_transferencia = ventas_dia.filter(
                    models.Q(metodopago='TRANSFERENCIA')
                ).aggregate(total=models.Sum('totalventa'))['total'] or 0.0
                
                total_sistema = ventas_efectivo + ventas_tarjeta + ventas_transferencia
                
                # CALCULAR EFECTIVO ESPERADO: Monto inicial + ventas en efectivo
                efectivo_esperado = caja.montoinicialcaja + ventas_efectivo
                
                # Obtener TODOS los movimientos del día (incluyendo ventas)
                movimientos_caja = Movimientosdecaja.objects.filter(
                    idcaja=caja,
                    fechamovcaja=hoy
                ).order_by('horamovcaja')
                
                print(f"📊 Movimientos encontrados: {movimientos_caja.count()}")
                for mov in movimientos_caja:
                    print(f"  - {mov.horamovcaja} | {mov.tipomovcaja} | {mov.conceptomovcaja} | ${mov.valormovcaja}")
                
        except Caja.DoesNotExist:
            messages.error(request, "No se encontró la caja.")
            request.session.pop('caja_abierta', None)
            request.session.pop('id_caja', None)
    
    if request.method == "POST" and caja:
        monto_final_efectivo = request.POST.get('monto_final_efectivo', 0)
        observacion_cierre = request.POST.get('observacion_cierre', '')
        
        try:
            monto_final_efectivo = float(monto_final_efectivo)
            
            # CALCULAR DIFERENCIA CON EL EFECTIVO ESPERADO
            diferencia = monto_final_efectivo - efectivo_esperado
            
            # Cerrar caja
            ahora = datetime.now()
            caja.horacierrecaja = ahora.time()
            caja.fechacierrecaja = ahora.date()
            caja.montofinalcaja = monto_final_efectivo
            
            # Guardar observación si existe
            if hasattr(caja, 'observacioncierre'):
                caja.observacioncierre = observacion_cierre
            
            caja.save()
            
            # Registrar movimiento de CIERRE
            try:
                Movimientosdecaja.objects.create(
                    nombreusuariomovcaja=usuario_nombre,
                    fechamovcaja=ahora.date(),
                    horamovcaja=ahora.time(),
                    nombrecajamovcaja=caja.nombrecaja,
                    tipomovcaja='CIERRE',
                    conceptomovcaja='Cierre de caja',
                    valormovcaja=0,
                    saldomovcaja=caja.saldo_actual,  # Usar saldo actual
                    idusuarios_id=usuario_id,
                    idcaja=caja
                )
            except Exception as e:
                print(f"Error registrando movimiento de cierre: {e}")
            
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
    
    return render(request, "cierredecaja.html", {
        "usuario_nombre": usuario_nombre,
        "fecha_actual": datetime.now().strftime("%d/%m/%Y"),
        "caja": caja,
        "ventas_efectivo": ventas_efectivo,
        "ventas_tarjeta": ventas_tarjeta,
        "ventas_transferencia": ventas_transferencia,
        "total_sistema": total_sistema,
        "efectivo_esperado": efectivo_esperado,
        "movimientos_caja": movimientos_caja,
        "saldo_actual_sistema": caja.saldo_actual if caja else 0,
        "efectivo_actual_sistema": caja.efectivo_actual if caja else 0
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
    """Vista para agregar movimiento de caja (solo admin) - ACTUALIZADA CON SALDO REAL"""
    usuario_id = request.session.get('usuario_id')
    usuario_nombre = request.session.get('nombre_usuario', 'Usuario')
    
    # Obtener caja activa si existe
    id_caja = request.session.get('id_caja')
    caja_activa = None
    saldo_actual = 0
    caja_abierta = False
    
    if id_caja:
        try:
            caja_activa = Caja.objects.get(idcaja=id_caja)
            # Verificar que la caja esté abierta
            if caja_activa.horacierrecaja == time(0, 0, 0):
                caja_abierta = True
                # Usar el saldo actual del modelo (no del último movimiento)
                saldo_actual = caja_activa.saldo_actual
            
        except Caja.DoesNotExist:
            request.session.pop('caja_abierta', None)
            request.session.pop('id_caja', None)
    
    # Si no hay caja abierta, mostrar mensaje de error
    if not caja_abierta and request.method == 'POST':
        messages.error(request, '❌ No hay una caja abierta. Debe abrir una caja para realizar movimientos.')
        return redirect('caja:agregar_movimiento_caja')
    
    if request.method == 'POST' and caja_abierta:
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
            
            # Calcular nuevo saldo según el tipo - ACTUALIZANDO EL SALDO REAL
            if tipo_movimiento == 'INGRESO':
                nuevo_saldo = saldo_actual + valor
            else:  # EGRESO
                if valor > saldo_actual:
                    messages.error(request, f'❌ No hay suficiente saldo en la caja. Saldo actual: ${saldo_actual:.2f}')
                    return redirect('caja:agregar_movimiento_caja')
                nuevo_saldo = saldo_actual - valor
            nuevo_saldo = actualizar_saldo_caja(caja_activa, valor, tipo_movimiento == 'INGRESO')
            # ACTUALIZAR EL SALDO REAL DE LA CAJA
            caja_activa.saldo_actual = nuevo_saldo
            caja_activa.save()
            
            # Crear movimiento
            ahora = datetime.now()
            movimiento = Movimientosdecaja.objects.create(
                nombreusuariomovcaja=usuario_nombre,
                fechamovcaja=ahora.date(),
                horamovcaja=ahora.time(),
                nombrecajamovcaja=caja_activa.nombrecaja,
                tipomovcaja=tipo_movimiento,
                conceptomovcaja=concepto,
                valormovcaja=valor,
                saldomovcaja=nuevo_saldo,  # Este es el saldo calculado
                idusuarios_id=usuario_id,
                idcaja=caja_activa
            )
            
            messages.success(request, f'✅ Movimiento registrado correctamente. Nuevo saldo: ${nuevo_saldo:.2f}')
            registrar_actividad(
                request,
                'MOVIMIENTO_CAJA',
                f'Movimiento de caja: {tipo_movimiento} - {concepto} - ${valor}',
                detalles={
                    'tipo': tipo_movimiento,
                    'concepto': concepto,
                    'valor': float(valor),
                    'saldo_anterior': float(saldo_actual),
                    'saldo_nuevo': float(nuevo_saldo)
                }
            )
            return redirect('caja:movimientos_caja_menu')
            
        except Exception as e:
            messages.error(request, f'❌ Error al registrar movimiento: {str(e)}')
    
    # El resto del código permanece igual...
    tipos_movimiento = [
        ('INGRESO', 'Ingreso'),
        ('EGRESO', 'Egreso'),
    ]
    
    conceptos_por_tipo = {
        'INGRESO': [
            'Venta de Producto',
            'Ajuste de caja',
            'Transf. a Caja',
            'Otros ingresos'
        ],
        'EGRESO': [
            'Pago de sueldos',
            'Pago a Proveedor',
            'Pago de servicios',
            'Gastos varios',
            'Transf. desde Caja',
            'Otros egresos'
        ]
    }
    
    import json
    conceptos_por_tipo_json = json.dumps(conceptos_por_tipo)
    
    return render(request, "agregar_movimiento_caja.html", {
        "usuario_nombre": usuario_nombre,
        "fecha_actual": datetime.now().strftime("%d/%m/%Y"),
        "hora_actual": datetime.now().strftime("%H:%M"),
        "caja_activa": caja_activa,
        "caja_abierta": caja_abierta,
        "saldo_actual": saldo_actual,
        "tipos_movimiento": tipos_movimiento,
        "conceptos_por_tipo": conceptos_por_tipo,
        "conceptos_por_tipo_json": conceptos_por_tipo_json
    })

@permiso_requerido(['Administrador', 'Cajero'])
def ver_movimientos_caja_view(request):
    """Vista para ver movimientos de caja con filtros MEJORADA"""
    movimientos = Movimientosdecaja.objects.all().order_by('-fechamovcaja', '-horamovcaja')
    
    # Aplicar filtros
    usuario_filter = request.GET.get('usuario')
    caja_filter = request.GET.get('caja')
    tipo_filter = request.GET.get('tipo')
    concepto_filter = request.GET.get('concepto')
    fecha_filter = request.GET.get('fecha')
    mes_filter = request.GET.get('mes')
    año_filter = request.GET.get('año')
    
    # Aplicar filtros de manera más robusta
    if usuario_filter and usuario_filter != '':
        movimientos = movimientos.filter(nombreusuariomovcaja__icontains=usuario_filter)
    if caja_filter and caja_filter != '':
        # Filtrar solo por nombre base de caja (sin fecha/hora)
        movimientos = movimientos.filter(
            models.Q(nombrecajamovcaja__icontains=caja_filter) |
            models.Q(nombrecajamovcaja__icontains=caja_filter.split(' - ')[0] if ' - ' in caja_filter else caja_filter)
        )
    if tipo_filter and tipo_filter != '':
        movimientos = movimientos.filter(tipomovcaja=tipo_filter)
    if concepto_filter and concepto_filter != '':
        # Simplificar conceptos para filtro
        conceptos_simplificados = {
            'efectivo': 'EFECTIVO',
            'tarjeta': 'TARJETA',
            'débito': 'DEBITO',
            'crédito': 'CREDITO',
            'transferencia': 'TRANSFERENCIA',
            'apertura': 'Apertura de caja',
            'cierre': 'Cierre de caja'
        }
        
        concepto_simple = conceptos_simplificados.get(concepto_filter.lower(), concepto_filter)
        movimientos = movimientos.filter(conceptomovcaja__icontains=concepto_simple)
    
    # Resto del código igual...
    if fecha_filter and fecha_filter != '':
        movimientos = movimientos.filter(fechamovcaja=fecha_filter)
    if mes_filter and mes_filter != '':
        try:
            movimientos = movimientos.filter(fechamovcaja__month=int(mes_filter))
        except (ValueError, TypeError):
            pass  # Ignorar si el valor no es válido
    if año_filter and año_filter != '':
        try:
            movimientos = movimientos.filter(fechamovcaja__year=int(año_filter))
        except (ValueError, TypeError):
            pass  # Ignorar si el valor no es válido
    
    # Obtener valores únicos para los filtros (excluyendo valores vacíos o nulos)
    usuarios = Movimientosdecaja.objects.exclude(
        nombreusuariomovcaja__isnull=True
    ).exclude(
        nombreusuariomovcaja=''
    ).values_list('nombreusuariomovcaja', flat=True).distinct().order_by('nombreusuariomovcaja')
    
    cajas = Movimientosdecaja.objects.exclude(
        nombrecajamovcaja__isnull=True
    ).exclude(
        nombrecajamovcaja=''
    ).values_list('nombrecajamovcaja', flat=True).distinct().order_by('nombrecajamovcaja')
    
    # Opciones para los filtros
    tipos = ['APERTURA', 'INGRESO', 'EGRESO', 'CIERRE']
    
    conceptos = Movimientosdecaja.objects.exclude(
        conceptomovcaja__isnull=True
    ).exclude(
        conceptomovcaja=''
    ).values_list('conceptomovcaja', flat=True).distinct().order_by('conceptomovcaja')
    
    meses = [
        ('1', 'Enero'),
        ('2', 'Febrero'), 
        ('3', 'Marzo'),
        ('4', 'Abril'),
        ('5', 'Mayo'),
        ('6', 'Junio'),
        ('7', 'Julio'),
        ('8', 'Agosto'),
        ('9', 'Septiembre'),
        ('10', 'Octubre'),
        ('11', 'Noviembre'),
        ('12', 'Diciembre')
    ]
    
    # Obtener años únicos de la base de datos
    años = Movimientosdecaja.objects.dates('fechamovcaja', 'year').order_by('-fechamovcaja')
    años_list = [str(año.year) for año in años]
    
    return render(request, "ver_movimientos_caja.html", {
        "movimientos": movimientos,
        "usuarios": usuarios,
        "cajas": cajas,
        "tipos": tipos,
        "conceptos": conceptos,
        "meses": meses,
        "años": años_list,
        "usuario_nombre": request.session.get('nombre_usuario', 'Usuario'),
        "filtros_activos": {
            'usuario': usuario_filter or '',
            'caja': caja_filter or '',
            'tipo': tipo_filter or '',
            'concepto': concepto_filter or '',
            'fecha': fecha_filter or '',
            'mes': mes_filter or '',
            'año': año_filter or '',
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
    """API para obtener opciones de filtros dependientes - MEJORADA"""
    caja_seleccionada = request.GET.get('caja', '')
    tipo_seleccionado = request.GET.get('tipo', '')
    
    # Filtrar movimientos
    movimientos = Movimientosdecaja.objects.all()
    
    if caja_seleccionada and caja_seleccionada != '':
        movimientos = movimientos.filter(nombrecajamovcaja__icontains=caja_seleccionada)
    
    if tipo_seleccionado and tipo_seleccionado != '':
        movimientos = movimientos.filter(tipomovcaja=tipo_seleccionado)
    
    # Obtener opciones únicas (excluyendo vacíos)
    usuarios = movimientos.exclude(
        nombreusuariomovcaja__isnull=True
    ).exclude(
        nombreusuariomovcaja=''
    ).values_list('nombreusuariomovcaja', flat=True).distinct().order_by('nombreusuariomovcaja')
    
    tipos = movimientos.exclude(
        tipomovcaja__isnull=True
    ).exclude(
        tipomovcaja=''
    ).values_list('tipomovcaja', flat=True).distinct().order_by('tipomovcaja')
    
    conceptos = movimientos.exclude(
        conceptomovcaja__isnull=True
    ).exclude(
        conceptomovcaja=''
    ).values_list('conceptomovcaja', flat=True).distinct().order_by('conceptomovcaja')
    
    return JsonResponse({
        'usuarios': list(usuarios),
        'tipos': list(tipos),
        'conceptos': list(conceptos),
    })

def actualizar_saldo_caja(caja, monto, es_ingreso=True):
    """Actualiza el saldo de la caja de manera segura"""
    if es_ingreso:
        caja.saldo_actual += monto
    else:
        caja.saldo_actual -= monto
    caja.save()
    return caja.saldo_actual

def actualizar_saldos_caja(caja, monto, es_efectivo=True, es_ingreso=True):
    """Actualiza ambos saldos de la caja de manera segura"""
    if es_ingreso:
        caja.saldo_actual += monto
        if es_efectivo:
            caja.efectivo_actual += monto
    else:
        caja.saldo_actual -= monto
        if es_efectivo:
            caja.efectivo_actual -= monto
    
    caja.save()
    return caja.saldo_actual, caja.efectivo_actual