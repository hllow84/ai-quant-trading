# Order-book capture — $5/month VPS deployment

**Status: infrastructure prep only. Nothing is deployed and no data has been
collected yet.** This is the deployment guide for `scripts/orderbook_capture.py`
(section 30 follow-up — see STATE_OF_PLAY.md and research_log.md). The script
was smoke-tested locally (a few minutes, live Binance stream, verified below)
but was not left running: this project's working environment kills background
processes when the terminal session ends (standing rule — see
`feedback_background_tasks` memory / `CLAUDE.md`), and a laptop that sleeps or
reboots loses the connection anyway. A real capture needs an always-on host.
This doc is what to follow once that host exists.

## Why a VPS, and why $5/month is enough

The capture script is a single lightweight Python process: one websocket
connection per symbol pair of streams (`depth20@100ms` + `aggTrade`), writing
gzip-compressed JSON Lines + a small CSV. No GPU, no database server, minimal
CPU. Measured locally: ~2,200 messages/minute for BTCUSDT alone, well under
1 Mbps of bandwidth, well under 100MB of RAM. The cheapest tier at any major
VPS provider (DigitalOcean "Basic" $4-6/mo, Vultr "Cloud Compute" $5/mo,
Linode/Akamai "Nanode" $5/mo, Hetzner CX22 ~€4/mo) has enough CPU/RAM/bandwidth
headroom for this with margin. Disk is the one resource to watch — see
**Disk budget** below.

## 1. Provision the VPS

Any of the above providers, smallest tier, **Ubuntu 24.04 LTS** (or latest
LTS). Pick a region close to Binance's own infra if latency ever matters for
a later, faster signal (AWS ap-northeast-1 Tokyo hosts Binance's matching
engine; a VPS in Tokyo/Singapore will have materially lower latency than one
in the US — not required for this capture, which is not latency-sensitive,
but worth choosing since it costs nothing extra).

```bash
# from your own machine, after the VPS is created and you have its IP:
ssh root@<VPS_IP>
```

## 2. System setup

```bash
apt update && apt upgrade -y
apt install -y python3 python3-venv python3-pip git ufw

# firewall: only SSH in, this box makes only OUTBOUND connections
ufw allow OpenSSH
ufw enable

# a non-root user to run the service (never run daemons as root)
adduser --disabled-password --gecos "" capture
```

## 3. Get the code onto the box

Two options — pick whichever matches how the repo is hosted:

```bash
su - capture
git clone https://github.com/<your-org>/ai-quant-trading.git
cd ai-quant-trading/crypto-factor-lab
python3 -m venv .venv
source .venv/bin/activate
pip install websockets
```

(If the repo is private and cloning needs auth, use a deploy key or a
fine-scoped personal access token — never commit it into the repo. This is a
read-only capture box; it never needs push access.)

## 4. Smoke-test it manually first

```bash
python scripts/orderbook_capture.py --symbols btcusdt,ethusdt --out data/orderbook_capture
# Ctrl-C after ~60s once you see "connected" and an "alive: N messages ..." line
ls -la data/orderbook_capture/raw/*/         # gzip files present
ls -la data/orderbook_capture/features_1s/   # feature CSVs present
tail data/orderbook_capture/features_1s/*.csv
```

## 5. Run it as a systemd service (auto-restart, survives reboot)

```bash
exit   # back to root
cat > /etc/systemd/system/orderbook-capture.service <<'EOF'
[Unit]
Description=Order-book + trade-flow capture (BTCUSDT/ETHUSDT)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=capture
WorkingDirectory=/home/capture/ai-quant-trading/crypto-factor-lab
ExecStart=/home/capture/ai-quant-trading/crypto-factor-lab/.venv/bin/python \
    scripts/orderbook_capture.py --symbols btcusdt,ethusdt \
    --out /home/capture/ai-quant-trading/crypto-factor-lab/data/orderbook_capture
Restart=on-failure
RestartSec=10
# graceful stop -> SIGTERM -> the script's own signal handler flushes and
# closes every file cleanly (see scripts/orderbook_capture.py Writer.rotate_raw
# docstring for why a HARD kill instead would risk the last unflushed minute)
TimeoutStopSec=30
KillSignal=SIGTERM

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now orderbook-capture
systemctl status orderbook-capture
journalctl -u orderbook-capture -f      # tail live logs
```

**Important — always stop it gracefully:** `systemctl stop orderbook-capture`
(sends SIGTERM, the script flushes and closes files) or `systemctl restart`.
Never `kill -9` / `systemctl kill --signal=SIGKILL` on it deliberately — the
script already protects against an *accidental* hard kill (power loss,
OOM-kill) by rotating the raw gzip file into complete, independently-readable
members roughly every 60 seconds, but a graceful stop loses nothing at all.

## 6. Disk budget and rotation

Rough measured rate (BTCUSDT alone, smoke test): ~2,200 raw messages/minute
compress to a few hundred KB/hour. Two symbols, running continuously:

| Duration | Approx. raw (gzip) size | Approx. feature-CSV size |
|---|---|---|
| 1 day | ~15-25 MB | ~2 MB |
| 30 days | ~500-750 MB | ~60 MB |
| 1 year | ~6-9 GB | ~700 MB |

A $5/mo VPS typically ships with 25-50 GB of disk — enough for **several
months to a year** of two-symbol capture before it needs attention. Two
housekeeping options, either is fine to add once real usage is observed:

1. **Periodic offload** (recommended): a weekly cron job that `rsync`s
   `data/orderbook_capture/` back to local/cold storage and then deletes
   raw files older than N days on the VPS (keep the small feature CSVs
   indefinitely; raw JSONL is the expensive, less frequently needed part).
2. **Cheap object storage**: point the offload at a $1-2/mo object-storage
   bucket (Backblaze B2, Wasabi, or the VPS provider's own block storage)
   instead of pulling to a local machine, if the capture needs to run longer
   than this machine stays reachable.

Neither is set up yet — add it once the capture has been running long enough
to see the REAL growth rate on real, not projected, data.

## 7. Pulling data back for a backtest

```bash
# from your local machine
rsync -avz capture@<VPS_IP>:~/ai-quant-trading/crypto-factor-lab/data/orderbook_capture/features_1s/ \
    "C:/Claude Code/AI Quant Trading/crypto-factor-lab/data/orderbook_capture/features_1s/"
```

Pull the raw JSONL too (`raw/`) only when actually needed — it is far larger
and the feature CSVs are what a first backtest would use.

## 8. What NOT to do

- Do not add API keys / trading credentials to this box. It only reads
  Binance's PUBLIC market-data websocket streams — no authentication, no
  account access, nothing that could place an order. Keep it that way; this
  is a data-collection box, not an execution box.
- Do not skip the graceful-stop discipline (§5) — while the rotation fix
  bounds the damage, a clean stop loses nothing and a repeated hard-kill
  habit will eventually lose more than one rotation window.
- Do not backtest on partial/still-accumulating data and call it a result —
  per this project's own honesty standard, wait for a real, stated
  history depth before drawing any conclusion, and pre-register the
  entry threshold from the FIRST batch's distribution before evaluating
  P&L on a second, later batch (see the pre-registration note in
  `scripts/orderbook_capture.py`'s docstring, metric 5).
