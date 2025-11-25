# GestionDeStock/forms.py
from django import forms
from caja.models import Proveedores as Proveedor, Categorias as Categoria, Productos as Producto

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ["nombreproveedor", "telefonoproveedor", "emailprov", "cuitproveedor"]
        widgets = {
            "nombreproveedor": forms.TextInput(attrs={"class": "form-control"}),
            "telefonoproveedor": forms.NumberInput(attrs={"class": "form-control"}),
            "emailprov": forms.EmailInput(attrs={"class": "form-control"}),
            "cuitproveedor": forms.NumberInput(attrs={"class": "form-control"}),
        }

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombrecategoria", "descripcioncategoria"]
        widgets = {
            "nombrecategoria": forms.TextInput(attrs={"class": "form-control"}),
            "descripcioncategoria": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }

class ProductoForm(forms.ModelForm):
    # Sobrescribir el campo idcategoria para personalizar cómo se muestran las opciones
    idcategoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all(),
        widget=forms.Select(attrs={"class": "form-control"}),
        empty_label="Seleccione una categoría",
        label="Categoría"
    )
    
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
        widgets = {
            "nombreproductos": forms.TextInput(attrs={"class": "form-control"}),
            "precioproducto": forms.NumberInput(attrs={"step": "0.01", "class": "form-control"}),
            "marcaproducto": forms.TextInput(attrs={"class": "form-control"}),
            "codigobarraproducto": forms.NumberInput(attrs={"class": "form-control"}),
            "imagenproducto": forms.ClearableFileInput(attrs={"class": "form-control"}),
            # NOTA: idcategoria ya tiene widget personalizado arriba, así que lo quitamos de aquí
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar cómo se muestran las opciones en el dropdown
        self.fields['idcategoria'].label_from_instance = lambda obj: obj.nombrecategoria