@echo off
echo Limpiando caché de íconos de Windows...

:: Detener el explorador de Windows
taskkill /f /im explorer.exe

:: Eliminar caché de íconos
del /a /q "%localappdata%\IconCache.db"
del /a /f /q "%localappdata%\Microsoft\Windows\Explorer\iconcache*"

:: Esperar un momento
timeout /t 2 /nobreak >nul

:: Reiniciar el explorador
start explorer.exe

echo.
echo Caché de íconos limpiado. El ícono debería actualizarse ahora.
echo Presiona cualquier tecla para cerrar...
pause >nul
