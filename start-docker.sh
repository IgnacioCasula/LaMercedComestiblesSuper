#!/bin/bash

# Script para iniciar MySQL con Docker y configurar la aplicación

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "🐳 Iniciando MySQL con Docker..."
echo ""

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker no está instalado. Por favor instálalo primero.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ docker-compose no está instalado. Por favor instálalo primero.${NC}"
    exit 1
fi

# Iniciar MySQL
echo "📦 Iniciando contenedor MySQL..."
docker-compose up -d

# Esperar a que MySQL esté listo
echo ""
echo "⏳ Esperando a que MySQL esté listo..."
sleep 5

# Verificar que está corriendo
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✅ MySQL está corriendo${NC}"
else
    echo -e "${RED}❌ Error al iniciar MySQL${NC}"
    docker-compose logs mysql
    exit 1
fi

# Verificar configuración de settings.py
echo ""
echo "🔍 Verificando configuración de base de datos..."

# Leer settings.py y verificar si usa las credenciales de Docker
if grep -q "lamerced_user" ProyectoSuper/settings.py 2>/dev/null; then
    echo -e "${GREEN}✅ Configuración de Docker detectada en settings.py${NC}"
else
    echo -e "${YELLOW}⚠️  Necesitas actualizar ProyectoSuper/settings.py para usar Docker${NC}"
    echo ""
    echo "Cambia estas líneas en ProyectoSuper/settings.py:"
    echo "  'USER': 'root',     →  'USER': 'lamerced_user',"
    echo "  'PASSWORD': '',      →  'PASSWORD': 'lamerced_pass',"
    echo ""
    read -p "¿Quieres que actualice settings.py automáticamente? (s/n): " update_settings
    
    if [ "$update_settings" = "s" ] || [ "$update_settings" = "S" ]; then
        # Backup del archivo original
        cp ProyectoSuper/settings.py ProyectoSuper/settings.py.backup
        
        # Actualizar settings.py (macOS/Linux)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/'USER': 'root'/'USER': 'lamerced_user'/" ProyectoSuper/settings.py
            sed -i '' "s/'PASSWORD': ''/'PASSWORD': 'lamerced_pass'/" ProyectoSuper/settings.py
        else
            sed -i "s/'USER': 'root'/'USER': 'lamerced_user'/" ProyectoSuper/settings.py
            sed -i "s/'PASSWORD': ''/'PASSWORD': 'lamerced_pass'/" ProyectoSuper/settings.py
        fi
        
        echo -e "${GREEN}✅ settings.py actualizado${NC}"
        echo -e "${YELLOW}📝 Backup guardado en: ProyectoSuper/settings.py.backup${NC}"
    fi
fi

echo ""
echo -e "${GREEN}✅ MySQL está listo!${NC}"
echo ""
echo "📝 Próximos pasos:"
echo "   1. Activa el entorno virtual: source venv/bin/activate"
echo "   2. Aplica migraciones: python manage.py migrate"
echo "   3. Crea usuario admin: python manage.py crear_usuarios"
echo "   4. Ejecuta el servidor: python manage.py runserver"
echo ""
echo "🔧 Comandos útiles:"
echo "   Ver logs de MySQL: docker-compose logs -f mysql"
echo "   Detener MySQL: docker-compose down"
echo "   Reiniciar MySQL: docker-compose restart"
echo ""

