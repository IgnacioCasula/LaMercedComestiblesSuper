import os
import django
import sys

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ProyectoSuper.settings')
django.setup()

from django.db import transaction
<<<<<<< HEAD
=======
# IMPORTAR DESDE CAJA EN LUGAR DE VENTAS
>>>>>>> e99069a0a67a380785dd9c147491b8dde27adb6e
from caja.models import Categorias, Productos, Inventarios, Sucursales

def cargar_categorias():
    """Cargar categorías básicas si no existen"""
    print("📂 Cargando categorías...")
<<<<<<< HEAD
    
=======
   
>>>>>>> e99069a0a67a380785dd9c147491b8dde27adb6e
    categorias_base = [
        {"nombre": "Almacén", "descripcion": "Productos de almacén y secos"},
        {"nombre": "Frutas y Verduras", "descripcion": "Frutas y verduras frescas"},
        {"nombre": "Lácteos", "descripcion": "Leche, quesos y derivados"},
        {"nombre": "Carnes", "descripcion": "Carnes y productos cárnicos"},
        {"nombre": "Panadería", "descripcion": "Pan y productos de panadería"},
    ]
<<<<<<< HEAD
    
=======
   
>>>>>>> e99069a0a67a380785dd9c147491b8dde27adb6e
    for cat_data in categorias_base:
        categoria, created = Categorias.objects.get_or_create(
            nombrecategoria=cat_data["nombre"],
            defaults={"descripcioncategoria": cat_data["descripcion"]}
        )
        if created:
            print(f"  ✅ Categoría creada: {cat_data['nombre']}")
        else:
            print(f"  ℹ️  Categoría existente: {cat_data['nombre']}")
<<<<<<< HEAD
    
=======
   
>>>>>>> e99069a0a67a380785dd9c147491b8dde27adb6e
    return Categorias.objects.all()

def cargar_productos_base():
    """Cargar productos básicos del supermercado"""
    print("📦 Cargando productos...")
<<<<<<< HEAD
    
=======
   
>>>>>>> e99069a0a67a380785dd9c147491b8dde27adb6e
    # Obtener categorías
    try:
        categorias = {
            "Almacén": Categorias.objects.get(nombrecategoria="Almacén"),
            "Frutas y Verduras": Categorias.objects.get(nombrecategoria="Frutas y Verduras"),
            "Lácteos": Categorias.objects.get(nombrecategoria="Lácteos"),
            "Carnes": Categorias.objects.get(nombrecategoria="Carnes"),
            "Panadería": Categorias.objects.get(nombrecategoria="Panadería"),
        }
    except Categorias.DoesNotExist as e:
        print(f"  ❌ Error: No se encontró alguna categoría. Ejecuta primero cargar_categorias()")
        return 0
<<<<<<< HEAD
    
=======
   
>>>>>>> e99069a0a67a380785dd9c147491b8dde27adb6e
    # TUS PRODUCTOS CON PRECIOS
    productos_data = [
        # Almacén
        {"nombre": "Fideos María", "precio": 500, "marca": "María", "codigo_barra": 7791234567890, "categoria": "Almacén"},
        {"nombre": "Arroz Largo Fino", "precio": 700, "marca": "Gallo", "codigo_barra": 7791234567891, "categoria": "Almacén"},
<<<<<<< HEAD
        
=======
       
>>>>>>> e99069a0a67a380785dd9c147491b8dde27adb6e
        # Frutas y Verduras
        {"nombre": "Manzana Roja", "precio": 300, "marca": "Fruta Fresca", "codigo_barra": 7791234567898, "categoria": "Frutas y Verduras"},
        {"nombre": "Banana", "precio": 200, "marca": "Fruta Fresca", "codigo_barra": 7791234567899, "categoria": "Frutas y Verduras"},
        {"nombre": "Naranja", "precio": 250, "marca": "Fruta Fresca", "codigo_barra": 7791234567800, "categoria": "Frutas y Verduras"},
        {"nombre": "Tomate Perita", "precio": 180, "marca": "Verdura Fresca", "codigo_barra": 7791234567801, "categoria": "Frutas y Verduras"},
        {"nombre": "Papa Negra", "precio": 120, "marca": "Verdura Fresca", "codigo_barra": 7791234567802, "categoria": "Frutas y Verduras"},
<<<<<<< HEAD
        
        # Lácteos
        {"nombre": "Leche Entera 1L", "precio": 800, "marca": "La Serenísima", "codigo_barra": 7791234567894, "categoria": "Lácteos"},
        {"nombre": "Queso Cremoso", "precio": 1800, "marca": "La Paulina", "codigo_barra": 7791234567895, "categoria": "Lácteos"},
        
        # Carnes
        {"nombre": "Pechuga de Pollo", "precio": 1500, "marca": "Granja", "codigo_barra": 7791234567804, "categoria": "Carnes"},
        {"nombre": "Carne Molida", "precio": 2200, "marca": "Carnicería", "codigo_barra": 7791234567805, "categoria": "Carnes"},
        
=======
       
        # Lácteos
        {"nombre": "Leche Entera 1L", "precio": 800, "marca": "La Serenísima", "codigo_barra": 7791234567894, "categoria": "Lácteos"},
        {"nombre": "Queso Cremoso", "precio": 1800, "marca": "La Paulina", "codigo_barra": 7791234567895, "categoria": "Lácteos"},
       
        # Carnes
        {"nombre": "Pechuga de Pollo", "precio": 1500, "marca": "Granja", "codigo_barra": 7791234567804, "categoria": "Carnes"},
        {"nombre": "Carne Molida", "precio": 2200, "marca": "Carnicería", "codigo_barra": 7791234567805, "categoria": "Carnes"},
       
>>>>>>> e99069a0a67a380785dd9c147491b8dde27adb6e
        # Panadería
        {"nombre": "Pan Lactal", "precio": 900, "marca": "Bimbo", "codigo_barra": 7791234567807, "categoria": "Panadería"},
        {"nombre": "Huevos (docena)", "precio": 1200, "marca": "Granja", "codigo_barra": 7791234567812, "categoria": "Panadería"},
    ]
<<<<<<< HEAD
    
    productos_creados = 0
    
=======
   
    productos_creados = 0
   
>>>>>>> e99069a0a67a380785dd9c147491b8dde27adb6e
    with transaction.atomic():
        for prod_data in productos_data:
            try:
                # Verificar si el producto ya existe por código de barras
                producto, created = Productos.objects.get_or_create(
                    codigobarraproducto=prod_data["codigo_barra"],
                    defaults={
                        "nombreproductos": prod_data["nombre"],
                        "precioproducto": prod_data["precio"],
                        "marcaproducto": prod_data["marca"],
                        "idcategoria": categorias[prod_data["categoria"]]
                    }
                )
<<<<<<< HEAD
                
=======
               
>>>>>>> e99069a0a67a380785dd9c147491b8dde27adb6e
                if created:
                    productos_creados += 1
                    print(f"  ✅ Producto creado: {prod_data['nombre']} - ${prod_data['precio']}")
                else:
                    print(f"  ℹ️  Producto existente: {prod_data['nombre']}")
<<<<<<< HEAD
                        
            except Exception as e:
                print(f"  ❌ Error al crear producto {prod_data['nombre']}: {str(e)}")
    
=======
                       
            except Exception as e:
                print(f"  ❌ Error al crear producto {prod_data['nombre']}: {str(e)}")
   
>>>>>>> e99069a0a67a380785dd9c147491b8dde27adb6e
    print(f"  📊 Productos creados: {productos_creados}")
    return productos_creados

def cargar_inventario_inicial():
    """Cargar inventario inicial para todos los productos"""
    print("🏪 Cargando inventario...")
<<<<<<< HEAD
    
=======
   
>>>>>>> e99069a0a67a380785dd9c147491b8dde27adb6e
    try:
        # Obtener la primera sucursal (crear una si no existe)
        sucursal, created = Sucursales.objects.get_or_create(
            idsucursal=1,
            defaults={
                "nombresucursal": "Sucursal Principal",
                "telefonosucursal": 1234567890,
                "idubicacion_id": 1
            }
        )
<<<<<<< HEAD
        
        if created:
            print("  ✅ Sucursal creada: Sucursal Principal")
        
        productos = Productos.objects.all()
        inventarios_creados = 0
        
=======
       
        if created:
            print("  ✅ Sucursal creada: Sucursal Principal")
       
        productos = Productos.objects.all()
        inventarios_creados = 0
       
>>>>>>> e99069a0a67a380785dd9c147491b8dde27adb6e
        with transaction.atomic():
            for producto in productos:
                inventario, created = Inventarios.objects.get_or_create(
                    producto=producto,
                    sucursal=sucursal,
                    defaults={"cantidad": 100}  # Stock inicial de 100 unidades
                )
<<<<<<< HEAD
                
                if created:
                    inventarios_creados += 1
                    print(f"  📦 Inventario creado para: {producto.nombreproductos}")
        
        print(f"  📊 Inventarios creados: {inventarios_creados}")
        return inventarios_creados
        
=======
               
                if created:
                    inventarios_creados += 1
                    print(f"  📦 Inventario creado para: {producto.nombreproductos}")
       
        print(f"  📊 Inventarios creados: {inventarios_creados}")
        return inventarios_creados
       
>>>>>>> e99069a0a67a380785dd9c147491b8dde27adb6e
    except Exception as e:
        print(f"  ❌ Error al cargar inventario: {str(e)}")
        return 0

def ejecutar_carga_completa():
    """Ejecutar toda la carga de datos"""
    print("🚀 Iniciando carga de datos...")
    print("=" * 50)
<<<<<<< HEAD
    
    # 1. Cargar categorías
    cargar_categorias()
    print("-" * 30)
    
    # 2. Cargar productos
    cargar_productos_base()
    print("-" * 30)
    
=======
   
    # 1. Cargar categorías
    cargar_categorias()
    print("-" * 30)
   
    # 2. Cargar productos
    cargar_productos_base()
    print("-" * 30)
   
>>>>>>> e99069a0a67a380785dd9c147491b8dde27adb6e
    # 3. Cargar inventario
    cargar_inventario_inicial()
    print("=" * 50)
    print("🎉 ¡Carga de datos completada!")

if __name__ == "__main__":
<<<<<<< HEAD
    ejecutar_carga_completa()
=======
    ejecutar_carga_completa()
>>>>>>> e99069a0a67a380785dd9c147491b8dde27adb6e
