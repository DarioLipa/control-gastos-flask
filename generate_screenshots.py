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
        "size": "1920,1080"
    },
    {
        "url": "/dashboard?demo=1",
        "output": "docs/capturas/02_dashboard.png",
        "size": "1920,1080"
    },
    {
        "url": "/gastos?demo=1",
        "output": "docs/capturas/03_gastos.png",
        "size": "1920,1080"
    },
    {
        "url": "/reportes?demo=1",
        "output": "docs/capturas/04_reportes.png",
        "size": "1920,1080"
    },
    {
        "url": "/dashboard?demo=1",
        "output": "docs/capturas/dashboard_1366x768.png",
        "size": "1366,768"
    },
    {
        "url": "/dashboard?demo=1",
        "output": "docs/capturas/dashboard_768x1024.png",
        "size": "768,1024"
    },
    {
        "url": "/dashboard?demo=1",
        "output": "docs/capturas/dashboard_390x844.png",
        "size": "390,844"
    }
]

for p in pages:
    print(f"Generando {p['output']} en {p['size']}...")
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
        f"--window-size={p['size']}",
        f"--screenshot={out_path}",
        file_url
    ]
    subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    print(f"-> {p['output']} generado: {os.path.exists(out_path)} ({os.path.getsize(out_path) if os.path.exists(out_path) else 0} bytes)")

    if os.path.exists(temp_html):
        os.remove(temp_html)

print("¡Todas las capturas oficiales generadas correctamente!")
