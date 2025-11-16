from django.urls import path
from . import views

app_name = 'stock'

urlpatterns = [
    # Vista principal
    path('', views.gestion_de_stock, name='gestion_de_stock'),
    
    # API Productos
    path('api/productos/', views.api_listar_productos, name='api_listar_productos'),
    path('api/productos/crear/', views.api_crear_producto, name='api_crear_producto'),
    path('api/productos/<int:producto_id>/editar/', views.api_editar_producto, name='api_editar_producto'),
    path('api/productos/<int:producto_id>/eliminar/', views.api_eliminar_producto, name='api_eliminar_producto'),
    
    # API Categorías
    path('api/categorias/', views.api_listar_categorias, name='api_listar_categorias'),
    path('api/categorias/crear/', views.api_crear_categoria, name='api_crear_categoria'),
    path('api/categorias/<int:categoria_id>/editar/', views.api_editar_categoria, name='api_editar_categoria'),
    path('api/categorias/<int:categoria_id>/eliminar/', views.api_eliminar_categoria, name='api_eliminar_categoria'),
    
    # API Proveedores
    path('api/proveedores/', views.api_listar_proveedores, name='api_listar_proveedores'),
    path('api/proveedores/crear/', views.api_crear_proveedor, name='api_crear_proveedor'),
    path('api/proveedores/<int:proveedor_id>/editar/', views.api_editar_proveedor, name='api_editar_proveedor'),
    path('api/proveedores/<int:proveedor_id>/eliminar/', views.api_eliminar_proveedor, name='api_eliminar_proveedor'),

    # API Movimientos
    path('api/movimientos/', views.api_listar_movimientos, name='api_listar_movimientos'),
    path('api/movimientos/crear/', views.api_crear_movimiento, name='api_crear_movimiento'),
    path('api/movimientos/mejorado/', views.api_listar_movimientos_mejorado, name='api_listar_movimientos_mejorado'),

    # API Ventas
    path('api/ventas/', views.api_listar_ventas, name='api_listar_ventas'),
    
    # API Estadísticas y Alertas (NUEVAS)
    path('api/estadisticas/', views.api_estadisticas_stock, name='api_estadisticas_stock'),
    path('api/alertas/', views.api_alertas_stock, name='api_alertas_stock'),
]