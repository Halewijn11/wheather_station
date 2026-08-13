// PROTOTYPE — throwaway, teaches the Scriptable workflow, not production code.
// Resolves ticket #110 (part of map #106 "iPhone Weather Widget").
//
// Four layout variants, switched by editing ACTIVE_VARIANT below and
// re-running (▶) on your phone:
//   A — Equal stack: temp / light / wind, three equal rows.
//   B — Wind-dominant split: sparklines left, big wind rose right.
//   C — Hero + tiles: temp is the big number, light/wind are small tiles.
//   D — Reference-style: mirrors the iOS weather-app screenshot you sent —
//       big "now" temp + condition top-left, wind badge top-right, a single
//       combined chart with the temp line drawn over rain bars, hour labels
//       along the bottom.
// None of them include light in variant D on purpose — the reference photo
// only has temp + rain + wind, so D tests "what if we drop light from the
// primary view" as a real structural option, not just a copy tweak.
//
// Pulls LIVE data from the doGet endpoint built in ticket #109. Falls back
// to seeded dummy data if the fetch fails (e.g. no network) so you can still
// preview the layout.
//
// HOW TO RUN THIS ON YOUR PHONE (Scriptable app, first time):
//   1. Install "Scriptable" from the App Store (free).
//   2. Open it, tap "+" top-right, paste this whole file in, name it
//      "widget-prototype".
//   3. Tap the ▶ Play button at the bottom — you'll see a preview alert
//      with the rendered widget image, built from your REAL sheet data.
//   4. To see it as an actual home-screen widget: long-press your home
//      screen -> "+" -> search "Scriptable" -> add it -> long-press the
//      placeholder -> Edit Widget -> Script: "widget-prototype" -> pick
//      the family matching the variant (see VARIANTS below).
//   5. To try another layout: edit ACTIVE_VARIANT to 'A'/'B'/'C'/'D',
//      tap ▶ again.

const ACTIVE_VARIANT = 'D';
const ENDPOINT_URL = 'https://script.google.com/macros/s/AKfycbxAX62uDNNXsPZ8dtsyTaL_p5Vmear12enFtOmN2TGXjbE1U9ExJVEVDA4DyfwfA7Ba/exec';

// ---- live data, with dummy fallback ----------------------------------------

function seededRandom(seed) {
  return function () {
    seed = (seed * 9301 + 49297) % 233280;
    return seed / 233280;
  };
}

function buildDummyData() {
  const rnd = seededRandom(42);
  const points = 48;
  const rows = [];
  let t = 14, l = 200, rainTotal = 0;
  for (let i = 0; i < points; i++) {
    t += (rnd() - 0.5) * 0.6;
    l += (rnd() - 0.5) * 40;
    l = Math.max(0, l);
    const rainTick = rnd() < 0.15 ? rnd() * 1.2 : 0;
    rainTotal += rainTick;
    rows.push({
      timestamp: new Date(Date.now() - (points - i) * 5 * 60 * 1000).toISOString(),
      temp_c: t,
      light: l,
      wind_kmh: Math.max(0, 8 + (rnd() - 0.4) * 10),
      rain_mm: Math.round(rainTotal * 10) / 10,
    });
  }
  return { latest: rows[rows.length - 1], today: rows };
}

async function fetchLiveData() {
  const req = new Request(ENDPOINT_URL);
  req.timeoutInterval = 8;
  const json = await req.loadJSON();
  if (!json || !json.today || !json.today.length) throw new Error('empty response');
  return json;
}

async function loadData() {
  try {
    return { data: await fetchLiveData(), live: true };
  } catch (e) {
    console.log(`live fetch failed (${e}), using dummy data`);
    return { data: buildDummyData(), live: false };
  }
}

// ---- drawing helpers, built on Scriptable's DrawContext --------------------

function drawText(dc, text, x, y, w, h, hex, size, weight = 'bold', align = 'left') {
  dc.setTextColor(new Color(hex));
  dc.setFont(weight === 'bold' ? Font.boldSystemFont(size) : Font.systemFont(size));
  if (align === 'left') dc.setTextAlignedLeft();
  else if (align === 'center') dc.setTextAlignedCenter();
  else dc.setTextAlignedRight();
  dc.drawTextInRect(text, new Rect(x, y, w, h));
}

function fillRoundedRect(dc, x, y, w, h, hex, radius = 0) {
  const path = new Path();
  path.addRoundedRect(new Rect(x, y, w, h), radius, radius);
  dc.addPath(path);
  dc.setFillColor(new Color(hex));
  dc.fillPath();
}

function drawSparkline(dc, x, y, w, h, values, hex, lineWidth = 2.5) {
  const min = Math.min(...values), max = Math.max(...values);
  const range = (max - min) || 1;
  const pts = values.map((v, i) => new Point(
    x + (i / (values.length - 1)) * w,
    y + h - ((v - min) / range) * h,
  ));
  const path = new Path();
  path.move(pts[0]);
  pts.slice(1).forEach(p => path.addLine(p));
  dc.addPath(path);
  dc.setStrokeColor(new Color(hex));
  dc.setLineWidth(lineWidth);
  dc.strokePath();
  return pts;
}

function drawBars(dc, x, y, w, h, values, hex) {
  const max = Math.max(...values, 0.1);
  const barW = w / values.length;
  values.forEach((v, i) => {
    const barH = (v / max) * h;
    fillRoundedRect(dc, x + i * barW + barW * 0.15, y + h - barH, barW * 0.7, barH, hex, barW * 0.2);
  });
}

const WIND_BINS = [0, 5, 10, 15, 20, Infinity];
const WIND_COLORS = ['#2c7bb6', '#abd9e9', '#ffffbf', '#fdae61', '#d7191c'];

function windBinIndex(speed) {
  for (let i = 0; i < WIND_BINS.length - 1; i++) {
    if (speed >= WIND_BINS[i] && speed < WIND_BINS[i + 1]) return i;
  }
  return WIND_BINS.length - 2;
}

function drawWindRose(dc, cx, cy, maxR, speeds) {
  // No direction in the payload (only wind_kmh), so this is a speed
  // DISTRIBUTION (binned histogram as a ring), not a directional rose.
  const sectors = speeds.length > 24 ? 24 : Math.max(8, speeds.length);
  const bucketed = Array.from({ length: sectors }, (_, i) => {
    const start = Math.floor((i / sectors) * speeds.length);
    const end = Math.floor(((i + 1) / sectors) * speeds.length);
    const slice = speeds.slice(start, Math.max(end, start + 1));
    return slice.reduce((a, b) => a + b, 0) / slice.length;
  });
  const sectorAngle = (Math.PI * 2) / sectors;
  const maxV = Math.max(...bucketed, 1);
  const segsPerWedge = 4;

  bucketed.forEach((v, s) => {
    const rOuter = Math.sqrt(v / maxV) * maxR;
    const a0 = s * sectorAngle - Math.PI / 2;
    const a1 = a0 + sectorAngle * 0.85;
    const path = new Path();
    const outerPts = [];
    for (let i = 0; i <= segsPerWedge; i++) {
      const a = a0 + (a1 - a0) * (i / segsPerWedge);
      outerPts.push(new Point(cx + Math.cos(a) * rOuter, cy + Math.sin(a) * rOuter));
    }
    path.move(new Point(cx, cy));
    outerPts.forEach(p => path.addLine(p));
    path.closeSubpath();
    dc.addPath(path);
    dc.setFillColor(new Color(WIND_COLORS[windBinIndex(v)]));
    dc.fillPath();
  });
}

function hourLabels(rows, n = 6) {
  const step = Math.max(1, Math.floor(rows.length / n));
  const labels = [];
  for (let i = 0; i < rows.length; i += step) {
    const d = new Date(rows[i].timestamp);
    labels.push(`${String(d.getHours()).padStart(2, '0')}:00`);
  }
  return labels;
}

// ---- four structurally different variants ----------------------------------

function VariantA(dc, W, H, { latest, today }) {
  fillRoundedRect(dc, 0, 0, W, H, '#000000', 0);
  const pad = 28, rowH = (H - pad * 2) / 3 - 10;
  const temp = today.map(r => r.temp_c), light = today.map(r => r.light), wind = today.map(r => r.wind_kmh);

  drawText(dc, `${latest.temp_c.toFixed(1)}°`, pad, pad, 140, 40, '#ffffff', 30);
  drawSparkline(dc, pad + 140, pad, W - pad * 2 - 140, rowH, temp, '#60A5FA');

  const y2 = pad + rowH + 15;
  drawText(dc, `${Math.round(latest.light)} lx`, pad, y2, 140, 34, '#ffffff', 24);
  drawSparkline(dc, pad + 140, y2, W - pad * 2 - 140, rowH, light, '#FB923C');

  const y3 = y2 + rowH + 15;
  drawText(dc, `${latest.wind_kmh.toFixed(1)} km/h`, pad, y3 + rowH / 2 - 12, 140, 26, '#ffffff', 20);
  drawWindRose(dc, W - pad - rowH / 2, y3 + rowH / 2, rowH / 2, wind);
}

function VariantB(dc, W, H, { latest, today }) {
  fillRoundedRect(dc, 0, 0, W, H, '#0b0b0c', 0);
  const pad = 26, colW = W * 0.42;
  const temp = today.map(r => r.temp_c), light = today.map(r => r.light), wind = today.map(r => r.wind_kmh);

  drawText(dc, 'TODAY', pad, pad, colW - pad, 16, '#8E8E93', 13);
  const rowH = (H - pad * 2 - 40) / 2;
  drawText(dc, `${latest.temp_c.toFixed(1)}°`, pad, pad + 20, colW - pad, 30, '#60A5FA', 22);
  drawSparkline(dc, pad, pad + 65, colW - pad, rowH - 40, temp, '#60A5FA');

  const y2 = pad + 55 + rowH;
  drawText(dc, `${Math.round(latest.light)} lx`, pad, y2 - 5, colW - pad, 30, '#FB923C', 22);
  drawSparkline(dc, pad, y2 + 40, colW - pad, rowH - 40, light, '#FB923C');

  const rcx = colW + (W - colW) / 2, rcy = H / 2;
  const r = Math.min(W - colW, H) / 2 - 20;
  drawWindRose(dc, rcx, rcy, r, wind);
  drawText(dc, `${latest.wind_kmh.toFixed(1)} km/h`, rcx - r, H - 30, r * 2, 20, '#ffffff', 15, 'bold', 'center');
}

function VariantC(dc, W, H, { latest, today }) {
  fillRoundedRect(dc, 0, 0, W, H, '#111318', 0);
  const pad = 26;
  const temp = today.map(r => r.temp_c), light = today.map(r => r.light), wind = today.map(r => r.wind_kmh);

  dc.setLineWidth(2);
  drawSparkline(dc, 0, H * 0.15, W * 0.62, H * 0.55, temp, '#3B5578', 6);
  drawText(dc, `${latest.temp_c.toFixed(1)}°`, pad, H * 0.5, W * 0.5, 60, '#ffffff', 46);
  drawText(dc, 'now', pad, H * 0.5 + 55, 100, 20, '#8E8E93', 13, 'regular');

  const tileW = W * 0.34, tileX = W - pad - tileW, tileH = (H - pad * 2 - 12) / 2;
  fillRoundedRect(dc, tileX, pad, tileW, tileH, '#1c1f26', 14);
  drawText(dc, `${Math.round(latest.light)} lx`, tileX + 12, pad + 10, tileW - 24, 22, '#FB923C', 16);
  drawSparkline(dc, tileX + 10, pad + 40, tileW - 20, tileH - 48, light, '#FB923C');

  const tileY2 = pad + tileH + 12;
  fillRoundedRect(dc, tileX, tileY2, tileW, tileH, '#1c1f26', 14);
  drawText(dc, `${latest.wind_kmh.toFixed(1)} km/h`, tileX + 12, tileY2 + 10, tileW - 24, 22, '#93C5FD', 16);
  drawWindRose(dc, tileX + tileW / 2, tileY2 + tileH / 2 + 14, Math.min(tileW, tileH) / 2 - 14, wind);
}

function VariantD(dc, W, H, { latest, today }) {
  // Mirrors the reference screenshot: location + big "now" temp top-left,
  // wind badge top-right, one combined chart (temp line over rain bars),
  // hour labels along the bottom. Light is dropped from this view — a real
  // structural bet, not a copy tweak (see the top-of-file note).
  fillRoundedRect(dc, 0, 0, W, H, '#1f4e8c', 24);
  const pad = 30;
  const temp = today.map(r => r.temp_c), rain = today.map(r => r.rain_mm);

  drawText(dc, 'Weather Station', pad, pad, W * 0.6, 24, '#ffffff', 17, 'bold');
  drawText(dc, `${latest.temp_c.toFixed(0)}°`, pad, pad + 26, W * 0.5, 70, '#ffffff', 56);

  // wind badge, top-right
  const badgeW = 150, badgeH = 44;
  fillRoundedRect(dc, W - pad - badgeW, pad, badgeW, badgeH, '#ffffff22', 12);
  drawText(dc, `${latest.wind_kmh.toFixed(0)} km/h`, W - pad - badgeW, pad + 10, badgeW, 24, '#ffffff', 14, 'bold', 'center');

  // combined chart: rain bars behind, temp line on top
  const chartY = H * 0.5, chartH = H * 0.34, chartX = pad, chartW = W - pad * 2;
  drawBars(dc, chartX, chartY, chartW, chartH, rain, '#4FC3F7AA');
  drawSparkline(dc, chartX, chartY, chartW, chartH, temp, '#FFC94A', 3);

  // hour labels along the bottom
  const labels = hourLabels(today, 6);
  const labelW = chartW / labels.length;
  labels.forEach((lbl, i) => {
    drawText(dc, lbl, chartX + i * labelW, chartY + chartH + 8, labelW, 16, '#ffffffAA', 11, 'regular', 'center');
  });
}

const VARIANTS = {
  A: { name: 'Equal stack', family: 'medium', size: [1014, 474], draw: VariantA },
  B: { name: 'Wind-dominant split', family: 'large', size: [1014, 1062], draw: VariantB },
  C: { name: 'Hero + tiles', family: 'medium', size: [1014, 474], draw: VariantC },
  D: { name: 'Reference-style (temp line + rain bars)', family: 'medium', size: [1014, 474], draw: VariantD },
};

// ---- build the widget image -------------------------------------------

async function createWidgetImage(payload) {
  const variant = VARIANTS[ACTIVE_VARIANT];
  const [W, H] = variant.size;
  const dc = new DrawContext();
  dc.size = new Size(W, H);
  dc.opaque = false;
  dc.respectScreenScale = true;
  variant.draw(dc, W, H, payload);
  return dc.getImage();
}

async function createWidget() {
  const { data, live } = await loadData();
  const widget = new ListWidget();
  widget.backgroundColor = new Color('#000000');
  const img = widget.addImage(await createWidgetImage(data));
  img.applyFillingContentMode();
  if (!config.runsInWidget && !live) {
    widget.addSpacer(4);
    const warn = widget.addText('⚠️ dummy data (live fetch failed)');
    warn.font = Font.systemFont(10);
    warn.textColor = new Color('#FF9999');
  }
  return widget;
}

const widget = await createWidget();

if (config.runsInWidget) {
  Script.setWidget(widget);
} else {
  const family = VARIANTS[ACTIVE_VARIANT].family;
  if (family === 'large') await widget.presentLarge();
  else await widget.presentMedium();
}
Script.complete();
