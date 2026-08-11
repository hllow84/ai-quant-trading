// download_pre2018.mjs — pull pre-2018 H1 bid+ask for the six basket indices and
// write files in the SAME schema as the 2018-2025 files, so the basket runner
// works unchanged. Uses scripts/duka_lib.mjs, which installs a custom undici DNS
// dispatcher (resolve via 8.8.8.8) because this host's OS resolver returns
// black-holed geo-DNS IPs for datafeed.dukascopy.com while public DNS returns a
// reachable one. Without that fix dukascopy-node fails with "fetch failed".
//
// Resumable: per (instrument, side, year) JSON cache in data/raw/pre2018_tmp.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { getHistoricalRates } from './duka_lib.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.dirname(__dirname);
const TMP = path.join(REPO, 'data', 'raw', 'pre2018_tmp');
fs.mkdirSync(TMP, { recursive: true });

// id -> [outputName, priceLo, priceHi]  (bands identical in spirit to merge_basket.py)
const INSTR = {
  usatechidxusd: ['NAS100', 2000, 30000],
  usa30idxusd:   ['US30',   10000, 50000],
  usa500idxusd:  ['SPX500', 1000,  9000],
  deuidxeur:     ['GER40',  6000, 30000],
  gbridxgbp:     ['UK100',  4000, 12000],
  jpnidxjpy:     ['JP225',  8000, 60000],
};
// 2013 starts 2013-09-30 for US30/GER40 (the binding constraint), earlier for the
// rest; request all six from the common start so the basket membership is uniform.
const START = '2013-09-30';
const YEARS = [2013, 2014, 2015, 2016, 2017];

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

async function fetchYear(inst, side, year) {
  const cache = path.join(TMP, `${inst}-${side}-${year}.json`);
  if (fs.existsSync(cache)) {
    const arr = JSON.parse(fs.readFileSync(cache, 'utf8'));
    return arr;
  }
  const from = year === 2013 ? new Date(START) : new Date(`${year}-01-01`);
  const to = new Date(`${year + 1}-01-01`);
  let lastErr;
  for (let attempt = 1; attempt <= 6; attempt++) {
    try {
      const r = await getHistoricalRates({
        instrument: inst, dates: { from, to }, timeframe: 'h1',
        priceType: side, format: 'json', utcOffset: 0, volumes: true,
        batchSize: 10, pauseBetweenBatches: 500,
      });
      // With DNS fixed, a genuinely reachable server that returns nothing means
      // that instrument/side simply has no data for this window (typical for the
      // partial 2013 start year on some instruments). Treat as no-data, not a
      // network failure: cache [] so re-runs skip it, and let the full-year gate
      // in buildInstrument decide whether the GAP is acceptable.
      const arr = Array.isArray(r) ? r : [];
      fs.writeFileSync(cache, JSON.stringify(arr));
      return arr;
    } catch (e) {
      lastErr = e;
      process.stdout.write(`  retry ${inst} ${side} ${year} (attempt ${attempt}: ${e.message})\n`);
      await sleep(3000 * attempt);
    }
  }
  throw new Error(`FAILED ${inst} ${side} ${year}: ${lastErr && lastErr.message}`);
}

function fmtDt(ms) {
  // "YYYY-MM-DD HH:MM:SS+00:00" to match the existing files exactly.
  return new Date(ms).toISOString().replace('T', ' ').replace(/\.\d{3}Z$/, '+00:00');
}

async function buildInstrument(inst) {
  const [name, lo, hi] = INSTR[inst];
  const out = path.join(REPO, 'data', `${name}_H1_2013_2017_cfd_dukascopy.csv`);
  if (fs.existsSync(out)) { console.log(`SKIP ${name} (exists)`); return; }

  const bidByTs = new Map(), askByTs = new Map();
  for (const y of YEARS) {
    for (const b of await fetchYear(inst, 'bid', y)) bidByTs.set(b.timestamp, b);
    for (const a of await fetchYear(inst, 'ask', y)) askByTs.set(a.timestamp, a);
  }
  const rows = [];
  for (const [ts, b] of bidByTs) {
    const a = askByTs.get(ts);
    if (!a) continue; // inner join on timestamp
    const spread = Math.round((a.close - b.close) * 1e4) / 1e4;
    rows.push([
      ts, fmtDt(ts),
      b.open, b.high, b.low, b.close,
      a.open, a.high, a.low, a.close,
      spread, (b.volume ?? 0),
    ]);
  }
  rows.sort((x, y) => x[0] - y[0]);

  // sanity gate before writing
  const closes = rows.map(r => r[5]);
  const pxLo = Math.min(...closes), pxHi = Math.max(...closes);
  const firstDt = rows[0][1], lastDt = rows[rows.length - 1][1];
  const perYear = {};
  for (const r of rows) { const y = r[1].slice(0, 4); perYear[y] = (perYear[y] || 0) + 1; }
  const negSpread = rows.filter(r => r[10] < 0).length;

  // HARD GATE: every full year 2014-2017 must have real coverage. A missing or
  // stub year is the exact failure that once let a file NAMED 2018_2025 hold only
  // two years. Index H1 is market-hours-only (~3000-6000 bars/yr); 2000 is a safe
  // floor that still catches a dropped year. 2013 is a partial warmup year, exempt.
  const shortYears = [2014, 2015, 2016, 2017].filter(y => (perYear[String(y)] || 0) < 2000);
  if (shortYears.length) {
    throw new Error(`${name}: full-year coverage gate FAILED for ${shortYears.join(',')} `
      + `(perYear=${JSON.stringify(perYear)}). Not writing ${name}.`);
  }
  if (!(pxLo >= lo && pxHi <= hi)) {
    throw new Error(`${name}: price ${pxLo}..${pxHi} outside band ${lo}-${hi}. Not writing.`);
  }
  if (negSpread > rows.length * 0.001) {
    throw new Error(`${name}: ${negSpread} negative spreads (>0.1%). Not writing.`);
  }

  const header = 'timestamp,datetime_utc,bid_open,bid_high,bid_low,bid_close,ask_open,ask_high,ask_low,ask_close,spread,volume\n';
  const body = rows.map(r => r.join(',')).join('\n') + '\n';
  fs.writeFileSync(out, header + body);

  const band = (pxLo >= lo && pxHi <= hi) ? 'OK in band' : `WARNING out of band ${lo}-${hi}`;
  console.log(`${name}: ${rows.length} bars  ${firstDt} -> ${lastDt}  px ${pxLo.toFixed(1)}..${pxHi.toFixed(1)} [${band}]  negSpread=${negSpread}  perYear=${JSON.stringify(perYear)}`);
}

const failures = [];
for (const inst of Object.keys(INSTR)) {
  try {
    await buildInstrument(inst);
  } catch (e) {
    console.log(`SKIP ${INSTR[inst][0]} — ${e.message}`);
    failures.push(INSTR[inst][0]);
  }
}
console.log(`DONE. failures=[${failures.join(', ')}]`);
