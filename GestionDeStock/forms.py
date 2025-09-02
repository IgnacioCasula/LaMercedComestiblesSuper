from django import forms
from .models import Product, Category, Supplier, Movement

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'code', 'name', 'description', 'category', 'supplier', 
            'price', 'cost', 'stock', 'min_stock', 'unit', 
            'location', 'expiration_date', 'active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'expiration_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean_code(self):
        code = self.cleaned_data['code']
        # Verificar si el código ya existe (excepto para esta instancia)
        if self.instance and self.instance.pk:
            if Product.objects.filter(code=code).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("Este código ya existe")
        else:
            if Product.objects.filter(code=code).exists():
                raise forms.ValidationError("Este código ya existe")
        return code

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'phone', 'email', 'address', 'active']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

class MovementForm(forms.ModelForm):
    class Meta:
        model = Movement
        fields = ['product', 'quantity', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }