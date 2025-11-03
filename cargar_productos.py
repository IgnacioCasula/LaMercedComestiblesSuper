import os
import django
import sys

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ProyectoSuper.settings')
django.setup()

from django.db import transaction
from caja.models import Categorias, Productos, Inventarios, Sucursales, Ubicaciones

def cargar_ubicacion_y_sucursal():
    """Cargar ubicación y sucursal base si no existen"""
    print("📍 Cargando ubicación y s
    ucursal...")
    
    # Crear ubicación
    ubicacion, created_ubicacion = Ubicaciones.objects.get_or_create(
        idubicacion=1,
        defaults={
            "direccionubicacion": "Av. Principal 123",
            "codigopostal": "4400",
            "localidad": "Salta",
            "provincia": "Salta"
        }
    )
    
    if created_ubicacion:
        print("  ✅ Ubicación creada")
    else:
        print("  ℹ️  Ubicación existente")
    
    # Crear sucursal
    sucursal, created_sucursal = Sucursales.objects.get_or_create(
        idsucursal=1,
        defaults={
            "nombresucursal": "Sucursal Principal",
            "telefonosucursal": "3875123456",
            "idubicacion": ubicacion
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
        {"nombre": "Frutas y Verduras", "descripcion": "Frutas y verduras frescas"},
        {"nombre": "Lácteos", "descripcion": "Leche, quesos y derivados"},
        {"nombre": "Carnes", "descripcion": "Carnes y productos cárnicos"},
        {"nombre": "Panadería", "descripcion": "Pan y productos de panadería"},
    ]
    
    for cat_data in categorias_base:
        categoria, created = Categorias.objects.get_or_create(
            nombrecategoria=cat_data["nombre"],
            defaults={"descripcioncategoria": cat_data["descripcion"]}
        )
        if created:
            print(f"  ✅ Categoría creada: {cat_data['nombre']}")
        else:
            print(f"  ℹ️  Categoría existente: {cat_data['nombre']}")
    
    return Categorias.objects.all()

def cargar_productos_base():
    """Cargar productos básicos del supermercado"""
    print("📦 Cargando productos...")
    
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
    
    # Productos con precios actualizados
    productos_data = [
        # 🥛 LÁCTEOS Y REFRIGERADOS
        {"nombre": "Leche Entera La Serenísima (1L)", "precio": 1450, "marca": "La Serenísima", "codigo_barra": 7790080080004, "categoria": "Lácteos"},
        {"nombre": "Yogur Bebible Sancor Frutilla (900g)", "precio": 2300, "marca": "Sancor", "codigo_barra": 7790070014022, "categoria": "Lácteos"},
        {"nombre": "Manteca La Primera (200g)", "precio": 3500, "marca": "La Primera", "codigo_barra": 7792742010202, "categoria": "Lácteos"},
        {"nombre": "Queso Cremoso Ilolay (250g)", "precio": 4800, "marca": "Ilolay", "codigo_barra": 7791850100251, "categoria": "Lácteos"},
        {"nombre": "Queso Rallado Sancor (40g)", "precio": 950, "marca": "Sancor", "codigo_barra": 7790070001859, "categoria": "Lácteos"},
        {"nombre": "Papas Bastón Congeladas McCain (720g)", "precio": 3700, "marca": "McCain", "codigo_barra": 7790750275816, "categoria": "Lácteos"},
        {"nombre": "Helado Pote Dulce de Leche Grido (1kg)", "precio": 6200, "marca": "Grido", "codigo_barra": 7790290123456, "categoria": "Lácteos"},

        # 🛒 ALMACÉN Y DESPENSA
        {"nombre": "Aceite de Girasol Cocinero (900ml)", "precio": 2800, "marca": "Cocinero", "codigo_barra": 7790750275816, "categoria": "Almacén"},
        {"nombre": "Fideos Spaghetti Lucchetti (500g)", "precio": 1300, "marca": "Lucchetti", "codigo_barra": 7790382000030, "categoria": "Almacén"},
        {"nombre": "Arroz Largo Fino Gallo (1kg)", "precio": 1950, "marca": "Gallo", "codigo_barra": 7790070502018, "categoria": "Almacén"},
        {"nombre": "Azúcar Ledesma (1kg)", "precio": 1200, "marca": "Ledesma", "codigo_barra": 7790150000010, "categoria": "Almacén"},
        {"nombre": "Yerba Mate Playadito (1kg)", "precio": 5900, "marca": "Playadito", "codigo_barra": 7791000000171, "categoria": "Almacén"},
        {"nombre": "Galletitas Cerealitas Avena (106g)", "precio": 1100, "marca": "Cerealitas", "codigo_barra": 7790382000047, "categoria": "Almacén"},
        {"nombre": "Arvejas en Lata Cumaná (350g)", "precio": 850, "marca": "Cumaná", "codigo_barra": 7790885100072, "categoria": "Almacén"},
        {"nombre": "Café Molido La Virginia (250g)", "precio": 2500, "marca": "La Virginia", "codigo_barra": 7790895011048, "categoria": "Almacén"},
        {"nombre": "Mayonesa Hellmann's Clásica (237g)", "precio": 1400, "marca": "Hellmann's", "codigo_barra": 7791290001042, "categoria": "Almacén"},

        # 🥤 BEBIDAS
        {"nombre": "Gaseosa Coca-Cola (1.5L)", "precio": 3100, "marca": "Coca-Cola", "codigo_barra": 7790070773663, "categoria": "Bebidas"},
        {"nombre": "Agua Mineral Villa del Sur (2L)", "precio": 1850, "marca": "Villa del Sur", "codigo_barra": 7790400012108, "categoria": "Bebidas"},
        {"nombre": "Agua Tónica Paso de los Toros (1.5L)", "precio": 2050, "marca": "Paso de los Toros", "codigo_barra": 7790400100650, "categoria": "Bebidas"},
        {"nombre": "Cerveza Quilmes Clásica (Lata 473ml)", "precio": 1800, "marca": "Quilmes", "codigo_barra": 7790400012146, "categoria": "Bebidas"},
        {"nombre": "Vino Tinto Malbec Alma Mora (750ml)", "precio": 4800, "marca": "Alma Mora", "codigo_barra": 7790080000453, "categoria": "Bebidas"},

        # 🧴 LIMPIEZA Y CUIDADO PERSONAL
        {"nombre": "Jabón en Polvo Ala (800g)", "precio": 3900, "marca": "Ala", "codigo_barra": 7791290022306, "categoria": "Limpieza"},
        {"nombre": "Shampoo Pantene Restauración (400ml)", "precio": 4200, "marca": "Pantene", "codigo_barra": 7500435165243, "categoria": "Limpieza"},
        {"nombre": "Lavandina Ayudín (1L)", "precio": 1350, "marca": "Ayudín", "codigo_barra": 7791290001806, "categoria": "Limpieza"},
        {"nombre": "Papel Higiénico Higienol (4 rollos)", "precio": 2700, "marca": "Higienol", "codigo_barra": 7790510000520, "categoria": "Limpieza"},
        {"nombre": "Detergente para Platos Magistral (500ml)", "precio": 1150, "marca": "Magistral", "codigo_barra": 7791290000212, "categoria": "Limpieza"},
        {"nombre": "Jabón Líquido para Ropa Skip (800ml)", "precio": 5100, "marca": "Skip", "codigo_barra": 7791290022801, "categoria": "Limpieza"},
        {"nombre": "Limpiador de Pisos Poett (900ml)", "precio": 1900, "marca": "Poett", "codigo_barra": 7790460045812, "categoria": "Limpieza"},

        # 🏠 PRODUCTOS PARA EL HOGAR
        {"nombre": "Piloto Automático Glade (Difusor + Repuesto)", "precio": 6700, "marca": "Glade", "codigo_barra": 7791290022306, "categoria": "Hogar"},
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
                    print(f"  ℹ️  Producto existente: {prod_data['nombre']}")
                        
            except Exception as e:
                print(f"  ❌ Error al crear producto {prod_data['nombre']}: {str(e)}")
    
    print(f"  📊 Productos creados: {productos_creados}")
    return productos_creados

def cargar_inventario_inicial(sucursal):
    """Cargar inventario inicial para todos los productos"""
    print("🏪 Cargando inventario...")
    
    try:
        productos = Productos.objects.all()
        inventarios_creados = 0
        
        with transaction.atomic():
            for producto in productos:
                inventario, created = Inventarios.objects.get_or_create(
                    producto=producto,
                    sucursal=sucursal,
                    defaults={"cantidad": 100}  # Stock inicial de 100 unidades
                )
                
                if created:
                    inventarios_creados += 1
                    print(f"  📦 Inventario creado para: {producto.nombreproductos}")
        
        print(f"  📊 Inventarios creados: {inventarios_creados}")
        return inventarios_creados
        
    except Exception as e:
        print(f"  ❌ Error al cargar inventario: {str(e)}")
        return 0

def ejecutar_carga_completa():
    """Ejecutar toda la carga de datos"""
    print("🚀 Iniciando carga de datos...")
    print("=" * 50)
    
    # 1. Cargar ubicación y sucursal
    sucursal = cargar_ubicacion_y_sucursal()
    print("-" * 30)
    
    # 2. Cargar categorías
    cargar_categorias()
    print("-" * 30)
    
    # 3. Cargar productos
    cargar_productos_base()
    print("-" * 30)
    
    # 4. Cargar inventario
    cargar_inventario_inicial(sucursal)
    print("=" * 50)
    print("🎉 ¡Carga de datos completada!")

if __name__ == "__main__":
    ejecutar_carga_completa()