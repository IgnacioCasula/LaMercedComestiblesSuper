from django.urls import path
from . import views

app_name = 'stock'

urlpatterns = [
    # Vista principal
    path('', views.gestion_de_stock, name='gestion_de_stock'),
    
    # Vistas de formularios
    path('productos/crear/', views.crear_producto_view, name='crear_producto'),
    path('productos/<int:producto_id>/editar/', views.editar_producto_view, name='editar_producto'),
    path('categorias/crear/', views.crear_categoria_view, name='crear_categoria'),
    path('categorias/<int:categoria_id>/editar/', views.editar_categoria_view, name='editar_categoria'),
    path('proveedores/crear/', views.crear_proveedor_view, name='crear_proveedor'),
    path('proveedores/<int:proveedor_id>/editar/', views.editar_proveedor_view, name='editar_proveedor'),
    
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
    
    # API Estadísticas y Alertas
    path('api/estadisticas/', views.api_estadisticas_stock, name='api_estadisticas_stock'),
    path('api/alertas/', views.api_alertas_stock, name='api_alertas_stock'),

    # URLs para Pedidos
    path('pedidos/', views.gestion_pedidos, name='gestion_pedidos'),
    path('pedidos/crear/', views.crear_pedido, name='crear_pedido'),
    path('pedidos/<int:pedido_id>/editar/', views.editar_pedido, name='editar_pedido'),
    path('pedidos/<int:pedido_id>/eliminar/', views.eliminar_pedido, name='eliminar_pedido'),

    path('api/productos/<int:producto_id>/actualizar-vencimiento/', views.api_actualizar_vencimiento, name='api_actualizar_vencimiento'),

]
