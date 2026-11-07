/* BM Energy Barabkunda Plant · offline support for the installed app. Prepared by Akib Fateh. */
const CACHE = "barabkunda-v1";
const CORE = ["./", "index.html", "manifest.webmanifest", "assets/logo.png", "assets/logo-alpha.webp", "assets/plant_1280.webp", "assets/plant_1920.webp", "assets/app/icon-192.png", "assets/app/icon-512.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(CORE)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});

// The page itself: newest version from the network, saved for offline use; the saved copy if the network is slow or absent.
async function page(req) {
  const cache = await caches.open(CACHE);
  const net = fetch(req, { cache: "no-store" }).then((res) => { if (res.ok) cache.put("index.html", res.clone()); return res; });
  const saved = await cache.match("index.html");
  if (!saved) return net.catch(() => new Response("Offline: open the app once with internet to save the plant data.", { status: 503, headers: { "Content-Type": "text/plain; charset=utf-8" } }));
  const slow = new Promise((r) => setTimeout(() => r(saved), 6000));
  return Promise.race([net.catch(() => saved), slow]);
}
// Images, fonts and other files: saved copy at once, refreshed in the background.
async function asset(req) {
  const cache = await caches.open(CACHE);
  const saved = await cache.match(req);
  const net = fetch(req).then((res) => { if (res.ok || res.type === "opaque") cache.put(req, res.clone()); return res; }).catch(() => saved);
  return saved || net;
}
self.addEventListener("fetch", (e) => {
  const req = e.request; if (req.method !== "GET") return;
  const url = new URL(req.url);
  const same = url.origin === location.origin;
  if (req.mode === "navigate" || (same && /\/(index\.html)?$/.test(url.pathname))) { e.respondWith(page(req)); return; }
  if (same && /\.apk$/.test(url.pathname)) return;
  if (same || /fonts\.(googleapis|gstatic)\.com$/.test(url.hostname)) e.respondWith(asset(req));
});
