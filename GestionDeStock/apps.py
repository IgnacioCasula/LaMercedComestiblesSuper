from django.apps import AppConfig

class StockConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stock'  # Cambia esto si tu app tiene otro nombre
    verbose_name = 'Gestión de Stock'