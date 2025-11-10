from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum, Count, F
from django.utils import timezone
import json
from datetime import datetime, timedelta

from caja.models import (
    Productos, Categorias, Proveedores, Inventarios,
    Sucursales, Usuarios, Roles, DetalleDeVentas, 
    Provxprod, Ventas, Compras, DetalleDeCompras
)

# Importar registrar_actividad desde usuarios.utils
try:
    from .utils import registrar_actividad
except ImportError:
    # Si no existe, crear función dummy
    def registrar_actividad(request, tipo, desc, detalles=None, nivel='INFO'):
        print(f"Log: {tipo} - {desc}")


def verificar_permisos_stock(request):
    """Verifica si el usuario tiene permisos para gestionar stock"""
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return False, None
    
    usuario = Usuarios.objects.filter(idusuarios=usuario_id).first()
    if not usuario:
        return False, None
    
    roles_usuario = list(
        Roles.objects.filter(usuxroles__idusuarios_id=usuario_id).values_list('nombrerol', flat=True)
    )
    
    is_admin = 'Administrador' in roles_usuario or 'Recursos Humanos' in roles_usuario
    has_gestion_stock = any('stock' in rol.lower() or 'inventario' in rol.lower() for rol in roles_usuario)
    
    return (is_admin or has_gestion_stock), usuario


def gestion_de_stock(request):
    """Vista principal de gestión de stock"""
    tiene_permiso, usuario = verificar_permisos_stock(request)
    
    if not tiene_permiso:
        messages.error(request, 'No tienes permisos para acceder a Gestión de Stock.')
        return redirect('inicio')
    
    nombre_usuario = request.session.get('nombre_usuario', 'Usuario')
    sucursal = Sucursales.objects.first()
    
    # Verificar si es admin
    roles_usuario = list(
        Roles.objects.filter(usuxroles__idusuarios_id=usuario.idusuarios).values_list('nombrerol', flat=True)
    )
    is_admin = 'Administrador' in roles_usuario or 'Recursos Humanos' in roles_usuario
    
    context = {
        'usuario_nombre': nombre_usuario,
        'sucursal': sucursal,
        'is_admin': is_admin
    }
    
    return render(request, 'GestionDeStock/index.html', context)


# ===== API: PRODUCTOS =====

@require_http_methods(['GET'])
def api_listar_productos(request):
    """API para listar todos los productos con su inventario"""
    try:
        tiene_permiso, _ = verificar_permisos_stock(request)
        if not tiene_permiso:
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        sucursal_id = request.GET.get('sucursal_id')
        search = request.GET.get('search', '').strip()
        
        productos_query = Productos.objects.select_related('idcategoria').all()
        
        if search:
            productos_query = productos_query.filter(
                Q(nombreproductos__icontains=search) |
                Q(marcaproducto__icontains=search) |
                Q(codigobarraproducto__icontains=search)
            )
        
        productos_list = []
        for producto in productos_query:
            # Obtener inventario
            if sucursal_id:
                inventario = Inventarios.objects.filter(
                    producto=producto,
                    sucursal_id=sucursal_id
                ).first()
            else:
                # Si no hay sucursal específica, sumar todo el inventario
                inventario_total = Inventarios.objects.filter(
                    producto=producto
                ).aggregate(total=Sum('cantidad'))
                stock_total = inventario_total['total'] or 0
                inventario = type('obj', (object,), {'cantidad': stock_total})()
            
            # Obtener proveedor
            proveedor_rel = Provxprod.objects.filter(idproducto=producto).first()
            proveedor_nombre = proveedor_rel.idproveedor.nombreproveedor if proveedor_rel else 'Sin proveedor'
            proveedor_id = proveedor_rel.idproveedor.idproveedor if proveedor_rel else None
            
            productos_list.append({
                'id': producto.idproducto,
                'nombre': producto.nombreproductos,
                'precio': float(producto.precioproducto),
                'marca': producto.marcaproducto,
                'codigo': str(producto.codigobarraproducto),
                'categoria': producto.idcategoria.nombrecategoria if producto.idcategoria else 'Sin categoría',
                'categoria_id': producto.idcategoria.idcategoria if producto.idcategoria else None,
                'proveedor': proveedor_nombre,
                'proveedor_id': proveedor_id,
                'stock': inventario.cantidad if inventario else 0,
                'stockMinimo': 10,
                'imagen': producto.imagenproducto if producto.imagenproducto else None
            })
        
        return JsonResponse(productos_list, safe=False)
    except Exception as e:
        print(f"Error en api_listar_productos: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['POST'])
@transaction.atomic
def api_crear_producto(request):
    """API para crear un nuevo producto"""
    try:
        tiene_permiso, _ = verificar_permisos_stock(request)
        if not tiene_permiso:
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        data = json.loads(request.body)
        
        # Validar campos obligatorios
        if not all([data.get('nombre'), data.get('precio'), data.get('marca'), 
                   data.get('codigo'), data.get('categoria_id')]):
            return JsonResponse({'error': 'Faltan campos obligatorios'}, status=400)
        
        # Validar que el código no exista
        if Productos.objects.filter(codigobarraproducto=data['codigo']).exists():
            return JsonResponse({'error': 'El código de barras ya existe'}, status=400)
        
        # Validar categoría
        try:
            categoria = Categorias.objects.get(idcategoria=data['categoria_id'])
        except Categorias.DoesNotExist:
            return JsonResponse({'error': 'Categoría no encontrada'}, status=404)
        
        # Crear producto
        producto = Productos.objects.create(
            nombreproductos=data['nombre'],
            precioproducto=float(data['precio']),
            marcaproducto=data['marca'],
            codigobarraproducto=int(data['codigo']),
            imagenproducto=data.get('imagen'),
            idcategoria=categoria
        )
        
        # Asociar proveedor si existe
        if data.get('proveedor_id'):
            try:
                proveedor = Proveedores.objects.get(idproveedor=data['proveedor_id'])
                Provxprod.objects.create(
                    idproducto=producto,
                    idproveedor=proveedor
                )
            except Proveedores.DoesNotExist:
                pass
        
        # Crear inventario inicial
        if data.get('sucursal_id'):
            try:
                sucursal = Sucursales.objects.get(idsucursal=data['sucursal_id'])
                cantidad = int(data.get('stock', 0))
                
                Inventarios.objects.create(
                    producto=producto,
                    sucursal=sucursal,
                    cantidad=cantidad
                )
                
                registrar_actividad(
                    request,
                    'CREAR_PRODUCTO',
                    f'Producto creado: {producto.nombreproductos}',
                    detalles={
                        'producto_id': producto.idproducto,
                        'stock_inicial': cantidad,
                        'precio': float(data['precio'])
                    }
                )
            except Sucursales.DoesNotExist:
                pass
        
        return JsonResponse({
            'success': True,
            'message': 'Producto creado correctamente',
            'producto_id': producto.idproducto
        })
    except Exception as e:
        print(f"Error en api_crear_producto: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['POST'])
@transaction.atomic
def api_editar_producto(request, producto_id):
    """API para editar un producto"""
    try:
        tiene_permiso, _ = verificar_permisos_stock(request)
        if not tiene_permiso:
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        data = json.loads(request.body)
        
        try:
            producto = Productos.objects.get(idproducto=producto_id)
        except Productos.DoesNotExist:
            return JsonResponse({'error': 'Producto no encontrado'}, status=404)
        
        # Actualizar campos
        if data.get('nombre'):
            producto.nombreproductos = data['nombre']
        if data.get('precio') is not None:
            producto.precioproducto = float(data['precio'])
        if data.get('marca'):
            producto.marcaproducto = data['marca']
        if data.get('codigo'):
            if Productos.objects.filter(codigobarraproducto=data['codigo']).exclude(idproducto=producto_id).exists():
                return JsonResponse({'error': 'El código de barras ya existe'}, status=400)
            producto.codigobarraproducto = int(data['codigo'])
        if data.get('imagen') is not None:
            producto.imagenproducto = data['imagen']
        if data.get('categoria_id'):
            try:
                categoria = Categorias.objects.get(idcategoria=data['categoria_id'])
                producto.idcategoria = categoria
            except Categorias.DoesNotExist:
                pass
        
        producto.save()
        
        # Actualizar proveedor
        if data.get('proveedor_id'):
            Provxprod.objects.filter(idproducto=producto).delete()
            try:
                proveedor = Proveedores.objects.get(idproveedor=data['proveedor_id'])
                Provxprod.objects.create(
                    idproducto=producto,
                    idproveedor=proveedor
                )
            except Proveedores.DoesNotExist:
                pass
        
        # Actualizar inventario
        if data.get('sucursal_id') and data.get('stock') is not None:
            inventario, created = Inventarios.objects.get_or_create(
                producto=producto,
                sucursal_id=data['sucursal_id'],
                defaults={'cantidad': int(data['stock'])}
            )
            if not created:
                stock_anterior = inventario.cantidad
                inventario.cantidad = int(data['stock'])
                inventario.save()
                
                registrar_actividad(
                    request,
                    'EDITAR_PRODUCTO',
                    f'Stock actualizado: {producto.nombreproductos}',
                    detalles={
                        'producto_id': producto.idproducto,
                        'stock_anterior': stock_anterior,
                        'stock_nuevo': inventario.cantidad
                    }
                )
        
        return JsonResponse({
            'success': True,
            'message': 'Producto actualizado correctamente'
        })
    except Exception as e:
        print(f"Error en api_editar_producto: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['DELETE'])
@transaction.atomic
def api_eliminar_producto(request, producto_id):
    """API para eliminar un producto"""
    try:
        tiene_permiso, _ = verificar_permisos_stock(request)
        if not tiene_permiso:
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        try:
            producto = Productos.objects.get(idproducto=producto_id)
        except Productos.DoesNotExist:
            return JsonResponse({'error': 'Producto no encontrado'}, status=404)
        
        # Verificar si hay ventas asociadas
        if DetalleDeVentas.objects.filter(idproducto=producto).exists():
            return JsonResponse({
                'error': 'No se puede eliminar: hay ventas asociadas a este producto'
            }, status=400)
        
        # Verificar si hay compras asociadas
        if DetalleDeCompras.objects.filter(idproducto=producto).exists():
            return JsonResponse({
                'error': 'No se puede eliminar: hay compras asociadas a este producto'
            }, status=400)
        
        nombre_producto = producto.nombreproductos
        producto.delete()
        
        registrar_actividad(
            request,
            'ELIMINAR_PRODUCTO',
            f'Producto eliminado: {nombre_producto}',
            detalles={'producto_id': producto_id}
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Producto eliminado correctamente'
        })
    except Exception as e:
        print(f"Error en api_eliminar_producto: {e}")
        return JsonResponse({'error': str(e)}, status=500)


# ===== API: CATEGORÍAS =====

@require_http_methods(['GET'])
def api_listar_categorias(request):
    """API para listar todas las categorías"""
    try:
        tiene_permiso, _ = verificar_permisos_stock(request)
        if not tiene_permiso:
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        categorias = Categorias.objects.all()
        categorias_list = [{
            'id': cat.idcategoria,
            'nombre': cat.nombrecategoria,
            'descripcion': cat.descripcioncategoria or ''
        } for cat in categorias]
        
        return JsonResponse(categorias_list, safe=False)
    except Exception as e:
        print(f"Error en api_listar_categorias: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['POST'])
def api_crear_categoria(request):
    """API para crear una nueva categoría"""
    try:
        tiene_permiso, _ = verificar_permisos_stock(request)
        if not tiene_permiso:
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        data = json.loads(request.body)
        
        if not data.get('nombre'):
            return JsonResponse({'error': 'El nombre es obligatorio'}, status=400)
        
        categoria = Categorias.objects.create(
            nombrecategoria=data['nombre'],
            descripcioncategoria=data.get('descripcion', '')
        )
        
        registrar_actividad(
            request,
            'CREAR_CATEGORIA',
            f'Categoría creada: {categoria.nombrecategoria}',
            detalles={'categoria_id': categoria.idcategoria}
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Categoría creada correctamente',
            'categoria_id': categoria.idcategoria
        })
    except Exception as e:
        print(f"Error en api_crear_categoria: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['POST'])
def api_editar_categoria(request, categoria_id):
    """API para editar una categoría"""
    try:
        tiene_permiso, _ = verificar_permisos_stock(request)
        if not tiene_permiso:
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        data = json.loads(request.body)
        
        try:
            categoria = Categorias.objects.get(idcategoria=categoria_id)
        except Categorias.DoesNotExist:
            return JsonResponse({'error': 'Categoría no encontrada'}, status=404)
        
        if data.get('nombre'):
            categoria.nombrecategoria = data['nombre']
        if 'descripcion' in data:
            categoria.descripcioncategoria = data['descripcion']
        
        categoria.save()
        
        registrar_actividad(
            request,
            'EDITAR_CATEGORIA',
            f'Categoría editada: {categoria.nombrecategoria}',
            detalles={'categoria_id': categoria_id}
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Categoría actualizada correctamente'
        })
    except Exception as e:
        print(f"Error en api_editar_categoria: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['DELETE'])
def api_eliminar_categoria(request, categoria_id):
    """API para eliminar una categoría"""
    try:
        tiene_permiso, _ = verificar_permisos_stock(request)
        if not tiene_permiso:
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        try:
            categoria = Categorias.objects.get(idcategoria=categoria_id)
        except Categorias.DoesNotExist:
            return JsonResponse({'error': 'Categoría no encontrada'}, status=404)
        
        if Productos.objects.filter(idcategoria=categoria).exists():
            return JsonResponse({
                'error': 'No se puede eliminar: hay productos asociados a esta categoría'
            }, status=400)
        
        nombre = categoria.nombrecategoria
        categoria.delete()
        
        registrar_actividad(
            request,
            'ELIMINAR_CATEGORIA',
            f'Categoría eliminada: {nombre}',
            detalles={'categoria_id': categoria_id}
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Categoría eliminada correctamente'
        })
    except Exception as e:
        print(f"Error en api_eliminar_categoria: {e}")
        return JsonResponse({'error': str(e)}, status=500)


# ===== API: PROVEEDORES =====

@require_http_methods(['GET'])
def api_listar_proveedores(request):
    """API para listar todos los proveedores"""
    try:
        tiene_permiso, _ = verificar_permisos_stock(request)
        if not tiene_permiso:
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        proveedores = Proveedores.objects.all()
        proveedores_list = [{
            'id': prov.idproveedor,
            'nombre': prov.nombreproveedor,
            'telefono': str(prov.telefonoproveedor),
            'email': prov.emailprov,
            'cuit': str(prov.cuitproveedor)
        } for prov in proveedores]
        
        return JsonResponse(proveedores_list, safe=False)
    except Exception as e:
        print(f"Error en api_listar_proveedores: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['POST'])
def api_crear_proveedor(request):
    """API para crear un nuevo proveedor"""
    try:
        tiene_permiso, _ = verificar_permisos_stock(request)
        if not tiene_permiso:
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        data = json.loads(request.body)
        
        if not all([data.get('nombre'), data.get('telefono'), 
                   data.get('email'), data.get('cuit')]):
            return JsonResponse({'error': 'Faltan campos obligatorios'}, status=400)
        
        if Proveedores.objects.filter(cuitproveedor=data['cuit']).exists():
            return JsonResponse({'error': 'El CUIT ya existe'}, status=400)
        
        proveedor = Proveedores.objects.create(
            nombreproveedor=data['nombre'],
            telefonoproveedor=int(data['telefono']),
            emailprov=data['email'],
            cuitproveedor=int(data['cuit'])
        )
        
        registrar_actividad(
            request,
            'CREAR_PROVEEDOR',
            f'Proveedor creado: {proveedor.nombreproveedor}',
            detalles={'proveedor_id': proveedor.idproveedor}
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Proveedor creado correctamente',
            'proveedor_id': proveedor.idproveedor
        })
    except Exception as e:
        print(f"Error en api_crear_proveedor: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['POST'])
def api_editar_proveedor(request, proveedor_id):
    """API para editar un proveedor"""
    try:
        tiene_permiso, _ = verificar_permisos_stock(request)
        if not tiene_permiso:
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        data = json.loads(request.body)
        
        try:
            proveedor = Proveedores.objects.get(idproveedor=proveedor_id)
        except Proveedores.DoesNotExist:
            return JsonResponse({'error': 'Proveedor no encontrado'}, status=404)
        
        if data.get('nombre'):
            proveedor.nombreproveedor = data['nombre']
        if data.get('telefono'):
            proveedor.telefonoproveedor = int(data['telefono'])
        if data.get('email'):
            proveedor.emailprov = data['email']
        if data.get('cuit'):
            if Proveedores.objects.filter(cuitproveedor=data['cuit']).exclude(idproveedor=proveedor_id).exists():
                return JsonResponse({'error': 'El CUIT ya existe'}, status=400)
            proveedor.cuitproveedor = int(data['cuit'])
        
        proveedor.save()
        
        registrar_actividad(
            request,
            'EDITAR_PROVEEDOR',
            f'Proveedor editado: {proveedor.nombreproveedor}',
            detalles={'proveedor_id': proveedor_id}
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Proveedor actualizado correctamente'
        })
    except Exception as e:
        print(f"Error en api_editar_proveedor: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['DELETE'])
def api_eliminar_proveedor(request, proveedor_id):
    """API para eliminar un proveedor"""
    try:
        tiene_permiso, _ = verificar_permisos_stock(request)
        if not tiene_permiso:
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        try:
            proveedor = Proveedores.objects.get(idproveedor=proveedor_id)
        except Proveedores.DoesNotExist:
            return JsonResponse({'error': 'Proveedor no encontrado'}, status=404)
        
        if Provxprod.objects.filter(idproveedor=proveedor).exists():
            return JsonResponse({
                'error': 'No se puede eliminar: hay productos asociados a este proveedor'
            }, status=400)
        
        nombre = proveedor.nombreproveedor
        proveedor.delete()
        
        registrar_actividad(
            request,
            'ELIMINAR_PROVEEDOR',
            f'Proveedor eliminado: {nombre}',
            detalles={'proveedor_id': proveedor_id}
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Proveedor eliminado correctamente'
        })
    except Exception as e:
        print(f"Error en api_eliminar_proveedor: {e}")
        return JsonResponse({'error': str(e)}, status=500)


# ===== API: MOVIMIENTOS =====

@require_http_methods(['GET'])
def api_listar_movimientos(request):
    """API para listar movimientos de inventario"""
    try:
        tiene_permiso, _ = verificar_permisos_stock(request)
        if not tiene_permiso:
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        # Obtener movimientos de compras y ventas
        movimientos = []
        
        # Movimientos de compras (entradas)
        compras = DetalleDeCompras.objects.select_related(
            'idcompras', 'idproducto'
        ).order_by('-idcompras__fechacompra')[:100]
        
        for detalle in compras:
            movimientos.append({
                'id': f'C-{detalle.iddetallecompras}',
                'fecha': detalle.idcompras.fechacompra.strftime('%Y-%m-%d'),
                'producto': detalle.idproducto.nombreproductos,
                'producto_id': detalle.idproducto.idproducto,
                'tipo': 'Entrada',
                'cantidad': detalle.cantidadcompra,
                'stock_resultante': None,  # Se calcula en el frontend
                'notas': f'Compra #{detalle.idcompras.idcompras}'
            })
        
        # Movimientos de ventas (salidas)
        ventas = DetalleDeVentas.objects.select_related(
            'idventa', 'idproducto'
        ).order_by('-idventa__fechaventa')[:100]
        
        for detalle in ventas:
            movimientos.append({
                'id': f'V-{detalle.iddetalleventas}',
                'fecha': detalle.idventa.fechaventa.strftime('%Y-%m-%d'),
                'producto': detalle.idproducto.nombreproductos,
                'producto_id': detalle.idproducto.idproducto,
                'tipo': 'Salida',
                'cantidad': detalle.cantidadvendida,
                'stock_resultante': None,
                'notas': f'Venta #{detalle.idventa.idventa}'
            })
        
        # Ordenar por fecha (más recientes primero)
        movimientos.sort(key=lambda x: x['fecha'], reverse=True)
        
        return JsonResponse(movimientos[:100], safe=False)
    except Exception as e:
        print(f"Error en api_listar_movimientos: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


# ===== API: VENTAS =====

@require_http_methods(['GET'])
def api_listar_ventas(request):
    """API para listar ventas (solo lectura)"""
    try:
        tiene_permiso, _ = verificar_permisos_stock(request)
        if not tiene_permiso:
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        ventas = DetalleDeVentas.objects.select_related(
            'idventa', 'idproducto'
        ).order_by('-idventa__fechaventa')[:200]
        
        ventas_list = []
        for detalle in ventas:
            ventas_list.append({
                'id': detalle.iddetalleventas,
                'venta_id': detalle.idventa.idventa,
                'fecha': detalle.idventa.fechaventa.strftime('%Y-%m-%d'),
                'hora': detalle.idventa.horaventa.strftime('%H:%M:%S'),
                'producto': detalle.idproducto.nombreproductos,
                'cantidad': detalle.cantidadvendida,
                'precio_unitario': float(detalle.preciounitariodv),
                'total': float(detalle.subtotaldv),
                'metodo': detalle.idventa.metodopago,
                'estado': detalle.idventa.estadoventa
            })
        
        return JsonResponse(ventas_list, safe=False)
    except Exception as e:
        print(f"Error en api_listar_ventas: {e}")
        return JsonResponse({'error': str(e)}, status=500)
    
# Agregar estas mejoras al archivo views.py existente

# MEJORA 1: API para crear movimientos de stock
@require_http_methods(['POST'])
@transaction.atomic
def api_crear_movimiento(request):
    """API para crear un movimiento de inventario (entrada/salida manual)"""
    try:
        tiene_permiso, _ = verificar_permisos_stock(request)
        if not tiene_permiso:
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        data = json.loads(request.body)
        
        # Validar campos obligatorios
        if not all([data.get('producto_id'), data.get('tipo'), 
                   data.get('cantidad'), data.get('sucursal_id')]):
            return JsonResponse({'error': 'Faltan campos obligatorios'}, status=400)
        
        # Obtener producto
        try:
            producto = Productos.objects.get(idproducto=data['producto_id'])
        except Productos.DoesNotExist:
            return JsonResponse({'error': 'Producto no encontrado'}, status=404)
        
        # Obtener sucursal
        try:
            sucursal = Sucursales.objects.get(idsucursal=data['sucursal_id'])
        except Sucursales.DoesNotExist:
            return JsonResponse({'error': 'Sucursal no encontrada'}, status=404)
        
        # Obtener o crear inventario
        inventario, created = Inventarios.objects.get_or_create(
            producto=producto,
            sucursal=sucursal,
            defaults={'cantidad': 0}
        )
        
        cantidad = int(data['cantidad'])
        tipo = data['tipo']
        stock_anterior = inventario.cantidad
        
        # Aplicar movimiento
        if tipo == 'Entrada':
            inventario.cantidad += cantidad
        elif tipo == 'Salida':
            if inventario.cantidad < cantidad:
                return JsonResponse({
                    'error': f'Stock insuficiente. Stock actual: {inventario.cantidad}'
                }, status=400)
            inventario.cantidad -= cantidad
        else:
            return JsonResponse({'error': 'Tipo de movimiento inválido'}, status=400)
        
        inventario.save()
        
        # Registrar actividad
        registrar_actividad(
            request,
            'MOVIMIENTO_STOCK',
            f'Movimiento de stock: {tipo} - {producto.nombreproductos}',
            detalles={
                'producto_id': producto.idproducto,
                'tipo': tipo,
                'cantidad': cantidad,
                'stock_anterior': stock_anterior,
                'stock_nuevo': inventario.cantidad,
                'notas': data.get('notas', '')
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Movimiento de {tipo.lower()} registrado correctamente',
            'stock_nuevo': inventario.cantidad
        })
        
    except Exception as e:
        print(f"Error en api_crear_movimiento: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


# MEJORA 2: API mejorada para listar movimientos con más detalles
@require_http_methods(['GET'])
def api_listar_movimientos_mejorado(request):
    """API mejorada para listar movimientos de inventario con filtros"""
    try:
        tiene_permiso, _ = verificar_permisos_stock(request)
        if not tiene_permiso:
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        # Parámetros de filtrado
        producto_id = request.GET.get('producto_id')
        tipo = request.GET.get('tipo')  # 'Entrada' o 'Salida'
        fecha_desde = request.GET.get('fecha_desde')
        fecha_hasta = request.GET.get('fecha_hasta')
        limit = int(request.GET.get('limit', 100))
        
        movimientos = []
        
        # Movimientos de compras (entradas)
        compras_query = DetalleDeCompras.objects.select_related(
            'idcompras', 'idproducto'
        ).order_by('-idcompras__fechacompra')
        
        if producto_id:
            compras_query = compras_query.filter(idproducto_id=producto_id)
        if fecha_desde:
            compras_query = compras_query.filter(idcompras__fechacompra__gte=fecha_desde)
        if fecha_hasta:
            compras_query = compras_query.filter(idcompras__fechacompra__lte=fecha_hasta)
        
        if not tipo or tipo == 'Entrada':
            for detalle in compras_query[:limit]:
                movimientos.append({
                    'id': f'C-{detalle.iddetallecompras}',
                    'fecha': detalle.idcompras.fechacompra.strftime('%Y-%m-%d'),
                    'hora': detalle.idcompras.horacompra.strftime('%H:%M:%S') if detalle.idcompras.horacompra else '00:00:00',
                    'producto': detalle.idproducto.nombreproductos,
                    'producto_id': detalle.idproducto.idproducto,
                    'tipo': 'Entrada',
                    'cantidad': detalle.cantidadcompra,
                    'precio_unitario': float(detalle.preciounitariodc),
                    'subtotal': float(detalle.subtotaldc),
                    'referencia': f'Compra #{detalle.idcompras.idcompras}',
                    'notas': f'Compra a {detalle.idcompras.idproveedor.nombreproveedor}'
                })
        
        # Movimientos de ventas (salidas)
        ventas_query = DetalleDeVentas.objects.select_related(
            'idventa', 'idproducto'
        ).order_by('-idventa__fechaventa')
        
        if producto_id:
            ventas_query = ventas_query.filter(idproducto_id=producto_id)
        if fecha_desde:
            ventas_query = ventas_query.filter(idventa__fechaventa__gte=fecha_desde)
        if fecha_hasta:
            ventas_query = ventas_query.filter(idventa__fechaventa__lte=fecha_hasta)
        
        if not tipo or tipo == 'Salida':
            for detalle in ventas_query[:limit]:
                movimientos.append({
                    'id': f'V-{detalle.iddetalleventas}',
                    'fecha': detalle.idventa.fechaventa.strftime('%Y-%m-%d'),
                    'hora': detalle.idventa.horaventa.strftime('%H:%M:%S'),
                    'producto': detalle.idproducto.nombreproductos,
                    'producto_id': detalle.idproducto.idproducto,
                    'tipo': 'Salida',
                    'cantidad': detalle.cantidadvendida,
                    'precio_unitario': float(detalle.preciounitariodv),
                    'subtotal': float(detalle.subtotaldv),
                    'referencia': f'Venta #{detalle.idventa.idventa}',
                    'notas': f'Venta - {detalle.idventa.metodopago}'
                })
        
        # Ordenar por fecha (más recientes primero)
        movimientos.sort(key=lambda x: (x['fecha'], x.get('hora', '00:00:00')), reverse=True)
        
        return JsonResponse(movimientos[:limit], safe=False)
        
    except Exception as e:
        print(f"Error en api_listar_movimientos_mejorado: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


# MEJORA 3: API para estadísticas de stock
@require_http_methods(['GET'])
def api_estadisticas_stock(request):
    """API para obtener estadísticas del inventario"""
    try:
        tiene_permiso, _ = verificar_permisos_stock(request)
        if not tiene_permiso:
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        sucursal_id = request.GET.get('sucursal_id')
        
        # Obtener productos con inventario
        if sucursal_id:
            inventarios = Inventarios.objects.filter(
                sucursal_id=sucursal_id
            ).select_related('producto', 'producto__idcategoria')
        else:
            inventarios = Inventarios.objects.all().select_related(
                'producto', 'producto__idcategoria'
            )
        
        # Calcular estadísticas
        total_productos = Productos.objects.count()
        total_stock = inventarios.aggregate(total=Sum('cantidad'))['total'] or 0
        
        # Valor total del inventario
        valor_total = 0
        productos_sin_stock = 0
        productos_bajo_stock = 0
        
        for inv in inventarios:
            valor_total += inv.cantidad * float(inv.producto.precioproducto)
            if inv.cantidad == 0:
                productos_sin_stock += 1
            elif inv.cantidad < 10:  # Considerar stock bajo si es menor a 10
                productos_bajo_stock += 1
        
        # Productos más vendidos (últimos 30 días)
        fecha_hace_30 = timezone.now() - timedelta(days=30)
        productos_mas_vendidos = DetalleDeVentas.objects.filter(
            idventa__fechaventa__gte=fecha_hace_30
        ).values('idproducto__nombreproductos').annotate(
            total_vendido=Sum('cantidadvendida')
        ).order_by('-total_vendido')[:10]
        
        # Categorías con más stock
        categorias_stock = inventarios.values(
            'producto__idcategoria__nombrecategoria'
        ).annotate(
            total_stock=Sum('cantidad'),
            total_productos=Count('producto', distinct=True)
        ).order_by('-total_stock')[:10]
        
        return JsonResponse({
            'resumen': {
                'total_productos': total_productos,
                'total_stock': total_stock,
                'valor_total_inventario': round(valor_total, 2),
                'productos_sin_stock': productos_sin_stock,
                'productos_bajo_stock': productos_bajo_stock
            },
            'productos_mas_vendidos': list(productos_mas_vendidos),
            'categorias_stock': list(categorias_stock)
        })
        
    except Exception as e:
        print(f"Error en api_estadisticas_stock: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


# MEJORA 4: API para alertas de stock
@require_http_methods(['GET'])
def api_alertas_stock(request):
    """API para obtener alertas de productos con problemas de stock"""
    try:
        tiene_permiso, _ = verificar_permisos_stock(request)
        if not tiene_permiso:
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        sucursal_id = request.GET.get('sucursal_id')
        
        alertas = []
        
        # Obtener todos los productos con su inventario
        productos_query = Productos.objects.select_related('idcategoria').all()
        
        for producto in productos_query:
            if sucursal_id:
                inventario = Inventarios.objects.filter(
                    producto=producto,
                    sucursal_id=sucursal_id
                ).first()
            else:
                inventario_total = Inventarios.objects.filter(
                    producto=producto
                ).aggregate(total=Sum('cantidad'))
                stock_total = inventario_total['total'] or 0
                inventario = type('obj', (object,), {'cantidad': stock_total})()
            
            stock_actual = inventario.cantidad if inventario else 0
            stock_minimo = 10  # Valor por defecto
            
            # Generar alertas
            if stock_actual == 0:
                alertas.append({
                    'producto_id': producto.idproducto,
                    'producto': producto.nombreproductos,
                    'categoria': producto.idcategoria.nombrecategoria if producto.idcategoria else 'Sin categoría',
                    'stock_actual': stock_actual,
                    'stock_minimo': stock_minimo,
                    'nivel': 'CRÍTICO',
                    'mensaje': 'Producto sin stock'
                })
            elif stock_actual < stock_minimo:
                alertas.append({
                    'producto_id': producto.idproducto,
                    'producto': producto.nombreproductos,
                    'categoria': producto.idcategoria.nombrecategoria if producto.idcategoria else 'Sin categoría',
                    'stock_actual': stock_actual,
                    'stock_minimo': stock_minimo,
                    'nivel': 'ADVERTENCIA',
                    'mensaje': f'Stock bajo (necesita {stock_minimo - stock_actual} unidades)'
                })
        
        # Ordenar por nivel (críticos primero)
        alertas.sort(key=lambda x: (x['nivel'] != 'CRÍTICO', x['stock_actual']))
        
        return JsonResponse({
            'total_alertas': len(alertas),
            'criticas': len([a for a in alertas if a['nivel'] == 'CRÍTICO']),
            'advertencias': len([a for a in alertas if a['nivel'] == 'ADVERTENCIA']),
            'alertas': alertas
        })
        
    except Exception as e:
        print(f"Error en api_alertas_stock: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)