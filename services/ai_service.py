import os
from openai import OpenAI

class AIService:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("OPENAI_API_KEY no encontrada.")
        self.client = OpenAI(api_key=api_key)

    def generate_response(self, text, prompt, model="gpt-4o"):
        """
        Generic GPT response generator.
        """
        try:
            full_prompt = f"Contexto: El siguiente es un texto transcrito de un contenido educativo.\n\nTexto:\n{text[:15000]}\n\nInstrucción: {prompt}"
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Eres un tutor experto que ayuda a estudiantes a aprender de sus clases transcritas."},
                    {"role": "user", "content": full_prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error en AI Service: {str(e)}"

    def generate_student_guide(self, text, model="gpt-4o"):
        """
        Generates a structured study guide.
        """
        prompt = (
            "Analiza la siguiente transcripción y genera una guía de estudio estructurada en Markdown que incluya:\n"
            "1. **Conceptos Clave**: Las 5-7 ideas más importantes.\n"
            "2. **Glosario**: Definiciones de términos técnicos o difíciles mencionados.\n"
            "3. **Resumen Ejecutivo**: Un resumen de 3 párrafos del contenido.\n"
            "4. **Preguntas de Autoevaluación**: 5 preguntas para que el estudiante pruebe su conocimiento."
        )
        return self.generate_response(text, prompt, model)
