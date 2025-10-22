# GestionDeStock/admin.py
from django.contrib import admin
from .models import Categoria, Proveedor, Producto
admin.site.register(Categoria)
admin.site.register(Proveedor)
admin.site.register(Producto)
