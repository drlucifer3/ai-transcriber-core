# AI Transcriber Core

Sistema de transcripción y análisis de video con IA.

## 🚀 Características

- ✅ Transcripción de videos MP4 a texto
- ✅ Modo local (Whisper) o cloud (OpenAI API)
- ✅ Generación de resúmenes con IA (GPT-3.5/GPT-4)
- ✅ Auto-eliminación de videos procesados
- ✅ Interfaz web moderna con barra de progreso visual
- ✅ Exportación de transcripciones y resúmenes

## 📋 Requisitos

- Python 3.8+
- FFmpeg (incluido en el proyecto)
- Clave API de OpenAI (para modo cloud y resúmenes)

## 🔧 Instalación

1. **Clonar el repositorio:**
```bash
git clone https://github.com/drlucifer3/ai-transcriber-core.git
cd ai-transcriber-core
```

2. **Descargar FFmpeg:**
   - Ve a https://github.com/BtbN/FFmpeg-Builds/releases
   - Descarga `ffmpeg-master-latest-win64-gpl.zip`
   - Extrae `ffmpeg.exe` y `ffprobe.exe` a la carpeta raíz del proyecto

3. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

4. **Configurar API Key de OpenAI:**
Edita `main.py` y reemplaza `YOUR_API_KEY_HERE` con tu clave:
```python
client = OpenAI(api_key="tu-clave-aqui")
```

## ▶️ Uso

1. **Iniciar la aplicación:**
```bash
iniciar_app.bat
```
O manualmente:
```bash
uvicorn main:app --reload --port 8002
```

2. **Abrir en el navegador:**
```
http://127.0.0.1:8002
```

3. **Transcribir un video:**
   - Arrastra un archivo MP4 a la zona de carga
   - Selecciona modo de transcripción (Local/Cloud)
   - Selecciona modelo para resumen (GPT-3.5/GPT-4)
   - Opcionalmente marca "Eliminar video original al finalizar"
   - Clic en "INICIAR PROCESAMIENTO"

4. **Generar resumen (opcional):**
   - Una vez completada la transcripción, ingresa un prompt para la IA
   - Ejemplo: "Resume en 3 puntos clave"
   - Clic en "EJECUTAR ANÁLISIS"

## 📁 Estructura del Proyecto

```
AI Transcriber Core/
├── main.py              # Backend FastAPI
├── iniciar_app.bat      # Script de inicio
├── ffmpeg.exe           # Procesador de video
├── ffprobe.exe          # Analizador de video
├── static/
│   ├── index.html       # Interfaz web
│   └── style.css        # Estilos
└── uploads/             # Videos y transcripciones
```

## 🛠️ Tecnologías

- **Backend:** FastAPI, Python
- **Transcripción:** OpenAI Whisper (local/cloud)
- **IA:** OpenAI GPT-3.5/GPT-4
- **Frontend:** HTML, CSS, JavaScript
- **Procesamiento:** FFmpeg

## 📝 Notas

- Los videos se procesan en chunks de 10 minutos
- Las transcripciones se guardan en la carpeta `uploads/`
- Los archivos temporales se limpian automáticamente
- El modo local usa el modelo Whisper "base"

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor abre un issue primero para discutir los cambios propuestos.

## 📄 Licencia

[Tu licencia aquí]
