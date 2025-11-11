# management/commands/limpiar_logs.py
from django.core.management.base import BaseCommand
import os
from datetime import datetime, timedelta
from django.conf import settings

class Command(BaseCommand):
    help = 'Elimina logs antiguos (mayores a 90 días)'

    def handle(self, *args, **kwargs):
        logs_dir = os.path.join(settings.BASE_DIR, 'logs')
        if not os.path.exists(logs_dir):
            return

        fecha_limite = datetime.now() - timedelta(days=90)
        eliminados = 0

        for filename in os.listdir(logs_dir):
            if filename.startswith('actividad_') and filename.endswith('.jsonl'):
                try:
                    fecha_str = filename.replace('actividad_', '').replace('.jsonl', '')
                    fecha_archivo = datetime.strptime(fecha_str, '%Y-%m-%d')
                    
                    if fecha_archivo < fecha_limite:
                        os.remove(os.path.join(logs_dir, filename))
                        eliminados += 1
                        self.stdout.write(f'Eliminado: {filename}')
                except:
                    pass

        self.stdout.write(self.style.SUCCESS(f'✅ {eliminados} archivos de logs eliminados'))