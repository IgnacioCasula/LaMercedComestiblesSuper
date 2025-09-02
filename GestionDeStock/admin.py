from django.contrib import admin
from .models import Category, Supplier, Product, Movement, Alert

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    list_per_page = 20

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'phone', 'email', 'active']
    list_filter = ['active']
    search_fields = ['name', 'contact_person']
    list_editable = ['active']
    list_per_page = 20

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'price', 'stock', 'min_stock', 'is_low_stock', 'active']
    list_filter = ['category', 'active', 'supplier']
    search_fields = ['code', 'name']
    list_editable = ['price', 'stock', 'min_stock', 'active']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 30
    
    def is_low_stock(self, obj):
        return obj.is_low_stock
    is_low_stock.boolean = True
    is_low_stock.short_description = 'Stock Bajo'

@admin.register(Movement)
class MovementAdmin(admin.ModelAdmin):
    list_display = ['product', 'movement_type', 'quantity', 'date', 'user']
    list_filter = ['movement_type', 'date', 'user']
    search_fields = ['product__name', 'product__code']
    readonly_fields = ['created_at']
    date_hierarchy = 'date'
    list_per_page = 30

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['title', 'alert_type', 'product', 'read', 'created_at']
    list_filter = ['alert_type', 'read', 'created_at']
    search_fields = ['title', 'message', 'product__name']
    list_editable = ['read']
    readonly_fields = ['created_at']
    list_per_page = 30