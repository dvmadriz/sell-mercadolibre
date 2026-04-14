"""
Servidor API para n8n — Repuestos Madriz C.A.
Ejecuta: python3 run_api.py
"""
import sys
import os
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

env_path = ROOT / ".env"
if not env_path.exists():
    print("\n  ERROR: no existe el archivo .env")
    print("  Copia .env.example como .env y agrega tu ANTHROPIC_API_KEY.\n")
    sys.exit(1)

from dotenv import load_dotenv
load_dotenv(env_path)

if not os.environ.get("ANTHROPIC_API_KEY", "").startswith("sk-"):
    print("\n  ERROR: ANTHROPIC_API_KEY inválida en .env\n")
    sys.exit(1)

import uvicorn
print("\n  RepuestoBot API iniciando en http://localhost:8000")
print("  Documentación: http://localhost:8000/docs\n")
uvicorn.run("api.app:app", host="0.0.0.0", port=8000, reload=False)
