from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.api import chat, health

app = FastAPI(title="ThreadBot", version="2.0")
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def serve_frontend():
    return FileResponse("frontend/index.html")

@app.get("/admin")
def admin_panel():
    html = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ThreadBot Admin</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: #0f0f0f; color: #ffffff; font-family: 'Helvetica Neue', Arial, sans-serif; }
  header { background: #1a1a1a; border-bottom: 3px solid #c9a84c; padding: 20px 40px; display: flex; align-items: center; gap: 16px; }
  header h1 { font-size: 22px; color: #c9a84c; letter-spacing: 3px; }
  header span { font-size: 12px; color: #888; letter-spacing: 1px; }
  .container { padding: 32px 40px; max-width: 1200px; margin: 0 auto; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; margin-bottom: 40px; }
  .card { background: #1a1a1a; border: 1px solid #2a2a2a; border-top: 3px solid #c9a84c; padding: 20px; border-radius: 4px; }
  .card .num { font-size: 36px; font-weight: bold; color: #c9a84c; }
  .card .label { font-size: 12px; color: #888; letter-spacing: 1px; margin-top: 4px; }
  h2 { font-size: 14px; color: #c9a84c; letter-spacing: 2px; margin-bottom: 16px; border-bottom: 1px solid #2a2a2a; padding-bottom: 8px; }
  table { width: 100%; border-collapse: collapse; margin-bottom: 40px; }
  th { background: #252525; padding: 12px 16px; text-align: left; font-size: 11px; color: #c9a84c; letter-spacing: 1px; border-bottom: 1px solid #333; }
  td { padding: 12px 16px; font-size: 13px; color: #cccccc; border-bottom: 1px solid #222; }
  tr:hover td { background: #1e1e1e; }
  .badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: bold; }
  .badge.pendiente { background: #2a2a00; color: #ffcc00; }
  .badge.confirmado { background: #002a1a; color: #00cc88; }
  .badge.enviado { background: #002233; color: #00aaff; }
  .badge.entregado { background: #1a2a00; color: #88cc00; }
  .badge.cancelado { background: #2a0000; color: #ff4444; }
  .stock-bar { background: #252525; border-radius: 4px; height: 6px; margin-top: 6px; }
  .stock-bar-fill { height: 6px; border-radius: 4px; background: #c9a84c; }
  .stock-low .stock-bar-fill { background: #ff4444; }
</style>
</head>
<body>
<header>
  <div>
    <h1>THREADBOT ADMIN</h1>
    <span>PANEL DE ADMINISTRACIÓN · THREADCO</span>
  </div>
</header>
<div class="container">
  <div class="grid" id="stats"></div>
  <h2>STOCK ACTUAL</h2>
  <table id="stock-table">
    <thead><tr><th>PRODUCTO</th><th>CATEGORÍA</th><th>PRECIO</th><th>TALLAS</th><th>STOCK</th></tr></thead>
    <tbody id="stock-body"></tbody>
  </table>
  <h2>ÚLTIMOS PEDIDOS</h2>
  <table id="orders-table">
    <thead><tr><th>ID</th><th>CLIENTE</th><th>EMAIL</th><th>TOTAL</th><th>ESTADO</th><th>FECHA</th></tr></thead>
    <tbody id="orders-body"></tbody>
  </table>
  <h2>CONFIGURACIÓN DEL CHATBOT</h2>
  <div id="config-section"></div>
</div>
<script>
async function guardarConfig(clave, valorForzado) {
  const valor = valorForzado !== undefined ? valorForzado : document.getElementById('input_' + clave).value;
  const res = await fetch('/config/' + clave + '?api_key=threadbot-internal-key&valor=' + encodeURIComponent(valor), {method: 'POST'});
  const data = await res.json();
  if (data.ok) {
    alert('✅ ' + clave + ' actualizado correctamente');
  } else {
    alert('❌ Error al guardar');
  }
}

async function actualizarStock(productoId) {
  const stock = parseInt(document.getElementById('stock_' + productoId).value);
  const res = await fetch('/products/' + productoId + '/stock?api_key=threadbot-internal-key&stock=' + stock, {method: 'POST'});
  const data = await res.json();
  if (data.ok) {
    load(); // refresca el panel
  } else {
    alert('❌ Error al actualizar stock');
  }
}

async function load() {
  const [products, orders] = await Promise.all([
    fetch('/products').then(r => r.json()),
    fetch('/orders-admin?api_key=threadbot-internal-key').then(r => r.json())
  ]);

  // Stats
  const stats = [
    { num: products.length, label: 'PRODUCTOS' },
    { num: orders.filter(o => o.estado === 'pendiente').length, label: 'PENDIENTES' },
    { num: orders.filter(o => o.estado === 'confirmado').length, label: 'CONFIRMADOS' },
    { num: orders.filter(o => o.estado === 'enviado').length, label: 'ENVIADOS' },
    { num: orders.filter(o => o.estado === 'entregado').length, label: 'ENTREGADOS' },
    { num: orders.filter(o => o.estado === 'cancelado').length, label: 'CANCELADOS' },
  ];
  document.getElementById('stats').innerHTML = stats.map(s =>
    `<div class="card"><div class="num">${s.num}</div><div class="label">${s.label}</div></div>`
  ).join('');

  // Stock
  const maxStock = Math.max(...products.map(p => p.stock), 1);
  document.getElementById('stock-body').innerHTML = products.map(p => {
    const pct = Math.round((p.stock / maxStock) * 100);
    const low = p.stock <= 5;
    return `<tr>
      <td><strong>${p.nombre}</strong></td>
      <td style="color:#888">${p.categoria}</td>
      <td style="color:#c9a84c">${p.precio}€</td>
      <td style="color:#888">${p.tallas}</td>
      <td>
        <div style="display:flex;align-items:center;gap:8px;">
          <input type="number" id="stock_${p.id}" value="${p.stock}" min="0"
            style="width:70px;background:#252525;border:1px solid #333;color:${p.stock<=5?'#ff4444':'#fff'};padding:4px 8px;border-radius:4px;font-size:13px;">
          <button onclick="actualizarStock(${p.id})"
            style="background:#c9a84c;color:#000;border:none;padding:4px 10px;border-radius:4px;font-size:11px;font-weight:bold;cursor:pointer;">
            ✓
          </button>
        </div>
        <div class="stock-bar ${p.stock<=5?'stock-low':''}">
          <div class="stock-bar-fill" style="width:${pct}%"></div>
        </div>
      </td>
    </tr>`;
  }).join('');

  // Orders
  document.getElementById('orders-body').innerHTML = orders.map(o =>
    `<tr>
      <td style="color:#c9a84c">#${o.id}</td>
      <td>${o.nombre_cliente}</td>
      <td style="color:#888;font-size:12px">${o.email_cliente}</td>
      <td style="color:#c9a84c">${o.total}€</td>
      <td><span class="badge ${o.estado}">${o.estado}</span></td>
      <td style="color:#888;font-size:12px">${o.fecha.split('.')[0]}</td>
    </tr>`
  ).join('');

  // Cargar configuración
  const config = await fetch('/config?api_key=threadbot-internal-key').then(r => r.json());

  document.getElementById('config-section').innerHTML = Object.entries(config).map(([clave, data]) => {
    if (clave === 'bot_activo') {
      return `
        <div style="background:#1e1e1e;border:1px solid #2a2a2a;border-radius:4px;padding:16px;margin-bottom:12px;display:flex;justify-content:space-between;align-items:center;">
          <div>
            <label style="font-size:11px;color:#c9a84c;font-weight:bold;letter-spacing:1px;">BOT ACTIVO</label>
            <p style="font-size:11px;color:#666;margin-top:4px;">${data.descripcion}</p>
          </div>
          <label style="position:relative;display:inline-block;width:52px;height:28px;">
            <input type="checkbox" id="toggle_bot_activo" ${data.valor === 'true' ? 'checked' : ''} 
              onchange="guardarConfig('bot_activo', this.checked ? 'true' : 'false')"
              style="opacity:0;width:0;height:0;">
            <span style="position:absolute;cursor:pointer;top:0;left:0;right:0;bottom:0;background:${data.valor === 'true' ? '#c9a84c' : '#444'};border-radius:28px;transition:.3s;">
              <span style="position:absolute;content:'';height:20px;width:20px;left:4px;bottom:4px;background:white;border-radius:50%;transition:.3s;transform:${data.valor === 'true' ? 'translateX(24px)' : 'translateX(0)'}"></span>
            </span>
          </label>
        </div>
      `;
    }
    return `
      <div style="background:#1e1e1e;border:1px solid #2a2a2a;border-radius:4px;padding:16px;margin-bottom:12px;">
        <label style="display:block;font-size:11px;color:#c9a84c;font-weight:bold;letter-spacing:1px;margin-bottom:8px;">${clave.toUpperCase().replace(/_/g,' ')}</label>
        <p style="font-size:11px;color:#666;margin-bottom:8px;">${data.descripcion}</p>
        <div style="display:flex;gap:8px;">
          <input id="input_${clave}" type="text" value="${data.valor}" 
            style="flex:1;background:#252525;border:1px solid #333;color:#fff;padding:8px 12px;border-radius:4px;font-size:13px;outline:none;">
          <button onclick="guardarConfig('${clave}')"
            style="background:#c9a84c;color:#000;border:none;padding:8px 16px;border-radius:4px;font-size:12px;font-weight:bold;cursor:pointer;">
            GUARDAR
          </button>
        </div>
      </div>
    `;
  }).join('');
}
load();
setInterval(load, 30000);
</script>
</body>
</html>"""
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html)

app.include_router(health.router)
app.include_router(chat.router)
