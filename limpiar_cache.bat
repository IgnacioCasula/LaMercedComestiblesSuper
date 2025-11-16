@echo off
echo ========================================
echo Limpiando cache de Django y archivos estaticos
echo ========================================
echo.

echo [1/3] Limpiando archivos __pycache__...
for /d /r . %%d in (__pycache__) do @if exist "%%d" (
    echo Eliminando: %%d
    rd /s /q "%%d" 2>nul
)
echo ✓ Archivos __pycache__ eliminados
echo.

echo [2/3] Limpiando archivos .pyc...
for /r . %%f in (*.pyc) do @if exist "%%f" (
    echo Eliminando: %%f
    del /q "%%f" 2>nul
)
echo ✓ Archivos .pyc eliminados
echo.

echo [3/3] Limpiando cache de archivos estaticos de Django...
if exist "staticfiles" (
    echo Eliminando carpeta staticfiles...
    rd /s /q "staticfiles" 2>nul
    echo ✓ Carpeta staticfiles eliminada
)

if exist "static_root" (
    echo Eliminando carpeta static_root...
    rd /s /q "static_root" 2>nul
    echo ✓ Carpeta static_root eliminada
)

if exist "collectstatic" (
    echo Eliminando carpeta collectstatic...
    rd /s /q "collectstatic" 2>nul
    echo ✓ Carpeta collectstatic eliminada
)
echo.

echo ========================================
echo ✓ Limpieza completada!
echo ========================================
echo.
echo Ahora recarga la pagina en el navegador con:
echo   - Ctrl + Shift + R (recarga forzada)
echo   - O Ctrl + F5
echo.
pause


