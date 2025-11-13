from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone
from django.contrib import messages
import json
from django.db.models import Q

# Importar modelos existentes
from caja.models import Caja, Productos, Ventas, Movimientosdecaja, DetalleDeVentas, Inventarios, Ofertas, Usuarios, Sucursales

class SistemaVentas:
    """Clase principal para gestionar el sistema de ventas"""
    
    @staticmethod
    def verificar_caja_activa(request):
        """Verificar si hay una caja activa en la sesión"""
        id_caja = request.session.get('id_caja')
        if not id_caja:
            return None, "No hay caja activa"
        
        try:
            caja_activa = Caja.objects.get(idcaja=id_caja)
            return caja_activa, None
        except Caja.DoesNotExist:
            return None, "La caja activa no existe"

    @staticmethod
    def obtener_productos_disponibles(caja_activa):
        """Obtener productos disponibles en la sucursal"""
        return Productos.objects.filter(
            inventarios__sucursal=caja_activa.idsucursal,
            inventarios__cantidad__gt=0
        ).distinct()

def registrar_venta(request):
    """Vista principal para registrar ventas"""
    
    # Verificar caja activa
    caja_activa, error = SistemaVentas.verificar_caja_activa(request)
    if error:
        messages.error(request, f'❌ {error}')
        return redirect('caja:menu_caja')
    
    # Obtener productos disponibles
    try:
        productos_disponibles = SistemaVentas.obtener_productos_disponibles(caja_activa)
        
        # Preparar datos para el template
        productos_data = {}
        for producto in productos_disponibles:
            inventario = Inventarios.objects.filter(
                producto=producto,
                sucursal=caja_activa.idsucursal
            ).first()
            
            if inventario:
                productos_data[producto.idproducto] = {
                    'id': producto.idproducto,
                    'nombre': producto.nombreproductos,
                    'precio': float(producto.precioproducto),
                    'stock': inventario.cantidad,
                    'codigo_barras': producto.codigobarraproducto,
                    'marca': producto.marcaproducto,
                    'categoria': producto.idcategoria.nombrecategoria if producto.idcategoria else 'Sin categoría'
                }
        
    except Exception as e:
        print(f"Error obteniendo productos: {e}")
        productos_data = {}
        messages.warning(request, '⚠️ Error al cargar productos disponibles')
    
    context = {
        'caja_activa': caja_activa,
        'sucursal': caja_activa.idsucursal,
        'usuario_nombre': request.session.get('nombre_usuario', 'Cajero'),
        'productos_json': json.dumps(productos_data),
        'today': timezone.now(),
    }
    
    return render(request, 'ventas/nueva_venta.html', context)

def buscar_productos(request):
    """API para búsqueda en tiempo real de productos"""
    if request.method == 'GET':
        query = request.GET.get('q', '').strip()
        
        if len(query) < 2:
            return JsonResponse({'resultados': []})
        
        # Verificar caja activa
        caja_activa, error = SistemaVentas.verificar_caja_activa(request)
        if error:
            return JsonResponse({'resultados': [], 'error': error})
        
        try:
            # Búsqueda flexible por nombre, marca o código de barras
            productos = Productos.objects.filter(
                Q(nombreproductos__icontains=query) |
                Q(marcaproducto__icontains=query) |
                Q(codigobarraproducto__icontains=query),
                inventarios__sucursal=caja_activa.idsucursal,
                inventarios__cantidad__gt=0
            ).distinct()[:20]
            
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
                        'codigo_barras': producto.codigobarraproducto,
                        'marca': producto.marcaproducto,
                        'categoria': producto.idcategoria.nombrecategoria if producto.idcategoria else 'General'
                    })
            
            # Ordenar por relevancia
            resultados.sort(key=lambda x: (
                0 if x['nombre'].lower().startswith(query.lower()) else
                1 if query.lower() in x['nombre'].lower() else
                2
            ))
            
            return JsonResponse({'resultados': resultados})
            
        except Exception as e:
            print(f"Error en búsqueda: {e}")
            return JsonResponse({'resultados': [], 'error': str(e)})
    
    return JsonResponse({'resultados': []})

@csrf_exempt
@transaction.atomic
def procesar_venta(request):
    """Procesar una venta completa"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print(f"📦 Procesando venta: {data}")
            
            # Verificar caja activa
            caja_activa, error = SistemaVentas.verificar_caja_activa(request)
            if error:
                return JsonResponse({'success': False, 'error': error})
            
            # Obtener usuario actual
            usuario_id = request.session.get('usuario_id')
            if not usuario_id:
                return JsonResponse({'success': False, 'error': 'Usuario no autenticado'})
            
            usuario = Usuarios.objects.get(idusuarios=usuario_id)
            
            # Crear oferta por defecto si no existe
            oferta_default = Ofertas.objects.first()
            if not oferta_default:
                primer_producto = Productos.objects.first()
                oferta_default = Ofertas.objects.create(
                    nombreoferta='Precio Regular',
                    descripcionoferta='Precio sin descuento',
                    fechainiciooferta=timezone.now().date(),
                    fechafinoferta=timezone.now().date() + timezone.timedelta(days=365),
                    valordescuento=0,
                    idproducto=primer_producto
                )
            
            # Crear la venta
            venta = Ventas(
                totalventa=0,  # Se calculará después
                metodopago=data.get('metodo_pago', 'EFECTIVO'),
                estadoventa='COMPLETADA',
                fechaventa=timezone.now().date(),
                horaventa=timezone.now().time(),
                idusuarios=usuario,
                idofertas=oferta_default,
                idcaja=caja_activa
            )
            venta.save()
            
            # Procesar items de la venta
            total_venta = 0
            items_procesados = []
            
            for item in data.get('items', []):
                producto_id = item.get('producto_id')
                cantidad = item.get('cantidad', 1)
                
                producto = get_object_or_404(Productos, idproducto=producto_id)
                
                # Verificar inventario
                inventario = Inventarios.objects.get(
                    producto=producto,
                    sucursal=caja_activa.idsucursal
                )
                
                if inventario.cantidad < cantidad:
                    raise Exception(f'Stock insuficiente para {producto.nombreproductos}')
                
                # Calcular subtotal
                subtotal = cantidad * producto.precioproducto
                total_venta += subtotal
                
                # Crear detalle de venta
                detalle = DetalleDeVentas(
                    cantidadvendida=cantidad,
                    preciounitariodv=producto.precioproducto,
                    subtotaldv=subtotal,
                    idventa=venta,
                    idproducto=producto
                )
                detalle.save()
                
                # Actualizar inventario
                inventario.cantidad -= cantidad
                inventario.save()
                
                items_procesados.append({
                    'producto': producto.nombreproductos,
                    'cantidad': cantidad,
                    'subtotal': subtotal
                })
            
            # Procesar venta rápida (frutas/verduras)
            venta_rapida_total = float(data.get('venta_rapida_total', 0))
            if venta_rapida_total > 0:
                total_venta += venta_rapida_total
                
                # Usar un producto placeholder para la venta rápida
                producto_placeholder = Productos.objects.filter(
                    nombreproductos__icontains='venta'
                ).first() or Productos.objects.first()
                
                DetalleDeVentas.objects.create(
                    cantidadvendida=1,
                    preciounitariodv=venta_rapida_total,
                    subtotaldv=venta_rapida_total,
                    idventa=venta,
                    idproducto=producto_placeholder
                )
            
            # Aplicar recargo
            recargo = float(data.get('recargo', 0))
            total_venta += recargo
            
            # Actualizar total de la venta
            venta.totalventa = total_venta
            venta.save()
            
            # Registrar movimiento de caja
            ultimo_movimiento = Movimientosdecaja.objects.filter(
                idcaja=caja_activa
            ).order_by('-idmovcaja').first()
            
            saldo_anterior = ultimo_movimiento.saldomovcaja if ultimo_movimiento else caja_activa.montoinicialcaja
            nuevo_saldo = saldo_anterior + total_venta
            
            Movimientosdecaja.objects.create(
                nombreusuariomovcaja=usuario.nombreusuario,
                fechamovcaja=timezone.now().date(),
                horamovcaja=timezone.now().time(),
                nombrecajamovcaja=caja_activa.nombrecaja,
                tipomovcaja='VENTA',
                conceptomovcaja=f'Venta #{venta.idventa}',
                valormovcaja=total_venta,
                saldomovcaja=nuevo_saldo,
                idusuarios=usuario,
                idcaja=caja_activa
            )
            
            return JsonResponse({
                'success': True,
                'venta_id': venta.idventa,
                'total': total_venta,
                'fecha': venta.fechaventa.strftime('%d/%m/%Y'),
                'hora': venta.horaventa.strftime('%H:%M'),
                'items_count': len(items_procesados),
                'tiene_venta_rapida': venta_rapida_total > 0
            })
            
        except Exception as e:
            print(f"❌ Error procesando venta: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

def obtener_detalle_venta(request, venta_id):
    """Obtener detalle de una venta para el ticket"""
    try:
        venta = Ventas.objects.get(idventa=venta_id)
        detalles = DetalleDeVentas.objects.filter(idventa=venta)
        
        items = []
        for detalle in detalles:
            items.append({
                'producto': detalle.idproducto.nombreproductos,
                'cantidad': detalle.cantidadvendida,
                'precio_unitario': float(detalle.preciounitariodv),
                'subtotal': float(detalle.subtotaldv)
            })
        
        return JsonResponse({
            'success': True,
            'venta': {
                'id': venta.idventa,
                'fecha': venta.fechaventa.strftime('%d/%m/%Y'),
                'hora': venta.horaventa.strftime('%H:%M'),
                'total': float(venta.totalventa),
                'metodo_pago': venta.metodopago
            },
            'items': items
        })
        
    except Ventas.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Venta no encontrada'})