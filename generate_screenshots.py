import os
import subprocess
import time
from app import app, init_db

init_db()
client = app.test_client()

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME_PATH):
    CHROME_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

profile_dir = os.path.abspath("screenshots/chrome_profile")
os.makedirs("screenshots", exist_ok=True)

# 1. Obtener HTMLs a través del test_client de Flask
pages = [
    {
        "url": "/login",
        "temp": "temp_login.html",
        "output": "screenshots/01_login.png",
        "modal_inject": None
    },
    {
        "url": "/dashboard?demo=1",
        "temp": "temp_dashboard.html",
        "output": "screenshots/02_dashboard.png",
        "modal_inject": None
    },
    {
        "url": "/dashboard?demo=1",
        "temp": "temp_modal.html",
        "output": "screenshots/03_registro_gasto.png",
        "modal_inject": "<script>document.addEventListener('DOMContentLoaded', () => openModal('modalNuevoGasto'));</script>"
    },
    {
        "url": "/reportes?demo=1",
        "temp": "temp_reportes.html",
        "output": "screenshots/04_reportes.png",
        "modal_inject": None
    }
]

for p in pages:
    print(f"Generando {p['output']}...")
    res = client.get(p["url"])
    html_content = res.data.decode("utf-8")

    # Ajustar rutas de estáticos para file:///
    html_content = html_content.replace('href="/static/', 'href="static/')
    html_content = html_content.replace('src="/static/', 'src="static/')

    if p["modal_inject"]:
        html_content = html_content.replace('</body>', f'{p["modal_inject"]}</body>')

    temp_path = os.path.abspath(p["temp"])
    with open(temp_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    file_url = f"file:///{temp_path.replace(os.sep, '/')}"
    out_path = os.path.abspath(p["output"])

    cmd = [
        CHROME_PATH,
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--hide-scrollbars",
        f"--user-data-dir={profile_dir}",
        "--window-size=1920,1080",
        f"--screenshot={out_path}",
        file_url
    ]
    subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    print(f"Resultado {p['output']}: Existe = {os.path.exists(out_path)}, Tam = {os.path.getsize(out_path) if os.path.exists(out_path) else 0} bytes")

    # Limpiar archivo temporal
    if os.path.exists(temp_path):
        os.remove(temp_path)

print("¡Todas las capturas se generaron con éxito!")
