// probe_refine.mjs — PASS C. Pin down, per instrument, the earliest date with a
// real BID AND a real ASK at H1 (i.e. the earliest date a spread-costed backtest
// can actually start). Pass B showed instrumentMetaData's claimed H1 start is
// optimistic (NAS100/SPX500/JP225 claim 2011-09-18 but return nothing at
// 2011-10-05) and that the ask archive starts LATER than the bid on GER40 and
// UK100. So the tradable start must be found empirically, per side.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { getHistoricalRates } from './duka_lib.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.dirname(__dirname);
const OUT = path.join(REPO, 'data', 'raw', 'earliest_probe');
fs.mkdirSync(OUT, { recursive: true });

const PLAN = {
  usatechidxusd: ['NAS100', ['2011-11-09', '2011-12-07', '2012-02-08', '2012-04-11']],
  usa500idxusd:  ['SPX500', ['2011-11-09', '2011-12-07', '2012-02-08', '2012-04-11']],
  jpnidxjpy:     ['JP225',  ['2011-11-09', '2011-12-07', '2012-02-08', '2012-04-11']],
  gbridxgbp:     ['UK100',  ['2012-10-10', '2013-02-13', '2013-06-12', '2013-09-11']],
};

async function withTimeout(p, ms, label) {
  let t;
  const timer = new Promise((_, rej) => { t = setTimeout(() => rej(new Error(`timeout ${label}`)), ms); });
  try { return await Promise.race([p, timer]); } finally { clearTimeout(t); }
}

async function probe(id, day, side) {
  const cache = path.join(OUT, `C-${id}-${side}-${day}.json`);
  if (fs.existsSync(cache)) return JSON.parse(fs.readFileSync(cache, 'utf8'));
  try {
    const r = await withTimeout(getHistoricalRates({
      instrument: id, dates: { from: new Date(`${day}T00:00:00Z`), to: new Date(`${day}T23:59:59Z`) },
      timeframe: 'h1', priceType: side, format: 'json', utcOffset: 0, volumes: true,
      retryCount: 0, batchSize: 12, pauseBetweenBatches: 150,
    }), 120000, `${id} ${side} ${day}`);
    const arr = Array.isArray(r) ? r : [];
    fs.writeFileSync(cache, JSON.stringify(arr));
    return arr;
  } catch (e) { return { __error: e.message }; }
}

const out = [];
console.log(`${'index'.padEnd(7)} ${'day'.padEnd(11)} ${'bid'.padEnd(12)} ${'ask'.padEnd(12)} spread-usable`);
console.log('-'.repeat(60));
for (const [id, [name, days]] of Object.entries(PLAN)) {
  for (const day of days) {
    const b = await probe(id, day, 'bid');
    const a = await probe(id, day, 'ask');
    const f = (x) => x.__error ? 'FAULT' : (x.length ? `${x.length} bars` : 'NO DATA');
    const ok = !b.__error && !a.__error && b.length > 0 && a.length > 0;
    out.push({ name, day, bid: f(b), ask: f(a), spreadable: ok });
    console.log(`${name.padEnd(7)} ${day.padEnd(11)} ${f(b).padEnd(12)} ${f(a).padEnd(12)} ${ok ? 'YES' : 'no'}`);
  }
}
fs.writeFileSync(path.join(OUT, 'passC.json'), JSON.stringify(out, null, 2));
