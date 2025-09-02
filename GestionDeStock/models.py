from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Supplier(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nombre")
    contact_person = models.CharField(max_length=100, blank=True, verbose_name="Persona de contacto")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, verbose_name="Correo electrónico")
    address = models.TextField(blank=True, verbose_name="Dirección")
    active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Product(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="Código")
    name = models.CharField(max_length=200, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name="Categoría")
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, verbose_name="Proveedor")
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], verbose_name="Precio")
    cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], verbose_name="Costo")
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Stock actual")
    min_stock = models.IntegerField(default=5, validators=[MinValueValidator(0)], verbose_name="Stock mínimo")
    unit = models.CharField(max_length=20, default="unidad", verbose_name="Unidad")
    location = models.CharField(max_length=100, blank=True, verbose_name="Ubicación en almacén")
    expiration_date = models.DateField(null=True, blank=True, verbose_name="Fecha de caducidad")
    active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    @property
    def is_low_stock(self):
        return self.stock <= self.min_stock
    
    @property
    def total_value(self):
        return self.stock * self.cost

class Movement(models.Model):
    MOVEMENT_TYPES = (
        ('in', 'Entrada'),
        ('out', 'Salida'),
        ('adjust', 'Ajuste'),
    )
    
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="Producto")
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_TYPES, verbose_name="Tipo de movimiento")
    quantity = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="Cantidad")
    date = models.DateTimeField(default=timezone.now, verbose_name="Fecha")
    user = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Usuario")
    notes = models.TextField(blank=True, verbose_name="Notas")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Movimiento"
        verbose_name_plural = "Movimientos"
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.product.name} - {self.quantity}"

class Alert(models.Model):
    ALERT_TYPES = (
        ('warning', 'Advertencia'),
        ('danger', 'Peligro'),
        ('info', 'Información'),
        ('success', 'Éxito'),
    )
    
    title = models.CharField(max_length=200, verbose_name="Título")
    message = models.TextField(verbose_name="Mensaje")
    alert_type = models.CharField(max_length=10, choices=ALERT_TYPES, default='warning', verbose_name="Tipo de alerta")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Producto")
    read = models.BooleanField(default=False, verbose_name="Leída")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Alerta"
        verbose_name_plural = "Alertas"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title