// Shared: install a working DNS dispatcher, export getHistoricalRates.
import dns from 'node:dns';
import { promises as dnsp } from 'node:dns';
import { Agent, setGlobalDispatcher } from 'undici';
dns.setServers(['8.8.8.8','1.1.1.1']);
const lookup = (hostname, opts, cb) => {
  dnsp.resolve4(hostname).then(addrs => {
    if (!addrs.length) return cb(new Error('no A record for '+hostname));
    if (opts && opts.all) cb(null, addrs.map(a=>({address:a,family:4})));
    else cb(null, addrs[0], 4);
  }).catch(cb);
};
setGlobalDispatcher(new Agent({ connect: { lookup, timeout: 25000 }, headersTimeout: 90000, bodyTimeout: 180000 }));
export { getHistoricalRates } from 'dukascopy-node';
