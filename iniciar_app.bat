@echo off
echo INICIANDO AI TRANSCRIBER CORE...
echo Por favor espere mientras se carga el servidor...

:: Agregar directorio actual al PATH para encontrar ffmpeg.exe
set PATH=%PATH%;%~dp0

:: Iniciar el servidor en segundo plano
start /B uvicorn main:app --reload --port 8002

:: Esperar 3 segundos para asegurar que el servidor arranque
timeout /t 3 /nobreak >nul

:: Abrir el navegador
start http://127.0.0.1:8002

echo.
echo APLICACION CORRIENDO.
echo NO CIERRES ESTA VENTANA mientras uses la app.
echo Para cerrar, simplemente cierra esta ventana.
