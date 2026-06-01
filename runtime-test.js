// runtime-test.js — execute bdr-map.html's inline JS with Leaflet stubbed,
// count markers, catch throws. Complements smoke-test.js (which is structural).
//
//   cd "Territory Dashboard" && node runtime-test.js
//
// Expects Node only (no jsdom required).

const fs   = require('fs');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, 'bdr-map.html'), 'utf8');

const scripts = [];
const re = /<script([^>]*)>([\s\S]*?)<\/script>/g;
let m;
while ((m = re.exec(html))) {
  if (!/\bsrc=/.test(m[1])) scripts.push(m[2]);
}
let js = scripts.sort((a, b) => b.length - a.length)[0];

// Skip the password gate (it blocks everything on sessionStorage).
js = js.replace(/\(function\(\)\{[\s\S]*?sessionStorage\.getItem[\s\S]*?\}\)\(\);?/, '');
// Disable network calls (state boundaries fetch).
js = js.replace(/fetch\(/g, 'NO_FETCH_(');

global.window = global;
const fakeEl = () => ({
  id: '', innerHTML: '', textContent: '', style: {}, dataset: {},
  addEventListener: () => {},
  classList: { add: () => {}, remove: () => {}, toggle: () => {}, contains: () => false },
  appendChild: () => {}, querySelectorAll: () => [], removeChild: () => {},
  getBoundingClientRect: () => ({ left: 0, top: 0, width: 800, height: 600 }),
  offsetWidth: 800, offsetHeight: 600, clientWidth: 800, clientHeight: 600,
});
global.document = {
  getElementById: () => fakeEl(),
  querySelector: () => fakeEl(),
  querySelectorAll: () => [],
  createElement: () => fakeEl(),
  addEventListener: () => {},
  body: fakeEl(),
};
global.sessionStorage = { getItem: () => '1', setItem: () => {} };
global.location = { reload: () => {} };
global.navigator = { userAgent: '' };
global.NO_FETCH_ = () => ({ then: () => ({ then: () => ({ catch: () => {} }) }), catch: () => {} });

const stats = {
  maps: 0, tileLayers: 0, layerGroups: 0, markers: 0, circleMarkers: 0,
  divIcons: 0, addLayerCalls: 0, geoJSONs: 0, tooltips: 0, permanentTooltips: 0,
  throws: [],
};

class LayerGroup {
  constructor() { stats.layerGroups++; this.layers = []; }
  addTo() { return this; }
  clearLayers() { this.layers.length = 0; return this; }
  addLayer(l) { stats.addLayerCalls++; this.layers.push(l); return this; }
}
class Marker {
  constructor(ll, opts) { stats.markers++; if (opts && opts.icon && opts.icon._divIcon) stats.divIcons++; }
  on() { return this; } setIcon() { return this; }
  bindTooltip(h, opts) { stats.tooltips++; if (opts && opts.permanent) stats.permanentTooltips++; return this; }
}
class CircleMarker {
  constructor() { stats.circleMarkers++; }
  on() { return this; } setStyle() { return this; }
  bindTooltip(h, opts) { stats.tooltips++; if (opts && opts.permanent) stats.permanentTooltips++; return this; }
}
class DivIcon { constructor() { this._divIcon = true; } }
class Canvas {}
class TileLayer {
  constructor() { stats.tileLayers++; }
  addTo() { return this; } on() { return this; }
  bringToBack() { return this; } bringToFront() { return this; }
  setOpacity() { return this; } remove() { return this; }
}
class LMap {
  constructor() { stats.maps++; this.zoomControl = { setPosition: () => {} }; }
  addLayer() { stats.addLayerCalls++; return this; }
  setView() { return this; } fitBounds() { return this; } flyTo() { return this; }
  flyToBounds() { return this; } on() { return this; } once() { return this; }
  getZoom() { return 4; } getCenter() { return { lat: 39, lng: -98 }; }
  latLngToLayerPoint() { return { x: 0, y: 0 }; }
  latLngToContainerPoint() { return { x: 0, y: 0 }; }
  getPanes() { return {}; }
  createPane(name) { this._panes = this._panes || {}; this._panes[name] = { style: {} }; return this._panes[name]; }
  getPane(name) { this._panes = this._panes || {}; if (!this._panes[name]) this._panes[name] = { style: {} }; return this._panes[name]; }
  whenReady(cb) { try { cb(); } catch (e) { stats.throws.push('whenReady:' + e.message); } return this; }
  getSize() { return { x: 800, y: 600 }; }
  removeLayer() { return this; } closePopup() { return this; }
  getContainer() { return fakeEl(); }
  zoomOut() { return this; } zoomIn() { return this; } setZoom() { return this; }
  getBoundsZoom() { return 6; }
}

global.L = {
  map: () => new LMap(),
  tileLayer: () => new TileLayer(),
  layerGroup: () => new LayerGroup(),
  marker: (ll, opts) => new Marker(ll, opts),
  circleMarker: () => new CircleMarker(),
  divIcon: () => new DivIcon(),
  canvas: () => new Canvas(),
  geoJSON: () => { stats.geoJSONs++; return { addTo: () => ({}), bringToBack: () => ({}) }; },
  control: () => ({ addTo: () => ({}) }),
  DomEvent: { stop: () => {}, stopPropagation: () => {} },
};

const chain = () => {
  const f = () => f;
  f.domain = () => f; f.range = () => f; f.clamp = () => f;
  f.type = () => f; f.size = () => f;
  return f;
};
global.d3 = {
  symbolStar: {}, symbolDiamond2: {}, symbolTriangle: {}, symbolSquare: {},
  symbolAsterisk: {}, symbolWye: {}, symbolCross: {}, symbolCircle: {},
  symbol: () => chain(),
  scaleLinear: () => chain(),
};
global.topojson = { feature: () => ({ features: [] }) };

console.log('Running inline JS...');
try {
  new Function(js)();
  console.log('Script completed cleanly');
} catch (e) {
  console.error('SCRIPT THREW:', e.message);
  console.error(e.stack.split('\n').slice(0, 15).join('\n'));
  process.exit(1);
}

console.log('\n── STATS ──');
console.log(JSON.stringify(stats, null, 2));
process.exit(stats.throws.length ? 1 : 0);
