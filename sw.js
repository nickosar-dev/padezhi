/* Офлайн-режим: файлы приложения берём из сети (не дольше 4 с), копию кладём в кэш.
   Нет сети — отдаём последнюю копию. Поэтому новая версия приложения подхватывается
   сама, как только телефон в сети. Колоду (packs/) не кэшируем: приложение хранит её
   у себя и само честно пишет, что сервер недоступен. */
var CACHE='padezhi';
var SHELL=['./','index.html','manifest.webmanifest','icon-192.png','icon-512.png'];
var TIMEOUT=4000;

self.addEventListener('install',function(e){
  e.waitUntil(caches.open(CACHE).then(function(c){return c.addAll(SHELL);}).then(function(){return self.skipWaiting();}));
});
self.addEventListener('activate',function(e){
  e.waitUntil(self.clients.claim());
});
self.addEventListener('fetch',function(e){
  var req=e.request, url=new URL(req.url);
  if(req.method!=='GET'||url.origin!==location.origin||url.pathname.indexOf('/packs/')>=0) return;
  var key=url.origin+url.pathname;
  e.respondWith(caches.open(CACHE).then(function(cache){
    var fromNet=fetch(req).then(function(resp){
      if(resp.ok) cache.put(key,resp.clone());
      return resp;
    });
    var timer=new Promise(function(res){setTimeout(res,TIMEOUT,null);});
    return Promise.race([fromNet.catch(function(){return null;}),timer]).then(function(resp){
      if(resp) return resp;
      return cache.match(key).then(function(hit){
        if(hit) return hit;
        if(req.mode==='navigate') return cache.match(url.origin+url.pathname.replace(/[^/]*$/,'')+'index.html').then(function(h){return h||fromNet;});
        return fromNet;
      });
    });
  }));
});
