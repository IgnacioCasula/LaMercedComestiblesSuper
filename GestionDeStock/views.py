from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
import json
import base64
from datetime import datetime

from caja.models import (
    Productos, Categorias, Proveedores, Inventarios,
    Sucursales, Usuarios, Roles
)

def gestion_de_stock(request):
    """Vista principal de gestión de stock"""
    # Verificar autenticación
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        messages.error(request, 'Acceso denegado. Por favor, inicia sesión.')
        return redirect('login')
    
    # Verificar permisos
    usuario = Usuarios.objects.filter(idusuarios=usuario_id).first()
    if not usuario:
        messages.error(request, 'Acceso denegado. Por favor, inicia sesión.')
        return redirect('login')
    
    roles_usuario = list(
        Roles.objects.filter(usuxroles__idusuarios_id=usuario_id).values_list('nombrerol', flat=True)
    )
    
    is_admin = 'Administrador' in roles_usuario or 'Recursos Humanos' in roles_usuario
    has_gestion_stock = any('stock' in rol.lower() or 'inventario' in rol.lower() for rol in roles_usuario)
    
    if not (is_admin or has_gestion_stock):
        messages.error(request, 'No tienes permisos para acceder a Gestión de Stock.')
        return redirect('inicio')
    
    # Obtener usuario y sucursal
    nombre_usuario = request.session.get('nombre_usuario', 'Usuario')
    
    # Obtener la primera sucursal disponible (o la del usuario si está asignada)
    sucursal = Sucursales.objects.first()
    
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
        sucursal_id = request.GET.get('sucursal_id')
        search = request.GET.get('search', '').strip()
        
        # Obtener productos
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
            inventario = Inventarios.objects.filter(
                producto=producto,
                sucursal_id=sucursal_id if sucursal_id else None
            ).first()
            
            # Obtener proveedor
            from caja.models import Provxprod
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
                'stockMinimo': 10,  # Valor por defecto
                'imagen': producto.imagenproducto if producto.imagenproducto else None
            })
        
        return JsonResponse(productos_list, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['POST'])
@transaction.atomic
def api_crear_producto(request):
    """API para crear un nuevo producto"""
    try:
        data = json.loads(request.body)
        
        # Validaciones
        if not all([data.get('nombre'), data.get('precio'), data.get('marca'), 
                   data.get('codigo'), data.get('categoria_id')]):
            return JsonResponse({'error': 'Faltan campos obligatorios'}, status=400)
        
        # Verificar código único
        if Productos.objects.filter(codigobarraproducto=data['codigo']).exists():
            return JsonResponse({'error': 'El código de barras ya existe'}, status=400)
        
        # Obtener categoría
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
        
        # Crear relación con proveedor si existe
        if data.get('proveedor_id'):
            from caja.models import Provxprod
            try:
                proveedor = Proveedores.objects.get(idproveedor=data['proveedor_id'])
                Provxprod.objects.create(
                    idproducto=producto,
                    idproveedor=proveedor
                )
            except Proveedores.DoesNotExist:
                pass
        
        # Crear inventario inicial
        if data.get('sucursal_id') and data.get('stock') is not None:
            try:
                sucursal = Sucursales.objects.get(idsucursal=data['sucursal_id'])
                Inventarios.objects.create(
                    producto=producto,
                    sucursal=sucursal,
                    cantidad=int(data['stock'])
                )
            except Sucursales.DoesNotExist:
                pass
        
        return JsonResponse({
            'success': True,
            'message': 'Producto creado correctamente',
            'producto_id': producto.idproducto
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['POST'])
@transaction.atomic
def api_editar_producto(request, producto_id):
    """API para editar un producto existente"""
    try:
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
            # Verificar que el código no esté en uso por otro producto
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
            from caja.models import Provxprod
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
                inventario.cantidad = int(data['stock'])
                inventario.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Producto actualizado correctamente'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['DELETE'])
@transaction.atomic
def api_eliminar_producto(request, producto_id):
    """API para eliminar un producto"""
    try:
        try:
            producto = Productos.objects.get(idproducto=producto_id)
        except Productos.DoesNotExist:
            return JsonResponse({'error': 'Producto no encontrado'}, status=404)
        
        producto.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Producto eliminado correctamente'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ===== API: CATEGORÍAS =====

@require_http_methods(['GET'])
def api_listar_categorias(request):
    """API para listar todas las categorías"""
    try:
        categorias = Categorias.objects.all()
        categorias_list = [{
            'id': cat.idcategoria,
            'nombre': cat.nombrecategoria,
            'descripcion': cat.descripcioncategoria or ''
        } for cat in categorias]
        
        return JsonResponse(categorias_list, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['POST'])
def api_crear_categoria(request):
    """API para crear una nueva categoría"""
    try:
        data = json.loads(request.body)
        
        if not data.get('nombre'):
            return JsonResponse({'error': 'El nombre es obligatorio'}, status=400)
        
        categoria = Categorias.objects.create(
            nombrecategoria=data['nombre'],
            descripcioncategoria=data.get('descripcion', '')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Categoría creada correctamente',
            'categoria_id': categoria.idcategoria
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['POST'])
def api_editar_categoria(request, categoria_id):
    """API para editar una categoría"""
    try:
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
        
        return JsonResponse({
            'success': True,
            'message': 'Categoría actualizada correctamente'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['DELETE'])
def api_eliminar_categoria(request, categoria_id):
    """API para eliminar una categoría"""
    try:
        try:
            categoria = Categorias.objects.get(idcategoria=categoria_id)
        except Categorias.DoesNotExist:
            return JsonResponse({'error': 'Categoría no encontrada'}, status=404)
        
        # Verificar que no tenga productos
        if Productos.objects.filter(idcategoria=categoria).exists():
            return JsonResponse({
                'error': 'No se puede eliminar: hay productos asociados a esta categoría'
            }, status=400)
        
        categoria.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Categoría eliminada correctamente'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ===== API: PROVEEDORES =====

@require_http_methods(['GET'])
def api_listar_proveedores(request):
    """API para listar todos los proveedores"""
    try:
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
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['POST'])
def api_crear_proveedor(request):
    """API para crear un nuevo proveedor"""
    try:
        data = json.loads(request.body)
        
        if not all([data.get('nombre'), data.get('telefono'), 
                   data.get('email'), data.get('cuit')]):
            return JsonResponse({'error': 'Faltan campos obligatorios'}, status=400)
        
        # Verificar CUIT único
        if Proveedores.objects.filter(cuitproveedor=data['cuit']).exists():
            return JsonResponse({'error': 'El CUIT ya existe'}, status=400)
        
        proveedor = Proveedores.objects.create(
            nombreproveedor=data['nombre'],
            telefonoproveedor=int(data['telefono']),
            emailprov=data['email'],
            cuitproveedor=int(data['cuit'])
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Proveedor creado correctamente',
            'proveedor_id': proveedor.idproveedor
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['POST'])
def api_editar_proveedor(request, proveedor_id):
    """API para editar un proveedor"""
    try:
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
        
        return JsonResponse({
            'success': True,
            'message': 'Proveedor actualizado correctamente'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(['DELETE'])
def api_eliminar_proveedor(request, proveedor_id):
    """API para eliminar un proveedor"""
    try:
        try:
            proveedor = Proveedores.objects.get(idproveedor=proveedor_id)
        except Proveedores.DoesNotExist:
            return JsonResponse({'error': 'Proveedor no encontrado'}, status=404)
        
        # Verificar que no tenga productos
        from caja.models import Provxprod
        if Provxprod.objects.filter(idproveedor=proveedor).exists():
            return JsonResponse({
                'error': 'No se puede eliminar: hay productos asociados a este proveedor'
            }, status=400)
        
        proveedor.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Proveedor eliminado correctamente'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)