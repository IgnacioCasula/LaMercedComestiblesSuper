# management/commands/productos.py
import os
import sys
from django.core.management.base import BaseCommand
from django.utils import timezone
from caja.models import Productos, Categorias, Inventarios, Sucursales
import random


class Command(BaseCommand):
    help = 'Carga productos de prueba en la base de datos'


    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Iniciando carga de productos...'))
       
        # Verificar si ya existen productos
        if Productos.objects.exists():
            self.stdout.write(self.style.WARNING('⚠️  Ya existen productos en la base de datos'))
            respuesta = input('¿Desea continuar y crear productos adicionales? (s/n): ')
            if respuesta.lower() != 's':
                self.stdout.write(self.style.ERROR('❌ Operación cancelada'))
                return


        # Crear categorías si no existen (SIN FRUTAS Y VERDURAS)
        categorias_data = [
            ('Lácteos', 'Productos lácteos y derivados'),
            ('Fiambres', 'Fiambres y embutidos'),
            ('Bebidas', 'Bebidas sin alcohol'),
            ('Bebidas Alcoholicas', 'Bebidas con alcohol'),
            ('Limpieza', 'Productos de limpieza'),
            ('Perfumería', 'Productos de perfumería'),
            ('Almacén', 'Productos de almacén'),
            ('Congelados', 'Productos congelados'),
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


        # LISTA ACTUALIZADA CON PRODUCTOS ESPECÍFICOS - SIN FRUTAS/VERDURAS
        productos_data = [
            # 🥛 LÁCTEOS (Nombres específicos)
            ('Leche Entera La Serenísima Sachet 1L', 'La Serenísima', 1450.00, 'Lácteos', 7790080080004),
            ('Yogur Bebible Sancor Frutilla 900g', 'Sancor', 2300.00, 'Lácteos', 7790070014022),
            ('Manteca La Primera 200g', 'La Primera', 3500.00, 'Lácteos', 7792742010202),
            ('Queso Cremoso Ilolay 250g', 'Ilolay', 4800.00, 'Lácteos', 7791850100251),
            ('Queso Rallado Sancor 40g', 'Sancor', 950.00, 'Lácteos', 7790070001859),
            ('Yogur Natural La Serenísima 190g', 'La Serenísima', 320.00, 'Lácteos', 779123456002),
            ('Queso Cremón La Paulina 500g', 'La Paulina', 2800.00, 'Lácteos', 779123456003),
            ('Crema de Leche Sancor 350ml', 'Sancor', 520.00, 'Lácteos', 779123456005),
            ('Leche Descremada Sancor 1L', 'Sancor', 470.00, 'Lácteos', 779123456061),
            ('Queso Parmesano Reggianito 200g', 'Reggianito', 3200.00, 'Lácteos', 779123456062),
            ('Ricotta Verónica 500g', 'Verónica', 850.00, 'Lácteos', 779123456063),
            ('Dulce de Leche Clásico Ilolay 400g', 'Ilolay', 620.00, 'Lácteos', 779123456064),
           
            # 🥓 FIAMBRES (Específicos)
            ('Salame Milán Paladini 200g', 'Paladini', 1800.00, 'Fiambres', 779123456006),
            ('Jamón Cocido Paladini 200g', 'Paladini', 2200.00, 'Fiambres', 779123456007),
            ('Queso Tybo Verónica 500g', 'Verónica', 1900.00, 'Fiambres', 779123456008),
            ('Mortadela Granja del Sol 500g', 'Granja del Sol', 1500.00, 'Fiambres', 779123456009),
            ('Panceta Ahumada Cabaña Argentina 500g', 'Cabaña Argentina', 3500.00, 'Fiambres', 779123456010),
           
            # 🥤 BEBIDAS (Específicos)
            ('Gaseosa Coca-Cola 1.5L', 'Coca-Cola', 3100.00, 'Bebidas', 7790070773663),
            ('Agua Mineral Villa del Sur 2L', 'Villa del Sur', 1850.00, 'Bebidas', 7790400012108),
            ('Agua Tónica Paso de los Toros 1.5L', 'Paso de los Toros', 2050.00, 'Bebidas', 7790400100650),
            ('Jugo de Naranja Baggio 1L', 'Baggio', 680.00, 'Bebidas', 779123456013),
            ('Gaseosa Naranja Cunnington 2L', 'Cunnington', 650.00, 'Bebidas', 779123456014),
            ('Agua Saborizada Levité 500ml', 'Levité', 420.00, 'Bebidas', 779123456015),
            ('Sprite 2L', 'Coca Cola', 1100.00, 'Bebidas', 779123456065),
            ('Pepsi 2.25L', 'Pepsi', 1150.00, 'Bebidas', 779123456066),
            ('Agua con Gas Eco de los Andes 500ml', 'Eco de los Andes', 520.00, 'Bebidas', 779123456067),
            ('Energizante Speed 500ml', 'Speed', 680.00, 'Bebidas', 779123456068),
           
            # 🍺 BEBIDAS ALCOHOLICAS (Específicos)
            ('Cerveza Quilmes Clásica Lata 473ml', 'Quilmes', 1800.00, 'Bebidas Alcoholicas', 7790400012146),
            ('Vino Tinto Malbec Alma Mora 750ml', 'Alma Mora', 4800.00, 'Bebidas Alcoholicas', 7790080000453),
            ('Cerveza Heineken Lata 473ml', 'Heineken', 800.00, 'Bebidas Alcoholicas', 779123456016),
            ('Fernet Branca 750ml', 'Branca', 3500.00, 'Bebidas Alcoholicas', 779123456018),
            ('Vodka Smirnoff 750ml', 'Smirnoff', 2800.00, 'Bebidas Alcoholicas', 779123456019),
            ('Whisky J&B 750ml', 'J&B', 4500.00, 'Bebidas Alcoholicas', 779123456020),
           
            # 🧼 LIMPIEZA (Específicos)
            ('Jabón en Polvo Ala 800g', 'Ala', 3900.00, 'Limpieza', 7791290022306),
            ('Lavandina Ayudín 1L', 'Ayudín', 1350.00, 'Limpieza', 7791290001806),
            ('Papel Higiénico Higienol 4 rollos', 'Higienol', 2700.00, 'Limpieza', 7790510000520),
            ('Detergente para Platos Magistral 500ml', 'Magistral', 1150.00, 'Limpieza', 7791290000212),
            ('Jabón Líquido Skip 800ml', 'Skip', 5100.00, 'Limpieza', 7791290022801),
            ('Limpiador de Pisos Poett 900ml', 'Poett', 1900.00, 'Limpieza', 7790460045812),
            ('Piloto Automático Glade', 'Glade', 6700.00, 'Limpieza', 7791290022307),
            ('Detergente Ala 500ml', 'Ala', 480.00, 'Limpieza', 779123456022),
            ('Desinfectante Lysoform 500ml', 'Lysoform', 580.00, 'Limpieza', 779123456024),
            ('Limpia Vidrios Mr. Músculo 500ml', 'Mr. Músculo', 680.00, 'Limpieza', 779123456025),
            ('Suavizante Suavitel 1L', 'Suavitel', 580.00, 'Limpieza', 779123456073),
            ('Jabón en Polvo Drive 800g', 'Drive', 720.00, 'Limpieza', 779123456074),
            ('Limpiador Multiuso Cif 500ml', 'Cif', 520.00, 'Limpieza', 779123456075),
            ('Insecticida Raid 500ml', 'Raid', 680.00, 'Limpieza', 779123456076),
           
            # 🧴 PERFUMERÍA (Específicos)
            ('Shampoo Pantene Restauración 400ml', 'Pantene', 4200.00, 'Perfumería', 7500435165243),
            ('Jabón Tocador Dove 90g', 'Dove', 350.00, 'Perfumería', 779123456026),
            ('Shampoo Sedal 400ml', 'Sedal', 820.00, 'Perfumería', 779123456027),
            ('Desodorante Rexona 48h 150ml', 'Rexona', 650.00, 'Perfumería', 779123456028),
            ('Crema Dental Colgate 90g', 'Colgate', 480.00, 'Perfumería', 779123456029),
            ('Acondicionador Sedal 400ml', 'Sedal', 820.00, 'Perfumería', 779123456077),
            ('Jabón Líquido Protex 500ml', 'Protex', 380.00, 'Perfumería', 779123456078),
            ('Crema Corporal Nivea 400ml', 'Nivea', 750.00, 'Perfumería', 779123456079),
            ('Gel de Baño Dove 500ml', 'Dove', 580.00, 'Perfumería', 779123456080),
           
            # 🛒 ALMACÉN (Específicos)
            ('Aceite de Girasol Cocinero 900ml', 'Cocinero', 2800.00, 'Almacén', 7790750275816),
            ('Fideos Spaghetti Lucchetti 500g', 'Lucchetti', 1300.00, 'Almacén', 7790382000030),
            ('Arroz Largo Fino Gallo 1kg', 'Gallo', 1950.00, 'Almacén', 7790070502018),
            ('Azúcar Ledesma 1kg', 'Ledesma', 1200.00, 'Almacén', 7790150000010),
            ('Yerba Mate Playadito 1kg', 'Playadito', 5900.00, 'Almacén', 7791000000171),
            ('Galletitas Cerealitas Avena 106g', 'Cerealitas', 1100.00, 'Almacén', 7790382000047),
            ('Arvejas en Lata Cumaná 350g', 'Cumaná', 850.00, 'Almacén', 7790885100072),
            ('Café Molido La Virginia 250g', 'La Virginia', 2500.00, 'Almacén', 7790895011048),
            ('Mayonesa Hellmann\'s Clásica 237g', 'Hellmann\'s', 1400.00, 'Almacén', 7791290001042),
            ('Fideos Spaghetti Marolio 500g', 'Marolio', 1050.00, 'Almacén', 7797470199367),
            ('Fideos Tallarín Matarazzo 500g', 'Matarazzo', 450.00, 'Almacén', 779123456032),
            ('Harina 000 Pureza 1kg', 'Pureza', 320.00, 'Almacén', 779123456033),
            ('Lentejas Gallo 500g', 'Gallo', 480.00, 'Almacén', 779123456069),
            ('Porotos Gallo 500g', 'Gallo', 450.00, 'Almacén', 779123456070),
            ('Polenta Morixe 500g', 'Morixe', 320.00, 'Almacén', 779123456071),
            ('Sal Fina Celusal 500g', 'Celusal', 180.00, 'Almacén', 779123456072),
           
            # ❄️ CONGELADOS (Específicos)
            ('Papas Bastón Congeladas McCain 720g', 'McCain', 3700.00, 'Congelados', 7790750275818),
            ('Helado Pote Dulce de Leche Grido 1kg', 'Grido', 6200.00, 'Congelados', 7790290123456),
            ('Pizza Mozzarella Buitoni 500g', 'Buitoni', 1200.00, 'Congelados', 779123456036),
            ('Hamburguesas Paty 4 unidades', 'Paty', 850.00, 'Congelados', 779123456037),
            ('Papas Fritas McCain 1kg', 'McCain', 720.00, 'Congelados', 779123456038),
            ('Helado Vainilla Grido 1L', 'Grido', 650.00, 'Congelados', 779123456039),
            ('Empanadas Carne La Salteña 12 unidades', 'La Salteña', 980.00, 'Congelados', 779123456040),
            ('Nuggets Pollo Granja del Sol 500g', 'Granja del Sol', 980.00, 'Congelados', 779123456081),
            ('Vegetales Mezcla La Huerta 500g', 'La Huerta', 620.00, 'Congelados', 779123456082),
            ('Pescado Filet Mar del Plata 500g', 'Mar del Plata', 1500.00, 'Congelados', 779123456083),
            ('Lasagna Buitoni 400g', 'Buitoni', 1800.00, 'Congelados', 779123456084),
           
            # 🥖 PANADERÍA (Específicos)
            ('Pan Francés 1 unidad', 'Panadería', 250.00, 'Panadería', 779123456051),
            ('Facturas 12 unidades', 'Panadería', 180.00, 'Panadería', 779123456052),
            ('Medialunas 12 unidades', 'Panadería', 200.00, 'Panadería', 779123456053),
            ('Torta 1kg', 'Panadería', 1200.00, 'Panadería', 779123456054),
            ('Galletitas Bagley 150g', 'Bagley', 350.00, 'Panadería', 779123456055),
            ('Pan Integral 1 unidad', 'Panadería', 300.00, 'Panadería', 779123456093),
            ('Tostadas Fargo 300g', 'Fargo', 280.00, 'Panadería', 779123456094),
            ('Budín 500g', 'Panadería', 450.00, 'Panadería', 779123456095),
           
            # 🥩 CARNES (Específicos)
            ('Carne Picada Especial 1kg', 'Carnicería', 2800.00, 'Carnes', 779123456056),
            ('Pechuga de Pollo 1kg', 'Avícola', 1800.00, 'Carnes', 779123456057),
            ('Asado 1kg', 'Carnicería', 3500.00, 'Carnes', 779123456058),
            ('Chorizo Parrillero 1kg', 'Carnicería', 2200.00, 'Carnes', 779123456059),
            ('Milanesas de Ternera 1kg', 'Carnicería', 3200.00, 'Carnes', 779123456060),
            ('Bife de Chorizo 1kg', 'Carnicería', 4200.00, 'Carnes', 779123456097),
            ('Pata y Muslo de Pollo 1kg', 'Avícola', 1500.00, 'Carnes', 779123456098),
            ('Costillas de Cerdo 1kg', 'Carnicería', 2800.00, 'Carnes', 779123456099),
            ('Matambre 1kg', 'Carnicería', 3200.00, 'Carnes', 779123456100),
        ]


        # Crear productos
        productos_creados = 0
        productos_con_error = 0
        
        for nombre, marca, precio, categoria_nombre, codigo_barras in productos_data:
            try:
                # Verificar si el código de barras ya existe
                if Productos.objects.filter(codigobarraproducto=codigo_barras).exists():
                    self.stdout.write(self.style.WARNING(f'⚠️  Producto con código {codigo_barras} ya existe, saltando...'))
                    productos_con_error += 1
                    continue


                producto = Productos.objects.create(
                    nombreproductos=nombre,
                    marcaproducto=marca,
                    precioproducto=precio,
                    codigobarraproducto=codigo_barras,
                    idcategoria=categorias[categoria_nombre],
                    imagenproducto=''
                )
                productos_creados += 1
                self.stdout.write(self.style.SUCCESS(f'✅ Producto creado: {nombre} - ${precio}'))


            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Error creando producto {nombre}: {str(e)}'))
                productos_con_error += 1


        self.stdout.write(self.style.SUCCESS(f'🎉 Se crearon {productos_creados} productos exitosamente!'))
        if productos_con_error > 0:
            self.stdout.write(self.style.WARNING(f'⚠️  {productos_con_error} productos no se pudieron crear (duplicados o errores)'))


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
       
        inventarios_creados = 0
        for sucursal in sucursales:
            for producto in productos:
                # Crear inventario con stock aleatorio entre 10 y 100
                stock = random.randint(10, 100)
                inventario, created = Inventarios.objects.get_or_create(
                    producto=producto,
                    sucursal=sucursal,
                    defaults={'cantidad': stock}
                )
                if created:
                    inventarios_creados += 1
            self.stdout.write(self.style.SUCCESS(f'✅ Inventario creado para sucursal: {sucursal.nombresucursal}'))
        
        self.stdout.write(self.style.SUCCESS(f'📊 Total inventarios creados: {inventarios_creados}'))