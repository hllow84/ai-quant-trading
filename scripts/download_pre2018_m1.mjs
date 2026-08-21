// download_pre2018_m1.mjs — pull pre-2018 M1 bid+ask for NAS100 and US30 across
// the US cash session, in the SAME schema as the 2018-2025 M1 files, so every
// RTH-anchored runner works unchanged.
//
// WHY: STATE_OF_PLAY §7 rule 3 — "any candidate must clear the out-of-regime
// test BEFORE anything else is measured. Test 2013-2017 first, not last."  The
// repo only holds M1 from 2018-01, so no intraday strategy can be regime-tested
// until this file exists.
//
// SCOPE — RTH ONLY, AND THE FILENAME SAYS SO.
// The output is `<NAME>_M1RTH_2013_2017_cfd_dukascopy.csv`, not `_M1_`, because
// it deliberately covers only 13:00-21:00 UTC — the window that contains
// 09:30-16:00 America/New_York under BOTH EST and EDT. Two reasons, one
// principled and one practical:
//   * Principled: the pre-2018 archive quotes these CFDs only across the US cash
//     session anyway (probed 2026-08-19: ~371 bars/day in 2013, 13:30-20:00 UTC,
//     widening to 06:00-20:00 by 2016). There is little outside RTH to fetch.
//   * Practical: Dukascopy serves ONE archive file per hour, so a full-day pull
//     is 24 requests/day and rate-limits (HTTP 429) within minutes. Fetching 8
//     hours instead of 24 cuts the request count ~3x.
// Any strategy that needs overnight bars must NOT use this file.
//
// Window: 2013-09-30 -> 2018-01-01. That floor is a HARD DATA FACT established
// on 2026-08-10 (see STATE_OF_PLAY §6): the Dukascopy ASK archive starts years
// after the bid, and 2013-09-30 is the earliest date at which US30 has a usable
// spread. NAS100 could start earlier (2012-04) but is pulled from the same date
// so the two series cover an identical window.
//
// Uses scripts/duka_lib.mjs for the custom undici DNS dispatcher (resolve via
// 8.8.8.8) — without it dukascopy-node fails on this host with "fetch failed".
//
// Resumable at DAY granularity, with an on-disk archive cache, so a restart
// after a rate-limit ban re-uses everything already fetched and costs nothing.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { getHistoricalRates } from './duka_lib.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.dirname(__dirname);
const TMP = path.join(REPO, 'data', 'raw', 'pre2018_m1_tmp');
const CACHE = path.join(TMP, 'cache');
fs.mkdirSync(CACHE, { recursive: true });

// id -> [outputName, priceLo, priceHi]  (sanity bands as in download_pre2018.mjs)
const INSTR = {
  usatechidxusd: ['NAS100', 2000, 30000],
  usa30idxusd:   ['US30',   10000, 50000],
};

const START = Date.UTC(2013, 8, 30);       // 2013-09-30
const END   = Date.UTC(2018, 0, 1);        // exclusive
const DAY_MS = 86_400_000;
const RTH_FROM_H = 13;                     // 13:00 UTC — before 09:30 ET in EDT and EST
const RTH_TO_H   = 21;                     // 21:00 UTC — after  16:00 ET in EDT and EST

// Throttle. Measured 2026-08-19: batch 40 / 300 ms -> 429 within one month;
// batch 8 / 1500 ms -> still 429. M1 is one file per hour, so the limiter is
// requests-per-second, not bytes. These settings are deliberately slow.
const BATCH = 4;
const PAUSE_MS = 2000;
const DAY_GAP_MS = 700;

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

function weekdays(fromMs, toMs) {
  const out = [];
  for (let t = fromMs; t < toMs; t += DAY_MS) {
    const d = new Date(t);
    const dow = d.getUTCDay();
    if (dow === 0 || dow === 6) continue;   // no cash session; skip the requests entirely
    out.push(d);
  }
  return out;
}

async function fetchSide(inst, side, day) {
  const from = new Date(day.getTime() + RTH_FROM_H * 3600_000);
  const to   = new Date(day.getTime() + RTH_TO_H * 3600_000);
  let lastErr;
  for (let attempt = 1; attempt <= 8; attempt++) {
    try {
      const r = await getHistoricalRates({
        instrument: inst, dates: { from, to }, timeframe: 'm1',
        priceType: side, format: 'json', utcOffset: 0,
        volumes: true, volumeUnits: 'units',
        batchSize: BATCH, pauseBetweenBatchesMs: PAUSE_MS,
        retryCount: 4, retryOnEmpty: false,
        useCache: true, cacheFolderPath: CACHE,
      });
      // With DNS fixed, a reachable server returning nothing means this
      // instrument/side genuinely has NO data for the window — not a fault.
      // Distinguishing the two is the lesson of the 2026-08-10 probe work.
      return Array.isArray(r) ? r : [];
    } catch (e) {
      lastErr = e;
      // A 429 cooldown outlasts any second-scale retry, so back off in minutes.
      const wait = /429/.test(e.message || '') ? 90_000 * attempt : 5_000 * attempt;
      process.stdout.write(`  retry ${inst} ${side} ${day.toISOString().slice(0, 10)} `
        + `(attempt ${attempt}: ${e.message}) — sleeping ${Math.round(wait / 1000)}s\n`);
      await sleep(wait);
    }
  }
  throw new Error(`FAILED ${inst} ${side} ${day.toISOString().slice(0, 10)}: ${lastErr && lastErr.message}`);
}

function fmtDt(ms) {
  // "YYYY-MM-DD HH:MM:SS+00:00" — byte-identical format to the 2018-2025 files.
  return new Date(ms).toISOString().replace('T', ' ').replace(/\.\d{3}Z$/, '+00:00');
}

const HEADER = 'timestamp,datetime_utc,bid_open,bid_high,bid_low,bid_close,'
  + 'ask_open,ask_high,ask_low,ask_close,spread,volume\n';

async function buildInstrument(inst) {
  const [name] = INSTR[inst];
  const out = path.join(REPO, 'data', `${name}_M1RTH_2013_2017_cfd_dukascopy.csv`);
  if (fs.existsSync(out)) { console.log(`SKIP ${name} (output exists)`); return; }

  const part = path.join(TMP, `${name}.part.csv`);
  const stats = path.join(TMP, `${name}.stats.json`);
  const doneFile = path.join(TMP, `${name}.days.done`);
  if (!fs.existsSync(part)) fs.writeFileSync(part, HEADER);
  const st = fs.existsSync(stats)
    ? JSON.parse(fs.readFileSync(stats, 'utf8'))
    : { rows: 0, days: 0, pxLo: Infinity, pxHi: -Infinity, negSpread: 0, perYear: {}, first: null, last: null };
  // One line per completed day beats one marker FILE per day (1,100 inodes).
  const done = new Set(fs.existsSync(doneFile)
    ? fs.readFileSync(doneFile, 'utf8').split('\n').filter(Boolean) : []);

  const days = weekdays(START, END);
  let i = 0;
  for (const day of days) {
    i += 1;
    const tag = day.toISOString().slice(0, 10);
    if (done.has(tag)) continue;

    const bid = await fetchSide(inst, 'bid', day);
    const ask = await fetchSide(inst, 'ask', day);
    const askByTs = new Map(ask.map(a => [a.timestamp, a]));

    const lines = [];
    let n = 0;
    for (const b of bid) {
      const a = askByTs.get(b.timestamp);
      if (!a) continue;                       // inner join on timestamp
      const spread = Math.round((a.close - b.close) * 1e4) / 1e4;
      lines.push([b.timestamp, fmtDt(b.timestamp),
        b.open, b.high, b.low, b.close,
        a.open, a.high, a.low, a.close,
        spread, (b.volume ?? 0)].join(','));
      n += 1;
      if (b.close < st.pxLo) st.pxLo = b.close;
      if (b.close > st.pxHi) st.pxHi = b.close;
      if (spread < 0) st.negSpread += 1;
      const y = String(new Date(b.timestamp).getUTCFullYear());
      st.perYear[y] = (st.perYear[y] || 0) + 1;
      if (st.first === null || b.timestamp < st.first) st.first = b.timestamp;
      if (st.last === null || b.timestamp > st.last) st.last = b.timestamp;
    }
    if (lines.length) fs.appendFileSync(part, lines.join('\n') + '\n');
    st.rows += n;
    if (n) st.days += 1;
    fs.writeFileSync(stats, JSON.stringify(st));
    fs.appendFileSync(doneFile, tag + '\n');
    done.add(tag);
    if (i % 20 === 0 || n === 0) {
      console.log(`${name} ${tag} [${i}/${days.length}]: bid=${bid.length} ask=${ask.length} `
        + `merged=${n} (rows ${st.rows}, days ${st.days})`);
    }
    await sleep(DAY_GAP_MS);
  }

  // ── Sanity gates before the part file is promoted to a real data file ───────
  const [, lo, hi] = INSTR[inst];
  const problems = [];
  // RTH-only: a full year is ~252 x 390 = 98k bars. 55k catches a silently
  // dropped or half-empty year without failing on legitimately thin 2013.
  const shortYears = [2014, 2015, 2016, 2017].filter(y => (st.perYear[String(y)] || 0) < 55000);
  if (shortYears.length) problems.push(`thin years ${shortYears.join(',')} perYear=${JSON.stringify(st.perYear)}`);
  if (!(st.pxLo >= lo && st.pxHi <= hi)) problems.push(`price ${st.pxLo}..${st.pxHi} outside band ${lo}-${hi}`);
  if (st.negSpread > st.rows * 0.001) problems.push(`${st.negSpread} negative spreads (>0.1%)`);
  if (problems.length) throw new Error(`GATE: ${name} FAILED — ${problems.join(' | ')}. Not writing ${name}.`);

  fs.renameSync(part, out);
  console.log(`${name}: ${st.rows} bars over ${st.days} days  ${fmtDt(st.first)} -> ${fmtDt(st.last)}  `
    + `px ${st.pxLo.toFixed(1)}..${st.pxHi.toFixed(1)}  negSpread=${st.negSpread}  `
    + `perYear=${JSON.stringify(st.perYear)}  -> ${out}`);
}

// A cold start right after a 429 ban just burns the first days, so wait first if
// asked to (`node download_pre2018_m1.mjs --cooldown 600`).
const cdIdx = process.argv.indexOf('--cooldown');
if (cdIdx !== -1) {
  const secs = Number(process.argv[cdIdx + 1] || 0);
  console.log(`cooldown: sleeping ${secs}s before the first request`);
  await sleep(secs * 1000);
}

// Day markers + the on-disk cache make a restart cheap, so a failed instrument is
// retried as a whole rather than abandoned. Only a repeated failure is real.
const failures = [];
for (const inst of Object.keys(INSTR)) {
  let ok = false;
  for (let pass = 1; pass <= 5 && !ok; pass++) {
    try {
      await buildInstrument(inst);
      ok = true;
    } catch (e) {
      console.log(`PASS ${pass} failed for ${INSTR[inst][0]} — ${e.message}`);
      if (/^GATE:/.test(e.message)) break;   // a data-quality verdict, not a transient fault
      if (pass < 5) await sleep(600_000);    // 10 min before another full pass
    }
  }
  if (!ok) failures.push(INSTR[inst][0]);
}
console.log(`DONE. failures=[${failures.join(', ')}]`);
