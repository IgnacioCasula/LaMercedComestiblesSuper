#!/usr/bin/env python
"""
Script para verificar productos en la base de datos
Ejecutar: python verificar_productos.py
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ProyectoSuper.settings')
django.setup()

from caja.models import Productos, Inventarios, Sucursales
from django.db.models import Sum

print("=" * 60)
print("VERIFICACIÓN DE PRODUCTOS EN LA BASE DE DATOS")
print("=" * 60)

# 1. Verificar productos totales
total_productos = Productos.objects.count()
print(f"\n📦 Total de productos en la BD: {total_productos}")

if total_productos == 0:
    print("⚠️  NO HAY PRODUCTOS EN LA BASE DE DATOS")
    print("   Ejecuta: python manage.py productos")
else:
    print("\n✅ Productos encontrados:")
    productos = Productos.objects.all()[:10]  # Mostrar primeros 10
    for p in productos:
        print(f"   - {p.nombreproductos} (ID: {p.idproducto})")

# 2. Verificar inventarios
print("\n" + "=" * 60)
print("VERIFICACIÓN DE INVENTARIOS")
print("=" * 60)

sucursales = Sucursales.objects.all()
print(f"\n🏢 Total de sucursales: {sucursales.count()}")

for sucursal in sucursales:
    inventarios = Inventarios.objects.filter(sucursal=sucursal)
    total_stock = inventarios.aggregate(total=Sum('cantidad'))['total'] or 0
    productos_con_stock = inventarios.filter(cantidad__gt=0).count()
    
    print(f"\n   Sucursal: {sucursal.nombresucursal}")
    print(f"   - Productos con inventario: {inventarios.count()}")
    print(f"   - Productos con stock > 0: {productos_con_stock}")
    print(f"   - Stock total: {total_stock}")
    
    if productos_con_stock == 0:
        print("   ⚠️  NO HAY PRODUCTOS CON STOCK EN ESTA SUCURSAL")
        print("   💡 Necesitas crear inventario para los productos")

# 3. Verificar estructura de datos
print("\n" + "=" * 60)
print("VERIFICACIÓN DE ESTRUCTURA DE DATOS")
print("=" * 60)

if total_productos > 0:
    producto_ejemplo = Productos.objects.first()
    print(f"\n📋 Ejemplo de producto (ID: {producto_ejemplo.idproducto}):")
    print(f"   - nombreproductos: {producto_ejemplo.nombreproductos}")
    print(f"   - precioproducto: {producto_ejemplo.precioproducto}")
    print(f"   - marcaproducto: {producto_ejemplo.marcaproducto}")
    print(f"   - codigobarraproducto: {producto_ejemplo.codigobarraproducto}")
    
    inventario_ejemplo = Inventarios.objects.filter(producto=producto_ejemplo).first()
    if inventario_ejemplo:
        print(f"   - stock (inventario): {inventario_ejemplo.cantidad}")
    else:
        print("   ⚠️  NO HAY INVENTARIO PARA ESTE PRODUCTO")

print("\n" + "=" * 60)
print("RECOMENDACIONES")
print("=" * 60)

if total_productos == 0:
    print("\n1. Crea productos ejecutando:")
    print("   python manage.py productos")
    
if productos_con_stock == 0:
    print("\n2. Crea inventario para los productos en las sucursales")
    print("   (Esto se hace automáticamente al ejecutar 'python manage.py productos')")

print("\n✅ Verificación completada")

