"""
probe_crypto_endpoints.py -- establish, EMPIRICALLY, what free crypto derivatives
data is actually obtainable and HOW FAR BACK. Nothing here is assumed from docs.

Rule carried from the Dukascopy work (STATE_OF_PLAY 6/9.5): archive availability
is PROBED per endpoint, never taken on trust from metadata.
"""
import json, sys, time
import requests

TIMEOUT = 20
S = requests.Session()
S.headers.update({"User-Agent": "research-probe/1.0"})

def get(url, params=None, tag=""):
    try:
        r = S.get(url, params=params or {}, timeout=TIMEOUT)
        if r.status_code != 200:
            return None, f"HTTP {r.status_code}: {r.text[:160]}"
        return r.json(), None
    except Exception as e:
        return None, f"{e.__class__.__name__}: {e}"

def ms(s):
    import datetime as dt
    return int(dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc).timestamp()*1000)

def show(label, data, err, fmt=None):
    if err:
        print(f"  [FAIL] {label}: {err}")
        return False
    n = len(data) if isinstance(data, list) else 1
    print(f"  [ OK ] {label}: n={n}")
    if isinstance(data, list) and data:
        print(f"         first={json.dumps(data[0])[:220]}")
    return True

FAPI = "https://fapi.binance.com"
SPOT = "https://api.binance.com"
BYBIT = "https://api.bybit.com"

print("="*78); print("BINANCE USD-M FUTURES"); print("="*78)

print("\n1. futures klines (12 fields incl taker-buy vol + trade count) -- 2019 probe")
d,e = get(f"{FAPI}/fapi/v1/klines", {"symbol":"BTCUSDT","interval":"1h","startTime":ms("2019-09-08"),"limit":3})
show("fapi klines 2019-09-08", d, e)

print("\n2. funding rate history depth")
for start in ["2019-09-01","2020-01-01"]:
    d,e = get(f"{FAPI}/fapi/v1/fundingRate", {"symbol":"BTCUSDT","startTime":ms(start),"limit":3})
    show(f"fundingRate from {start}", d, e)

print("\n3. premium index klines (perp basis vs index) depth")
for start in ["2019-09-08","2020-01-01","2021-01-01"]:
    d,e = get(f"{FAPI}/fapi/v1/premiumIndexKlines", {"symbol":"BTCUSDT","interval":"1h","startTime":ms(start),"limit":3})
    show(f"premiumIndexKlines from {start}", d, e)

print("\n4. open interest history depth (docs say 30d retention -- verify)")
for start in ["2020-01-01","2024-01-01","2026-07-01","2026-08-01"]:
    d,e = get(f"{FAPI}/futures/data/openInterestHist", {"symbol":"BTCUSDT","period":"1h","startTime":ms(start),"limit":3})
    show(f"openInterestHist from {start}", d, e)

print("\n5. long/short ratios depth")
for ep in ["globalLongShortAccountRatio","topLongShortAccountRatio","topLongShortPositionRatio","takerlongshortRatio"]:
    for start in ["2021-01-01","2026-07-01","2026-08-01"]:
        d,e = get(f"{FAPI}/futures/data/{ep}", {"symbol":"BTCUSDT","period":"1h","startTime":ms(start),"limit":2})
        show(f"{ep} from {start}", d, e)

print("\n6. liquidations")
d,e = get(f"{FAPI}/fapi/v1/allForceOrders", {"symbol":"BTCUSDT","limit":3})
show("allForceOrders", d, e)

print("\n7. spot klines depth (BTC 2017)")
d,e = get(f"{SPOT}/api/v3/klines", {"symbol":"BTCUSDT","interval":"1h","startTime":ms("2017-08-17"),"limit":3})
show("spot klines 2017-08-17", d, e)

print("\n" + "="*78); print("BYBIT V5"); print("="*78)
print("\n8. bybit open interest depth")
for start in ["2021-01-01","2023-01-01","2024-01-01","2025-01-01"]:
    d,e = get(f"{BYBIT}/v5/market/open-interest",
              {"category":"linear","symbol":"BTCUSDT","intervalTime":"1h","startTime":ms(start),"endTime":ms(start)+86400000*3,"limit":3})
    if e: print(f"  [FAIL] bybit OI {start}: {e}")
    else:
        lst = (d.get("result") or {}).get("list") or []
        print(f"  [ {'OK ' if lst else 'EMPTY'}] bybit OI from {start}: n={len(lst)} retCode={d.get('retCode')} first={json.dumps(lst[0]) if lst else '-'}")

print("\n9. bybit funding depth")
for start in ["2020-01-01","2021-01-01"]:
    d,e = get(f"{BYBIT}/v5/market/funding/history",
              {"category":"linear","symbol":"BTCUSDT","startTime":ms(start),"endTime":ms(start)+86400000*5,"limit":3})
    if e: print(f"  [FAIL] bybit funding {start}: {e}")
    else:
        lst = (d.get("result") or {}).get("list") or []
        print(f"  [ {'OK ' if lst else 'EMPTY'}] bybit funding from {start}: n={len(lst)} first={json.dumps(lst[0]) if lst else '-'}")

print("\n10. bybit long/short ratio depth")
for start in ["2023-01-01","2025-01-01","2026-08-01"]:
    d,e = get(f"{BYBIT}/v5/market/account-ratio",
              {"category":"linear","symbol":"BTCUSDT","period":"1h","startTime":ms(start),"endTime":ms(start)+86400000*3,"limit":3})
    if e: print(f"  [FAIL] bybit LSR {start}: {e}")
    else:
        lst = (d.get("result") or {}).get("list") or []
        print(f"  [ {'OK ' if lst else 'EMPTY'}] bybit account-ratio from {start}: n={len(lst)} retCode={d.get('retCode')} msg={d.get('retMsg')} first={json.dumps(lst[0]) if lst else '-'}")
