// smoke-test.js — structural checks on bdr-map.html + JS parse check.
// Catches regressions that would be obvious on page load (missing UI, data
// injection failures, broken JS). Run from a session sandbox with Node + jsdom:
//
//   cd "Territory Dashboard" && node smoke-test.js
//
// jsdom install (one-time per session):  npm install --prefix /tmp jsdom

const fs   = require('fs');
const path = require('path');
const { JSDOM } = (() => {
  try { return require('jsdom'); }
  catch { return require(path.join('/tmp/node_modules/jsdom')); }
})();

const htmlPath = path.join(__dirname, 'bdr-map.html');
const html = fs.readFileSync(htmlPath, 'utf8');

const dom = new JSDOM(html, { runScripts: 'outside-only' });
const { document } = dom.window;

const checks = [];
const check = (name, fn, detail = () => '') => {
  try {
    const res = fn();
    checks.push([name, res ? 'PASS' : 'FAIL', detail(res)]);
  } catch (e) { checks.push([name, 'THROW', e.message]); }
};

// ── DOM structure ────────────────────────────────────────────
check('map container (#map)',       () => !!document.getElementById('map'));
check('header',                     () => !!document.getElementById('header'));
check('BDR row container',          () => !!document.getElementById('bdrRow'));
check('dot toggle bar',             () => !!document.getElementById('dotToggle'), () => `children: ${document.querySelectorAll('#dotToggle .dt-btn').length}`);
check('basemap toggle',             () => !!document.getElementById('basemapToggle'), () => `children: ${document.querySelectorAll('#basemapToggle .bm-btn').length}`);
check('back button',                () => !!document.getElementById('backBtn'));
check('legend container',           () => !!document.getElementById('legend'));
check('panel / panelEmpty',         () => !!document.getElementById('panel') && !!document.getElementById('panelEmpty'));
check('tooltip elements',           () => !!document.getElementById('tooltip') && !!document.getElementById('stateTip') && !!document.getElementById('filterTip'));
check('search box DOM',             () => !!document.getElementById('searchBox') && !!document.getElementById('searchInput') && !!document.getElementById('searchResults'));
check('refreshed chip present',     () => !!document.getElementById('refreshedChip'), () => `text: ${document.getElementById('refreshedChip')?.textContent.trim().slice(0,60)}`);

// ── CDN resources ────────────────────────────────────────────
check('Leaflet CSS link',           () => !!document.querySelector('link[href*="leaflet"]'));
check('Leaflet JS script',          () => !!document.querySelector('script[src*="leaflet"]'));
check('D3 JS script',               () => !!document.querySelector('script[src*="d3"]'));
check('topojson JS script',         () => !!document.querySelector('script[src*="topojson"]'));

// ── JS content spot-checks ───────────────────────────────────
const scriptBlocks = [...document.querySelectorAll('script')].map(s => s.textContent || '').join('\n');
check('ACCOUNTS data injected',     () => scriptBlocks.includes('const ACCOUNTS = [{'), () => `len ≈ ${scriptBlocks.length.toLocaleString()}`);
check('DATA_VERSION substituted',   () => !scriptBlocks.includes('%%DATA_VERSION%%'));
check('DATA_REFRESHED substituted', () => !html.includes('%%DATA_REFRESHED%%'));
check('state-click fallback wired', () => scriptBlocks.includes('d3.geoContains'));
check('Password gate',              () => scriptBlocks.includes('Permitplease') && scriptBlocks.includes('gw_auth'));
check('Leaflet map() call',         () => scriptBlocks.includes("L.map('map'"));
check('CartoDB tile URL',           () => scriptBlocks.includes('basemaps.cartocdn.com'));
check('Leaflet-native markers',     () => scriptBlocks.includes('L.canvas') && scriptBlocks.includes('L.circleMarker') && scriptBlocks.includes('L.divIcon') && scriptBlocks.includes('L.layerGroup'));
check('Mouse-following tooltip',    () => scriptBlocks.includes('showDotTip') && scriptBlocks.includes("on('mousemove'") && !scriptBlocks.includes('bindTooltip'));
check('No leftover acctCard/hint',  () => !scriptBlocks.includes('acctCard') && !scriptBlocks.includes('hintBanner'));
check('State layer + click handler',() => scriptBlocks.includes('L.geoJSON') && scriptBlocks.includes('selectState'));
check('BDR pills dynamic build',    () => scriptBlocks.includes('buildPills'));
check('byState pre-compute',        () => scriptBlocks.includes('const byState'));
check('renderDots / filterForView', () => scriptBlocks.includes('function renderDots') && scriptBlocks.includes('filterForView'));
check('renderPanel function',       () => scriptBlocks.includes('function renderPanel'));
check('search JS wired',            () => scriptBlocks.includes('setupSearch') && scriptBlocks.includes('lastMatches') && scriptBlocks.includes('latLngToContainerPoint'));
check('empty-default filter',       () => scriptBlocks.includes("dotFilter    = 'none'") || scriptBlocks.includes("dotFilter = 'none'"));

// Parse the inline JS with Node — catches syntax errors.
const inlineScript = [...document.querySelectorAll('script')].map(s => s.textContent).find(t => t && t.includes('const ACCOUNTS'));
try {
  new (require('vm').Script)(inlineScript);
  checks.push(['Inline JS parses', 'PASS', '']);
} catch (e) {
  checks.push(['Inline JS parses', 'FAIL', e.message]);
}

// ── Output ───────────────────────────────────────────────────
console.log('\n──── SMOKE TEST ────');
let fails = 0;
checks.forEach(([n, st, d]) => {
  const mark = st === 'PASS' ? '✓' : '✗';
  if (st !== 'PASS') fails++;
  console.log(`  ${mark} ${n}: ${st}${d ? '  — ' + d : ''}`);
});
console.log(`\n${fails ? 'FAILED' : 'ALL GREEN'}: ${checks.length - fails}/${checks.length} passed`);
process.exit(fails ? 1 : 0);
