#!/bin/bash
# Script para limpiar cache de Django (Linux/Mac)

echo "========================================"
echo "Limpiando cache de Django y archivos estaticos"
echo "========================================"
echo ""

echo "[1/3] Limpiando archivos __pycache__..."
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
echo "✓ Archivos __pycache__ eliminados"
echo ""

echo "[2/3] Limpiando archivos .pyc..."
find . -type f -name "*.pyc" -delete 2>/dev/null || true
echo "✓ Archivos .pyc eliminados"
echo ""

echo "[3/3] Limpiando cache de archivos estaticos de Django..."
if [ -d "staticfiles" ]; then
    rm -rf staticfiles
    echo "✓ Carpeta staticfiles eliminada"
fi

if [ -d "static_root" ]; then
    rm -rf static_root
    echo "✓ Carpeta static_root eliminada"
fi

if [ -d "collectstatic" ]; then
    rm -rf collectstatic
    echo "✓ Carpeta collectstatic eliminada"
fi

echo ""
echo "========================================"
echo "✓ Limpieza completada!"
echo "========================================"
echo ""
echo "Ahora recarga la pagina en el navegador con:"
echo "  - Ctrl + Shift + R (recarga forzada)"
echo "  - O Cmd + Shift + R (en Mac)"
echo ""


