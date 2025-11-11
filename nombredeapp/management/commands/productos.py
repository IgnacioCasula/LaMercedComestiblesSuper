# management/commands/productos.py
import os
import sys
from django.core.management.base import BaseCommand
from django.utils import timezone
from caja.models import Productos, Categorias, Inventarios, Sucursales
import random

class Command(BaseCommand):
    help = 'Carga 100 productos de prueba en la base de datos'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Iniciando carga de productos...'))
        
        # Verificar si ya existen productos
        if Productos.objects.exists():
            self.stdout.write(self.style.WARNING('⚠️  Ya existen productos en la base de datos'))
            respuesta = input('¿Desea continuar y crear productos adicionales? (s/n): ')
            if respuesta.lower() != 's':
                self.stdout.write(self.style.ERROR('❌ Operación cancelada'))
                return

        # Crear categorías si no existen
        categorias_data = [
            ('Lácteos', 'Productos lácteos y derivados'),
            ('Fiambres', 'Fiambres y embutidos'),
            ('Bebidas', 'Bebidas sin alcohol'),
            ('Bebidas Alcoholicas', 'Bebidas con alcohol'),
            ('Limpieza', 'Productos de limpieza'),
            ('Perfumería', 'Productos de perfumería'),
            ('Almacén', 'Productos de almacén'),
            ('Congelados', 'Productos congelados'),
            ('Frutas', 'Frutas frescas'),
            ('Verduras', 'Verduras frescas'),
            ('Panadería', 'Productos de panadería'),
            ('Carnes', 'Carnes y derivados'),
        ]

        categorias = {}
        for nombre, descripcion in categorias_data:
            cat, created = Categorias.objects.get_or_create(
                nombrecategoria=nombre,
                defaults={'descripcioncategoria': descripcion}
            )
            categorias[nombre] = cat
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Categoría creada: {nombre}'))

        # Datos de productos de ejemplo para un almacén
        productos_data = [
            # Lácteos
            ('Leche Entera 1L', 'La Serenísima', 450.00, 'Lácteos', 779123456001),
            ('Yogur Natural', 'La Serenísima', 320.00, 'Lácteos', 779123456002),
            ('Queso Cremón', 'La Paulina', 2800.00, 'Lácteos', 779123456003),
            ('Manteca 200g', 'La Serenísima', 650.00, 'Lácteos', 779123456004),
            ('Crema de Leche', 'Sancor', 520.00, 'Lácteos', 779123456005),
            
            # Fiambres
            ('Salame Milán', 'Paladini', 1800.00, 'Fiambres', 779123456006),
            ('Jamón Cocido', 'Paladini', 2200.00, 'Fiambres', 779123456007),
            ('Queso Tybo', 'Verónica', 1900.00, 'Fiambres', 779123456008),
            ('Mortadela', 'Granja del Sol', 1500.00, 'Fiambres', 779123456009),
            ('Panceta', 'Cabaña Argentina', 3500.00, 'Fiambres', 779123456010),
            
            # Bebidas
            ('Agua Mineral 2L', 'Villavicencio', 480.00, 'Bebidas', 779123456011),
            ('Coca Cola 2.25L', 'Coca Cola', 1200.00, 'Bebidas', 779123456012),
            ('Jugo de Naranja 1L', 'Baggio', 680.00, 'Bebidas', 779123456013),
            ('Gaseosa Naranja 2L', 'Cunnington', 650.00, 'Bebidas', 779123456014),
            ('Agua Saborizada', 'Levité', 420.00, 'Bebidas', 779123456015),
            
            # Bebidas Alcoholicas
            ('Cerveza Heineken', 'Heineken', 800.00, 'Bebidas Alcoholicas', 779123456016),
            ('Vino Malbec', 'Alamos', 2500.00, 'Bebidas Alcoholicas', 779123456017),
            ('Fernet Branca', 'Branca', 3500.00, 'Bebidas Alcoholicas', 779123456018),
            ('Vodka Smirnoff', 'Smirnoff', 2800.00, 'Bebidas Alcoholicas', 779123456019),
            ('Whisky J&B', 'J&B', 4500.00, 'Bebidas Alcoholicas', 779123456020),
            
            # Limpieza
            ('Lavandina 1L', 'Ayudín', 620.00, 'Limpieza', 779123456021),
            ('Detergente', 'Ala', 480.00, 'Limpieza', 779123456022),
            ('Jabón Líquido', 'Skip', 720.00, 'Limpieza', 779123456023),
            ('Desinfectante', 'Lysoform', 580.00, 'Limpieza', 779123456024),
            ('Limpia Vidrios', 'Mr. Músculo', 680.00, 'Limpieza', 779123456025),
            
            # Perfumería
            ('Jabón Tocador', 'Dove', 350.00, 'Perfumería', 779123456026),
            ('Shampoo', 'Sedal', 820.00, 'Perfumería', 779123456027),
            ('Desodorante', 'Rexona', 650.00, 'Perfumería', 779123456028),
            ('Crema Dental', 'Colgate', 480.00, 'Perfumería', 779123456029),
            ('Papel Higiénico', 'Higgienol', 420.00, 'Perfumería', 779123456030),
            
            # Almacén
            ('Arroz 1Kg', 'Gallo', 680.00, 'Almacén', 779123456031),
            ('Fideos Tallarín', 'Matarazzo', 450.00, 'Almacén', 779123456032),
            ('Harina 000', 'Pureza', 320.00, 'Almacén', 779123456033),
            ('Aceite Girasol', 'Cocinero', 980.00, 'Almacén', 779123456034),
            ('Azúcar 1Kg', 'Chango', 480.00, 'Almacén', 779123456035),
            
            # Congelados
            ('Pizza Mozzarella', 'Buitoni', 1200.00, 'Congelados', 779123456036),
            ('Hamburguesas', 'Paty', 850.00, 'Congelados', 779123456037),
            ('Papas Fritas', 'McCain', 720.00, 'Congelados', 779123456038),
            ('Helado Vainilla', 'Grido', 650.00, 'Congelados', 779123456039),
            ('Empanadas Carne', 'La Salteña', 980.00, 'Congelados', 779123456040),
            
            # Frutas (precios por kg)
            ('Manzana Roja Kg', 'Mendoza', 850.00, 'Frutas', 779123456041),
            ('Banana Kg', 'Ecuador', 680.00, 'Frutas', 779123456042),
            ('Naranja Kg', 'Tucumán', 520.00, 'Frutas', 779123456043),
            ('Limón Kg', 'Tucumán', 480.00, 'Frutas', 779123456044),
            ('Uva Kg', 'Mendoza', 1200.00, 'Frutas', 779123456045),
            
            # Verduras (precios por kg)
            ('Tomate Kg', 'Córdoba', 750.00, 'Verduras', 779123456046),
            ('Lechuga', 'Buenos Aires', 350.00, 'Verduras', 779123456047),
            ('Cebolla Kg', 'San Juan', 420.00, 'Verduras', 779123456048),
            ('Zanahoria Kg', 'Santa Fe', 380.00, 'Verduras', 779123456049),
            ('Papa Kg', 'Balcarce', 320.00, 'Verduras', 779123456050),
            
            # Panadería
            ('Pan Frances', 'Panadería', 250.00, 'Panadería', 779123456051),
            ('Facturas', 'Panadería', 180.00, 'Panadería', 779123456052),
            ('Medialunas', 'Panadería', 200.00, 'Panadería', 779123456053),
            ('Tortas', 'Panadería', 1200.00, 'Panadería', 779123456054),
            ('Galletitas', 'Bagley', 350.00, 'Panadería', 779123456055),
            
            # Carnes
            ('Carne Picada Kg', 'Carnicería', 2800.00, 'Carnes', 779123456056),
            ('Pechuga Pollo Kg', 'Avícola', 1800.00, 'Carnes', 779123456057),
            ('Asado Kg', 'Carnicería', 3500.00, 'Carnes', 779123456058),
            ('Chorizo Kg', 'Carnicería', 2200.00, 'Carnes', 779123456059),
            ('Milanesas Kg', 'Carnicería', 3200.00, 'Carnes', 779123456060),
        ]

        # Agregar 40 productos más variados
        productos_extra = [
            # Más lácteos
            ('Leche Descremada', 'Sancor', 470.00, 'Lácteos', 779123456061),
            ('Queso Parmesano', 'Reggianito', 3200.00, 'Lácteos', 779123456062),
            ('Ricotta', 'Verónica', 850.00, 'Lácteos', 779123456063),
            ('Dulce de Leche', 'Ilolay', 620.00, 'Lácteos', 779123456064),
            
            # Más bebidas
            ('Sprite 2L', 'Coca Cola', 1100.00, 'Bebidas', 779123456065),
            ('Pepsi 2.25L', 'Pepsi', 1150.00, 'Bebidas', 779123456066),
            ('Agua con Gas', 'Eco de los Andes', 520.00, 'Bebidas', 779123456067),
            ('Energizante', 'Speed', 680.00, 'Bebidas', 779123456068),
            
            # Más almacén
            ('Lentejas 500g', 'Gallo', 480.00, 'Almacén', 779123456069),
            ('Porotos 500g', 'Gallo', 450.00, 'Almacén', 779123456070),
            ('Polenta', 'Morixe', 320.00, 'Almacén', 779123456071),
            ('Sal Fina', 'Celusal', 180.00, 'Almacén', 779123456072),
            
            # Más limpieza
            ('Suavizante', 'Suavitel', 580.00, 'Limpieza', 779123456073),
            ('Jabón en Polvo', 'Drive', 720.00, 'Limpieza', 779123456074),
            ('Limpiador Multiuso', 'Cif', 520.00, 'Limpieza', 779123456075),
            ('Insecticida', 'Raid', 680.00, 'Limpieza', 779123456076),
            
            # Más perfumería
            ('Acondicionador', 'Sedal', 820.00, 'Perfumería', 779123456077),
            ('Jabón Líquido', 'Protex', 380.00, 'Perfumería', 779123456078),
            ('Crema Corporal', 'Nivea', 750.00, 'Perfumería', 779123456079),
            ('Gel de Baño', 'Dove', 580.00, 'Perfumería', 779123456080),
            
            # Más congelados
            ('Nuggets Pollo', 'Granja del Sol', 980.00, 'Congelados', 779123456081),
            ('Vegetales Mezcla', 'La Huerta', 620.00, 'Congelados', 779123456082),
            ('Pescado Filet', 'Mar del Plata', 1500.00, 'Congelados', 779123456083),
            ('Lasagna', 'Buitoni', 1800.00, 'Congelados', 779123456084),
            
            # Más frutas
            ('Pera Kg', 'Río Negro', 780.00, 'Frutas', 779123456085),
            ('Durazno Kg', 'Mendoza', 950.00, 'Frutas', 779123456086),
            ('Frutilla Kg', 'Coronda', 1800.00, 'Frutas', 779123456087),
            ('Ciruela Kg', 'Mendoza', 850.00, 'Frutas', 779123456088),
            
            # Más verduras
            ('Zapallo Kg', 'Córdoba', 320.00, 'Verduras', 779123456089),
            ('Espinaca', 'Buenos Aires', 280.00, 'Verduras', 779123456090),
            ('Brócoli', 'Buenos Aires', 450.00, 'Verduras', 779123456091),
            ('Ajo Kg', 'Córdoba', 1200.00, 'Verduras', 779123456092),
            
            # Más panadería
            ('Pan Integral', 'Panadería', 300.00, 'Panadería', 779123456093),
            ('Tostadas', 'Fargo', 280.00, 'Panadería', 779123456094),
            ('Budín', 'Panadería', 450.00, 'Panadería', 779123456095),
            ('Manteca', 'Panadería', 180.00, 'Panadería', 779123456096),
            
            # Más carnes
            ('Bife Chorizo Kg', 'Carnicería', 4200.00, 'Carnes', 779123456097),
            ('Pata Muslo Kg', 'Avícola', 1500.00, 'Carnes', 779123456098),
            ('Costillas Kg', 'Carnicería', 2800.00, 'Carnes', 779123456099),
            ('Matambre Kg', 'Carnicería', 3200.00, 'Carnes', 779123456100),
        ]

        productos_data.extend(productos_extra)

        # Crear productos
        productos_creados = 0
        for nombre, marca, precio, categoria_nombre, codigo_barras in productos_data:
            try:
                # Verificar si el código de barras ya existe
                if Productos.objects.filter(codigobarraproducto=codigo_barras).exists():
                    self.stdout.write(self.style.WARNING(f'⚠️  Producto con código {codigo_barras} ya existe, saltando...'))
                    continue

                producto = Productos.objects.create(
                    nombreproductos=nombre,
                    marcaproducto=marca,
                    precioproducto=precio,
                    codigobarraproducto=codigo_barras,
                    idcategoria=categorias[categoria_nombre],
                    imagenproducto=''  # Imagen vacía por ahora
                )
                productos_creados += 1
                self.stdout.write(self.style.SUCCESS(f'✅ Producto creado: {nombre} - ${precio}'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Error creando producto {nombre}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS(f'🎉 Se crearon {productos_creados} productos exitosamente!'))

        # Crear inventario para todas las sucursales
        self.crear_inventario_para_productos()

    def crear_inventario_para_productos(self):
        """Crear inventario para todos los productos en todas las sucursales"""
        self.stdout.write(self.style.SUCCESS('📦 Creando inventario...'))
        
        sucursales = Sucursales.objects.all()
        productos = Productos.objects.all()
        
        if not sucursales.exists():
            self.stdout.write(self.style.WARNING('⚠️  No hay sucursales creadas. Creando sucursal por defecto...'))
            from caja.models import Ubicaciones, Codigopostal
            
            # Crear código postal
            cp, _ = Codigopostal.objects.get_or_create(
                codigopostal=5000,
                defaults={'nombrelocalidad': 'Córdoba Capital'}
            )
            
            # Crear ubicación
            ubicacion, _ = Ubicaciones.objects.get_or_create(
                ciudad='Córdoba',
                nombrecalle='Av. Colón 1000',
                barrio='Centro',
                idcodigopostal=cp
            )
            
            # Crear sucursal
            sucursal = Sucursales.objects.create(
                nombresucursal='Sucursal Central',
                telefonosucursal=3511234567,
                idubicacion=ubicacion
            )
            sucursales = [sucursal]
        
        for sucursal in sucursales:
            for producto in productos:
                # Crear inventario con stock aleatorio entre 10 y 100
                stock = random.randint(10, 100)
                Inventarios.objects.get_or_create(
                    producto=producto,
                    sucursal=sucursal,
                    defaults={'cantidad': stock}
                )
            self.stdout.write(self.style.SUCCESS(f'✅ Inventario creado para sucursal: {sucursal.nombresucursal}'))