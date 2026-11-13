import os
import subprocess
import tempfile
from app import app, init_db

init_db()
client = app.test_client()

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME_PATH):
    CHROME_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

profile_dir = tempfile.mkdtemp()
os.makedirs("docs/capturas", exist_ok=True)

pages = [
    {
        "url": "/login",
        "output": "docs/capturas/01_login.png",
        "inject": None
    },
    {
        "url": "/dashboard?demo=1",
        "output": "docs/capturas/02_dashboard.png",
        "inject": None
    },
    {
        "url": "/gastos?demo=1",
        "output": "docs/capturas/03_gastos.png",
        "inject": None
    },
    {
        "url": "/reportes?demo=1",
        "output": "docs/capturas/04_reportes.png",
        "inject": None
    }
]

for p in pages:
    print(f"Generando {p['output']}...")
    res = client.get(p["url"])
    html_content = res.data.decode("utf-8")

    # Ajustar rutas de estáticos para file:///
    html_content = html_content.replace('href="/static/', 'href="static/')
    html_content = html_content.replace('src="/static/', 'src="static/')

    temp_html = os.path.abspath(f"temp_{os.path.basename(p['output'])}.html")
    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(html_content)

    file_url = f"file:///{temp_html.replace(os.sep, '/')}"
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
    print(f"-> {p['output']} generado: {os.path.exists(out_path)} ({os.path.getsize(out_path) if os.path.exists(out_path) else 0} bytes)")

    if os.path.exists(temp_html):
        os.remove(temp_html)

print("¡Todas las capturas oficiales generadas correctamente!")
