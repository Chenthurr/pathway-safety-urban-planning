"""Small standard-library dashboard server for the Render deployment.

The public Render port serves the dashboard and proxies API requests to the
Pathway REST server running on a private localhost port. This keeps the
existing Pathway REST API available at the same public URLs without adding a
second web framework or dependency.
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


DASHBOARD_HTML = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Urban Safety & Planning</title>
<style>
:root{--bg:#07111f;--panel:#0d1b2d;--panel2:#10233a;--text:#eaf2ff;--muted:#8fa4bd;--line:#20344c;--ok:#39d98a;--warn:#ffcc66;--danger:#ff6b6b;--accent:#61a8ff}
*{box-sizing:border-box} body{margin:0;font-family:Inter,Segoe UI,Arial,sans-serif;background:linear-gradient(135deg,#06101d,#0b1728 55%,#07111f);color:var(--text);min-height:100vh}
.wrap{max-width:1200px;margin:auto;padding:28px 22px 44px}.top{display:flex;justify-content:space-between;align-items:flex-start;gap:18px;margin-bottom:24px}.brand h1{margin:0;font-size:30px;letter-spacing:-.6px}.brand p{margin:7px 0 0;color:var(--muted)}
.badge{display:flex;align-items:center;gap:9px;background:#0c241c;border:1px solid #1e6648;color:#8ff0bd;padding:9px 13px;border-radius:999px;font-weight:700;font-size:13px}.dot{width:9px;height:9px;border-radius:50%;background:var(--ok);box-shadow:0 0 12px var(--ok)}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.card{background:rgba(13,27,45,.88);border:1px solid var(--line);border-radius:16px;padding:18px;box-shadow:0 12px 30px rgba(0,0,0,.16)}.label{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.8px}.value{font-size:24px;font-weight:800;margin-top:8px}.sub{font-size:12px;color:var(--muted);margin-top:5px}
.two{display:grid;grid-template-columns:1.3fr .7fr;gap:14px;margin-top:14px}.section h2{font-size:16px;margin:0 0 14px}.list{display:grid;gap:9px;max-height:300px;overflow:auto}.item{background:var(--panel2);border:1px solid #1b324c;border-radius:11px;padding:11px 12px}.item strong{display:block;font-size:13px}.item span{display:block;color:var(--muted);font-size:12px;margin-top:4px;line-height:1.45}.empty{color:var(--muted);font-size:13px;padding:16px 0}
.chat{margin-top:14px}.chatbox{display:flex;gap:9px}.chatbox input{flex:1;background:#081625;color:var(--text);border:1px solid var(--line);border-radius:10px;padding:13px;font-size:14px;outline:none}.chatbox button{border:0;border-radius:10px;padding:0 18px;background:var(--accent);color:#06101d;font-weight:800;cursor:pointer}.answer{margin-top:12px;background:#081625;border:1px solid var(--line);border-radius:11px;padding:14px;min-height:52px;white-space:pre-wrap;line-height:1.55;font-size:13px}.footer{margin-top:18px;color:var(--muted);font-size:11px;text-align:center}.refresh{background:transparent;border:1px solid var(--line);color:var(--muted);border-radius:9px;padding:7px 10px;cursor:pointer}
@media(max-width:850px){.grid{grid-template-columns:repeat(2,1fr)}.two{grid-template-columns:1fr}.top{flex-direction:column}}@media(max-width:520px){.grid{grid-template-columns:1fr}.wrap{padding:20px 14px}}
</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <div class="brand"><h1>Urban Safety & Planning</h1><p>Real-time Pathway pipeline with Gemini-powered intelligence</p></div>
    <div style="display:flex;gap:8px;align-items:center"><button class="refresh" onclick="loadAll()">Refresh</button><div class="badge"><span class="dot"></span> SYSTEM ONLINE</div></div>
  </div>
  <div class="grid">
    <div class="card"><div class="label">Safety detection</div><div class="value" id="safety">Enabled</div><div class="sub">Anomaly rules active</div></div>
    <div class="card"><div class="label">Planning engine</div><div class="value" id="planning">Running</div><div class="sub">Traffic · transit · environment</div></div>
    <div class="card"><div class="label">Gemini RAG</div><div class="value" id="rag">Ready</div><div class="sub" id="ragSub">Live knowledge index</div></div>
    <div class="card"><div class="label">Indexed files</div><div class="value" id="files">—</div><div class="sub" id="indexed">Checking vector store…</div></div>
  </div>
  <div class="two">
    <div class="card section"><h2>Safety anomalies</h2><div id="anomalies" class="list"><div class="empty">Loading live anomaly stream…</div></div></div>
    <div class="card section"><h2>Planning status</h2><div id="status" class="list"><div class="empty">Checking pipeline…</div></div></div>
  </div>
  <div class="card section chat"><h2>Ask the Gemini RAG assistant</h2><div class="chatbox"><input id="question" placeholder="Ask about safety, traffic, transit, or environment…" onkeydown="if(event.key==='Enter')ask()"><button onclick="ask()">Ask</button></div><div id="answer" class="answer">Ask a question to search the live city knowledge index.</div></div>
  <div class="footer">Pathway real-time processing · Gemini 2.5 Flash · <a href="/healthz" style="color:#61a8ff">health check</a> · <a href="/v1/statistics" style="color:#61a8ff">RAG statistics</a></div>
</div>
<script>
const $=id=>document.getElementById(id);
async function api(path, options={}){const r=await fetch(path,options); if(!r.ok) throw new Error(r.status+' '+r.statusText); return r.json();}
function rows(data){if(Array.isArray(data))return data; if(data&&Array.isArray(data.result))return data.result; if(data&&typeof data==='object')return [data]; return []}
function text(v){return v===null||v===undefined?'':String(v)}
async function loadAll(){
  try{await api('/healthz'); $('safety').textContent='Enabled'; $('planning').textContent='Running'; $('rag').textContent='Ready';}catch(e){$('safety').textContent='Offline';$('planning').textContent='Offline';$('rag').textContent='Unavailable'}
  try{const s=await api('/v1/statistics'); const o=rows(s)[0]||s; $('files').textContent=text(o.file_count||o.files||'—'); $('indexed').textContent=o.last_indexed?'Last indexed: '+new Date(Number(o.last_indexed)).toLocaleString():'Vector store connected';}catch(e){$('files').textContent='—';$('indexed').textContent='Statistics unavailable'}
  try{const p=await fetch('/planning/status'); const j=await p.json(); $('status').innerHTML='<div class="item"><strong>Pipeline running</strong><span>'+escapeHtml(JSON.stringify(j).replace(/[{}\"]/g,''))+'</span></div>';}catch(e){$('status').innerHTML='<div class="empty">Planning status unavailable</div>'}
  try{const r=await fetch('/safety/anomalies',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({severity:'all'})}); const j=await r.json(); const a=rows(j); $('anomalies').innerHTML=a.length?a.slice(0,12).map(x=>'<div class="item"><strong>'+escapeHtml(text(x.anomaly_type||x.severity||'Safety event'))+'</strong><span>'+escapeHtml(text(x.description||x.result||JSON.stringify(x)))+'</span></div>').join(''):'<div class="empty">No anomaly records returned.</div>';}catch(e){$('anomalies').innerHTML='<div class="empty">Anomaly feed unavailable</div>'}
}
function escapeHtml(s){return text(s).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]))}
async function ask(){const q=$('question').value.trim();if(!q)return;$('answer').textContent='Thinking…';try{const r=await api('/v2/answer',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt:q,return_context_docs:false})});const a=r.answer||r.result||r; $('answer').textContent=typeof a==='string'?a:JSON.stringify(a,null,2);}catch(e){$('answer').textContent='Unable to query Gemini RAG: '+e.message}}
loadAll();setInterval(loadAll,30000);
</script>
</body>
</html>'''


class DashboardHandler(BaseHTTPRequestHandler):
    pathway_port = 10001

    def _send(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept")
        self.end_headers()

    def do_GET(self) -> None:
        if urlsplit(self.path).path == "/":
            self._send(200, "text/html; charset=utf-8", DASHBOARD_HTML.encode("utf-8"))
            return
        self._proxy("GET")

    def do_POST(self) -> None:
        self._proxy("POST")

    def _proxy(self, method: str) -> None:
        target = f"http://127.0.0.1:{self.pathway_port}{self.path}"
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else None
        headers = {"Accept": self.headers.get("Accept", "*/*")}
        if body is not None:
            headers["Content-Type"] = self.headers.get("Content-Type", "application/json")
        try:
            req = Request(target, data=body, headers=headers, method=method)
            with urlopen(req, timeout=90) as response:
                payload = response.read()
                self._send(response.status, response.headers.get_content_type() or "application/json", payload)
        except HTTPError as exc:
            payload = exc.read()
            self._send(exc.code, "application/json", payload)
        except URLError as exc:
            payload = json.dumps({"error": "Pathway API unavailable", "detail": str(exc.reason)}).encode()
            self._send(502, "application/json", payload)
        except Exception as exc:
            payload = json.dumps({"error": "Dashboard proxy error", "detail": str(exc)}).encode()
            self._send(500, "application/json", payload)

    def log_message(self, fmt: str, *args: object) -> None:
        print("Dashboard: " + (fmt % args), flush=True)


def start_dashboard(public_port: int, pathway_port: int) -> ThreadingHTTPServer:
    DashboardHandler.pathway_port = pathway_port
    server = ThreadingHTTPServer(("0.0.0.0", public_port), DashboardHandler)
    server.daemon_threads = True
    server.timeout = 1
    server_thread = __import__("threading").Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    print(f"Visual dashboard configured on 0.0.0.0:{public_port}; Pathway API on 127.0.0.1:{pathway_port}", flush=True)
    return server
