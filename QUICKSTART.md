# 🚀 Inicio Rápido con Docker

## Pasos Rápidos (5 minutos)

### 1. Iniciar MySQL con Docker
```bash
./start-docker.sh
```

O manualmente:
```bash
docker-compose up -d
```

### 2. Actualizar configuración de base de datos

Edita `ProyectoSuper/settings.py` y cambia:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'lamercedcomestibles',
        'USER': 'lamerced_user',      # ← Cambiar de 'root'
        'PASSWORD': 'lamerced_pass',  # ← Cambiar de ''
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'sql_mode': 'STRICT_TRANS_TABLES',
        },
    }
}
```

### 3. Configurar Python
```bash
# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configurar base de datos
```bash
# Aplicar migraciones
python manage.py migrate

# Crear usuario administrador
python manage.py crear_usuarios
```

### 5. Ejecutar aplicación
```bash
python manage.py runserver
```

Abre en tu navegador: **http://127.0.0.1:8000/**

**Credenciales por defecto:**
- Usuario: `admin`
- Contraseña: `admin123`

## Comandos Docker Útiles

```bash
# Ver estado
docker-compose ps

# Ver logs
docker-compose logs -f mysql

# Detener MySQL
docker-compose down

# Detener y eliminar datos
docker-compose down -v

# Reiniciar
docker-compose restart
```

## Solución de Problemas

### Error: "Can't connect to MySQL server"
```bash
# Verificar que el contenedor esté corriendo
docker-compose ps

# Si no está corriendo, iniciarlo
docker-compose up -d

# Ver logs para diagnosticar
docker-compose logs mysql
```

### Error: "Access denied for user"
- Verifica que `settings.py` use `lamerced_user` y `lamerced_pass`
- Verifica que el contenedor esté completamente iniciado (espera 10 segundos)

### Reiniciar desde cero
```bash
# Detener y eliminar todo
docker-compose down -v

# Volver a iniciar
docker-compose up -d

# Re-aplicar migraciones
python manage.py migrate
```

