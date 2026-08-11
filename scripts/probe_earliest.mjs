// probe_earliest.mjs — determine the REAL earliest available Dukascopy date for
// each of the six basket indices, per side (bid and ask), empirically.
//
// WHY DAILY: an h1 request pulls one binary per hour of the window (~48 fetches
// for a 2-day probe), which is what made the 15-year h1 pull time out. Daily
// candles come from a single per-instrument file, so one request covers 2000-2018.
// Availability is a property of the instrument's archive start, not the
// resolution, so d1 answers "how far back" cheaply. Pass B then CONFIRMS the
// discovered start at h1 on a narrow window, because h1 is what we actually trade.
//
// Retries are OFF by design: a missing archive should return fast and empty, not
// be retried. Network faults are distinguished from no-data by the error path.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { getHistoricalRates } from './duka_lib.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.dirname(__dirname);
const OUT = path.join(REPO, 'data', 'raw', 'earliest_probe');
fs.mkdirSync(OUT, { recursive: true });

const INSTR = {
  usatechidxusd: 'NAS100',
  usa30idxusd:   'US30',
  usa500idxusd:  'SPX500',
  deuidxeur:     'GER40',
  gbridxgbp:     'UK100',
  jpnidxjpy:     'JP225',
};
const SIDES = ['bid', 'ask'];

const iso = (ms) => new Date(ms).toISOString().slice(0, 10);

async function withTimeout(p, ms, label) {
  let t;
  const timer = new Promise((_, rej) => { t = setTimeout(() => rej(new Error(`timeout ${label}`)), ms); });
  try { return await Promise.race([p, timer]); } finally { clearTimeout(t); }
}

// PASS A — one daily request per (instrument, side) covering 2000-2018.
async function passA() {
  const rows = [];
  for (const [id, name] of Object.entries(INSTR)) {
    for (const side of SIDES) {
      const cache = path.join(OUT, `A-${id}-${side}.json`);
      let arr;
      if (fs.existsSync(cache)) {
        arr = JSON.parse(fs.readFileSync(cache, 'utf8'));
      } else {
        try {
          const r = await withTimeout(getHistoricalRates({
            instrument: id, dates: { from: new Date('2000-01-01'), to: new Date('2018-01-01') },
            timeframe: 'd1', priceType: side, format: 'json', utcOffset: 0, volumes: true,
            retryCount: 0, batchSize: 10, pauseBetweenBatches: 200,
          }), 180000, `${id} ${side}`);
          arr = Array.isArray(r) ? r : [];
          fs.writeFileSync(cache, JSON.stringify(arr));
        } catch (e) {
          console.log(`  ERROR ${name} ${side}: ${e.message}`);
          rows.push({ name, id, side, status: 'ERROR', first: null, n: 0 });
          continue;
        }
      }
      const nz = arr.filter(b => b && b.close != null && b.close > 0);
      const first = nz.length ? iso(nz[0].timestamp) : null;
      const last = nz.length ? iso(nz[nz.length - 1].timestamp) : null;
      rows.push({ name, id, side, status: nz.length ? 'OK' : 'EMPTY', first, last, n: nz.length });
      console.log(`  ${name.padEnd(7)} ${side}  n=${String(nz.length).padStart(5)}  first=${first}  last=${last}`);
    }
  }
  return rows;
}

console.log('PASS A — daily archive start, 2000-01-01 -> 2018-01-01, per instrument per side');
const rowsA = await passA();
fs.writeFileSync(path.join(OUT, 'passA.json'), JSON.stringify(rowsA, null, 2));

console.log('\nSUMMARY (earliest usable = later of bid/ask, since spread needs both)');
const byName = {};
for (const r of rowsA) (byName[r.name] ||= {})[r.side] = r;
for (const [name, o] of Object.entries(byName)) {
  const b = o.bid?.first, a = o.ask?.first;
  const usable = (b && a) ? (b > a ? b : a) : null;
  console.log(`  ${name.padEnd(7)} bid_from=${b ?? 'NONE'}  ask_from=${a ?? 'NONE'}  -> spread-usable from ${usable ?? 'N/A'}`);
}
