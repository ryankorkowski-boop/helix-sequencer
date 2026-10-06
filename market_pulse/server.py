import asyncio, json, time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

HTML = """<!doctype html><html><head><meta charset=utf-8><title>Market Pulse</title>
<style>body{font-family:system-ui;background:#101216;color:#eee;margin:30px}table{width:100%;border-collapse:collapse}td,th{padding:8px;border-bottom:1px solid #333;text-align:left}.signal{color:#ffd166}.muted{color:#999}</style>
</head><body><h1>MARKET PULSE</h1><p class=muted>Live intelligence prototype — observe/paper mode only.</p><div id=a>Loading…</div>
<script>
async function tick(){const r=await fetch('/api/state');const d=await r.json();
document.getElementById('a').innerHTML='<p>Events: '+d.events+' | Signals: '+d.signals+'</p><table><tr><th>Time</th><th>Symbol</th><th>Type</th><th>Score</th><th>Price</th><th>Evidence</th></tr>'+
d.recent.map(x=>'<tr><td>'+new Date(x.ts*1000).toLocaleTimeString()+'</td><td>'+x.symbol+'</td><td class=signal>'+x.kind+'</td><td>'+x.score+'</td><td>'+x.price.toFixed(2)+'</td><td>'+x.message+'</td></tr>').join('')+'</table>'}
setInterval(tick,1000);tick();
</script></body></html>"""

class State:
    def __init__(self):
        self.events = 0
        self.signals = deque(maxlen=100)

class Handler(BaseHTTPRequestHandler):
    state = None
    def do_GET(self):
        if self.path == "/api/state":
            body = json.dumps({"events": self.state.events, "signals": len(self.state.signals), "recent": list(self.state.signals)[-30:]}).encode()
            self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers(); self.wfile.write(body); return
        body = HTML.encode(); self.send_response(200); self.send_header("Content-Type","text/html"); self.end_headers(); self.wfile.write(body)
    def log_message(self, *_): pass

def start_server(host, port, state):
    Handler.state = state
    ThreadingHTTPServer((host, port), Handler).serve_forever()

async def run(feed, engine, state):
    async for event in feed:
        state.events += 1
        for sig in engine.update(event["S"], event["p"], event["v"]):
            item = {"ts": time.time(), **sig.__dict__}
            state.signals.append(item)

def serve(host, port, feed, engine, state):
    Thread(target=start_server, args=(host, port, state), daemon=True).start()
    asyncio.run(run(feed, engine, state))
