# Guía de Instalación Local - La Merced Comestibles Super

## 📋 Prerequisitos

### 1. Python 3.8 o superior
```bash
# Verificar versión de Python
python3 --version
# o
python --version
```

### 2. MySQL Server (Opciones)

#### Opción A: Docker (Recomendado) 🐳
```bash
# Verificar Docker
docker --version
docker-compose --version
```

#### Opción B: MySQL Local
```bash
# macOS (con Homebrew)
brew install mysql
brew services start mysql

# Linux (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install mysql-server
sudo systemctl start mysql

# Windows
# Descargar desde: https://dev.mysql.com/downloads/mysql/
```

### 3. Git (opcional, si clonas el repo)
```bash
git --version
```

## 🚀 Pasos de Instalación

### Paso 1: Clonar/Navegar al proyecto
```bash
cd /Users/guilletala/repos/guille/LaMercedComestiblesSuper
```

### Paso 2: Configurar MySQL con Docker 🐳

Si usas Docker (recomendado):

```bash
# Iniciar MySQL en Docker
docker-compose up -d

# Verificar que está corriendo
docker-compose ps

# Ver logs (opcional)
docker-compose logs -f mysql
```

**Credenciales de MySQL en Docker:**
- Host: `localhost`
- Puerto: `3306`
- Base de datos: `lamercedcomestibles`
- Usuario: `lamerced_user`
- Contraseña: `lamerced_pass`
- Root password: `rootpassword`

**Actualizar settings.py para Docker:**
Edita `ProyectoSuper/settings.py` líneas 59-70:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'lamercedcomestibles',
        'USER': 'lamerced_user',  # Cambiar de 'root'
        'PASSWORD': 'lamerced_pass',  # Cambiar de ''
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'sql_mode': 'STRICT_TRANS_TABLES',
        },
    }
}
```

**Para detener MySQL:**
```bash
docker-compose down
# O para eliminar también los datos:
docker-compose down -v
```

### Paso 3: Crear entorno virtual (recomendado)
```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
# macOS/Linux:
source venv/bin/activate

# Windows:
# venv\Scripts\activate
```

### Paso 3: Instalar dependencias
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Nota:** Si tienes problemas con `mysqlclient`, prueba:
```bash
# macOS
brew install mysql-client
export PATH="/usr/local/opt/mysql-client/bin:$PATH"
pip install mysqlclient

# Linux
sudo apt-get install python3-dev default-libmysqlclient-dev build-essential
pip install mysqlclient

# Windows
# Descargar wheel desde: https://www.lfd.uci.edu/~gohlke/pythonlibs/#mysqlclient
# pip install mysqlclient‑2.2.0‑cp39‑cp39‑win_amd64.whl
```

### Paso 4: Aplicar migraciones
```bash
# Crear las tablas en la base de datos
python manage.py migrate
```

### Paso 5: Crear usuario administrador
```bash
# Crear usuario admin con el comando personalizado
python manage.py crear_usuarios

# O crear superusuario de Django (opcional)
python manage.py createsuperuser
```

### Paso 6: Recolectar archivos estáticos
```bash
python manage.py collectstatic --noinput
```

### Paso 7: Ejecutar el servidor de desarrollo
```bash
python manage.py runserver
```

La aplicación estará disponible en: **http://127.0.0.1:8000/**

## 🔧 Solución de Problemas Comunes

### Error: "No module named 'mysqlclient'"
```bash
# Instalar dependencias del sistema primero
# macOS:
brew install mysql-client pkg-config

# Luego instalar mysqlclient
pip install mysqlclient
```

### Error: "Can't connect to MySQL server"
1. Verificar que MySQL esté corriendo:
   ```bash
   # macOS/Linux
   brew services list  # o systemctl status mysql
   ```

2. Verificar credenciales en `settings.py`

3. Probar conexión:
   ```bash
   mysql -u root -p
   ```

### Error: "Table doesn't exist"
```bash
# Aplicar migraciones nuevamente
python manage.py migrate
```

### Error: "ModuleNotFoundError"
```bash
# Asegúrate de estar en el entorno virtual
which python  # Debe mostrar la ruta del venv

# Reinstalar dependencias
pip install -r requirements.txt
```

## 📝 Comandos Útiles

### Verificar configuración
```bash
python manage.py check
```

### Ver las migraciones pendientes
```bash
python manage.py showmigrations
```

### Crear nuevas migraciones (si modificas modelos)
```bash
python manage.py makemigrations
python manage.py migrate
```

### Acceder al shell de Django
```bash
python manage.py shell
```

### Ver las URLs disponibles
```bash
python manage.py show_urls  # Si tienes django-extensions instalado
```

## 🌐 Acceso a la Aplicación

- **URL Principal:** http://127.0.0.1:8000/
- **Admin Panel:** http://127.0.0.1:8000/admin/
- **Login:** http://127.0.0.1:8000/login/

## 📦 Estructura de URLs

- `/` - Inicio (requiere login)
- `/login` - Login
- `/caja/` - Gestión de caja
- `/asistencias/` - Control de asistencias
- `/ventas/` - Registro de ventas
- `/GestionDeStock/` - Gestión de inventario

## ⚠️ Notas Importantes

1. **Base de datos vacía**: La primera vez que ejecutes, la base de datos estará vacía. Necesitarás crear usuarios/empleados desde el admin o usando los comandos de management.

2. **Archivos estáticos**: En desarrollo, Django sirve los archivos estáticos automáticamente. En producción necesitarías configurar un servidor web.

3. **SECRET_KEY**: El `SECRET_KEY` en `settings.py` está expuesto. Para producción, usa variables de entorno.

4. **DEBUG**: Está en `True` para desarrollo. Cambiar a `False` en producción.

## 🎯 Próximos Pasos

1. Crear un usuario administrador
2. Configurar áreas y puestos
3. Crear empleados de prueba
4. Cargar productos y categorías
5. Configurar sucursales

## 📞 Soporte

Si encuentras problemas, verifica:
- Versión de Python (3.8+)
- MySQL corriendo y accesible
- Todas las dependencias instaladas
- Migraciones aplicadas

