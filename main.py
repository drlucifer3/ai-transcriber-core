import uvicorn
import webbrowser
import threading
import os
import shutil
import ffmpeg
import whisper
import uuid
import time
import sys
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from openai import OpenAI

# Configuración de OpenAI
client = OpenAI(api_key="YOUR_API_KEY_HERE")  # Reemplaza con tu API key de OpenAI

app = FastAPI()

# Helper for PyInstaller to find "static" folder
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Mount static files for the frontend
app.mount("/static", StaticFiles(directory=resource_path("static")), name="static")

# Ensure ffmpeg is found by adding the app directory to PATH
app_dir = os.path.dirname(os.path.abspath(__file__))
cwd = os.getcwd()

# Add both the script directory and current working directory to PATH
os.environ["PATH"] = cwd + os.pathsep + app_dir + os.pathsep + os.environ.get("PATH", "")

if getattr(sys, 'frozen', False):
    # If bundled, also add the _MEIPASS directory
    os.environ["PATH"] = sys._MEIPASS + os.pathsep + os.environ["PATH"]

print(f"[STARTUP] Current working directory: {cwd}")
print(f"[STARTUP] Script directory: {app_dir}")
print(f"[STARTUP] PATH: {os.environ['PATH'][:200]}...")  # Print first 200 chars


# Global in-memory storage for job status
jobs = {}

class VideoPath(BaseModel):
    path: str

class SummaryRequest(BaseModel):
    text: str
    prompt: str
    model: str = "gpt-3.5-turbo"

@app.get("/")
async def read_root():
    # Serve index.html from the correct path
    with open(resource_path("static/index.html"), "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/debug")
def list_routes():
    routes = []
    for route in app.routes:
        routes.append({
            "path": route.path,
            "name": route.name,
            "methods": list(route.methods) if hasattr(route, "methods") else None
        })
    return {"routes": routes}

def convert_and_transcribe(job_id: str, file_path: str, mode: str = "local", auto_delete: bool = False):
    try:
        jobs[job_id]['status'] = 'processing'
        jobs[job_id]['stage'] = 'preparing'
        
        base_name = os.path.splitext(file_path)[0]
        chunks_dir = os.path.join(os.path.dirname(file_path), "chunks_" + job_id)
        
        # Get video duration for estimation
        try:
            probe = ffmpeg.probe(file_path)
            duration = float(probe['format']['duration'])
            # Estimate: 20% of duration for base model (rough estimate)
            estimated_seconds = duration * 0.2
            jobs[job_id]['duration'] = duration
            jobs[job_id]['estimated_time'] = estimated_seconds
            print(f"[{job_id}] Duración: {duration}s. Estimado: {estimated_seconds}s")
        except Exception as e:
            print(f"[{job_id}] No se pudo obtener duración: {e}")
            jobs[job_id]['duration'] = 0
            jobs[job_id]['estimated_time'] = 0

        if not os.path.exists(chunks_dir):
            os.makedirs(chunks_dir)

        print(f"[{job_id}] --- Iniciando proceso ({mode}) para: {file_path} ---")
        
        # 1. Extraer y dividir audio (Chunking)
        jobs[job_id]['stage'] = 'converting_and_chunking'
        chunk_pattern = os.path.join(chunks_dir, "chunk_%03d.mp3")
        
        print(f"[{job_id}] Dividiendo audio en chunks de 10 min en {chunks_dir}...")
        print(f"[{job_id}] DEBUG: About to enter try block")
        print(f"[{job_id}] DEBUG: file_path = {file_path}")
        print(f"[{job_id}] DEBUG: chunk_pattern = {chunk_pattern}")

        try:
            print(f"[{job_id}] DEBUG: Inside try block")
            print(f"[{job_id}] Running ffmpeg command...")
            print(f"[{job_id}] Input file: {file_path}")
            print(f"[{job_id}] Output pattern: {chunk_pattern}")
            
            # Set explicit ffmpeg executable path
            ffmpeg_exe = os.path.join(os.getcwd(), "ffmpeg.exe")
            print(f"[{job_id}] Using ffmpeg at: {ffmpeg_exe}")
            print(f"[{job_id}] FFmpeg exists: {os.path.exists(ffmpeg_exe)}")
            
            print(f"[{job_id}] DEBUG: About to call ffmpeg.input()")
            stream = ffmpeg.input(file_path)
            print(f"[{job_id}] DEBUG: ffmpeg.input() successful")
            
            print(f"[{job_id}] DEBUG: About to call .output()")
            stream = stream.output(chunk_pattern, f='segment', segment_time='600', acodec='libmp3lame', **{'q:a': 4, 'vn': None})
            print(f"[{job_id}] DEBUG: .output() successful")
            
            print(f"[{job_id}] DEBUG: About to call .overwrite_output()")
            stream = stream.overwrite_output()
            print(f"[{job_id}] DEBUG: .overwrite_output() successful")
            
            print(f"[{job_id}] DEBUG: About to call .run()")
            stream.run(cmd=ffmpeg_exe, capture_stdout=True, capture_stderr=True)
            print(f"[{job_id}] FFmpeg command completed successfully")
        except ffmpeg.Error as e:
            stderr_out = e.stderr.decode('utf8') if e.stderr else "No stderr output"
            stdout_out = e.stdout.decode('utf8') if e.stdout else "No stdout output"
            error_msg = f"Error de FFmpeg: {stderr_out}"
            print(f"[{job_id}] FFmpeg Error Details:")
            print(f"[{job_id}]   STDERR: {stderr_out}")
            print(f"[{job_id}]   STDOUT: {stdout_out}")
            jobs[job_id]['status'] = 'failed'
            jobs[job_id]['error'] = error_msg
            return
        except Exception as e:
            error_msg = f"Error inesperado ejecutando FFmpeg: {str(e)}"
            print(f"[{job_id}] {error_msg}")
            import traceback
            traceback.print_exc()
            jobs[job_id]['status'] = 'failed'
            jobs[job_id]['error'] = error_msg
            return

        # Listar chunks generados
        chunk_files = sorted([os.path.join(chunks_dir, f) for f in os.listdir(chunks_dir) if f.endswith('.mp3')])
        total_chunks = len(chunk_files)
        print(f"[{job_id}] Se generaron {total_chunks} chunks.")
        
        # Update job with total chunks for progress tracking
        jobs[job_id]['total_chunks'] = total_chunks

        # 2. Transcribir
        full_transcript = []
        
        if mode == "local":
            print(f"[{job_id}] Cargando modelo Whisper LOCAL...")
            model = whisper.load_model("base") 
            
            for i, chunk_file in enumerate(chunk_files):
                current_step = i + 1
                jobs[job_id]['stage'] = f'transcribing_chunk_{current_step}_of_{total_chunks}'
                jobs[job_id]['current_chunk'] = current_step
                print(f"[{job_id}] Transcribiendo chunk {current_step}/{total_chunks} (LOCAL): {chunk_file}...")
                
                result = model.transcribe(chunk_file)
                full_transcript.append(result["text"])
        
        elif mode == "cloud":
            print(f"[{job_id}] Usando Whisper API (CLOUD)...")
            
            for i, chunk_file in enumerate(chunk_files):
                current_step = i + 1
                jobs[job_id]['stage'] = f'transcribing_chunk_{current_step}_of_{total_chunks}'
                jobs[job_id]['current_chunk'] = current_step
                print(f"[{job_id}] Transcribiendo chunk {current_step}/{total_chunks} (CLOUD): {chunk_file}...")
                
                with open(chunk_file, "rb") as audio_file:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1", 
                        file=audio_file
                    )
                    full_transcript.append(transcript.text)

        final_text = " ".join(full_transcript)
        
        # 3. Guardar resultado
        text_path = f"{base_name}.txt"
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(final_text)
            
        print(f"[{job_id}] ¡Transcripción completada! Guardada en: {text_path}")
        
        # 4. Limpieza
        try:
            # Wait a bit to ensure all file handles are released
            time.sleep(1)
            
            # Retry logic for folder deletion
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    shutil.rmtree(chunks_dir)
                    print(f"[{job_id}] Carpeta de chunks eliminada.")
                    break
                except PermissionError as e:
                    if attempt < max_retries - 1:
                        print(f"[{job_id}] Intento {attempt + 1} falló, reintentando en 2 segundos...")
                        time.sleep(2)
                    else:
                        print(f"[{job_id}] No se pudo eliminar carpeta de chunks después de {max_retries} intentos: {e}")
        except Exception as e:
            print(f"[{job_id}] Error eliminando chunks: {e}")
            
        # Auto-delete video if requested
        if auto_delete:
            try:
                os.remove(file_path)
                print(f"[{job_id}] Video original eliminado (Auto-Delete).")
            except Exception as e:
                print(f"[{job_id}] Error eliminando video original: {e}")
            
        # Update job status
        jobs[job_id]['status'] = 'completed'
        jobs[job_id]['stage'] = 'finished'
        jobs[job_id]['result'] = final_text
        jobs[job_id]['output_file'] = text_path

    except Exception as e:
        print(f"[{job_id}] Error crítico: {e}")
        jobs[job_id]['status'] = 'failed'
        jobs[job_id]['error'] = str(e)

@app.get("/status/{job_id}")
def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    elapsed = time.time() - job['start_time']
    
    return {
        "job_id": job_id,
        "status": job['status'],
        "stage": job['stage'],
        "elapsed_seconds": elapsed,
        "estimated_time": job.get('estimated_time', 0),
        "current_chunk": job.get('current_chunk', 0),
        "total_chunks": job.get('total_chunks', 0),
        "result": job['result'],
        "error": job['error']
    }

@app.post("/upload")
def upload_video(
    file: UploadFile = File(...),
    transcription_mode: str = Form("local"),
    summary_model: str = Form("gpt-3.5-turbo")
):
    # Validate extension
    if not file.filename.lower().endswith('.mp4'):
        raise HTTPException(status_code=400, detail="El archivo debe ser MP4")

    # Create uploads directory
    uploads_dir = "uploads"
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)

    # Generate Job ID
    job_id = str(uuid.uuid4())
    
    # Define file path
    file_path = os.path.join(uploads_dir, f"{job_id}_{file.filename}")
    
    # Save file (Stream)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error guardando archivo: {e}")
    finally:
        file.file.close()

    # Initialize Job Status
    jobs[job_id] = {
        'id': job_id,
        'status': 'uploaded',
        'stage': 'ready_to_process',
        'start_time': time.time(),
        'file': file_path,
        'error': None,
        'result': None,
        'mode': transcription_mode
    }
    
    return {
        "message": "Subida completada. Esperando confirmación para iniciar.", 
        "job_id": job_id
    }

@app.post("/start_process/{job_id}")
def start_process(job_id: str, background_tasks: BackgroundTasks, auto_delete: bool = Form(False)):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    # Update status
    job['status'] = 'queued'
    job['stage'] = 'starting'
    job['start_time'] = time.time() # Reset start time for accurate timing
    
    print(f"[{job_id}] START_PROCESS called")
    print(f"[{job_id}] File: {job['file']}")
    print(f"[{job_id}] Mode: {job['mode']}")
    print(f"[{job_id}] Auto-delete: {auto_delete}")
    
    # Start Processing with error wrapper
    def safe_convert_and_transcribe():
        try:
            print(f"[{job_id}] Background task starting...")
            convert_and_transcribe(job_id, job['file'], job['mode'], auto_delete)
            print(f"[{job_id}] Background task completed")
        except Exception as e:
            print(f"[{job_id}] CRITICAL ERROR in background task: {e}")
            import traceback
            traceback.print_exc()
            jobs[job_id]['status'] = 'failed'
            jobs[job_id]['error'] = f"Error crítico: {str(e)}"
    
    background_tasks.add_task(safe_convert_and_transcribe)
    
    return {"message": "Procesamiento iniciado"}

@app.post("/summary")
async def generate_summary(req: SummaryRequest):
    try:
        # Construct the prompt
        full_prompt = f"Contexto: El siguiente es un texto transcrito de un video.\n\nTexto:\n{req.text[:15000]}...\n\nInstrucción del usuario: {req.prompt}\n\nPor favor, responde a la instrucción basándote en el texto."
        
        print(f"Enviando petición a OpenAI ({req.model})...")
        response = client.chat.completions.create(
            model=req.model,
            messages=[
                {"role": "system", "content": "Eres un asistente útil que analiza transcripciones de videos."},
                {"role": "user", "content": full_prompt}
            ]
        )
        
        summary = response.choices[0].message.content
        return {"summary": summary}
        
    except Exception as e:
        print(f"Error OpenAI: {e}")
        return {"summary": f"Error generando resumen: {str(e)}"}

if __name__ == "__main__":
    def open_browser():
        time.sleep(1.5)
        webbrowser.open("http://127.0.0.1:8001")

    # Launch browser in a separate thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run the server
    # workers=1 is important for PyInstaller to avoid multiprocessing issues
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
