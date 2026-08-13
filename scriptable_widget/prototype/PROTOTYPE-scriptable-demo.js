// PROTOTYPE — throwaway, teaches the Scriptable workflow, not production code.
// Resolves ticket #110 (part of map #106 "iPhone Weather Widget").
//
// Four layout variants, switched by editing ACTIVE_VARIANT below and
// re-running (▶) on your phone:
//   A — Equal stack: temp / light / wind, three equal rows.
//   B — Wind-dominant split: sparklines left, big wind rose right.
//   C — Hero + tiles: temp is the big number, light/wind are small tiles.
//   D — Reference-style (WINNER, picked on ticket #110): mirrors the iOS
//       weather-app screenshot — big "now" temp top-left, wind badge (speed
//       only, no direction in the payload) top-right, one combined chart
//       (temp line + rain bars) with a value label above/below every point,
//       hour labels along the bottom. Fixed, disjoint vertical bands for
//       every text row so labels can never overlap regardless of data range.
// Light is dropped from variant D on purpose — the reference photo only has
// temp + rain + wind, so D tests "what if we drop light from the primary
// view" as a real structural option, not just a copy tweak.
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
      wind_dir_deg: Math.floor(rnd() * 360),
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

const CARDINALS = ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW'];
function cardinal(deg) {
  return CARDINALS[Math.round((((deg % 360) + 360) % 360) / 22.5) % 16];
}

function drawWindArrow(dc, cx, cy, r, deg, hex) {
  // Meteorological convention (same as the reference screenshot): the LABEL
  // says where the wind comes FROM ("SW"), the ARROW points where it blows
  // TOWARD — hence the +180.
  const a = (deg + 180) * Math.PI / 180;
  const tip = new Point(cx + Math.sin(a) * r, cy - Math.cos(a) * r);
  const tail = new Point(cx - Math.sin(a) * r, cy + Math.cos(a) * r);
  const head = r * 0.55;

  const shaft = new Path();
  shaft.move(tail);
  shaft.addLine(tip);
  dc.addPath(shaft);

  const barb1 = new Path();
  barb1.move(tip);
  barb1.addLine(new Point(tip.x - Math.sin(a - 0.5) * head, tip.y + Math.cos(a - 0.5) * head));
  dc.addPath(barb1);

  const barb2 = new Path();
  barb2.move(tip);
  barb2.addLine(new Point(tip.x - Math.sin(a + 0.5) * head, tip.y + Math.cos(a + 0.5) * head));
  dc.addPath(barb2);

  dc.setStrokeColor(new Color(hex));
  dc.setLineWidth(r * 0.22);
  dc.strokePath();
}

function downsample(rows, n) {
  if (rows.length <= n) return rows;
  return Array.from({ length: n }, (_, i) => rows[Math.round(i * (rows.length - 1) / (n - 1))]);
}

function VariantD(dc, W, H, { latest, today }) {
  // "D2" — winner of ticket #110. Mirrors the reference screenshot: location
  // + big "now" temp top-left, wind badge (speed only — payload has no
  // direction) top-right, ONE combined chart (temp line + rain bars) with
  // per-point value labels and hour labels. Light dropped from this view —
  // a real structural bet, not a copy tweak (see top-of-file note).
  //
  // Layout is laid out in fixed 338x158pt "bands" (see the design-check
  // widget on ticket #110) then scaled to the actual W/H so every element
  // has a disjoint vertical range and can never overlap another:
  //   header        8–58pt    location + big temp (left), wind badge (right)
  //   temp line     78–98pt   line + dots; each label rides ~7pt above its
  //                           OWN datapoint (tracking the line, not a fixed
  //                           row), so labels occupy 60–93pt
  //   rain bars    104–130pt  own band — never overlaps the temp line
  //   rain labels  133–144pt  "0.2" etc
  //   hour labels  145–157pt  "20:00" etc, bottom row
  const s = W / 338; // scale from design pt-space to this widget's actual pixels
  fillRoundedRect(dc, 0, 0, W, H, '#1f4e8c', 24 * s);

  drawText(dc, 'Weather Station', 16 * s, 8 * s, 200 * s, 18 * s, '#ffffff', 13 * s, 'bold');
  drawText(dc, `${latest.temp_c.toFixed(0)}°`, 16 * s, 28 * s, 140 * s, 30 * s, '#ffffff', 24 * s, 'bold');

  // wind badge: arrow + cardinal origin on top, speed below (reference layout).
  // wind_dir_deg only appears once the doGet endpoint is redeployed with the
  // direction column (V); until then the badge falls back to speed-only.
  const dir = latest.wind_dir_deg;
  const hasDir = dir !== null && dir !== undefined;
  const badgeW = (hasDir ? 78 : 62) * s, badgeH = (hasDir ? 32 : 24) * s, badgeX = W - 16 * s - badgeW;
  fillRoundedRect(dc, badgeX, 8 * s, badgeW, badgeH, '#ffffff33', 10 * s);
  if (hasDir) {
    drawWindArrow(dc, badgeX + 15 * s, 8 * s + badgeH / 2, 8 * s, dir, '#ffffff');
    drawText(dc, cardinal(dir), badgeX + 29 * s, 12 * s, 44 * s, 12 * s, '#ffffff', 10 * s, 'bold');
    drawText(dc, `${latest.wind_kmh.toFixed(0)} km/h`, badgeX + 29 * s, 25 * s, 44 * s, 12 * s, '#ffffff', 10 * s, 'regular');
  } else {
    drawText(dc, `${latest.wind_kmh.toFixed(0)} km/h`, badgeX, 12 * s, badgeW, badgeH - 6 * s, '#ffffff', 10 * s, 'bold', 'center');
  }

  const rows = downsample(today, 6);
  const chartX = 26 * s, chartW = W - 2 * chartX;
  const lineTop = 78 * s, lineH = 20 * s;
  const rainBase = 130 * s, maxBarH = 26 * s, barW = 20 * s;
  const rainLabelY = 133 * s, rainLabelH = 11 * s, hourLabelY = 145 * s, hourLabelH = 12 * s;
  const step = chartW / (rows.length - 1);

  const temps = rows.map(r => r.temp_c), rains = rows.map(r => r.rain_mm);
  const tMin = Math.min(...temps), tMax = Math.max(...temps), tRg = tMax - tMin || 1;
  const pts = temps.map((v, i) => new Point(chartX + i * step, lineTop + lineH - ((v - tMin) / tRg) * lineH));

  const rMax = Math.max(...rains, 0.1) * 1.15;
  rains.forEach((r, i) => {
    const barH = (r / rMax) * maxBarH;
    fillRoundedRect(dc, chartX + i * step - barW / 2, rainBase - barH, barW, barH, '#4FC3F773', 4 * s);
  });

  const linePath = new Path();
  linePath.move(pts[0]);
  pts.slice(1).forEach(p => linePath.addLine(p));
  dc.addPath(linePath);
  dc.setStrokeColor(new Color('#FFC94A'));
  dc.setLineWidth(2.5 * s);
  dc.strokePath();

  // temp label rides just above its OWN datapoint, tracking the line
  pts.forEach((p, i) => {
    const dot = new Path();
    dot.addEllipse(new Rect(p.x - 2.5 * s, p.y - 2.5 * s, 5 * s, 5 * s));
    dc.addPath(dot);
    dc.setFillColor(new Color('#FFC94A'));
    dc.fillPath();
    drawText(dc, `${temps[i].toFixed(0)}°`, p.x - step / 2, p.y - 18 * s, step, 13 * s, '#ffffff', 11 * s, 'bold', 'center');
  });
  rains.forEach((r, i) => drawText(dc, r.toFixed(1), chartX + i * step - step / 2, rainLabelY, step, rainLabelH, '#dceaff', 9 * s, 'regular', 'center'));
  rows.forEach((r, i) => {
    const d = new Date(r.timestamp);
    const lbl = `${String(d.getHours()).padStart(2, '0')}:00`;
    drawText(dc, lbl, chartX + i * step - step / 2, hourLabelY, step, hourLabelH, '#a9c3e0', 9 * s, 'regular', 'center');
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
