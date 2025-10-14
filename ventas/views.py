from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone
from django.contrib import messages
import json
from caja.models import Caja, Productos, Ventas, DetalleDeVentas, Inventarios, Ofertas
from nombredeapp.decorators import permiso_requerido
from .forms import VentaForm, RecargoForm

@permiso_requerido(roles_permitidos=['Supervisor de Caja'])
def registrar_venta(request):
    """Vista para registrar una nueva venta"""
    
    # USAR LA MISMA LÓGICA QUE CAJA/VIEWS.PY (SESSION)
    id_caja = request.session.get('id_caja')
    caja_activa = None
    
    if id_caja:
        try:
            caja_activa = Caja.objects.get(idcaja=id_caja)
        except Caja.DoesNotExist:
            # Si no existe en BD, limpiar session
            request.session.pop('caja_abierta', None)
            request.session.pop('id_caja', None)
    
    if not caja_activa:
        messages.error(request, '❌ Debe tener una caja activa para registrar ventas')
        return redirect('caja:menu_caja')
    
    # Obtener productos disponibles en la sucursal
    productos_disponibles = Productos.objects.filter(
        inventarios__sucursal=caja_activa.idsucursal,
        inventarios__cantidad__gt=0
    ).distinct()
    
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
                'stock': inventario.cantidad,
                'codigo_barras': producto.codigobarraproducto
            }
    
    venta_form = VentaForm()
    recargo_form = RecargoForm()
    
    return render(request, 'HTML/registrar_venta.html', {
        'venta_form': venta_form,
        'recargo_form': recargo_form,
        'productos_json': json.dumps(productos_json),
        'caja_activa': caja_activa,
        'sucursal': caja_activa.idsucursal,
        'today': timezone.now(),
        'usuario_nombre': request.session.get('nombre_usuario', 'Usuario')
    })

@permiso_requerido(roles_permitidos=['Supervisor de Caja'])
def buscar_producto(request):
    """API para buscar productos"""
    if request.method == 'GET' and 'q' in request.GET:
        query = request.GET.get('q', '').lower()
        
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
        
        return JsonResponse(resultados, safe=False)
    
    return JsonResponse([], safe=False)

@csrf_exempt
@permiso_requerido(roles_permitidos=['Supervisor de Caja'])
def procesar_venta(request):
    """API para procesar venta via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
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
            
            # Obtener oferta por defecto (usar la primera disponible)
            oferta_default = Ofertas.objects.first()
            if not oferta_default:
                # Crear una oferta por defecto si no existe
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
                # Crear la venta
                venta = Ventas(
                    totalventa=0,
                    metodopago=data.get('metodo_pago', 'EFECTIVO'),
                    estadoventa='COMPLETADA',
                    fechaventa=timezone.now().date(),
                    horaventa=timezone.now().time(),
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
                
                return JsonResponse({
                    'success': True,
                    'venta_id': venta.idventa,
                    'total': float(total_venta),
                    'fecha': venta.fechaventa.strftime('%d/%m/%Y'),
                    'hora': venta.horaventa.strftime('%H:%M')
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})