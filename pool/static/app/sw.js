// Pool LNH service worker: push notifications ONLY.
// No fetch handler and no cache on purpose: the page always comes from the network, so it can never get stuck
// on an old version.
self.addEventListener('install', function () { self.skipWaiting(); });
self.addEventListener('activate', function (e) { e.waitUntil(self.clients.claim()); });

self.addEventListener('push', function (e) {
  var d = {};
  try { d = e.data ? e.data.json() : {}; } catch (err) { d = { body: e.data ? e.data.text() : '' }; }
  e.waitUntil(self.registration.showNotification(d.title || 'Pool LNH', {
    body: d.body || '',
    icon: 'icon-192.png?v=2',
    badge: 'badge-96.png',            // white on transparent: Android's status bar uses only the transparency
    tag: d.tag || 'pool',
    data: { url: d.url || './' }
  }));
});

self.addEventListener('notificationclick', function (e) {
  e.notification.close();
  var url = new URL((e.notification.data && e.notification.data.url) || './', self.registration.scope).href;
  e.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (wins) {
    for (var i = 0; i < wins.length; i++) {
      if (wins[i].url.indexOf(self.registration.scope) === 0 && 'focus' in wins[i]) {
        return wins[i].focus().then(function (w) { return w && w.navigate ? w.navigate(url) : w; });
      }
    }
    return self.clients.openWindow(url);
  }));
});
