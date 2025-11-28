# management/commands/productos.py
import os
import sys
from django.core.management.base import BaseCommand
from django.utils import timezone
from caja.models import Productos, Categorias, Inventarios, Sucursales, Proveedores, Provxprod
import random
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Carga 100 productos de prueba en la base de datos con fechas de vencimiento y proveedores'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Iniciando carga de productos con fechas de vencimiento y proveedores...'))
        
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

        # Crear proveedores si no existen
        proveedores_data = [
            ('La Serenísima', 1145678901, 'contacto@laserenisima.com', 30123456789),
            ('Sancor', 1145678902, 'contacto@sancor.com', 30123456790),
            ('Paladini', 1145678903, 'contacto@paladini.com', 30123456791),
            ('Coca Cola', 1145678904, 'contacto@cocacola.com', 30123456792),
            ('PepsiCo', 1145678905, 'contacto@pepsico.com', 30123456793),
            ('Unilever', 1145678906, 'contacto@unilever.com', 30123456794),
            ('Procter & Gamble', 1145678907, 'contacto@pg.com', 30123456795),
            ('Nestlé', 1145678908, 'contacto@nestle.com', 30123456796),
            ('Molinos Río de la Plata', 1145678909, 'contacto@molinos.com', 30123456797),
            ('Arcor', 1145678910, 'contacto@arcor.com', 30123456798),
            ('Ledesma', 1145678911, 'contacto@ledesma.com', 30123456799),
            ('Bagley', 1145678912, 'contacto@bagley.com', 30123456800),
            ('La Salteña', 1145678913, 'contacto@lasaltena.com', 30123456801),
            ('Granja del Sol', 1145678914, 'contacto@granjadelsol.com', 30123456802),
            ('Adecoagro', 1145678915, 'contacto@adecoagro.com', 30123456803),
            ('Danone', 1145678916, 'contacto@danone.com', 30123456804),
            ('Quilmes', 1145678917, 'contacto@quilmes.com', 30123456805),
            ('Branca', 1145678918, 'contacto@branca.com', 30123456806),
            ('La Paulina', 1145678919, 'contacto@lapaulina.com', 30123456807),
            ('Verónica', 1145678920, 'contacto@veronica.com', 30123456808),
        ]

        proveedores = {}
        for nombre, telefono, email, cuit in proveedores_data:
            prov, created = Proveedores.objects.get_or_create(
                cuitproveedor=cuit,
                defaults={
                    'nombreproveedor': nombre,
                    'telefonoproveedor': telefono,
                    'emailprov': email
                }
            )
            proveedores[nombre] = prov
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Proveedor creado: {nombre}'))

        # Mapeo de productos a proveedores
        producto_proveedor_map = {
            # Lácteos
            'Leche Entera 1L': 'La Serenísima',
            'Yogur Natural': 'La Serenísima',
            'Queso Cremón': 'La Paulina',
            'Manteca 200g': 'La Serenísima',
            'Crema de Leche': 'Sancor',
            'Leche Descremada': 'Sancor',
            'Queso Parmesano': 'La Paulina',
            'Ricotta': 'Verónica',
            'Dulce de Leche': 'Sancor',
            
            # Fiambres
            'Salame Milán': 'Paladini',
            'Jamón Cocido': 'Paladini',
            'Queso Tybo': 'Verónica',
            'Mortadela': 'Granja del Sol',
            'Panceta': 'Paladini',
            
            # Bebidas
            'Agua Mineral 2L': 'Nestlé',
            'Coca Cola 2.25L': 'Coca Cola',
            'Jugo de Naranja 1L': 'Baggio',
            'Gaseosa Naranja 2L': 'Coca Cola',
            'Agua Saborizada': 'Nestlé',
            'Sprite 2L': 'Coca Cola',
            'Pepsi 2.25L': 'PepsiCo',
            'Agua con Gas': 'Nestlé',
            'Energizante': 'PepsiCo',
            
            # Bebidas Alcoholicas
            'Cerveza Heineken': 'Quilmes',
            'Vino Malbec': 'Adecoagro',
            'Fernet Branca': 'Branca',
            'Vodka Smirnoff': 'PepsiCo',
            'Whisky J&B': 'PepsiCo',
            
            # Limpieza
            'Lavandina 1L': 'Unilever',
            'Detergente': 'Unilever',
            'Jabón Líquido': 'Unilever',
            'Desinfectante': 'Unilever',
            'Limpia Vidrios': 'Procter & Gamble',
            'Suavizante': 'Procter & Gamble',
            'Jabón en Polvo': 'Unilever',
            'Limpiador Multiuso': 'Unilever',
            'Insecticida': 'Procter & Gamble',
            
            # Perfumería
            'Jabón Tocador': 'Unilever',
            'Shampoo': 'Unilever',
            'Desodorante': 'Unilever',
            'Crema Dental': 'Procter & Gamble',
            'Papel Higiénico': 'Procter & Gamble',
            'Acondicionador': 'Unilever',
            'Jabón Líquido': 'Procter & Gamble',
            'Crema Corporal': 'Unilever',
            'Gel de Baño': 'Unilever',
            
            # Almacén
            'Arroz 1Kg': 'Molinos Río de la Plata',
            'Fideos Tallarín': 'Molinos Río de la Plata',
            'Harina 000': 'Molinos Río de la Plata',
            'Aceite Girasol': 'Molinos Río de la Plata',
            'Azúcar 1Kg': 'Ledesma',
            'Lentejas 500g': 'Molinos Río de la Plata',
            'Porotos 500g': 'Molinos Río de la Plata',
            'Polenta': 'Molinos Río de la Plata',
            'Sal Fina': 'Arcor',
            
            # Congelados
            'Pizza Mozzarella': 'Molinos Río de la Plata',
            'Hamburguesas': 'Granja del Sol',
            'Papas Fritas': 'McCain',
            'Helado Vainilla': 'Unilever',
            'Empanadas Carne': 'La Salteña',
            'Nuggets Pollo': 'Granja del Sol',
            'Vegetales Mezcla': 'Granja del Sol',
            'Pescado Filet': 'Granja del Sol',
            'Lasagna': 'Molinos Río de la Plata',
            
            # Frutas y Verduras (proveedores locales)
            'Manzana Roja Kg': 'Adecoagro',
            'Banana Kg': 'Adecoagro',
            'Naranja Kg': 'Adecoagro',
            'Limón Kg': 'Adecoagro',
            'Uva Kg': 'Adecoagro',
            'Tomate Kg': 'Adecoagro',
            'Lechuga': 'Adecoagro',
            'Cebolla Kg': 'Adecoagro',
            'Zanahoria Kg': 'Adecoagro',
            'Papa Kg': 'Adecoagro',
            'Pera Kg': 'Adecoagro',
            'Durazno Kg': 'Adecoagro',
            'Frutilla Kg': 'Adecoagro',
            'Ciruela Kg': 'Adecoagro',
            'Zapallo Kg': 'Adecoagro',
            'Espinaca': 'Adecoagro',
            'Brócoli': 'Adecoagro',
            'Ajo Kg': 'Adecoagro',
            
            # Panadería
            'Pan Frances': 'Arcor',
            'Facturas': 'Arcor',
            'Medialunas': 'Arcor',
            'Tortas': 'Arcor',
            'Galletitas': 'Bagley',
            'Pan Integral': 'Arcor',
            'Tostadas': 'Bagley',
            'Budín': 'Arcor',
            'Manteca': 'Arcor',
            
            # Carnes
            'Carne Picada Kg': 'Granja del Sol',
            'Pechuga Pollo Kg': 'Granja del Sol',
            'Asado Kg': 'Granja del Sol',
            'Chorizo Kg': 'Granja del Sol',
            'Milanesas Kg': 'Granja del Sol',
            'Bife Chorizo Kg': 'Granja del Sol',
            'Pata Muslo Kg': 'Granja del Sol',
            'Costillas Kg': 'Granja del Sol',
            'Matambre Kg': 'Granja del Sol',
        }

        # Función para generar fechas de vencimiento realistas según categoría
        def generar_fecha_vencimiento(categoria_nombre):
            hoy = timezone.now().date()
            
            if categoria_nombre in ['Lácteos', 'Fiambres']:
                # Productos perecederos: 15-60 días
                return hoy + timedelta(days=random.randint(15, 60))
            
            elif categoria_nombre in ['Frutas', 'Verduras']:
                # Productos frescos: 3-14 días
                return hoy + timedelta(days=random.randint(3, 14))
            
            elif categoria_nombre in ['Carnes', 'Panadería']:
                # Productos muy perecederos: 2-7 días
                return hoy + timedelta(days=random.randint(2, 7))
            
            elif categoria_nombre == 'Congelados':
                # Congelados: 6-24 meses
                return hoy + timedelta(days=random.randint(180, 720))
            
            elif categoria_nombre in ['Bebidas', 'Bebidas Alcoholicas']:
                # Bebidas: 6-36 meses
                return hoy + timedelta(days=random.randint(180, 1080))
            
            elif categoria_nombre in ['Limpieza', 'Perfumería']:
                # Productos no perecederos: 12-48 meses
                return hoy + timedelta(days=random.randint(360, 1440))
            
            elif categoria_nombre == 'Almacén':
                # Almacén: 6-24 meses
                return hoy + timedelta(days=random.randint(180, 720))
            
            else:
                # Por defecto: 12 meses
                return hoy + timedelta(days=365)

        # Datos de productos de ejemplo para un almacén CON FECHAS DE VENCIMIENTO
        productos_data = [
            # Lácteos (15-60 días)
            ('Leche Entera 1L', 'La Serenísima', 450.00, 'Lácteos', 779123456001),
            ('Yogur Natural', 'La Serenísima', 320.00, 'Lácteos', 779123456002),
            ('Queso Cremón', 'La Paulina', 2800.00, 'Lácteos', 779123456003),
            ('Manteca 200g', 'La Serenísima', 650.00, 'Lácteos', 779123456004),
            ('Crema de Leche', 'Sancor', 520.00, 'Lácteos', 779123456005),
            
            # Fiambres (15-60 días)
            ('Salame Milán', 'Paladini', 1800.00, 'Fiambres', 779123456006),
            ('Jamón Cocido', 'Paladini', 2200.00, 'Fiambres', 779123456007),
            ('Queso Tybo', 'Verónica', 1900.00, 'Fiambres', 779123456008),
            ('Mortadela', 'Granja del Sol', 1500.00, 'Fiambres', 779123456009),
            ('Panceta', 'Paladini', 3500.00, 'Fiambres', 779123456010),
            
            # Bebidas (6-36 meses)
            ('Agua Mineral 2L', 'Villavicencio', 480.00, 'Bebidas', 779123456011),
            ('Coca Cola 2.25L', 'Coca Cola', 1200.00, 'Bebidas', 779123456012),
            ('Jugo de Naranja 1L', 'Baggio', 680.00, 'Bebidas', 779123456013),
            ('Gaseosa Naranja 2L', 'Cunnington', 650.00, 'Bebidas', 779123456014),
            ('Agua Saborizada', 'Levité', 420.00, 'Bebidas', 779123456015),
            
            # Bebidas Alcoholicas (6-36 meses)
            ('Cerveza Heineken', 'Heineken', 800.00, 'Bebidas Alcoholicas', 779123456016),
            ('Vino Malbec', 'Alamos', 2500.00, 'Bebidas Alcoholicas', 779123456017),
            ('Fernet Branca', 'Branca', 3500.00, 'Bebidas Alcoholicas', 779123456018),
            ('Vodka Smirnoff', 'Smirnoff', 2800.00, 'Bebidas Alcoholicas', 779123456019),
            ('Whisky J&B', 'J&B', 4500.00, 'Bebidas Alcoholicas', 779123456020),
            
            # Limpieza (12-48 meses)
            ('Lavandina 1L', 'Ayudín', 620.00, 'Limpieza', 779123456021),
            ('Detergente', 'Ala', 480.00, 'Limpieza', 779123456022),
            ('Jabón Líquido', 'Skip', 720.00, 'Limpieza', 779123456023),
            ('Desinfectante', 'Lysoform', 580.00, 'Limpieza', 779123456024),
            ('Limpia Vidrios', 'Mr. Músculo', 680.00, 'Limpieza', 779123456025),
            
            # Perfumería (12-48 meses)
            ('Jabón Tocador', 'Dove', 350.00, 'Perfumería', 779123456026),
            ('Shampoo', 'Sedal', 820.00, 'Perfumería', 779123456027),
            ('Desodorante', 'Rexona', 650.00, 'Perfumería', 779123456028),
            ('Crema Dental', 'Colgate', 480.00, 'Perfumería', 779123456029),
            ('Papel Higiénico', 'Higgienol', 420.00, 'Perfumería', 779123456030),
            
            # Almacén (6-24 meses)
            ('Arroz 1Kg', 'Gallo', 680.00, 'Almacén', 779123456031),
            ('Fideos Tallarín', 'Matarazzo', 450.00, 'Almacén', 779123456032),
            ('Harina 000', 'Pureza', 320.00, 'Almacén', 779123456033),
            ('Aceite Girasol', 'Cocinero', 980.00, 'Almacén', 779123456034),
            ('Azúcar 1Kg', 'Chango', 480.00, 'Almacén', 779123456035),
            
            # Congelados (6-24 meses)
            ('Pizza Mozzarella', 'Buitoni', 1200.00, 'Congelados', 779123456036),
            ('Hamburguesas', 'Paty', 850.00, 'Congelados', 779123456037),
            ('Papas Fritas', 'McCain', 720.00, 'Congelados', 779123456038),
            ('Helado Vainilla', 'Grido', 650.00, 'Congelados', 779123456039),
            ('Empanadas Carne', 'La Salteña', 980.00, 'Congelados', 779123456040),
            
            # Frutas (3-14 días)
            ('Manzana Roja Kg', 'Mendoza', 850.00, 'Frutas', 779123456041),
            ('Banana Kg', 'Ecuador', 680.00, 'Frutas', 779123456042),
            ('Naranja Kg', 'Tucumán', 520.00, 'Frutas', 779123456043),
            ('Limón Kg', 'Tucumán', 480.00, 'Frutas', 779123456044),
            ('Uva Kg', 'Mendoza', 1200.00, 'Frutas', 779123456045),
            
            # Verduras (3-14 días)
            ('Tomate Kg', 'Córdoba', 750.00, 'Verduras', 779123456046),
            ('Lechuga', 'Buenos Aires', 350.00, 'Verduras', 779123456047),
            ('Cebolla Kg', 'San Juan', 420.00, 'Verduras', 779123456048),
            ('Zanahoria Kg', 'Santa Fe', 380.00, 'Verduras', 779123456049),
            ('Papa Kg', 'Balcarce', 320.00, 'Verduras', 779123456050),
            
            # Panadería (2-7 días)
            ('Pan Frances', 'Panadería', 250.00, 'Panadería', 779123456051),
            ('Facturas', 'Panadería', 180.00, 'Panadería', 779123456052),
            ('Medialunas', 'Panadería', 200.00, 'Panadería', 779123456053),
            ('Tortas', 'Panadería', 1200.00, 'Panadería', 779123456054),
            ('Galletitas', 'Bagley', 350.00, 'Panadería', 779123456055),
            
            # Carnes (2-7 días)
            ('Carne Picada Kg', 'Carnicería', 2800.00, 'Carnes', 779123456056),
            ('Pechuga Pollo Kg', 'Avícola', 1800.00, 'Carnes', 779123456057),
            ('Asado Kg', 'Carnicería', 3500.00, 'Carnes', 779123456058),
            ('Chorizo Kg', 'Carnicería', 2200.00, 'Carnes', 779123456059),
            ('Milanesas Kg', 'Carnicería', 3200.00, 'Carnes', 779123456060),
        ]

        # Agregar 40 productos más variados CON FECHAS DE VENCIMIENTO
        productos_extra = [
            # Más lácteos (15-60 días)
            ('Leche Descremada', 'Sancor', 470.00, 'Lácteos', 779123456061),
            ('Queso Parmesano', 'Reggianito', 3200.00, 'Lácteos', 779123456062),
            ('Ricotta', 'Verónica', 850.00, 'Lácteos', 779123456063),
            ('Dulce de Leche', 'Ilolay', 620.00, 'Lácteos', 779123456064),
            
            # Más bebidas (6-36 meses)
            ('Sprite 2L', 'Coca Cola', 1100.00, 'Bebidas', 779123456065),
            ('Pepsi 2.25L', 'Pepsi', 1150.00, 'Bebidas', 779123456066),
            ('Agua con Gas', 'Eco de los Andes', 520.00, 'Bebidas', 779123456067),
            ('Energizante', 'Speed', 680.00, 'Bebidas', 779123456068),
            
            # Más almacén (6-24 meses)
            ('Lentejas 500g', 'Gallo', 480.00, 'Almacén', 779123456069),
            ('Porotos 500g', 'Gallo', 450.00, 'Almacén', 779123456070),
            ('Polenta', 'Morixe', 320.00, 'Almacén', 779123456071),
            ('Sal Fina', 'Celusal', 180.00, 'Almacén', 779123456072),
            
            # Más limpieza (12-48 meses)
            ('Suavizante', 'Suavitel', 580.00, 'Limpieza', 779123456073),
            ('Jabón en Polvo', 'Drive', 720.00, 'Limpieza', 779123456074),
            ('Limpiador Multiuso', 'Cif', 520.00, 'Limpieza', 779123456075),
            ('Insecticida', 'Raid', 680.00, 'Limpieza', 779123456076),
            
            # Más perfumería (12-48 meses)
            ('Acondicionador', 'Sedal', 820.00, 'Perfumería', 779123456077),
            ('Jabón Líquido', 'Protex', 380.00, 'Perfumería', 779123456078),
            ('Crema Corporal', 'Nivea', 750.00, 'Perfumería', 779123456079),
            ('Gel de Baño', 'Dove', 580.00, 'Perfumería', 779123456080),
            
            # Más congelados (6-24 meses)
            ('Nuggets Pollo', 'Granja del Sol', 980.00, 'Congelados', 779123456081),
            ('Vegetales Mezcla', 'La Huerta', 620.00, 'Congelados', 779123456082),
            ('Pescado Filet', 'Mar del Plata', 1500.00, 'Congelados', 779123456083),
            ('Lasagna', 'Buitoni', 1800.00, 'Congelados', 779123456084),
            
            # Más frutas (3-14 días)
            ('Pera Kg', 'Río Negro', 780.00, 'Frutas', 779123456085),
            ('Durazno Kg', 'Mendoza', 950.00, 'Frutas', 779123456086),
            ('Frutilla Kg', 'Coronda', 1800.00, 'Frutas', 779123456087),
            ('Ciruela Kg', 'Mendoza', 850.00, 'Frutas', 779123456088),
            
            # Más verduras (3-14 días)
            ('Zapallo Kg', 'Córdoba', 320.00, 'Verduras', 779123456089),
            ('Espinaca', 'Buenos Aires', 280.00, 'Verduras', 779123456090),
            ('Brócoli', 'Buenos Aires', 450.00, 'Verduras', 779123456091),
            ('Ajo Kg', 'Córdoba', 1200.00, 'Verduras', 779123456092),
            
            # Más panadería (2-7 días)
            ('Pan Integral', 'Panadería', 300.00, 'Panadería', 779123456093),
            ('Tostadas', 'Fargo', 280.00, 'Panadería', 779123456094),
            ('Budín', 'Panadería', 450.00, 'Panadería', 779123456095),
            ('Manteca', 'Panadería', 180.00, 'Panadería', 779123456096),
            
            # Más carnes (2-7 días)
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

                # Generar fecha de vencimiento realista
                fecha_vencimiento = generar_fecha_vencimiento(categoria_nombre)

                producto = Productos.objects.create(
                    nombreproductos=nombre,
                    marcaproducto=marca,
                    precioproducto=precio,
                    codigobarraproducto=codigo_barras,
                    idcategoria=categorias[categoria_nombre],
                    imagenproducto='',  # Imagen vacía por ahora
                    fechavencimiento=fecha_vencimiento  # NUEVO: Fecha de vencimiento
                )
                
                # Asociar proveedor si existe en el mapeo
                if nombre in producto_proveedor_map:
                    proveedor_nombre = producto_proveedor_map[nombre]
                    if proveedor_nombre in proveedores:
                        Provxprod.objects.create(
                            idproducto=producto,
                            idproveedor=proveedores[proveedor_nombre]
                        )
                        self.stdout.write(self.style.SUCCESS(f'✅ Producto creado: {nombre} - ${precio} - Vence: {fecha_vencimiento} - Proveedor: {proveedor_nombre}'))
                    else:
                        self.stdout.write(self.style.WARNING(f'⚠️  Proveedor no encontrado para {nombre}: {proveedor_nombre}'))
                        self.stdout.write(self.style.SUCCESS(f'✅ Producto creado: {nombre} - ${precio} - Vence: {fecha_vencimiento}'))
                else:
                    self.stdout.write(self.style.WARNING(f'⚠️  No se encontró proveedor para {nombre}'))
                    self.stdout.write(self.style.SUCCESS(f'✅ Producto creado: {nombre} - ${precio} - Vence: {fecha_vencimiento}'))
                
                productos_creados += 1

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