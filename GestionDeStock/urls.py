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
]