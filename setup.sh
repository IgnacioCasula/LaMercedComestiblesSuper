#!/bin/bash

# Script de instalación para La Merced Comestibles Super
# Uso: ./setup.sh

set -e  # Salir si hay algún error

echo "🚀 Iniciando instalación de La Merced Comestibles Super..."
echo ""

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar Python
echo "📦 Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 no está instalado. Por favor instálalo primero.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✅ Python encontrado: $(python3 --version)${NC}"

# Verificar MySQL
echo ""
echo "🗄️  Verificando MySQL..."
if ! command -v mysql &> /dev/null; then
    echo -e "${YELLOW}⚠️  MySQL no encontrado en PATH. Asegúrate de tenerlo instalado.${NC}"
    echo "   macOS: brew install mysql"
    echo "   Linux: sudo apt-get install mysql-server"
else
    echo -e "${GREEN}✅ MySQL encontrado${NC}"
fi

# Crear entorno virtual si no existe
echo ""
echo "🔧 Configurando entorno virtual..."
if [ ! -d "venv" ]; then
    echo "   Creando entorno virtual..."
    python3 -m venv venv
    echo -e "${GREEN}✅ Entorno virtual creado${NC}"
else
    echo -e "${GREEN}✅ Entorno virtual ya existe${NC}"
fi

# Activar entorno virtual
echo "   Activando entorno virtual..."
source venv/bin/activate

# Actualizar pip
echo ""
echo "📥 Actualizando pip..."
pip install --upgrade pip --quiet

# Instalar dependencias
echo ""
echo "📦 Instalando dependencias..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Dependencias instaladas${NC}"
else
    echo -e "${RED}❌ No se encontró requirements.txt${NC}"
    exit 1
fi

# Verificar MySQL connection
echo ""
echo "🔌 Verificando conexión a MySQL..."
echo -e "${YELLOW}⚠️  Asegúrate de que MySQL esté corriendo y que la base de datos 'lamercedcomestibles' exista.${NC}"
echo ""
echo "   Para crear la base de datos, ejecuta:"
echo "   mysql -u root -p"
echo "   CREATE DATABASE lamercedcomestibles CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
echo ""

read -p "¿La base de datos ya está creada? (s/n): " db_exists

if [ "$db_exists" != "s" ] && [ "$db_exists" != "S" ]; then
    echo -e "${YELLOW}⚠️  Por favor crea la base de datos primero y luego ejecuta:${NC}"
    echo "   python manage.py migrate"
    exit 0
fi

# Aplicar migraciones
echo ""
echo "🗄️  Aplicando migraciones..."
python manage.py migrate

# Recolectar archivos estáticos
echo ""
echo "📁 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput || echo -e "${YELLOW}⚠️  No se pudieron recolectar archivos estáticos (puede ser normal en desarrollo)${NC}"

# Verificar configuración
echo ""
echo "🔍 Verificando configuración..."
python manage.py check

echo ""
echo -e "${GREEN}✅ Instalación completada!${NC}"
echo ""
echo "📝 Próximos pasos:"
echo "   1. Activa el entorno virtual: source venv/bin/activate"
echo "   2. Crea un superusuario: python manage.py createsuperuser"
echo "   3. Ejecuta el servidor: python manage.py runserver"
echo ""
echo "🌐 La aplicación estará disponible en: http://127.0.0.1:8000/"
echo ""

