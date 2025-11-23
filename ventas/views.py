from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone
from django.contrib import messages
import json
from caja.models import Caja, Productos, Ventas, Movimientosdecaja, DetalleDeVentas, Inventarios, Ofertas
from .forms import VentaForm, RecargoForm
from caja.views import actualizar_saldo_caja



def registrar_venta(request):
    """Vista para registrar una nueva venta"""
    
    # 🔥 DIAGNÓSTICO MEJORADO
    print("🔍 INICIANDO VISTA REGISTRAR_VENTA")
    
    # USAR LA MISMA LÓGICA QUE CAJA/VIEWS.PY (SESSION)
    id_caja = request.session.get('id_caja')
    caja_activa = None
    
    print(f"🔍 ID Caja desde session: {id_caja}")
    
    if id_caja:
        try:
            caja_activa = Caja.objects.get(idcaja=id_caja)
            print(f"✅ Caja activa encontrada: {caja_activa.nombrecaja}")
        except Caja.DoesNotExist:
            print("❌ Caja no existe en BD")
            request.session.pop('caja_abierta', None)
            request.session.pop('id_caja', None)
    
    if not caja_activa:
        print("❌ No hay caja activa - redirigiendo")
        messages.error(request, '❌ Debe tener una caja activa para registrar ventas')
        return redirect('caja:menu_caja')
    
    # Obtener productos disponibles en la sucursal
    productos_disponibles = Productos.objects.filter(
        inventarios__sucursal=caja_activa.idsucursal,
        inventarios__cantidad__gt=0
    ).distinct()
    
    print(f"🔍 Productos disponibles: {productos_disponibles.count()}")
    print(f"🔍 Sucursal activa: {caja_activa.idsucursal.nombresucursal} (ID: {caja_activa.idsucursal.idsucursal})")
    
    # DEBUG: Verificar "Yogur Natural" específicamente
    yogur_natural = Productos.objects.filter(nombreproductos__icontains="Yogur Natural").first()
    if yogur_natural:
        inventario_yogur = Inventarios.objects.filter(
            producto=yogur_natural,
            sucursal=caja_activa.idsucursal
        ).first()
        print(f"🔍 Yogur Natural encontrado - ID: {yogur_natural.idproducto}, Stock en sucursal: {inventario_yogur.cantidad if inventario_yogur else 0}")
    
    # DEBUG: Verificar "Yogur Bebible Sancor Frutilla"
    yogur_frutilla = Productos.objects.filter(nombreproductos__icontains="Yogur Bebible Sancor Frutilla").first()
    if yogur_frutilla:
        inventario_frutilla = Inventarios.objects.filter(
            producto=yogur_frutilla,
            sucursal=caja_activa.idsucursal
        ).first()
        print(f"🔍 Yogur Bebible Sancor Frutilla encontrado - ID: {yogur_frutilla.idproducto}, Stock en sucursal: {inventario_frutilla.cantidad if inventario_frutilla else 0}")
    else:
        print(f"⚠️  Yogur Bebible Sancor Frutilla NO existe en la base de datos")
    
    # Preparar datos para JavaScript
    productos_json = {}
    for producto in productos_disponibles:
        inventario = Inventarios.objects.filter(
            producto=producto,
            sucursal=caja_activa.idsucursal
        ).first()
        if inventario:
            productos_json[str(producto.idproducto)] = {
                'nombre': producto.nombreproductos,
                'precio': float(producto.precioproducto),
                'stock': inventario.cantidad if inventario else 0,
                'codigo_barras': producto.codigobarraproducto if producto.codigobarraproducto else None,
                'marca': producto.marcaproducto if producto.marcaproducto else 'N/A'
            }
            print(f"  📦 {producto.nombreproductos} - Stock: {inventario.cantidad}, Código: {producto.codigobarraproducto}, Marca: {producto.marcaproducto}")
    
    print(f"🔍 Productos JSON preparados: {len(productos_json)} productos")
    
    # Debug: mostrar nombres de productos
    print("📋 Productos que se pasarán al template:")
    for prod_id, prod_data in productos_json.items():
        print(f"  - {prod_data['nombre']} (ID: {prod_id})")
    
    venta_form = VentaForm()
    recargo_form = RecargoForm()
    
    return render(request, 'HTML/registrar_venta.html', {
        'venta_form': venta_form,
        'recargo_form': recargo_form,
        'productos_json': json.dumps(productos_json),  # Para JavaScript
        'productos_dict': productos_json,  # Para el template (datalist)
        'caja_activa': caja_activa,
        'sucursal': caja_activa.idsucursal,
        'today': timezone.now(),
        'usuario_nombre': request.session.get('nombre_usuario', 'Usuario')
    })

def buscar_producto(request):
    """API para buscar productos"""
    if request.method == 'GET' and 'q' in request.GET:
        query = request.GET.get('q', '').lower()
        
        print(f"🔍 API Buscar producto: '{query}'")
        
        # USAR LA MISMA LÓGICA QUE CAJA/VIEWS.PY (SESSION)
        id_caja = request.session.get('id_caja')
        caja_activa = None
        
        if id_caja:
            try:
                caja_activa = Caja.objects.get(idcaja=id_caja)
            except Caja.DoesNotExist:
                return JsonResponse([], safe=False)
        
        if not caja_activa:
            return JsonResponse([], safe=False)
        
        productos = Productos.objects.filter(
            nombreproductos__icontains=query,
            inventarios__sucursal=caja_activa.idsucursal,
            inventarios__cantidad__gt=0
        ).distinct()[:10]
        
        resultados = []
        for producto in productos:
            inventario = Inventarios.objects.filter(
                producto=producto,
                sucursal=caja_activa.idsucursal
            ).first()
            if inventario:
                resultados.append({
                    'id': producto.idproducto,
                    'nombre': producto.nombreproductos,
                    'precio': float(producto.precioproducto),
                    'stock': inventario.cantidad,
                    'codigo_barras': producto.codigobarraproducto
                })
        
        print(f"🔍 API Resultados: {len(resultados)} productos")
        return JsonResponse(resultados, safe=False)
    
    return JsonResponse([], safe=False)

@csrf_exempt
def procesar_venta(request):
    """API para procesar venta via AJAX - CORREGIDO ZONA HORARIA"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            print("🔍 API Procesar venta recibida")
            
            # USAR LA MISMA LÓGICA QUE CAJA/VIEWS.PY (SESSION)
            id_caja = request.session.get('id_caja')
            caja_activa = None
            
            if id_caja:
                try:
                    caja_activa = Caja.objects.get(idcaja=id_caja)
                except Caja.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'No hay caja activa'
                    })
            
            if not caja_activa:
                return JsonResponse({
                    'success': False,
                    'error': 'No hay caja activa'
                })
            
            # Obtener método de pago
            metodo_pago = data.get('metodo_pago', 'EFECTIVO')
            es_efectivo = metodo_pago.upper() in ['EFECTIVO', 'EFECTIVO']
            
            print(f"💰 Método de pago: {metodo_pago}, Es efectivo: {es_efectivo}")
            
            # Obtener oferta por defecto
            oferta_default = Ofertas.objects.first()
            if not oferta_default:
                primer_producto = Productos.objects.first()
                if primer_producto:
                    oferta_default = Ofertas.objects.create(
                        nombreoferta='Sin Oferta',
                        descripcionoferta='Precio regular',
                        fechainiciooferta=timezone.now().date(),
                        fechafinoferta=timezone.now().date(),
                        valordescuento=0,
                        idproducto=primer_producto
                    )
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'No hay productos en el sistema'
                    })
            
            with transaction.atomic():
                # ✅ USAR timezone.localtime() PARA OBTENER LA HORA LOCAL CORRECTA
                ahora = timezone.localtime(timezone.now())
                
                # Crear la venta
                venta = Ventas(
                    totalventa=0,
                    metodopago=metodo_pago,
                    estadoventa='COMPLETADA',
                    fechaventa=ahora.date(),
                    horaventa=ahora.time(),
                    idusuarios_id=request.session.get('usuario_id'),
                    idofertas=oferta_default,
                    idcaja=caja_activa
                )
                venta.save()
                
                # Procesar detalles
                total_venta = 0
                for item in data.get('items', []):
                    producto = get_object_or_404(Productos, idproducto=item['producto_id'])
                    
                    # Verificar inventario
                    inventario = Inventarios.objects.filter(
                        producto=producto,
                        sucursal=caja_activa.idsucursal
                    ).first()
                    
                    if not inventario or inventario.cantidad < item['cantidad']:
                        raise Exception(f'Stock insuficiente para {producto.nombreproductos}')
                    
                    # Crear detalle
                    subtotal = item['cantidad'] * producto.precioproducto
                    detalle = DetalleDeVentas(
                        cantidadvendida=item['cantidad'],
                        preciounitariodv=producto.precioproducto,
                        subtotaldv=subtotal,
                        idventa=venta,
                        idproducto=producto
                    )
                    detalle.save()
                    
                    total_venta += subtotal
                    
                    # Actualizar inventario
                    inventario.cantidad -= item['cantidad']
                    inventario.save()
                
                # Aplicar recargo
                recargo = data.get('recargo', 0) or 0
                total_venta += recargo
                
                # Actualizar venta
                venta.totalventa = total_venta
                venta.save()
                
                # ACTUALIZAR CAJA SEGÚN MÉTODO DE PAGO
                if es_efectivo:
                    caja_activa.saldo_actual += total_venta
                    caja_activa.efectivo_actual += total_venta
                else:
                    caja_activa.saldo_actual += total_venta
                
                caja_activa.save()
                
                # ✅ REGISTRAR MOVIMIENTO DE CAJA CON LA MISMA HORA LOCAL
                try:
                    concepto_movimiento = f"VENTA - {metodo_pago}"
                    
                    Movimientosdecaja.objects.create(
                        nombreusuariomovcaja=request.session.get('nombre_usuario', 'Usuario'),
                        fechamovcaja=ahora.date(),
                        horamovcaja=ahora.time(),  # ✅ MISMA HORA LOCAL
                        nombrecajamovcaja=caja_activa.nombrecaja,
                        tipomovcaja='INGRESO',
                        conceptomovcaja=concepto_movimiento,
                        valormovcaja=total_venta,
                        saldomovcaja=caja_activa.saldo_actual,
                        idusuarios_id=request.session.get('usuario_id'),
                        idcaja=caja_activa
                    )
                    print(f"✅ Movimiento de caja registrado: ${total_venta} a las {ahora.time()}")
                    
                except Exception as e:
                    print(f"❌ Error registrando movimiento de caja: {e}")

                print(f"✅ Venta procesada exitosamente: #{venta.idventa}")
                print(f"💰 Método pago: {metodo_pago}, Total: ${total_venta}")
                print(f"🕐 Hora registrada: {ahora.time()}")
                print(f"📊 Nuevo saldo: ${caja_activa.saldo_actual}")
                
                return JsonResponse({
                    'success': True,
                    'venta_id': venta.idventa,
                    'total': float(total_venta),
                    'fecha': venta.fechaventa.strftime('%d/%m/%Y'),
                    'hora': venta.horaventa.strftime('%H:%M'),
                    'metodo_pago': metodo_pago,
                    'nuevo_saldo': float(caja_activa.saldo_actual),
                    'nuevo_efectivo': float(caja_activa.efectivo_actual),
                    'hora_registrada': ahora.time().strftime('%H:%M')  # Para debugging
                })
                
        except Exception as e:
            print(f"❌ Error procesando venta: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})