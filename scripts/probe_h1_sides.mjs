// probe_h1_sides.mjs — PASS B. Confirm, at H1 and per SIDE, the availability that
// dukascopy-node's instrumentMetaData claims. Metadata is a claim; a backtest needs
// a real bid AND a real ask (the spread is the cost model), and the prior session
// found GER40's ask missing for years its bid was present. So probe both sides.
//
// Narrow 1-day windows, retries OFF: a missing archive must return fast and empty
// rather than being retried. Distinguishes NO-DATA (empty array) from FAULT (throw).
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { getHistoricalRates } from './duka_lib.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.dirname(__dirname);
const OUT = path.join(REPO, 'data', 'raw', 'earliest_probe');
fs.mkdirSync(OUT, { recursive: true });

// Each probe: [instrumentId, label, YYYY-MM-DD midweek day, why we are asking]
const PROBES = [
  ['usatechidxusd', 'NAS100', '2011-10-05', 'claimed H1 start 2011-09-18'],
  ['usa500idxusd',  'SPX500', '2011-10-05', 'claimed H1 start 2011-09-18'],
  ['gbridxgbp',     'UK100',  '2011-10-05', 'claimed H1 start 2011-09-18'],
  ['jpnidxjpy',     'JP225',  '2011-10-05', 'claimed H1 start 2011-09-18'],
  ['usa30idxusd',   'US30',   '2011-10-05', 'expected NO DATA (claimed start 2013-09-30)'],
  ['deuidxeur',     'GER40',  '2011-10-05', 'expected NO DATA (claimed start 2013-09-30)'],
  ['usa30idxusd',   'US30',   '2013-10-02', 'claimed H1 start 2013-09-30'],
  ['deuidxeur',     'GER40',  '2013-10-02', 'claimed H1 start 2013-09-30 — ask suspect'],
  ['deuidxeur',     'GER40',  '2014-06-11', 're-verify: cached ask was EMPTY for 2014'],
  ['deuidxeur',     'GER40',  '2015-06-10', 'control: ask known present from 2015'],
  ['usatechidxusd', 'NAS100', '2012-06-13', 'ask depth check in the 2012 extension zone'],
  ['usa500idxusd',  'SPX500', '2012-06-13', 'ask depth check in the 2012 extension zone'],
  ['gbridxgbp',     'UK100',  '2012-06-13', 'ask depth check in the 2012 extension zone'],
  ['jpnidxjpy',     'JP225',  '2012-06-13', 'ask depth check in the 2012 extension zone'],
];

async function withTimeout(p, ms, label) {
  let t;
  const timer = new Promise((_, rej) => { t = setTimeout(() => rej(new Error(`timeout ${label}`)), ms); });
  try { return await Promise.race([p, timer]); } finally { clearTimeout(t); }
}

async function probe(id, day, side) {
  const cache = path.join(OUT, `B-${id}-${side}-${day}.json`);
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
  } catch (e) {
    return { __error: e.message };
  }
}

const results = [];
console.log(`${'index'.padEnd(7)} ${'day'.padEnd(11)} ${'bid'.padEnd(22)} ${'ask'.padEnd(22)} note`);
console.log('-'.repeat(100));
for (const [id, name, day, why] of PROBES) {
  const bid = await probe(id, day, 'bid');
  const ask = await probe(id, day, 'ask');
  const fmt = (a) => a.__error ? `FAULT ${a.__error.slice(0, 14)}`
    : (a.length ? `${a.length} bars @${a[0].close}` : 'NO DATA');
  const ok = !bid.__error && !ask.__error && bid.length > 0 && ask.length > 0;
  results.push({ name, id, day, why, bid: fmt(bid), ask: fmt(ask), spreadable: ok });
  console.log(`${name.padEnd(7)} ${day.padEnd(11)} ${fmt(bid).padEnd(22)} ${fmt(ask).padEnd(22)} ${why}`);
}
fs.writeFileSync(path.join(OUT, 'passB.json'), JSON.stringify(results, null, 2));
console.log('\nSpread-usable (real bid AND real ask) at each probed date:');
for (const r of results) console.log(`  ${r.name.padEnd(7)} ${r.day}  ${r.spreadable ? 'YES' : 'NO'}`);
