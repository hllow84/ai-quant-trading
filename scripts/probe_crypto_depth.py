"""Second probe: find the TRUE earliest bar per series per symbol (bisection),
not the doc-claimed one. Same discipline as probe_earliest.mjs on Dukascopy."""
import datetime as dt, json, requests

S = requests.Session(); S.headers.update({"User-Agent":"research-probe/1.0"})
BYBIT="https://api.bybit.com"; FAPI="https://fapi.binance.com"
def ms(s): return int(dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc).timestamp()*1000)
def d(x): return dt.datetime.fromtimestamp(x/1000, dt.timezone.utc).strftime("%Y-%m-%d %H:%M")

def bybit_has(path, params):
    try:
        r=S.get(BYBIT+path, params=params, timeout=20)
        if r.status_code!=200: return None
        j=r.json()
        return len((j.get("result") or {}).get("list") or [])>0
    except Exception: return None

def bisect_start(test, lo="2019-01-01", hi="2026-08-01"):
    lo_ms, hi_ms = ms(lo), ms(hi)
    if test(lo_ms): return lo_ms, "<= "+lo
    if not test(hi_ms): return None, "no data even at "+hi
    while hi_ms-lo_ms > 86400000*3:
        mid=(lo_ms+hi_ms)//2
        if test(mid): hi_ms=mid
        else: lo_ms=mid
    return hi_ms, d(hi_ms)

SYMS=["BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","BNBUSDT","DOGEUSDT","ADAUSDT","LINKUSDT","AVAXUSDT","LTCUSDT"]

print("="*90); print("BYBIT open-interest 1h -- true start per symbol"); print("="*90)
for s in SYMS:
    f=lambda t,s=s: bybit_has("/v5/market/open-interest",
        {"category":"linear","symbol":s,"intervalTime":"1h","startTime":t,"endTime":t+86400000*2,"limit":5})
    _,lab=bisect_start(f); print(f"  {s:10s} OI start ~ {lab}")

print("\n"+"="*90); print("BYBIT account-ratio 1h -- true start per symbol"); print("="*90)
for s in SYMS:
    f=lambda t,s=s: bybit_has("/v5/market/account-ratio",
        {"category":"linear","symbol":s,"period":"1h","startTime":t,"endTime":t+86400000*2,"limit":5})
    _,lab=bisect_start(f); print(f"  {s:10s} LSR start ~ {lab}")

print("\n"+"="*90); print("BINANCE funding + kline true start per symbol"); print("="*90)
def bin_has_funding(t,s):
    try:
        r=S.get(FAPI+"/fapi/v1/fundingRate",params={"symbol":s,"startTime":t,"endTime":t+86400000*2,"limit":5},timeout=20)
        return r.status_code==200 and len(r.json())>0
    except Exception: return None
def bin_has_kline(t,s):
    try:
        r=S.get(FAPI+"/fapi/v1/klines",params={"symbol":s,"interval":"1h","startTime":t,"endTime":t+86400000*2,"limit":5},timeout=20)
        return r.status_code==200 and len(r.json())>0
    except Exception: return None
def bin_has_prem(t,s):
    try:
        r=S.get(FAPI+"/fapi/v1/premiumIndexKlines",params={"symbol":s,"interval":"1h","startTime":t,"endTime":t+86400000*2,"limit":5},timeout=20)
        return r.status_code==200 and len(r.json())>0
    except Exception: return None
for s in SYMS:
    _,a=bisect_start(lambda t,s=s: bin_has_kline(t,s))
    _,b=bisect_start(lambda t,s=s: bin_has_funding(t,s))
    _,c=bisect_start(lambda t,s=s: bin_has_prem(t,s))
    print(f"  {s:10s} kline {a:20s} funding {b:20s} premium {c}")

print("\n"+"="*90); print("BYBIT OI pagination / max limit check"); print("="*90)
r=S.get(BYBIT+"/v5/market/open-interest",params={"category":"linear","symbol":"BTCUSDT","intervalTime":"1h",
        "startTime":ms("2024-01-01"),"endTime":ms("2024-01-20"),"limit":200},timeout=20).json()
res=r.get("result",{}); lst=res.get("list",[])
print(f"  limit=200 -> n={len(lst)} cursor={'yes' if res.get('nextPageCursor') else 'no'}")
if lst: print(f"  newest={d(int(lst[0]['timestamp']))} oldest={d(int(lst[-1]['timestamp']))}")
