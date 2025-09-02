from django.shortcuts import render, redirect
from .models import Producto
from .forms import ProductForm

def gestion(request):
    productos = Producto.objects.all()
    stock_total = sum(p.stock for p in productos)
    stock_bajo = productos.filter(stock__lt=10).count()

    context = {
        "productos": productos,
        "stock_total": stock_total,
        "stock_bajo": stock_bajo,
    }
    return render(request, "GestionDeStock/gestion.html", context)

def agregar_producto(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("dashboard")  # vuelve al Dashboard
    else:
        form = ProductForm()

    return render(request, "GestionDeStock/agregar_producto.html", {"form": form})
