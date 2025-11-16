# Limpiar Cache de Django

## Para Windows (Terminal de Visual Studio Code)

Copia y pega este comando completo en la terminal:

```cmd
for /d /r . %d in (__pycache__) do @if exist "%d" rd /s /q "%d" 2>nul & for /r . %f in (*.pyc) do @if exist "%f" del /q "%f" 2>nul & if exist "staticfiles" rd /s /q "staticfiles" 2>nul & if exist "static_root" rd /s /q "static_root" 2>nul & if exist "collectstatic" rd /s /q "collectstatic" 2>nul & echo Cache limpiado exitosamente!
```

## O ejecuta paso a paso:

```cmd
REM Limpiar __pycache__
for /d /r . %d in (__pycache__) do @if exist "%d" rd /s /q "%d"

REM Limpiar .pyc
for /r . %f in (*.pyc) do @if exist "%f" del /q "%f"

REM Limpiar carpetas de static
if exist "staticfiles" rd /s /q "staticfiles"
if exist "static_root" rd /s /q "static_root"
if exist "collectstatic" rd /s /q "collectstatic"

echo ✓ Cache limpiado!
```

## Después de limpiar:

1. Recarga la página en el navegador con `Ctrl + Shift + R` (recarga forzada)
2. O limpia la caché del navegador manualmente


