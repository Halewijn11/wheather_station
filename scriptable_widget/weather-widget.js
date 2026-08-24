// Weather Station — iPhone home-screen widget (Scriptable).
// Resolves ticket #110 (part of map #106 "iPhone Weather Widget").
//
// Layout: mirrors the iOS weather-app reference — "Weather Station" +
// big "now" temp top-left, wind badge (arrow + cardinal origin + speed)
// top-right, ONE combined chart (temp line + rain bars) with hour labels
// along the bottom. Light is deliberately not shown: the primary view is
// temp + rain + wind.
//
// Temperature is drawn at FULL resolution (every sample of today's series);
// dots, temp labels, rain bars, rain values and hour labels sit on 6
// four-hourly marks so the widget stays readable at widget size.
//
// Pulls live data from the doGet endpoint built in ticket #109. Falls back
// to seeded dummy data if the fetch fails (e.g. no network) so the widget
// still renders.
//
// HOW TO RUN THIS ON YOUR PHONE (Scriptable app, first time):
//   1. Install "Scriptable" from the App Store (free).
//   2. Open it, tap "+" top-right, paste this whole file in, name it
//      "weather-widget".
//   3. Tap the ▶ Play button at the bottom — you'll see a preview alert
//      with the rendered widget image, built from your REAL sheet data.
//   4. To see it as an actual home-screen widget: long-press your home
//      screen -> "+" -> search "Scriptable" -> add it -> long-press the
//      placeholder -> Edit Widget -> Script: "weather-widget" -> family:
//      MEDIUM.

const ENDPOINT_URL = 'https://script.google.com/macros/s/AKfycbxAX62uDNNXsPZ8dtsyTaL_p5Vmear12enFtOmN2TGXjbE1U9ExJVEVDA4DyfwfA7Ba/exec';

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
// already renders at 3x on a Retina phone. Passing an already-3x-scaled size
// here meant a 9x bitmap (~3042x1422, ~17MB), which the in-app preview
// tolerates but a widget extension does not — iOS kills it and Scriptable
// reports "received timeout when running script".
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
  // Measured: this endpoint takes ~38s. doGet reads every row of the sheet
  // and runs a per-row Utilities.formatDate to filter to today, so it is slow
  // by construction; a cold start adds more. Anything under a minute here is
  // indistinguishable from a broken endpoint.
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
  if (!json || !json.today || !json.today.length) throw new Error(`HTTP ${status}: JSON had no "today" rows`);
  return json;
}

async function loadData() {
  try {
    return { data: await fetchLiveData(), live: true, error: null };
  } catch (e) {
    console.log(`live fetch failed (${e}), using dummy data`);
    return { data: buildDummyData(), live: false, error: `${e && e.message ? e.message : e}` };
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

function downsampleIdx(len, n) {
  if (len <= n) return Array.from({ length: len }, (_, i) => i);
  return Array.from({ length: n }, (_, i) => Math.round(i * (len - 1) / (n - 1)));
}

// ---- the widget layout ----------------------------------------------------

function drawWidget(dc, W, H, { latest, today }) {
  // Laid out in fixed 338x158pt "bands", then scaled to the actual W/H, so
  // every element has a disjoint vertical range and can never overlap
  // another regardless of the data's range:
  //   header         4–50pt    location + big temp (left), wind badge (right)
  //   temp line     68–104pt   full-res line + dots on the 6 marks; each
  //                            label rides above its OWN datapoint (tracking
  //                            the line, not a fixed row) -> labels 50–99pt
  //   rain bars    112–130pt   own band — never overlaps the temp line
  //   rain labels  133–144pt   "0.2" etc
  //   hour labels  145–157pt   "20:00" etc, bottom row
  const s = W / 338; // scale from design pt-space to this widget's actual pixels
  fillRoundedRect(dc, 0, 0, W, H, '#1f4e8c', 24 * s);

  drawText(dc, 'Weather Station', 16 * s, 4 * s, 200 * s, 16 * s, '#ffffff', 13 * s, 'bold');
  drawText(dc, `${latest.temp_c.toFixed(0)}°`, 16 * s, 20 * s, 140 * s, 30 * s, '#ffffff', 24 * s, 'bold');

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

  // temp is drawn at FULL resolution (every sample of today's series); rain
  // bars and all labels (temp / rain / hour) stay on the 6 four-hourly marks
  // so the widget stays readable. Both share one x-axis: sample index
  // i -> chartX + (i / (N-1)) * chartW, so the labelled dots sit exactly on
  // the high-res line.
  const N = today.length;
  const idx = downsampleIdx(N, 6);
  const tempAll = today.map(r => r.temp_c);
  const temps = idx.map(i => tempAll[i]);

  // rain_mm is a per-record delta (rain since the last ~5min report), not a
  // running total -- see payload_formatter and doPost. Reading it off just
  // the 6 sampled rows (like temps do) drops almost every record's rain, so
  // instead each bar SUMS rain_mm over its slice of the day, bucketed around
  // the same 6 marks used for temp/hour labels.
  const bucketEdges = [0];
  for (let i = 0; i < idx.length - 1; i++) bucketEdges.push(Math.round((idx[i] + idx[i + 1]) / 2));
  bucketEdges.push(N);
  const rains = idx.map((_, i) => {
    let sum = 0;
    for (let j = bucketEdges[i]; j < bucketEdges[i + 1]; j++) sum += today[j].rain_mm;
    return Math.round(sum * 10) / 10;
  });

  const chartX = 26 * s, chartW = W - 2 * chartX;
  const lineTop = 68 * s, lineH = 36 * s;
  const rainBase = 130 * s, maxBarH = 18 * s, barW = 20 * s;
  const rainLabelY = 133 * s, rainLabelH = 11 * s, hourLabelY = 145 * s, hourLabelH = 12 * s;
  const labelW = chartW / 6;
  const xOf = i => chartX + (N > 1 ? (i / (N - 1)) * chartW : chartW / 2);

  // y-scale spans the FULL series, else the high-res line would overshoot the
  // band that was sized off the 6 sampled values.
  const tMin = Math.min(...tempAll), tMax = Math.max(...tempAll), tRg = tMax - tMin || 1;
  const yOf = v => lineTop + lineH - ((v - tMin) / tRg) * lineH;
  const linePts = tempAll.map((v, i) => new Point(xOf(i), yOf(v)));
  const pts = idx.map(i => new Point(xOf(i), yOf(tempAll[i])));

  const rMax = Math.max(...rains, 0.1) * 1.15;
  rains.forEach((r, i) => {
    const barH = (r / rMax) * maxBarH;
    fillRoundedRect(dc, xOf(idx[i]) - barW / 2, rainBase - barH, barW, barH, '#4FC3F773', 4 * s);
  });

  const linePath = new Path();
  linePath.move(linePts[0]);
  linePts.slice(1).forEach(p => linePath.addLine(p));
  dc.addPath(linePath);
  dc.setStrokeColor(new Color('#FFC94A'));
  dc.setLineWidth(2.5 * s);
  dc.strokePath();

  // temp label rides just above its OWN four-hourly datapoint, tracking the line
  pts.forEach((p, i) => {
    const dot = new Path();
    dot.addEllipse(new Rect(p.x - 2.5 * s, p.y - 2.5 * s, 5 * s, 5 * s));
    dc.addPath(dot);
    dc.setFillColor(new Color('#FFC94A'));
    dc.fillPath();
    drawText(dc, `${temps[i].toFixed(0)}°`, p.x - labelW / 2, p.y - 18 * s, labelW, 13 * s, '#ffffff', 11 * s, 'bold', 'center');
  });
  rains.forEach((r, i) => drawText(dc, r.toFixed(1), xOf(idx[i]) - labelW / 2, rainLabelY, labelW, rainLabelH, '#dceaff', 9 * s, 'regular', 'center'));
  idx.forEach((rowIdx, i) => {
    const d = new Date(today[rowIdx].timestamp);
    const lbl = `${String(d.getHours()).padStart(2, '0')}:00`;
    drawText(dc, lbl, xOf(rowIdx) - labelW / 2, hourLabelY, labelW, hourLabelH, '#a9c3e0', 9 * s, 'regular', 'center');
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
  widget.backgroundColor = new Color('#000000');
  const img = widget.addImage(await createWidgetImage(data));
  img.applyFillingContentMode();
  if (!config.runsInWidget && !live) {
    widget.addSpacer(4);
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
