import os

class ExportService:
    def __init__(self, output_dir="uploads"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def to_markdown(self, filename, transcript, analysis=None, metadata=None):
        """
        Generates a Markdown file optimized for NotebookLM.
        """
        if not filename.endswith(".md"):
            filename += ".md"
            
        path = os.path.join(self.output_dir, filename)
        
        content = []
        if metadata:
            content.append(f"# {metadata.get('title', 'Transcripción de Clase')}")
            content.append(f"**Fecha**: {metadata.get('date', 'N/A')}")
            content.append("\n---")
            
        if analysis:
            content.append("\n## 🧠 Análisis e Inteligencia")
            content.append(analysis)
            content.append("\n---")
            
        content.append("\n## 📝 Transcripción Completa")
        content.append(transcript)
        
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(content))
            
        return path
