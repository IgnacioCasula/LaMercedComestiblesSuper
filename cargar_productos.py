import os
import django
import sys

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ProyectoSuper.settings')
django.setup()

from django.db import transaction
from caja.models import Categorias, Productos, Inventarios, Sucursales, Ubicaciones, Codigopostal

def cargar_codigo_postal():
    """Cargar código postal base si no existe"""
    print("📮 Cargando código postal...")
    
    codigo_postal, created = Codigopostal.objects.get_or_create(
        idcodigopostal=1,
        defaults={
            "codigopostal": 4400,
            "nombrelocalidad": "Salta",
        }
    )
    
    if created:
        print("  ✅ Código postal creado: 4400 - Salta")
    else:
        print("  ℹ️  Código postal existente: 4400 - Salta")
    
    return codigo_postal

def cargar_ubicacion():
    """Cargar ubicación base si no existe"""
    print("🗺️ Cargando ubicación...")
    
    codigo_postal = cargar_codigo_postal()
    
    ubicacion, created = Ubicaciones.objects.get_or_create(
        idubicacion=1,
        defaults={
            "ciudad": "Salta",
            "nombrecalle": "Av. Principal",
            "barrio": "Centro",
            "idcodigopostal": codigo_postal,
        }
    )
    
    if created:
        print("  ✅ Ubicación creada: Av. Principal 123, Salta")
    else:
        print("  ℹ️  Ubicación existente: Av. Principal 123, Salta")
    
    return ubicacion

def cargar_sucursal():
    """Cargar sucursal base si no existe"""
    print("📍 Cargando sucursal...")
    
    ubicacion = cargar_ubicacion()
    
    # Crear sucursal con ubicación
    sucursal, created_sucursal = Sucursales.objects.get_or_create(
        idsucursal=1,
        defaults={
            "nombresucursal": "Sucursal Principal",
            "telefonosucursal": 3875123456,
            "idubicacion": ubicacion,
        }
    )
    
    if created_sucursal:
        print("  ✅ Sucursal creada: Sucursal Principal")
    else:
        print("  ℹ️  Sucursal existente: Sucursal Principal")
    
    return sucursal

def cargar_categorias():
    """Cargar categorías básicas si no existen"""
    print("📂 Cargando categorías...")
    
    categorias_base = [
        {"nombre": "Almacén", "descripcion": "Productos de almacén y secos"},
        {"nombre": "Lácteos", "descripcion": "Leche, quesos y derivados"},
        {"nombre": "Bebidas", "descripcion": "Bebidas y refrescos"},
        {"nombre": "Limpieza", "descripcion": "Productos de limpieza y cuidado personal"},
        {"nombre": "Hogar", "descripcion": "Productos para el hogar"},
    ]
    
    categorias_creadas = 0
    
    for cat_data in categorias_base:
        try:
            categoria, created = Categorias.objects.get_or_create(
                nombrecategoria=cat_data["nombre"],
                defaults={"descripcioncategoria": cat_data["descripcion"]}
            )
            if created:
                categorias_creadas += 1
                print(f"  ✅ Categoría creada: {cat_data['nombre']}")
            else:
                print(f"  ℹ️  Categoría existente: {cat_data['nombre']}")
        except Exception as e:
            print(f"  ❌ Error creando categoría {cat_data['nombre']}: {e}")
    
    print(f"  📊 Total categorías: {Categorias.objects.count()}")
    return Categorias.objects.all()

def cargar_productos_base():
    """Cargar productos básicos del supermercado"""
    print("📦 Cargando productos...")
    
    # Obtener categorías
    try:
        categorias = {
            "Almacén": Categorias.objects.get(nombrecategoria="Almacén"),
            "Lácteos": Categorias.objects.get(nombrecategoria="Lácteos"),
            "Bebidas": Categorias.objects.get(nombrecategoria="Bebidas"),
            "Limpieza": Categorias.objects.get(nombrecategoria="Limpieza"),
            "Hogar": Categorias.objects.get(nombrecategoria="Hogar"),
        }
    except Categorias.DoesNotExist as e:
        print(f"  ❌ Error: No se encontró alguna categoría: {e}")
        return 0
    
    # LISTA SIMPLIFICADA DE PRODUCTOS
    productos_data = [
        # 🥛 LÁCTEOS
        {"nombre": "Leche Entera La Serenísima (1L)", "precio": 1450, "marca": "La Serenísima", "codigo_barra": 7790080080004, "categoria": "Lácteos"},
        {"nombre": "Yogur Bebible Sancor Frutilla (900g)", "precio": 2300, "marca": "Sancor", "codigo_barra": 7790070014022, "categoria": "Lácteos"},
        {"nombre": "Queso Cremoso Ilolay (250g)", "precio": 4800, "marca": "Ilolay", "codigo_barra": 7791850100251, "categoria": "Lácteos"},
       
        # 🛒 ALMACÉN
        {"nombre": "Aceite de Girasol Cocinero (900ml)", "precio": 2800, "marca": "Cocinero", "codigo_barra": 7790750275000, "categoria": "Almacén"},
        {"nombre": "Fideos Spaghetti Lucchetti (500g)", "precio": 1300, "marca": "Lucchetti", "codigo_barra": 7790382000030, "categoria": "Almacén"},
        {"nombre": "Arroz Largo Fino Gallo (1kg)", "precio": 1950, "marca": "Gallo", "codigo_barra": 7790070502018, "categoria": "Almacén"},
        {"nombre": "Azúcar Ledesma (1kg)", "precio": 1200, "marca": "Ledesma", "codigo_barra": 7790150000010, "categoria": "Almacén"},
       
        # 🥤 BEBIDAS
        {"nombre": "Gaseosa Coca-Cola (1.5L)", "precio": 3100, "marca": "Coca-Cola", "codigo_barra": 7790070773663, "categoria": "Bebidas"},
        {"nombre": "Cerveza Quilmes Clásica (Lata 473ml)", "precio": 1800, "marca": "Quilmes", "codigo_barra": 7790400012146, "categoria": "Bebidas"},
       
        # 🧴 LIMPIEZA
        {"nombre": "Jabón en Polvo Ala (800g)", "precio": 3900, "marca": "Ala", "codigo_barra": 7791290022306, "categoria": "Limpieza"},
        {"nombre": "Papel Higiénico Higienol (4 rollos)", "precio": 2700, "marca": "Higienol", "codigo_barra": 7790510000520, "categoria": "Limpieza"},
    ]
    
    productos_creados = 0
    
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
               
                if created:
                    productos_creados += 1
                    print(f"  ✅ Producto creado: {prod_data['nombre']} - ${prod_data['precio']}")
                else:
                    # Actualizar producto existente
                    producto.nombreproductos = prod_data["nombre"]
                    producto.precioproducto = prod_data["precio"]
                    producto.marcaproducto = prod_data["marca"]
                    producto.idcategoria = categorias[prod_data["categoria"]]
                    producto.save()
                    print(f"  🔄 Producto actualizado: {prod_data['nombre']} - ${prod_data['precio']}")
                       
            except Exception as e:
                print(f"  ❌ Error al crear producto {prod_data['nombre']}: {str(e)}")
    
    print(f"  📊 Total productos en sistema: {Productos.objects.count()}")
    return productos_creados

def cargar_inventario_inicial(sucursal):
    """Cargar inventario inicial para todos los productos"""
    print("🏪 Cargando inventario...")
    
    try:
        productos = Productos.objects.all()
        inventarios_creados = 0
        
        with transaction.atomic():
            for producto in productos:
                try:
                    inventario, created = Inventarios.objects.get_or_create(
                        producto=producto,
                        sucursal=sucursal,
                        defaults={"cantidad": 50}  # Stock inicial de 50 unidades
                    )
                   
                    if created:
                        inventarios_creados += 1
                        print(f"  📦 Inventario creado para: {producto.nombreproductos}")
                except Exception as e:
                    print(f"  ⚠️  Error con inventario de {producto.nombreproductos}: {e}")
        
        print(f"  📊 Inventarios creados: {inventarios_creados}")
        return inventarios_creados
        
    except Exception as e:
        print(f"  ❌ Error al cargar inventario: {str(e)}")
        return 0

def ejecutar_carga_completa():
    """Ejecutar toda la carga de datos"""
    print("🚀 Iniciando carga de datos...")
    print("=" * 50)
    
    try:
        # 1. Crear sucursal (con manejo de errores)
        sucursal = cargar_sucursal()
        print("-" * 30)
        
        # 2. Cargar categorías
        cargar_categorias()
        print("-" * 30)
        
        # 3. Cargar productos
        productos_creados = cargar_productos_base()
        print("-" * 30)
        
        # 4. Cargar inventario
        if productos_creados > 0:
            cargar_inventario_inicial(sucursal)
        else:
            print("⚠️  No se crearon productos nuevos, saltando inventario")
            
        print("=" * 50)
        print("🎉 ¡Carga de datos completada!")
        
    except Exception as e:
        print(f"❌ ERROR CRÍTICO: {e}")
        print("💡 Verifica que la base de datos esté configurada correctamente")

if __name__ == "__main__":
    ejecutar_carga_completa()