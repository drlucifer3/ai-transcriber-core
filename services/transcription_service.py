import os
import shutil
import ffmpeg
import whisper
import time
import sys
from openai import OpenAI

class TranscriptionService:
    def __init__(self, api_key=None, ffmpeg_path=None):
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.ffmpeg_path = ffmpeg_path or self._find_ffmpeg()
        
    def _find_ffmpeg(self):
        # Look for ffmpeg.exe in current directory or script directory
        cwd_ffmpeg = os.path.join(os.getcwd(), "ffmpeg.exe")
        if os.path.exists(cwd_ffmpeg):
            return cwd_ffmpeg
        
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        script_ffmpeg = os.path.join(script_dir, "ffmpeg.exe")
        if os.path.exists(script_ffmpeg):
            return script_ffmpeg
            
        return "ffmpeg" # Fallback to system path

    def extract_audio(self, video_path, output_pattern, segment_time=600):
        """
        Extracts audio and splits into segments.
        Using segment time (default 10 mins).
        """
        try:
            stream = ffmpeg.input(video_path)
            # q:a 4 is roughly 128kbps, vn means no video
            stream = stream.output(
                output_pattern, 
                f='segment', 
                segment_time=str(segment_time), 
                acodec='libmp3lame', 
                **{'q:a': 4, 'vn': None}
            )
            stream = stream.overwrite_output()
            stream.run(cmd=self.ffmpeg_path, capture_stdout=True, capture_stderr=True)
            return True
        except ffmpeg.Error as e:
            stderr = e.stderr.decode('utf8') if e.stderr else "No stderr"
            raise Exception(f"FFmpeg error: {stderr}")

    def transcribe_local(self, audio_files, model_name="base", progress_callback=None):
        model = whisper.load_model(model_name)
        full_transcript = []
        full_segments = []
        
        total = len(audio_files)
        for i, file in enumerate(audio_files):
            if progress_callback:
                progress_callback(i + 1, total)
                
            result = model.transcribe(file)
            
            # Adjust timestamps based on segment index
            offset = i * 600 # assuming 600s segments
            for seg in result.get("segments", []):
                seg["start"] += offset
                seg["end"] += offset
                full_segments.append(seg)
                
            full_transcript.append(result["text"])
            
        return {
            "text": " ".join(full_transcript),
            "segments": full_segments
        }

    def transcribe_cloud(self, audio_files, progress_callback=None):
        if not self.client:
            raise ValueError("OpenAI client not initialized (API Key missing)")
            
        full_transcript = []
        
        total = len(audio_files)
        for i, file in enumerate(audio_files):
            if progress_callback:
                progress_callback(i + 1, total)
                
            with open(file, "rb") as f:
                # Note: Whisper API doesn't return detailed segments easily with simple .create()
                # for now we'll match original behavior but improve later if needed
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=f
                )
                full_transcript.append(transcript.text)
                
        return {
            "text": " ".join(full_transcript),
            "segments": [] # Cloud API requires more params for segments
        }
