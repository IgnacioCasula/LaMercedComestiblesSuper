# views.py
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Producto, Categoria, Proveedor
from django.db.models import Q

class ProductListView(ListView):
    model = Producto
    template_name = 'products_list.html'
    context_object_name = 'productos'

class ProductCreateView(CreateView):
    model = Producto
    template_name = 'products_form.html'
    fields = ['codigo', 'nombre', 'categoria', 'stock_actual', 'stock_minimo', 'precio', 'proveedor']
    success_url = reverse_lazy('product_list')

class ProductUpdateView(UpdateView):
    model = Producto
    template_name = 'products_form.html'
    fields = ['codigo', 'nombre', 'categoria', 'stock_actual', 'stock_minimo', 'precio', 'proveedor']
    success_url = reverse_lazy('product_list')

class ProductDeleteView(DeleteView):
    model = Producto
    template_name = 'products_confirm_delete.html'
    success_url = reverse_lazy('product_list')

class CategoriaListView(ListView):
    model = Categoria
    template_name = 'categorias_list.html'
    context_object_name = 'categorias'

class CategoriaCreateView(CreateView):
    model = Categoria
    template_name = 'categorias_form.html'
    fields = ['nombre', 'descripcion', 'activa']
    success_url = reverse_lazy('categoria_list')

class CategoriaUpdateView(UpdateView):
    model = Categoria
    template_name = 'categorias_form.html'
    fields = ['nombre', 'descripcion', 'activa']
    success_url = reverse_lazy('categoria_list')

class CategoriaDeleteView(DeleteView):
    model = Categoria
    template_name = 'categorias_confirm_delete.html'
    success_url = reverse_lazy('categoria_list')

class ProveedorListView(ListView):
    model = Proveedor
    template_name = 'proveedores_list.html'
    context_object_name = 'proveedores'

class ProveedorCreateView(CreateView):
    model = Proveedor
    template_name = 'proveedores_form.html'
    fields = ['nombre', 'contacto', 'telefono', 'email', 'direccion', 'activo']
    success_url = reverse_lazy('proveedor_list')

class ProveedorUpdateView(UpdateView):
    model = Proveedor
    template_name = 'proveedores_form.html'
    fields = ['nombre', 'contacto', 'telefono', 'email', 'direccion', 'activo']
    success_url = reverse_lazy('proveedor_list')

class ProveedorDeleteView(DeleteView):
    model = Proveedor
    template_name = 'proveedores_confirm_delete.html'
    success_url = reverse_lazy('proveedor_list')

class StockBajoListView(ListView):
    model = Producto
    template_name = 'stock_bajo_list.html'
    context_object_name = 'productos'
    
    def get_queryset(self):
        return Producto.objects.filter(
            Q(stock_actual__lte=models.F('stock_minimo')) | 
            Q(stock_actual=0)
        ).select_related('categoria')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        productos = self.get_queryset()
        context['productos_criticos'] = productos.filter(stock_actual__lte=models.F('stock_minimo')).count()
        context['productos_sin_stock'] = productos.filter(stock_actual=0).count()
        return context

def gestion_stock_view(request):
    # Vista para el dashboard principal
    total_productos = Producto.objects.count()
    stock_optimo = Producto.objects.filter(stock_actual__gt=models.F('stock_minimo') * 1.5).count()
    stock_bajo = Producto.objects.filter(
        stock_actual__lte=models.F('stock_minimo') * 1.5,
        stock_actual__gt=models.F('stock_minimo')
    ).count()
    sin_stock = Producto.objects.filter(stock_actual__lte=models.F('stock_minimo')).count()
    
    context = {
        'total_productos': total_productos,
        'stock_optimo': stock_optimo,
        'stock_bajo': stock_bajo,
        'sin_stock': sin_stock,
    }
    return render(request, 'gestion_stock.html', context)