# GestionDeStock/forms.py
from django import forms
# Usamos los modelos de la app 'caja' para evitar duplicados de tablas
from caja.models import Proveedores as Proveedor, Categorias as Categoria, Productos as Producto

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ["nombreproveedor", "telefonoproveedor", "emailprov", "cuitproveedor"]
        labels = {
            "nombreproveedor": "Nombre",
            "telefonoproveedor": "Teléfono",
            "emailprov": "Email",
            "cuitproveedor": "CUIT",
        }
        widgets = {
            "nombreproveedor": forms.TextInput(attrs={"class": "form-control"}),
            "telefonoproveedor": forms.TextInput(attrs={"class": "form-control"}),
            "emailprov": forms.EmailInput(attrs={"class": "form-control"}),
            "cuitproveedor": forms.TextInput(attrs={"class": "form-control"}),
        }

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombrecategoria", "descripcioncategoria"]
        labels = {
            "nombrecategoria": "Nombre",
            "descripcioncategoria": "Descripción",
        }
        widgets = {
            "nombrecategoria": forms.TextInput(attrs={"class": "form-control"}),
            "descripcioncategoria": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            "nombreproductos",
            "precioproducto",
            "marcaproducto",
            "codigobarraproducto",
            "imagenproducto",
            "idcategoria",
        ]
        labels = {
            "nombreproductos": "Nombre",
            "precioproducto": "Precio",
            "marcaproducto": "Marca",
            "codigobarraproducto": "Código de barras",
            "imagenproducto": "Imagen",
            "idcategoria": "Categoría",
        }
        widgets = {
            "nombreproductos": forms.TextInput(attrs={"class": "form-control"}),
            "precioproducto": forms.NumberInput(attrs={"step": "0.01", "class": "form-control"}),
            "marcaproducto": forms.TextInput(attrs={"class": "form-control"}),
            "codigobarraproducto": forms.TextInput(attrs={"class": "form-control"}),
            "imagenproducto": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "idcategoria": forms.Select(attrs={"class": "form-control"}),
        }
