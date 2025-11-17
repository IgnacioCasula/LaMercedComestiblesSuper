# GestionDeStock/urls.py
from django.urls import path
from . import views

app_name = 'gestion_stock'  # ← Esto es lo importante

urlpatterns = [
    path('', views.gestion_stock_view, name='gestion_stock'),
    
    # Productos
    path('productos/', views.ProductListView.as_view(), name='product_list'),
    path('productos/nuevo/', views.ProductCreateView.as_view(), name='product_create'),
    path('productos/<int:pk>/editar/', views.ProductUpdateView.as_view(), name='product_update'),
    path('productos/<int:pk>/eliminar/', views.ProductDeleteView.as_view(), name='product_delete'),
    
    # Categorías
    path('categorias/', views.CategoriaListView.as_view(), name='categoria_list'),
    path('categorias/nueva/', views.CategoriaCreateView.as_view(), name='categoria_create'),
    path('categorias/<int:pk>/editar/', views.CategoriaUpdateView.as_view(), name='categoria_update'),
    path('categorias/<int:pk>/eliminar/', views.CategoriaDeleteView.as_view(), name='categoria_delete'),
    
    # Proveedores
    path('proveedores/', views.ProveedorListView.as_view(), name='proveedor_list'),
    path('proveedores/nuevo/', views.ProveedorCreateView.as_view(), name='proveedor_create'),
    path('proveedores/<int:pk>/editar/', views.ProveedorUpdateView.as_view(), name='proveedor_update'),
    path('proveedores/<int:pk>/eliminar/', views.ProveedorDeleteView.as_view(), name='proveedor_delete'),
    
    # Stock Bajo
    path('stock-bajo/', views.StockBajoListView.as_view(), name='stock_bajo_list'),
]