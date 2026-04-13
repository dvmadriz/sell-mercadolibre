"""
Punto de entrada — Repuestos Madriz C.A.
Ejecuta: python3 run.py
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
    print("\n  ERROR: ANTHROPIC_API_KEY inválida o no configurada en .env\n")
    sys.exit(1)

from central_madre.main import main
main()
