const CACHE="nexusmed-v1";
const CORE=["/","/manifest.json","/icon-192.svg","/icon-512.svg"];
self.addEventListener("install",e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(CORE).catch(()=>0)))});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))))});
self.addEventListener("fetch",e=>{
  if(e.request.method!=="GET")return;
  const u=new URL(e.request.url);
  if(u.pathname.startsWith("/api/"))return;
  e.respondWith(fetch(e.request).then(r=>{
    if(r.ok){const cl=r.clone();caches.open(CACHE).then(c=>c.put(e.request,cl))}
    return r;
  }).catch(()=>caches.match(e.request)));
});
