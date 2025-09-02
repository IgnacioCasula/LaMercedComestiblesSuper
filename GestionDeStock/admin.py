from django.contrib import admin
from .models import  Proveedor, Producto, Movimiento, Compra, Detallecompras, Venta, Detalleventas


# Registro de modelos en el admin
@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'descripcion')


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'contacto', 'telefono', 'email', 'activo')


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('id', 'codigo', 'nombre', 'categoria', 'proveedor', 'precio', 'stock', 'activo')
    list_filter = ('categoria', 'proveedor', 'activo')
    search_fields = ('codigo', 'nombre')


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = ('id', 'producto', 'cantidad', 'fecha', 'notas')


@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha', 'proveedor')


@admin.register(Detallecompras)
class DetalleComprasAdmin(admin.ModelAdmin):
    list_display = ('id', 'compra', 'producto', 'cantidad', 'precio_compra')


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha',)


@admin.register(Detalleventas)
class DetalleVentasAdmin(admin.ModelAdmin):
    list_display = ('id', 'venta', 'producto', 'cantidad', 'precio_venta')
