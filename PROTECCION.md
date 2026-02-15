# Guía de Protección - AI Transcriber Core

## ✅ Protecciones Implementadas

### 1. **Git: Ignorar cambios en `main.py`**
He configurado git para que ignore los cambios locales en `main.py`:
```bash
git update-index --assume-unchanged main.py
```

**Beneficio:** Puedes modificar tu API key localmente sin riesgo de subirla accidentalmente a GitHub.

**Para revertir (si necesitas actualizar main.py en GitHub):**
```bash
git update-index --no-assume-unchanged main.py
```

---

## 🛡️ Otras Protecciones Recomendadas

### 2. **GitHub: Proteger la rama `main`**
1. Ve a tu repositorio: https://github.com/drlucifer3/ai-transcriber-core
2. Settings → Branches → Add rule
3. Branch name pattern: `main`
4. Marca:
   - ✅ Require pull request reviews before merging
   - ✅ Require status checks to pass
   - ✅ Include administrators

**Beneficio:** Nadie (ni tú) puede hacer push directo a `main` sin revisión.

### 3. **Usar variables de entorno (Mejor práctica)**

Crea un archivo `.env` (ya está en .gitignore):
```bash
OPENAI_API_KEY=sk-proj-9BuPOJLdeEoaV...
```

Modifica `main.py` para leerlo:
```python
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
```

Agrega a `requirements.txt`:
```
python-dotenv
```

**Beneficio:** La API key nunca está en el código, solo en un archivo local.

### 4. **Pre-commit hooks**
Instala un hook que verifique que no subes API keys:
```bash
pip install pre-commit
```

Crea `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
```

**Beneficio:** Git bloqueará automáticamente commits con secretos.

---

## 📋 Resumen de Protecciones Actuales

| Protección | Estado | Descripción |
|------------|--------|-------------|
| `.gitignore` | ✅ Activo | Excluye archivos temporales y binarios |
| `main.py` ignorado | ✅ Activo | Git ignora cambios locales en main.py |
| GitHub Push Protection | ✅ Activo | GitHub detecta y bloquea API keys |
| Rama protegida | ⚠️ Opcional | Requiere configuración manual en GitHub |
| Variables de entorno | ⚠️ Recomendado | Mejor práctica para producción |

---

## 🔄 Workflow Recomendado

1. **Desarrollo local:** Modifica código libremente
2. **Antes de commit:** Verifica que no incluyes secretos
3. **Push a GitHub:** Solo código sin API keys
4. **Otros usuarios:** Configuran su propia API key localmente

¿Quieres que implemente alguna de las protecciones adicionales?
