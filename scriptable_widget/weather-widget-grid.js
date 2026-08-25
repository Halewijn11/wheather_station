// Weather Station — iPhone home-screen widget, GRID layout (Scriptable).
//
// Second, separately-installable widget. `weather-widget.js` (temp+rain chart
// + wind badge) stays as-is and keeps running; this one is the 9-field grid
// design prototyped in docs/widget_mockup/Main.dc.html:
//   left column  — big amber temp, sunrise, sunset
//   divider
//   right 3x2    — humidity, wind speed, wind direction, pressure, light, rain
//
// Data freshness convention:
//   rain  = SUM of today's rain_mm rows (since local midnight)
//   every other field = the latest reading
// rain_mm is a per-report delta (~5min ticks), so a single latest reading
// reads 0.0mm almost always — same reasoning as the other widget's rain bars.
//
// Sunrise/sunset have no sensor source (the station does not measure them),
// so they are computed locally from STATION_LAT/STATION_LON + today's date
// with the NOAA sunrise equation. No API call, no quota, works offline.
//
// HOW TO RUN THIS ON YOUR PHONE (Scriptable app, first time):
//   1. Install "Scriptable" from the App Store (free).
//   2. Open it, tap "+" top-right, paste this whole file in, name it
//      "weather-widget-grid".
//   3. Tap the ▶ Play button at the bottom for a preview built from your REAL
//      sheet data.
//   4. Home screen -> long-press -> "+" -> "Scriptable" -> add -> long-press
//      the placeholder -> Edit Widget -> Script: "weather-widget-grid" ->
//      family: MEDIUM.

const ENDPOINT_URL = 'https://script.google.com/macros/s/AKfycbxAX62uDNNXsPZ8dtsyTaL_p5Vmear12enFtOmN2TGXjbE1U9ExJVEVDA4DyfwfA7Ba/exec';

// Station coordinates, used ONLY for the local sunrise/sunset computation.
// Same fix the OpenWeather forecast Apps Script uses
// (streamlit_app/openwheather_appscript.txt).
const STATION_LAT = 50.908;
const STATION_LON = 4.113; // east-positive

// Medium widget size, in POINTS — varies per iPhone model (e.g. 338x158 on a
// 12/13, 364x170 on a 12/13 Pro Max, 344x162 on a 16 Pro). A single hardcoded
// size only matches the model it was measured on; on any other phone iOS
// letterboxes the image inside the actual (differently-sized) widget slot,
// which is the black-bar gap seen around the widget on non-matching devices.
// Device.screenSize() (in points) keys into the per-device-class table below;
// unrecognized devices fall back to the 12/13 size. Source: widget sizes are
// fixed per screen-size class, not derivable from screenSize() by formula —
// see https://github.com/simonbs/ios-widget-sizes.
// Do not pre-multiply this by the screen scale: respectScreenScale = true
// already renders at 3x on a Retina phone.
const MEDIUM_WIDGET_SIZE_BY_SCREEN_PT = {
  '320x568': [291, 141], // SE (1st gen), iPod touch 7
  '375x667': [321, 148], // 6s/7/8, SE (2nd/3rd gen)
  '414x736': [348, 157], // 6s/7/8 Plus
  '375x812': [329, 155], // X/Xs, 11 Pro
  '414x896': [360, 169], // Xr/Xs Max, 11/11 Pro Max
  '360x780': [329, 155], // 12 mini, 13 mini
  '390x844': [338, 158], // 12, 12 Pro, 13, 13 Pro, 14
  '428x926': [364, 170], // 12 Pro Max, 13 Pro Max, 14 Plus
  '393x852': [338, 158], // 14 Pro, 15, 15 Pro, 16, 16e
  '430x932': [364, 170], // 14 Pro Max, 15 Pro Max, 16 Plus
  '402x874': [344, 162], // 16 Pro, 17 Pro
  '440x956': [364, 170], // 16 Pro Max, 17 Pro Max (unconfirmed, Pro-Max-class fallback)
};

function getMediumWidgetSize() {
  const { width, height } = Device.screenSize();
  const key = width < height ? `${width}x${height}` : `${height}x${width}`;
  return MEDIUM_WIDGET_SIZE_BY_SCREEN_PT[key] || [338, 158];
}

const WIDGET_SIZE = getMediumWidgetSize();

// Mockup design space. Every coordinate below is expressed in this 364x170pt
// frame and multiplied by `s = W / DESIGN_W` at draw time, so the layout is a
// straight scale of Main.dc.html onto whatever phone this runs on.
const DESIGN_W = 364;

const COLOR_BG = '#17558F';
const COLOR_ACCENT = '#F5A623';     // temp only
const COLOR_TEXT = '#ffffff';
const COLOR_LABEL = '#ffffff99';    // rgba(255,255,255,0.6)
const COLOR_HAIRLINE = '#ffffff29'; // rgba(255,255,255,0.16)

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
  let t = 14, l = 200, h = 58, p = 101300;
  for (let i = 0; i < points; i++) {
    t += (rnd() - 0.5) * 0.6;
    l += (rnd() - 0.5) * 40;
    l = Math.max(0, l);
    h += (rnd() - 0.5) * 3;
    h = Math.min(100, Math.max(0, h));
    p += (rnd() - 0.5) * 40;
    rows.push({
      timestamp: new Date(Date.now() - (points - i) * 5 * 60 * 1000).toISOString(),
      temp_c: t,
      humidity: h,
      pressure_pa: p,
      light: l,
      wind_dir_deg: Math.floor(rnd() * 360),
      wind_kmh: Math.max(0, 8 + (rnd() - 0.4) * 10),
      // per-report delta, matching the real feed — NOT a running total
      rain_mm: rnd() < 0.15 ? Math.round(rnd() * 12) / 10 : 0,
    });
  }
  return { latest: rows[rows.length - 1], today: rows };
}

async function fetchLiveData() {
  const req = new Request(ENDPOINT_URL);
  // The endpoint caches, but a cold start still costs tens of seconds.
  req.timeoutInterval = 60;
  // loadString, not loadJSON: if the deployment's access is "Anyone with
  // Google account" the response is a Google sign-in HTML page, and loadJSON
  // fails with a generic parse error that hides the real cause.
  const body = await req.loadString();
  const status = req.response ? req.response.statusCode : '?';
  let json;
  try {
    json = JSON.parse(body);
  } catch (e) {
    const looksLikeLogin = /accounts\.google\.com|ServiceLogin|<html/i.test(body);
    throw new Error(looksLikeLogin
      ? `HTTP ${status}: got an HTML page, not JSON — the web app is probably deployed as "Anyone with Google account". Redeploy with access "Anyone".`
      : `HTTP ${status}: response was not JSON — ${body.slice(0, 120)}`);
  }
  if (!json || !json.latest) throw new Error(`HTTP ${status}: JSON had no "latest" record`);
  // humidity/pressure_pa only appear once the Apps Script doGet is redeployed
  // with the extended field set; the cells fall back to "--" until then.
  return { latest: json.latest, today: json.today || [] };
}

async function loadData() {
  try {
    return { data: await fetchLiveData(), live: true, error: null };
  } catch (e) {
    console.log(`live fetch failed (${e}), using dummy data`);
    return { data: buildDummyData(), live: false, error: `${e && e.message ? e.message : e}` };
  }
}

// ---- sunrise / sunset ------------------------------------------------------

const DEG = Math.PI / 180;

// NOAA / "sunrise equation" (the Wikipedia formulation), accurate to well
// under a minute for our purposes. Returns { sunrise, sunset } as local
// "HH:MM" strings, or "--:--" during polar day/night where the sun never
// crosses the horizon on the given date.
function computeSunTimes(lat, lon, date) {
  const jd = date.getTime() / 86400000 + 2440587.5; // Julian date
  const n = Math.round(jd - 2451545.0 + 0.0008);    // days since J2000, day-rounded

  const lw = -lon;                     // the equation wants WEST-positive longitude
  const jStar = n + lw / 360;          // mean solar time
  const M = (357.5291 + 0.98560028 * jStar) % 360;  // solar mean anomaly
  const C = 1.9148 * Math.sin(M * DEG)              // equation of the center
          + 0.0200 * Math.sin(2 * M * DEG)
          + 0.0003 * Math.sin(3 * M * DEG);
  const lambda = (M + C + 180 + 102.9372) % 360;    // ecliptic longitude
  const jTransit = 2451545.0 + jStar
                 + 0.0053 * Math.sin(M * DEG)
                 - 0.0069 * Math.sin(2 * lambda * DEG);
  const sinDec = Math.sin(lambda * DEG) * Math.sin(23.4397 * DEG);
  const cosDec = Math.cos(Math.asin(sinDec));

  // -0.833° = atmospheric refraction + the sun's apparent disc radius.
  const cosOmega = (Math.sin(-0.833 * DEG) - Math.sin(lat * DEG) * sinDec)
                 / (Math.cos(lat * DEG) * cosDec);
  if (cosOmega > 1 || cosOmega < -1) return { sunrise: '--:--', sunset: '--:--' };

  const omega = Math.acos(cosOmega) / DEG;          // hour angle, degrees
  const jdToDate = j => new Date((j - 2440587.5) * 86400000);
  return {
    sunrise: hhmm(jdToDate(jTransit - omega / 360)),
    sunset: hhmm(jdToDate(jTransit + omega / 360)),
  };
}

function hhmm(d) {
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
}

// ---- value formatting ------------------------------------------------------

const CARDINALS = ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW'];
function cardinal(deg) {
  return CARDINALS[Math.round((((deg % 360) + 360) % 360) / 22.5) % 16];
}

function has(v) { return v !== null && v !== undefined && v !== '' && !isNaN(v); }
function fmt(v, f) { return has(v) ? f(Number(v)) : '--'; }

function fmtLight(lx) {
  return lx >= 1000 ? `${(lx / 1000).toFixed(1)}k lx` : `${lx.toFixed(0)} lx`;
}

// rain = today's total, not the latest 5-minute delta (see header note).
function rainTotalToday(today) {
  let sum = 0, seen = false;
  for (const r of today) {
    if (!has(r.rain_mm)) continue;
    sum += Number(r.rain_mm);
    seen = true;
  }
  return seen ? Math.round(sum * 10) / 10 : null;
}

// ---- drawing helpers, built on Scriptable's DrawContext --------------------

// SF Pro Rounded is the mockup's face; Scriptable exposes it as the rounded
// system font family. Weight names map to the mockup's 800/700/600.
function fontFor(size, weight) {
  if (weight === 'heavy') return Font.heavyRoundedSystemFont(size);
  if (weight === 'bold') return Font.boldRoundedSystemFont(size);
  if (weight === 'semibold') return Font.semiboldRoundedSystemFont(size);
  return Font.regularRoundedSystemFont(size);
}

function drawText(dc, text, x, y, w, h, hex, size, weight = 'bold', align = 'left') {
  dc.setTextColor(new Color(hex));
  dc.setFont(fontFor(size, weight));
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

// ---- icons -----------------------------------------------------------------
//
// Every icon below is a hand-transcription of the corresponding 24x24-viewBox
// SVG in docs/widget_mockup/Main.dc.html, expressed as primitive ops in that
// same 24x24 space and stroked as a Path — the technique the chart widget
// already uses for its wind arrow. SVG elliptical-arc ("A"/"a") commands have
// no Path equivalent, so each was solved for its centre/radius/sweep once and
// is recorded here as {arc: [cx, cy, r, startDeg, endDeg]}, angles measured in
// the SVG's y-down frame (0deg = +x, 90deg = +y i.e. downward).
//
// SVG stroke-width is 1.3 in viewBox units, i.e. 1.3 * 16/24 ~= 0.87pt on
// screen. That renders too faint at widget size; 1.1pt reads like the mockup.
const ICON_SIZE = 16;
const ICON_STROKE = 1.1;

const ICON_SUNRISE = [
  { line: [3, 18, 21, 18] },
  { arc: [12, 18, 6, 180, 360] },  // M6 18 a6 6 0 0 1 12 0
  { line: [12, 9, 12, 2] },
  { poly: [[8, 6], [12, 2], [16, 6]] },
];

const ICON_SUNSET = [
  { line: [3, 18, 21, 18] },
  { arc: [12, 18, 6, 180, 360] },
  { line: [12, 2, 12, 9] },
  { poly: [[8, 5], [12, 9], [16, 5]] },
];

const ICON_DROPLET = [
  // M12 3 s7 7.5 7 12  a7 7 0 0 1 -14 0  c0 -4.5 7 -12 7 -12 z
  { curve: [12, 3, 12, 3, 19, 10.5, 19, 15] },
  { arc: [12, 15, 7, 0, 180] },
  { curve: [5, 15, 5, 10.5, 12, 3, 12, 3] },
];

const ICON_WIND = [
  { line: [3, 8, 15, 8] },
  { arc: [15, 5, 3, 90, -180] },    // a3 3 0 1 0 -3 -3
  { line: [3, 12.5, 18, 12.5] },
  { arc: [18, 15.5, 3, -90, 180] }, // a3 3 0 1 1 -3 3
  { line: [3, 17, 12, 17] },
];

// Needle drawn pointing up (north) at rotation 0; drawWidget rotates it by the
// wind bearing so it agrees with the cardinal label beside it.
const ICON_COMPASS = [
  { arc: [12, 12, 9, 0, 360] },
  { line: [12, 12, 12, 5] },
  { poly: [[9, 8], [12, 5], [15, 8]] },
  { disc: [12, 12, 1] },
];

const ICON_GAUGE = [
  { arc: [12, 13, 8, 0, 360] },
  { line: [12, 13, 15.5, 9.5] },
  { line: [12, 6.5, 12, 7.5] },
  { line: [5.5, 13, 6.5, 13] },
];

const ICON_SUN = [
  { arc: [12, 12, 4, 0, 360] },
  { line: [12, 2, 12, 5] },
  { line: [12, 19, 12, 22] },
  { line: [2, 12, 5, 12] },
  { line: [19, 12, 22, 12] },
  { line: [4.9, 4.9, 7, 7] },
  { line: [17, 17, 19.1, 19.1] },
  { line: [4.9, 19.1, 7, 17] },
  { line: [17, 7, 19.1, 4.9] },
];

const ICON_RAIN = [
  // M7 15 a4 4 0 0 1 .5-7.9 A5.5 5.5 0 0 1 18 9.5 A3.5 3.5 0 0 1 17.5 16 H7 z
  { arc: [7.828, 11.087, 4, 101.95, 265.3] },
  { arc: [12.502, 9.386, 5.5, 204.56, 361.19] },
  { arc: [16.479, 12.652, 3.5, 295.76, 433.0] },
  { line: [17.5, 16, 7, 15] },
  { line: [9, 19, 9, 21] },
  { line: [13, 19, 13, 21] },
];

// Rotate every point of an icon's ops about (cx, cy) in viewBox space. An arc
// centred ON the pivot only needs its angles shifted; any other arc would need
// its centre moved too — which is why this is used only on the compass, whose
// arc IS the pivot-centred outer ring.
function rotateIcon(ops, deg, cx = 12, cy = 12) {
  const a = deg * DEG, ca = Math.cos(a), sa = Math.sin(a);
  const rp = (x, y) => [cx + (x - cx) * ca - (y - cy) * sa, cy + (x - cx) * sa + (y - cy) * ca];
  return ops.map(op => {
    if (op.line) { const [x1, y1, x2, y2] = op.line; return { line: [...rp(x1, y1), ...rp(x2, y2)] }; }
    if (op.poly) return { poly: op.poly.map(([x, y]) => rp(x, y)) };
    if (op.arc) { const [ax, ay, r, a0, a1] = op.arc; return { arc: [ax, ay, r, a0 + deg, a1 + deg] }; }
    if (op.curve) {
      const c = op.curve, out = [];
      for (let i = 0; i < 8; i += 2) out.push(...rp(c[i], c[i + 1]));
      return { curve: out };
    }
    return op; // disc sits on the pivot
  });
}

// Draw one 24x24-viewBox icon with its top-left at (x, y), rendered `size` pt
// square, all strokes in `hex`.
function drawIcon(dc, ops, x, y, size, hex, lineWidth) {
  const k = size / 24;
  const P = (vx, vy) => new Point(x + vx * k, y + vy * k);

  for (const op of ops) {
    if (op.disc) {
      const [cx, cy, r] = op.disc;
      const dot = new Path();
      dot.addEllipse(new Rect(x + (cx - r) * k, y + (cy - r) * k, 2 * r * k, 2 * r * k));
      dc.addPath(dot);
      dc.setFillColor(new Color(hex));
      dc.fillPath();
      continue;
    }
    const path = new Path();
    if (op.line) {
      const [x1, y1, x2, y2] = op.line;
      path.move(P(x1, y1));
      path.addLine(P(x2, y2));
    } else if (op.poly) {
      path.move(P(op.poly[0][0], op.poly[0][1]));
      op.poly.slice(1).forEach(([px, py]) => path.addLine(P(px, py)));
    } else if (op.curve) {
      const [x0, y0, c1x, c1y, c2x, c2y, x1, y1] = op.curve;
      path.move(P(x0, y0));
      path.addCurve(P(x1, y1), P(c1x, c1y), P(c2x, c2y));
    } else if (op.arc) {
      // Path has no arc primitive, so flatten to a polyline — ~10deg per
      // segment is indistinguishable from a curve at 16pt.
      const [cx, cy, r, a0, a1] = op.arc;
      const steps = Math.max(8, Math.ceil(Math.abs(a1 - a0) / 10));
      for (let i = 0; i <= steps; i++) {
        const a = (a0 + (a1 - a0) * (i / steps)) * DEG;
        const p = P(cx + Math.cos(a) * r, cy + Math.sin(a) * r);
        if (i === 0) path.move(p); else path.addLine(p);
      }
    }
    dc.addPath(path);
    dc.setStrokeColor(new Color(hex));
    dc.setLineWidth(lineWidth);
    dc.strokePath();
  }
}

// ---- the widget layout ----------------------------------------------------

function drawWidget(dc, W, H, { latest, today }) {
  // 1:1 with docs/widget_mockup/Main.dc.html at 364x170pt:
  //   card padding 16pt vertical / 18pt horizontal
  //   left column 92pt wide, gap 14, 1pt divider, gap 14, then the 3x2 grid
  //   left column stack: 40pt temp + "TEMP" label, sunrise row, sunset row
  //   grid cell stack:   16pt icon, 13pt value, 8pt label (47pt tall)
  // The mockup's flex/grid centering is resolved here into fixed design-pt
  // tops — taken from the rendered boxes of Main.dc.html itself, not re-derived
  // — so nothing can reflow into an overlap at an unexpected widget size.
  const s = W / DESIGN_W;
  const D = v => v * s; // design-pt -> this widget's pt

  // Full-bleed, NO corner radius of our own: iOS masks the widget's corners
  // itself. Rounding here too leaves the corners transparent, so the widget's
  // backgroundColor shows through as dark wedges at each corner.
  fillRoundedRect(dc, 0, 0, W, H, COLOR_BG, 0);

  // The mockup's 1px card border, drawn just inside the edge rather than as a
  // CSS border. Radius 20 matches the mockup; iOS's own mask is a little
  // larger, so the 1.5pt inset keeps the arcs from being clipped away.
  const borderPath = new Path();
  borderPath.addRoundedRect(new Rect(D(1.5), D(1.5), W - D(3), H - D(3)), D(20), D(20));
  dc.addPath(borderPath);
  dc.setStrokeColor(new Color(COLOR_HAIRLINE));
  dc.setLineWidth(Math.max(1, D(1)));
  dc.strokePath();

  const iconStroke = Math.max(0.8, D(ICON_STROKE));

  // ---- left column -------------------------------------------------------
  const LX = 18;
  // 40pt text in a 44pt rect so the rect's centre lands on the mockup's own
  // 40pt line box (y 22..62) without risking a clipped glyph.
  drawText(dc, fmt(latest.temp_c, v => `${v.toFixed(0)}°C`), D(LX), D(20), D(92), D(44),
    COLOR_ACCENT, D(40), 'heavy');
  drawText(dc, 'TEMP', D(LX), D(63), D(92), D(11), COLOR_LABEL, D(8), 'semibold');

  const sun = computeSunTimes(STATION_LAT, STATION_LON, new Date());
  const sunRow = (top, ops, value, label) => {
    // the 16pt icon is vertically centred against the 26pt value+label stack
    drawIcon(dc, ops, D(LX), D(top + 5), D(ICON_SIZE), COLOR_TEXT, iconStroke);
    const tx = D(LX + ICON_SIZE + 6);
    drawText(dc, value, tx, D(top), D(60), D(15), COLOR_TEXT, D(11), 'bold');
    drawText(dc, label, tx, D(top + 15), D(60), D(11), COLOR_LABEL, D(8), 'semibold');
  };
  sunRow(84, ICON_SUNRISE, sun.sunrise, 'SUNRISE');
  sunRow(120, ICON_SUNSET, sun.sunset, 'SUNSET');

  // ---- divider -----------------------------------------------------------
  fillRoundedRect(dc, D(124), D(16), Math.max(1, D(1)), D(136), COLOR_HAIRLINE, 0);

  // ---- 3x2 grid ----------------------------------------------------------
  // grid box measured off the mockup (its 1pt card border eats 2pt of width):
  // x 139, width 205, two 64pt rows whose 47pt content stacks sit centred at
  // y 23 and y 95.
  const GRID_X = 139, GRID_W = 205, COL_GAP = 10;
  const COL_W = (GRID_W - 2 * COL_GAP) / 3;
  const ROW_TOP = [23, 95];

  const dir = latest.wind_dir_deg;
  const rain = rainTotalToday(today);

  const cells = [
    { ops: ICON_DROPLET, value: fmt(latest.humidity, v => `${v.toFixed(0)}%`), label: 'HUMIDITY' },
    { ops: ICON_WIND, value: fmt(latest.wind_kmh, v => `${v.toFixed(0)} km/h`), label: 'WIND' },
    { ops: has(dir) ? rotateIcon(ICON_COMPASS, Number(dir)) : ICON_COMPASS,
      value: has(dir) ? cardinal(Number(dir)) : '--', label: 'DIRECTION' },
    { ops: ICON_GAUGE, value: fmt(latest.pressure_pa, v => `${(v / 100).toFixed(0)} hPa`), label: 'PRESSURE' },
    { ops: ICON_SUN, value: fmt(latest.light, fmtLight), label: 'LIGHT' },
    { ops: ICON_RAIN, value: fmt(rain, v => `${v.toFixed(1)} mm`), label: 'RAIN' },
  ];

  cells.forEach((cell, i) => {
    const x = GRID_X + (i % 3) * (COL_W + COL_GAP);
    const y = ROW_TOP[Math.floor(i / 3)];
    drawIcon(dc, cell.ops, D(x), D(y), D(ICON_SIZE), COLOR_TEXT, iconStroke);
    // text rect runs one gap wider than the column so a long value ("14 km/h")
    // can bleed into the gutter instead of being truncated
    drawText(dc, cell.value, D(x), D(y + 19), D(COL_W + COL_GAP), D(17), COLOR_TEXT, D(13), 'bold');
    drawText(dc, cell.label, D(x), D(y + 39), D(COL_W + COL_GAP), D(11), COLOR_LABEL, D(8), 'semibold');
  });
}

// ---- build the widget image -------------------------------------------

async function createWidgetImage(payload) {
  const [W, H] = WIDGET_SIZE;
  const dc = new DrawContext();
  dc.size = new Size(W, H);
  dc.opaque = false;
  dc.respectScreenScale = true;
  drawWidget(dc, W, H, payload);
  return dc.getImage();
}

async function createWidget() {
  const { data, live, error } = await loadData();
  const widget = new ListWidget();
  // backgroundImage, not addImage: a ListWidget applies its own default
  // padding (~11-16pt) to its CONTENT, so an added image is inset on all four
  // sides and the widget's backgroundColor shows through as a border — the
  // black frame around the card. backgroundImage bypasses the content area and
  // fills the whole widget edge to edge. setPadding(0,...) additionally lets
  // the not-in-widget fallback text sit flush.
  widget.backgroundColor = new Color(COLOR_BG);
  widget.backgroundImage = await createWidgetImage(data);
  widget.setPadding(0, 0, 0, 0);
  if (!config.runsInWidget && !live) {
    // the image is now the BACKGROUND, so this text overlays it; push it to
    // the bottom edge instead of floating over the temp.
    widget.addSpacer();
    const warn = widget.addText(`⚠️ dummy data — ${error}`);
    warn.font = Font.systemFont(10);
    warn.textColor = new Color('#FF9999');
  }
  return widget;
}

const widget = await createWidget();

if (config.runsInWidget) {
  Script.setWidget(widget);
} else {
  await widget.presentMedium();
}
Script.complete();
