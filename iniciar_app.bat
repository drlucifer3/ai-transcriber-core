@echo off
setlocal
cd /d "%~dp0"
echo INICIANDO AI TRANSCRIBER CORE...
echo Por favor espere mientras se carga el servidor...

:: Borrar log anterior si existe
if exist "server_log.txt" del "server_log.txt"

:: Agregar directorio actual al PATH para encontrar ffmpeg.exe y ffprobe.exe
set PATH=%PATH%;%~dp0

:: Definir ruta al ejecutable de python del entorno virtual
set PYTHON_EXE="%~dp0.venv\Scripts\python.exe"

:: Verificar si el entorno virtual existe
if not exist %PYTHON_EXE% (
    echo [ERROR] No se encuentra el entorno virtual en .venv
    echo Por favor asegurese de que la carpeta .venv existe.
    pause
    exit /b
)

:: Iniciar el servidor en segundo plano y redirigir salida a un log
:: Se usa "python -m uvicorn" para asegurar que use el uvicorn del entorno
echo Iniciando Uvicorn en puerto 8002...
start /B "" %PYTHON_EXE% -m uvicorn main:app --reload --port 8002 > server_log.txt 2>&1

:: Esperar 5 segundos para asegurar que el servidor arranque
timeout /t 5 /nobreak >nul

:: Verificar si el log contiene errores inmediatamente
echo Verificando estado...

:: Abrir el navegador
start http://127.0.0.1:8002

echo.
echo APLICACION CORRIENDO.
echo Si el navegador muestra un error, revisa el archivo "server_log.txt" para ver que paso.
echo.
echo NO CIERRES ESTA VENTANA mientras uses la app.
echo Para cerrar, simplemente cierra esta ventana o presiona Ctrl+C.
