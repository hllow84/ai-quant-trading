//+------------------------------------------------------------------+
//| ORB_Gold_US30_VIX_RealYield_4Leg_Combined.mq5                     |
//|                                                                    |
//| v2 of ORB_Gold_RETEST_US30_Breakout_Combined.mq5 -- adds TWO new   |
//| legs (STATE_OF_PLAY.md Sec75/Sec79/Sec84/Sec89-Sec91 in the        |
//| crypto-factor-lab repo) on top of the original two, unchanged.     |
//|                                                                    |
//| LEG 1 -- ORB GOLD RETEST (XAUUSD, US cash session, M1): UNCHANGED  |
//| from v1 -- see that file's own header for the full description.   |
//|                                                                    |
//| LEG 2 -- US30 BREAKOUT-RETEST (H4, 24h continuous): UNCHANGED      |
//| from v1.                                                           |
//|                                                                    |
//| LEG 3 -- VIX SPIKE SIGNAL (Sec79/Sec83, gold): a rolling z-score   |
//|   of the VIX index level (window=120 trading days, threshold      |
//|   +/-1.25) -- VIX spiking => LONG gold (flight to safety),         |
//|   VIX unusually calm => SHORT gold. Always in a position (never   |
//|   flat) once 120 days of VIX history exist. NO STOP-LOSS, NO      |
//|   TARGET -- this is a multi-day swing position, matching exactly  |
//|   how it was backtested (a daily mark-to-market return series,    |
//|   not a stop/target trade). Data: CBOE's free public VIX History  |
//|   CSV, fetched live via WebRequest() once per UTC calendar day.   |
//|                                                                    |
//| LEG 4 -- REAL-YIELD TREND SIGNAL (Sec75/Sec82, gold): sign of the  |
//|   20-trading-day change in the 10yr TIPS real yield (FRED DFII10) |
//|   -- falling real yields => LONG gold, rising => SHORT. Also NO   |
//|   STOP-LOSS, NO TARGET, same reasoning as Leg 3. Data: FRED's free |
//|   public CSV export, fetched live via WebRequest() once per UTC   |
//|   calendar day.                                                    |
//|                                                                    |
//| WHY NO STOP ON LEGS 3/4 -- STATED EXPLICITLY, NOT AN OVERSIGHT:    |
//|   the backtest (research/run_vix_gold_joint_grid.py, research/    |
//|   run_real_yield_gold_lookback_grid.py) never modeled a stop for   |
//|   either signal -- it is a continuously-held directional position |
//|   marked to market daily. Adding a stop here would be a real,     |
//|   untested DEVIATION from what was actually backtested. This is a |
//|   genuine live-trading risk difference from Legs 1/2 (which DO    |
//|   have stops) -- an uncapped adverse gap on Legs 3/4 is possible.  |
//|   Flagged prominently in docs/mt5_ea_deployment.md; watch this     |
//|   closely on the demo.                                             |
//|                                                                    |
//| SLEEVE WEIGHTING -- A REAL, STATED SIMPLIFICATION: the backtested  |
//|   "best" result (Sec89/Sec91, 3-way book incl. Legs 1+2+the        |
//|   VIX/real-yield sleeve) used a CAUSAL ROLLING risk-parity weight  |
//|   across all three pieces, recomputed monthly from each leg's      |
//|   trailing 90-day volatility -- NOT implemented here (a real,      |
//|   bounded follow-up, same category of gap as v1's own              |
//|   RiskParity_TODO()). This EA uses FIXED weights instead           |
//|   (InpSleeveWeightPct, split 50/50 between Legs 3 and 4) chosen    |
//|   from Sec90's in-sample weight-grid finding that the sleeve's own |
//|   optimal share was small (~10%) -- an approximation, not the      |
//|   exact deployable scheme, stated here and in the deployment doc.  |
//|                                                                    |
//| STATUS: written 2026-09-18, NOT YET COMPILED OR TESTED. Legs 1/2   |
//| are the same code already compiled clean and running on the FTMO  |
//| free demo (v1, Sec69/Sec70) -- Legs 3/4 and the WebRequest/CSV     |
//| parsing plumbing are BRAND NEW, untested MQL5 code written in a    |
//| single session under real time pressure (2-3 hours before market  |
//| open). Treat this as materially higher-risk than v1 was on its own |
//| first deployment -- read docs/mt5_ea_deployment.md's v2 section    |
//| in full, including the required one-time WebRequest URL whitelist |
//| step, before attaching this to any account.                        |
//+------------------------------------------------------------------+
#property copyright "crypto-factor-lab research project"
#property strict

#include <Trade\Trade.mqh>

//====================== INPUTS =======================================

input group "=== General ==="
input int      InpTimerSeconds        = 20;         // OnTimer poll interval (seconds)
input int      InpMagicGold           = 39100;       // magic number, gold leg (Sec39)
input int      InpMagicUS30           = 45100;       // magic number, US30 leg (Sec45)
input int      InpSlippagePoints      = 50;
input bool     InpVerboseLog          = true;
input bool     InpUseNewsFilter       = true;        // FTMO: no entries within N min of high-impact US news
input int      InpNewsBufferMinutes   = 2;           // matches FTMO's stated 2-minute rule

input group "=== Leg 1: ORB Gold RETEST (Sec39) ==="
input string   InpGoldSymbol          = "XAUUSD";    // set to your broker's exact gold symbol
input double   InpGoldRiskPct         = 0.5;         // % of equity risked per gold trade
input int      InpGold_OR_Minutes     = 30;           // opening range length, minutes
input double   InpGold_RetestTolFrac  = 0.20;         // retest tolerance, fraction of OR width
input double   InpGold_StopBps        = 25.0;         // fixed stop, basis points of entry price
input double   InpGold_TargetR        = 1.0;          // target, multiples of R

input group "=== Leg 2: US30 Breakout-Retest (Sec45) ==="
input string   InpUS30Symbol          = "US30.cash";  // set to your broker's exact US30/Dow CFD symbol
input double   InpUS30RiskPct         = 0.5;          // % of equity risked per US30 trade
input int      InpUS30_Lookback       = 20;           // rolling H4 range lookback, bars
input int      InpUS30_ATR_Period     = 14;            // ATR period (SIMPLE mean, not Wilder)
input double   InpUS30_K_ATR          = 4.0;           // stop distance, multiples of ATR
input double   InpUS30_TargetR        = 0.25;          // target, multiples of R
input int      InpUS30_MaxHoldBars    = 20;            // force-flat after this many H4 bars

input group "=== Legs 3+4: VIX + Real-Yield Sleeve (Sec75/Sec79/Sec84) ==="
input bool     InpUseSleeve           = true;          // master on/off for Legs 3+4
input double   InpSleeveWeightPct     = 10.0;          // TOTAL % of equity notional across Legs 3+4 combined (Sec90's in-sample finding)
input int      InpVixWindowDays       = 120;           // VIX z-score trailing window, trading days (Sec83)
input double   InpVixThreshold        = 1.25;          // VIX z-score entry threshold (Sec83)
input int      InpRealYieldLookbackDays = 20;          // real-yield trend lookback, trading days (Sec75)
input string   InpVixUrl              = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv";
input string   InpFredUrl             = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFII10";
input int      InpWebRequestTimeoutMs = 8000;
input int      InpMagicVix            = 79100;         // magic number, VIX leg (Sec79)
input int      InpMagicRealYield      = 75100;         // magic number, real-yield leg (Sec75)

//====================== GLOBALS =======================================

CTrade trade;

// ---- Sleeve (Legs 3+4) state ----
datetime g_sleeveLastFetchDate = 0;   // UTC date (midnight) of the last successful data fetch
int      g_vixSignal           = 0;   // -1/0/+1, last computed VIX leg signal
int      g_realYieldSignal     = 0;   // -1/0/+1, last computed real-yield leg signal
bool     g_sleeveDataOk         = false;

// ---- Gold (ORB RETEST) daily state ----
datetime g_goldSessionDate   = 0;     // ET calendar date (midnight ET, stored as a UTC instant) of current session
bool     g_goldORBuilt       = false;
double   g_goldORHigh        = 0.0;
double   g_goldORLow         = 0.0;
int      g_goldBreakoutSide  = 0;     // 0=none, 1=long, -1=short
datetime g_goldBreakoutTime  = 0;     // broker-time of the breakout bar
bool     g_goldSetupCancelled= false;
bool     g_goldTradeTakenToday = false;
datetime g_goldLastM1Checked = 0;     // last M1 bar (broker time) already scanned

// ---- US30 (breakout-retest) state ----
datetime g_us30LastClosedBar  = 0;    // broker time of the last H4 bar already evaluated
datetime g_us30EntryBarTime   = 0;    // broker time of the H4 bar on which the current position entered

//====================== TIMEZONE HELPERS ==============================
// The gold leg's whole edge depends on correctly locating 09:30/10:00/16:00
// America/New_York, across US daylight saving -- NOT the broker server's own
// DST (which most brokers set to EU rules, e.g. GMT+2/GMT+3 EET). This block
// anchors everything to TRUE UTC (via TimeGMT(), which MQL5 derives from the
// trading PC/VPS's own OS timezone settings -- keep that VPS set to UTC or a
// known-correct timezone) and then applies the REAL US federal DST rule
// (2nd Sunday of March 07:00 UTC -> 1st Sunday of November 06:00 UTC) by
// direct calculation, rather than trusting the broker server clock's DST
// behaviour. See strategies/orb.py's own docstring in the Python backtest
// for the same warning -- this is the single most fragile detail to get
// wrong when porting an ORB strategy live.

datetime NthSundayUTC(int year, int month, int n)
  {
   MqlDateTime dt;
   dt.year = year; dt.mon = month; dt.day = 1;
   dt.hour = 0; dt.min = 0; dt.sec = 0;
   datetime firstOfMonth = StructToTime(dt);
   TimeToStruct(firstOfMonth, dt);
   int dow = dt.day_of_week;               // 0 = Sunday
   int firstSunday = 1 + ((7 - dow) % 7);
   int day = firstSunday + (n - 1) * 7;
   dt.day = day;
   return StructToTime(dt);
  }

// Returns the ET UTC-offset in hours (-4 during EDT, -5 during EST) for a
// given TRUE UTC instant.
int ETOffsetHours(datetime utcTime)
  {
   MqlDateTime dt;
   TimeToStruct(utcTime, dt);
   int year = dt.year;
   datetime dstStart = NthSundayUTC(year, 3, 2)  + 7 * 3600;  // 2nd Sun Mar, 07:00 UTC
   datetime dstEnd   = NthSundayUTC(year, 11, 1) + 6 * 3600;  // 1st Sun Nov, 06:00 UTC
   if(utcTime >= dstStart && utcTime < dstEnd)
      return -4;  // EDT
   return -5;     // EST
  }

// Current broker-server-time minus true-UTC offset, recomputed every call so
// it self-corrects across the BROKER's own DST transitions too.
datetime BrokerToUTC(datetime brokerTime)
  {
   int offsetSec = (int)(TimeCurrent() - TimeGMT());
   return brokerTime - offsetSec;
  }

// ET minute-of-day (0-1439) for a broker-server-time timestamp.
int ETMinuteOfDay(datetime brokerTime, datetime &etDateOut)
  {
   datetime utc = BrokerToUTC(brokerTime);
   int etOff = ETOffsetHours(utc);
   datetime etTime = utc + etOff * 3600;
   MqlDateTime dt;
   TimeToStruct(etTime, dt);
   etDateOut = etTime - (dt.hour * 3600 + dt.min * 60 + dt.sec); // ET midnight of that date
   return dt.hour * 60 + dt.min;
  }

//====================== NEWS FILTER ====================================

bool IsNearHighImpactUSNews(int bufferMinutes)
  {
   if(!InpUseNewsFilter)
      return false;
   datetime nowUTC = TimeGMT();
   datetime from = nowUTC - bufferMinutes * 60;
   datetime to   = nowUTC + bufferMinutes * 60;
   MqlCalendarValue values[];
   int n = CalendarValueHistory(values, from, to, "US");
   if(n <= 0)
      return false;
   for(int i = 0; i < n; i++)
     {
      MqlCalendarEvent ev;
      if(CalendarEventById(values[i].event_id, ev))
        {
         if(ev.importance == CALENDAR_IMPORTANCE_HIGH)
            return true;
        }
     }
   return false;
  }

//====================== POSITION SIZING =================================

double LotsForRisk(string symbol, double riskPct, double riskPriceDistance)
  {
   if(riskPriceDistance <= 0)
      return 0.0;
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double riskAmount = equity * riskPct / 100.0;

   double tickValue = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize  = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tickSize <= 0)
      return 0.0;
   double valuePerPriceUnit = tickValue / tickSize;   // account-currency value of a 1.0 price move, 1 lot

   double lots = riskAmount / (riskPriceDistance * valuePerPriceUnit);

   double minLot  = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
   double maxLot  = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
   double stepLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
   if(stepLot <= 0)
      stepLot = minLot;

   lots = MathFloor(lots / stepLot) * stepLot;
   if(lots < minLot)
      lots = 0.0;   // risk too small for min lot size -- skip rather than over-risk
   if(lots > maxLot)
      lots = maxLot;
   return lots;
  }

//====================== LEG 1: ORB GOLD RETEST ===========================

void ResetGoldDailyState(datetime etDate)
  {
   g_goldSessionDate     = etDate;
   g_goldORBuilt         = false;
   g_goldORHigh          = 0.0;
   g_goldORLow           = 0.0;
   g_goldBreakoutSide    = 0;
   g_goldBreakoutTime    = 0;
   g_goldSetupCancelled  = false;
   g_goldTradeTakenToday = false;
  }

bool GoldPositionOpen()
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0)
         continue;
      if(PositionGetString(POSITION_SYMBOL) == InpGoldSymbol &&
         PositionGetInteger(POSITION_MAGIC) == InpMagicGold)
         return true;
     }
   return false;
  }

void ForceFlatGold()
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0)
         continue;
      if(PositionGetString(POSITION_SYMBOL) == InpGoldSymbol &&
         PositionGetInteger(POSITION_MAGIC) == InpMagicGold)
        {
         trade.PositionClose(ticket);
         if(InpVerboseLog)
            PrintFormat("[GOLD] force-flat at 16:00 ET, ticket=%I64u", ticket);
        }
     }
  }

// Builds the 09:30-10:00 ET opening range from M1 bars once that window has
// fully elapsed. Mirrors strategies/orb.py's opening_ranges(): high/low over
// bars whose ET minute-of-day is in [open_min, open_min+or_minutes).
bool BuildGoldOpeningRange(double &orHigh, double &orLow)
  {
   double hi = -DBL_MAX, lo = DBL_MAX;
   int found = 0;
   // Scans up to a full day back so a LATE EA (re)start -- e.g. attached or
   // reconnected mid-afternoon ET -- can still locate this morning's OR
   // window, not just the ~last hour of bars.
   for(int shift = 1; shift <= 1440; shift++)
     {
      datetime bt = iTime(InpGoldSymbol, PERIOD_M1, shift);
      if(bt == 0)
         break;
      datetime dummyDate;
      int mod = ETMinuteOfDay(bt, dummyDate);
      if(dummyDate != g_goldSessionDate)
         break; // walked past the start of today's session into yesterday
      if(mod >= 9 * 60 + 30 && mod < 9 * 60 + 30 + InpGold_OR_Minutes)
        {
         hi = MathMax(hi, iHigh(InpGoldSymbol, PERIOD_M1, shift));
         lo = MathMin(lo, iLow(InpGoldSymbol, PERIOD_M1, shift));
         found++;
        }
     }
   double coverageNeeded = 0.85 * InpGold_OR_Minutes;
   if(found < coverageNeeded || hi <= lo)
      return false;
   orHigh = hi;
   orLow  = lo;
   return true;
  }

void ProcessGoldLeg()
  {
   datetime nowBroker = TimeCurrent();
   datetime etDate;
   int etMin = ETMinuteOfDay(nowBroker, etDate);

   if(etDate != g_goldSessionDate)
      ResetGoldDailyState(etDate);

   // Force-flat at/after 16:00 ET.
   if(etMin >= 16 * 60)
     {
      if(GoldPositionOpen())
         ForceFlatGold();
      return;
     }

   // Still inside/before the opening range window -- nothing to do yet.
   if(etMin < 9 * 60 + 30 + InpGold_OR_Minutes)
      return;

   if(!g_goldORBuilt)
     {
      double hi, lo;
      if(BuildGoldOpeningRange(hi, lo))
        {
         g_goldORHigh  = hi;
         g_goldORLow   = lo;
         g_goldORBuilt = true;
         if(InpVerboseLog)
            PrintFormat("[GOLD] OR built: high=%.2f low=%.2f", hi, lo);
        }
      else
         return; // couldn't build a valid OR today (gap/holiday) -- no trade
     }

   if(g_goldTradeTakenToday || g_goldSetupCancelled || GoldPositionOpen())
      return;

   double rng = g_goldORHigh - g_goldORLow;

   // Scan any new M1 bars since the last check, in chronological order, so
   // "first break wins" and the retest/cancel walk-forward logic matches the
   // Python backtest's bar-by-bar resolution rather than only looking at the
   // single latest bar (which could skip an intervening bar's condition).
   int newestShift = 1;
   datetime newestTime = iTime(InpGoldSymbol, PERIOD_M1, newestShift);
   if(newestTime == 0 || newestTime <= g_goldLastM1Checked)
      return;

   // Collect unchecked bars, oldest first. 500 bars (~8.3h) comfortably
   // covers a full RTH session (390 min) plus margin for a late (re)start.
   int shifts[]; ArrayResize(shifts, 0);
   for(int s = 1; s < 500; s++)
     {
      datetime bt = iTime(InpGoldSymbol, PERIOD_M1, s);
      if(bt == 0 || bt <= g_goldLastM1Checked)
         break;
      int n = ArraySize(shifts);
      ArrayResize(shifts, n + 1);
      shifts[n] = s;
     }
   // reverse into chronological order
   int cnt = ArraySize(shifts);
   for(int a = 0; a < cnt / 2; a++)
     {
      int tmp = shifts[a]; shifts[a] = shifts[cnt - 1 - a]; shifts[cnt - 1 - a] = tmp;
     }

   for(int idx = 0; idx < cnt; idx++)
     {
      int s = shifts[idx];
      datetime bt = iTime(InpGoldSymbol, PERIOD_M1, s);
      double bhi = iHigh(InpGoldSymbol, PERIOD_M1, s);
      double blo = iLow(InpGoldSymbol, PERIOD_M1, s);
      double bcl = iClose(InpGoldSymbol, PERIOD_M1, s);

      datetime barEtDate; int barEtMin = ETMinuteOfDay(bt, barEtDate);
      if(barEtDate != g_goldSessionDate || barEtMin < 9 * 60 + 30 + InpGold_OR_Minutes || barEtMin >= 16 * 60)
        {
         g_goldLastM1Checked = bt;
         continue;
        }

      if(g_goldBreakoutSide == 0)
        {
         bool up = (bhi >= g_goldORHigh);
         bool dn = (blo <= g_goldORLow);
         if(up && dn)
           {
            // ambiguous same-bar double break -- skip the whole day, matches orb.py
            g_goldSetupCancelled = true;
            g_goldLastM1Checked = bt;
            break;
           }
         if(up)
           {
            g_goldBreakoutSide = 1;
            g_goldBreakoutTime = bt;
           }
         else if(dn)
           {
            g_goldBreakoutSide = -1;
            g_goldBreakoutTime = bt;
           }
         g_goldLastM1Checked = bt;
         continue;
        }

      // Past the breakout bar: look for cancellation (close back through the
      // level) or a valid retest, in that priority order per bar.
      double tol = InpGold_RetestTolFrac * rng;
      if(g_goldBreakoutSide == 1)
        {
         if(bcl < g_goldORHigh)
           {
            g_goldSetupCancelled = true;
            g_goldLastM1Checked = bt;
            if(InpVerboseLog) Print("[GOLD] long setup cancelled -- closed back below OR high");
            break;
           }
         if(bt > g_goldBreakoutTime && blo <= g_goldORHigh + tol)
           {
            EnterGold(ORDER_TYPE_BUY, g_goldORHigh);
            g_goldLastM1Checked = bt;
            break;
           }
        }
      else // short
        {
         if(bcl > g_goldORLow)
           {
            g_goldSetupCancelled = true;
            g_goldLastM1Checked = bt;
            if(InpVerboseLog) Print("[GOLD] short setup cancelled -- closed back above OR low");
            break;
           }
         if(bt > g_goldBreakoutTime && bhi >= g_goldORLow - tol)
           {
            EnterGold(ORDER_TYPE_SELL, g_goldORLow);
            g_goldLastM1Checked = bt;
            break;
           }
        }
      g_goldLastM1Checked = bt;
     }
  }

void EnterGold(ENUM_ORDER_TYPE dir, double entryLevel)
  {
   if(IsNearHighImpactUSNews(InpNewsBufferMinutes))
     {
      if(InpVerboseLog) Print("[GOLD] entry skipped -- within FTMO news blackout window");
      return;
     }

   double price = (dir == ORDER_TYPE_BUY) ? SymbolInfoDouble(InpGoldSymbol, SYMBOL_ASK)
                                            : SymbolInfoDouble(InpGoldSymbol, SYMBOL_BID);
   double riskDist = InpGold_StopBps / 10000.0 * price;
   double stop   = (dir == ORDER_TYPE_BUY) ? price - riskDist : price + riskDist;
   double target = (dir == ORDER_TYPE_BUY) ? price + InpGold_TargetR * riskDist
                                             : price - InpGold_TargetR * riskDist;

   double lots = LotsForRisk(InpGoldSymbol, InpGoldRiskPct, riskDist);
   if(lots <= 0)
     {
      if(InpVerboseLog) Print("[GOLD] computed lot size is 0 -- skipping (risk too small for min lot)");
      g_goldTradeTakenToday = true; // still counts as "handled" for today
      return;
     }

   trade.SetExpertMagicNumber(InpMagicGold);
   trade.SetDeviationInPoints(InpSlippagePoints);
   bool ok = (dir == ORDER_TYPE_BUY) ? trade.Buy(lots, InpGoldSymbol, price, stop, target, "ORB_Gold_RETEST")
                                       : trade.Sell(lots, InpGoldSymbol, price, stop, target, "ORB_Gold_RETEST");
   // Marked "taken" even on a failed send (deliberately conservative -- avoids
   // hammering the broker with retries on a persistent error and re-entering
   // the SAME setup repeatedly; a failed send is logged and surfaces as a
   // missed day, not silently retried).
   g_goldTradeTakenToday = true;
   if(InpVerboseLog)
      PrintFormat("[GOLD] entry %s lots=%.2f price=%.2f stop=%.2f target=%.2f ok=%s",
                  (dir == ORDER_TYPE_BUY ? "LONG" : "SHORT"), lots, price, stop, target, ok ? "true" : "false");
  }

//====================== LEG 2: US30 BREAKOUT-RETEST =======================

bool US30PositionOpen(ulong &outTicket)
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0)
         continue;
      if(PositionGetString(POSITION_SYMBOL) == InpUS30Symbol &&
         PositionGetInteger(POSITION_MAGIC) == InpMagicUS30)
        {
         outTicket = ticket;
         return true;
        }
     }
   outTicket = 0;
   return false;
  }

// Simple (non-Wilder) mean true range over `period` bars ending at
// `signalShift` -- matches strategies/ftmo_gold.py's atr(): a plain rolling
// mean of true range, NOT MT5's built-in iATR (which is Wilder-smoothed).
double SimpleATR(string symbol, ENUM_TIMEFRAMES tf, int signalShift, int period)
  {
   double sum = 0.0;
   for(int i = 0; i < period; i++)
     {
      int idx = signalShift + i;
      double hi = iHigh(symbol, tf, idx);
      double lo = iLow(symbol, tf, idx);
      double prevClose = iClose(symbol, tf, idx + 1);
      double tr = MathMax(hi - lo, MathMax(MathAbs(hi - prevClose), MathAbs(lo - prevClose)));
      sum += tr;
     }
   return sum / period;
  }

void ProcessUS30Leg()
  {
   datetime lastClosed = iTime(InpUS30Symbol, PERIOD_H4, 1);
   if(lastClosed == 0)
      return;

   ulong openTicket;
   bool hasPos = US30PositionOpen(openTicket);

   // Max-hold time exit: count H4 bars since entry.
   if(hasPos && g_us30EntryBarTime != 0)
     {
      int barsHeld = iBarShift(InpUS30Symbol, PERIOD_H4, g_us30EntryBarTime, true) -
                     iBarShift(InpUS30Symbol, PERIOD_H4, lastClosed, true);
      if(barsHeld >= InpUS30_MaxHoldBars)
        {
         trade.PositionClose(openTicket);
         if(InpVerboseLog) PrintFormat("[US30] max-hold exit after %d H4 bars", barsHeld);
         g_us30EntryBarTime = 0;
         hasPos = false;
        }
     }

   // Only look for a NEW signal once per newly-closed H4 bar.
   if(lastClosed == g_us30LastClosedBar)
      return;
   g_us30LastClosedBar = lastClosed;

   if(hasPos)
      return; // one position at a time, matches the backtest's de_overlap

   int N = InpUS30_Lookback;
   double rollingHigh = -DBL_MAX, rollingLow = DBL_MAX;
   for(int s = 2; s <= 1 + N; s++)  // the N bars PRIOR to the just-closed signal bar
     {
      rollingHigh = MathMax(rollingHigh, iHigh(InpUS30Symbol, PERIOD_H4, s));
      rollingLow  = MathMin(rollingLow,  iLow(InpUS30Symbol, PERIOD_H4, s));
     }

   double sigHigh  = iHigh(InpUS30Symbol, PERIOD_H4, 1);
   double sigLow   = iLow(InpUS30Symbol, PERIOD_H4, 1);
   double sigClose = iClose(InpUS30Symbol, PERIOD_H4, 1);

   bool longSignal  = (sigClose > rollingHigh) && (sigLow <= rollingHigh);
   bool shortSignal = (sigClose < rollingLow)  && (sigHigh >= rollingLow);
   if(longSignal && shortSignal)
      return; // shouldn't happen given the > / < asymmetry, but stay safe
   if(!longSignal && !shortSignal)
      return;

   double atr = SimpleATR(InpUS30Symbol, PERIOD_H4, 1, InpUS30_ATR_Period);
   if(atr <= 0)
      return;

   ENUM_ORDER_TYPE dir = longSignal ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   double brokenLevel = longSignal ? rollingHigh : rollingLow;
   double stop   = longSignal ? brokenLevel - InpUS30_K_ATR * atr : brokenLevel + InpUS30_K_ATR * atr;
   double price  = (dir == ORDER_TYPE_BUY) ? SymbolInfoDouble(InpUS30Symbol, SYMBOL_ASK)
                                             : SymbolInfoDouble(InpUS30Symbol, SYMBOL_BID);
   double riskDist = MathAbs(price - stop);
   double target = longSignal ? price + InpUS30_TargetR * riskDist : price - InpUS30_TargetR * riskDist;

   if(IsNearHighImpactUSNews(InpNewsBufferMinutes))
     {
      if(InpVerboseLog) Print("[US30] entry skipped -- within FTMO news blackout window");
      return;
     }

   double lots = LotsForRisk(InpUS30Symbol, InpUS30RiskPct, riskDist);
   if(lots <= 0)
     {
      if(InpVerboseLog) Print("[US30] computed lot size is 0 -- skipping (risk too small for min lot)");
      return;
     }

   trade.SetExpertMagicNumber(InpMagicUS30);
   trade.SetDeviationInPoints(InpSlippagePoints);
   bool ok = (dir == ORDER_TYPE_BUY) ? trade.Buy(lots, InpUS30Symbol, price, stop, target, "US30_Breakout_Retest")
                                       : trade.Sell(lots, InpUS30Symbol, price, stop, target, "US30_Breakout_Retest");
   if(ok)
      g_us30EntryBarTime = lastClosed;
   if(InpVerboseLog)
      PrintFormat("[US30] entry %s lots=%.2f price=%.2f stop=%.2f target=%.2f atr=%.2f ok=%s",
                  (dir == ORDER_TYPE_BUY ? "LONG" : "SHORT"), lots, price, stop, target, atr, ok ? "true" : "false");
  }

//====================== ROLLING RISK-PARITY (NOT IMPLEMENTED) ============
// docs/manual_trading_rules.md section 3 describes the FAITHFUL sizing
// scheme actually used for this project's best backtested result (Sec52):
// monthly-rebalanced inverse-volatility weights from each leg's trailing
// 90-day daily returns. That requires persisting each leg's own daily P&L
// history (e.g. to a CSV/file the EA appends to) and recomputing weights
// once a month -- a real but bounded follow-up, deliberately NOT built in
// this first version so the EA could ship and go on the free demo now.
// Until it exists, InpGoldRiskPct / InpUS30RiskPct implement the documented
// "simple version" (fixed 50/50 of a combined risk budget) instead.
void RiskParity_TODO() {}

//====================== LEGS 3+4: VIX + REAL-YIELD SLEEVE ================
// Both legs fetch their FULL free history in one GET request each (matching
// the Python backtest's own data source exactly -- CBOE's public VIX CSV,
// FRED's public DFII10 CSV, no API key, no auth) once per UTC calendar day,
// recompute the signal from scratch, and hold a continuously-invested
// directional position with NO STOP AND NO TARGET (see the file header --
// this matches exactly how Sec75/Sec79 backtested it; it is a real, stated
// live-risk difference from Legs 1/2).
//
// REQUIRED ONE-TIME SETUP: MT5 -> Tools -> Options -> Expert Advisors ->
// check "Allow WebRequest for listed URL" and add BOTH InpVixUrl and
// InpFredUrl to the list, exactly as configured in the inputs. Without
// this, WebRequest() fails with error 4060 and the sleeve silently stays
// flat forever -- watch the Experts log for "[SLEEVE]" error lines.

bool WebGetText(const string url, string &out_text)
  {
   char post[]; char result[]; string result_headers;
   ResetLastError();
   int status = WebRequest("GET", url, "", InpWebRequestTimeoutMs, post, result, result_headers);
   if(status == -1)
     {
      PrintFormat("[SLEEVE] ERROR: WebRequest failed for %s -- error=%d. Did you whitelist this URL "
                  "in Tools>Options>Expert Advisors>Allow WebRequest for listed URL?", url, GetLastError());
      return false;
     }
   if(status != 200)
     {
      PrintFormat("[SLEEVE] ERROR: HTTP status %d fetching %s", status, url);
      return false;
     }
   out_text = CharArrayToString(result, 0, ArraySize(result), CP_UTF8);
   return true;
  }

// Parses CBOE's "DATE,OPEN,HIGH,LOW,CLOSE" CSV (mm/dd/yyyy dates) into an
// ascending array of CLOSE values (skips the header row).
int ParseVixCloses(const string csv_text, double &closes[])
  {
   string lines[];
   int n_lines = StringSplit(csv_text, '\n', lines);
   ArrayResize(closes, 0);
   for(int i = 1; i < n_lines; i++)  // skip header
     {
      string line = lines[i];
      StringReplace(line, "\r", ""); StringTrimRight(line); StringTrimLeft(line);
      if(StringLen(line) == 0)
         continue;
      string fields[];
      int n_fields = StringSplit(line, ',', fields);
      if(n_fields < 5)
         continue;
      double close = StringToDouble(fields[4]);
      if(close <= 0)
         continue;
      int n = ArraySize(closes);
      ArrayResize(closes, n + 1);
      closes[n] = close;
     }
   return ArraySize(closes);
  }

// Parses FRED's "observation_date,DFII10" CSV (yyyy-mm-dd dates, "." for
// missing/holiday rows) into an ascending array of values.
int ParseFredValues(const string csv_text, double &values[])
  {
   string lines[];
   int n_lines = StringSplit(csv_text, '\n', lines);
   ArrayResize(values, 0);
   for(int i = 1; i < n_lines; i++)  // skip header
     {
      string line = lines[i];
      StringReplace(line, "\r", ""); StringTrimRight(line); StringTrimLeft(line);
      if(StringLen(line) == 0)
         continue;
      string fields[];
      int n_fields = StringSplit(line, ',', fields);
      if(n_fields < 2)
         continue;
      if(fields[1] == "." || StringLen(fields[1]) == 0)
         continue;  // FRED's own marker for a non-trading/missing day
      double v = StringToDouble(fields[1]);
      int n = ArraySize(values);
      ArrayResize(values, n + 1);
      values[n] = v;
     }
   return ArraySize(values);
  }

double ArrayMeanTail(const double &arr[], int window)
  {
   int n = ArraySize(arr);
   double sum = 0.0;
   for(int i = n - window; i < n; i++)
      sum += arr[i];
   return sum / window;
  }

double ArrayStdTail(const double &arr[], int window, double mean)
  {
   int n = ArraySize(arr);
   double sumsq = 0.0;
   for(int i = n - window; i < n; i++)
      sumsq += (arr[i] - mean) * (arr[i] - mean);
   return MathSqrt(sumsq / (window - 1));
  }

// z >= +thr -> +1 (VIX spiking, long gold); z <= -thr -> -1; else 0.
int ComputeVixSignal(const double &closes[], int window, double threshold)
  {
   int n = ArraySize(closes);
   if(n < window)
     {
      Print("[SLEEVE][VIX] not enough history yet (", n, "/", window, ") -- flat");
      return 0;
     }
   double mean = ArrayMeanTail(closes, window);
   double sd   = ArrayStdTail(closes, window, mean);
   if(sd <= 0)
      return 0;
   double z = (closes[n - 1] - mean) / sd;
   if(InpVerboseLog) PrintFormat("[SLEEVE][VIX] latest=%.2f mean=%.2f sd=%.2f z=%.2f", closes[n-1], mean, sd, z);
   if(z >= threshold)  return  1;
   if(z <= -threshold) return -1;
   return 0;
  }

// change<0 (real yields falling) -> +1 (long gold); change>0 -> -1; else 0.
int ComputeRealYieldSignal(const double &values[], int lookback)
  {
   int n = ArraySize(values);
   if(n < lookback + 1)
     {
      Print("[SLEEVE][REALYIELD] not enough history yet (", n, "/", lookback + 1, ") -- flat");
      return 0;
     }
   double change = values[n - 1] - values[n - 1 - lookback];
   if(InpVerboseLog) PrintFormat("[SLEEVE][REALYIELD] latest=%.3f%% %dd-ago=%.3f%% change=%.3f%%",
                                  values[n-1], lookback, values[n-1-lookback], change);
   if(change < 0) return  1;
   if(change > 0) return -1;
   return 0;
  }

// NOTIONAL sizing (NOT stop-based, since these legs have no stop) -- lots
// such that the position's dollar notional equals equityFraction * equity,
// matching the backtest's "position in {-1,0,+1} = fully-invested fraction
// of capital" construction exactly.
double LotsForNotional(string symbol, double equityFraction)
  {
   if(equityFraction <= 0)
      return 0.0;
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double notional = equity * equityFraction;
   double price = SymbolInfoDouble(symbol, SYMBOL_BID);
   double contractSize = SymbolInfoDouble(symbol, SYMBOL_TRADE_CONTRACT_SIZE);
   if(price <= 0 || contractSize <= 0)
      return 0.0;
   double lots = notional / (price * contractSize);

   double minLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
   double maxLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
   double stepLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
   if(stepLot <= 0) stepLot = minLot;
   lots = MathFloor(lots / stepLot) * stepLot;
   if(lots < minLot) lots = 0.0;
   if(lots > maxLot) lots = maxLot;
   return lots;
  }

bool GetOpenPositionDirection(string symbol, int magic, int &outDir, ulong &outTicket)
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) == symbol && PositionGetInteger(POSITION_MAGIC) == magic)
        {
         outTicket = ticket;
         outDir = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? 1 : -1;
         return true;
        }
     }
   outDir = 0; outTicket = 0;
   return false;
  }

// Closes any existing position under this magic, then opens a new one in
// `desiredDir` (skips entirely if desiredDir==0 or lots compute to 0).
void SetSleevePosition(string symbol, int magic, string comment, int desiredDir, double equityFraction)
  {
   int curDir; ulong curTicket;
   bool hasPos = GetOpenPositionDirection(symbol, magic, curDir, curTicket);
   if(hasPos && curDir == desiredDir)
      return;  // already correctly positioned, nothing to do
   if(hasPos)
     {
      trade.PositionClose(curTicket);
      if(InpVerboseLog) PrintFormat("[SLEEVE] %s closed (magic=%d) ahead of a direction change", symbol, magic);
     }
   if(desiredDir == 0)
      return;

   double lots = LotsForNotional(symbol, equityFraction);
   if(lots <= 0)
     {
      if(InpVerboseLog) Print("[SLEEVE] computed lot size is 0 for ", symbol, " (magic=", magic, ") -- skipping");
      return;
     }
   double price = (desiredDir > 0) ? SymbolInfoDouble(symbol, SYMBOL_ASK) : SymbolInfoDouble(symbol, SYMBOL_BID);
   trade.SetExpertMagicNumber(magic);
   trade.SetDeviationInPoints(InpSlippagePoints);
   bool ok = (desiredDir > 0) ? trade.Buy(lots, symbol, price, 0, 0, comment)
                               : trade.Sell(lots, symbol, price, 0, 0, comment);
   PrintFormat("[SLEEVE] %s entry %s lots=%.2f price=%.2f magic=%d ok=%s", symbol,
               (desiredDir > 0 ? "LONG" : "SHORT"), lots, price, magic, ok ? "true" : "false");
  }

void ProcessSleeve()
  {
   if(!InpUseSleeve)
      return;

   datetime todayUTC = TimeGMT() - (TimeGMT() % 86400);  // UTC midnight of today
   if(todayUTC == g_sleeveLastFetchDate)
      return;  // already fetched+recomputed today, hold existing positions

   string vixText, fredText;
   bool vixOk  = WebGetText(InpVixUrl, vixText);
   bool fredOk = WebGetText(InpFredUrl, fredText);
   if(!vixOk || !fredOk)
     {
      Print("[SLEEVE] fetch failed this cycle -- will retry next timer tick (existing positions untouched)");
      return;  // do NOT flatten on a transient fetch failure -- leave positions as-is
     }

   double vixCloses[]; double realYieldValues[];
   int nVix = ParseVixCloses(vixText, vixCloses);
   int nRy  = ParseFredValues(fredText, realYieldValues);
   if(nVix < InpVixWindowDays || nRy < InpRealYieldLookbackDays + 1)
     {
      PrintFormat("[SLEEVE] parsed but insufficient history (VIX=%d/%d, real-yield=%d/%d) -- flat",
                  nVix, InpVixWindowDays, nRy, InpRealYieldLookbackDays + 1);
      g_sleeveLastFetchDate = todayUTC;
      return;
     }

   g_vixSignal       = ComputeVixSignal(vixCloses, InpVixWindowDays, InpVixThreshold);
   g_realYieldSignal = ComputeRealYieldSignal(realYieldValues, InpRealYieldLookbackDays);
   g_sleeveDataOk    = true;
   g_sleeveLastFetchDate = todayUTC;

   double perLegFraction = (InpSleeveWeightPct / 100.0) / 2.0;  // sleeve weight split 50/50 across Legs 3+4
   PrintFormat("[SLEEVE] recomputed: VIX signal=%d, real-yield signal=%d, per-leg notional=%.2f%% of equity",
               g_vixSignal, g_realYieldSignal, perLegFraction * 100.0);

   SetSleevePosition(InpGoldSymbol, InpMagicVix, "VIX_Sleeve", g_vixSignal, perLegFraction);
   SetSleevePosition(InpGoldSymbol, InpMagicRealYield, "RealYield_Sleeve", g_realYieldSignal, perLegFraction);
  }

//====================== MT5 EVENT HANDLERS ================================

int OnInit()
  {
   if(!SymbolSelect(InpGoldSymbol, true))
     {
      PrintFormat("ERROR: could not select gold symbol '%s' -- check InpGoldSymbol against your broker's exact name", InpGoldSymbol);
      return(INIT_FAILED);
     }
   if(!SymbolSelect(InpUS30Symbol, true))
     {
      PrintFormat("ERROR: could not select US30 symbol '%s' -- check InpUS30Symbol against your broker's exact name", InpUS30Symbol);
      return(INIT_FAILED);
     }
   EventSetTimer(InpTimerSeconds);
   Print("ORB_Gold_US30_VIX_RealYield_4Leg_Combined initialised.");
   if(InpUseSleeve)
      Print("[SLEEVE] enabled -- first WebRequest fetch happens on the next OnTimer tick. "
            "If nothing appears within a few timer intervals, check the Experts log for a "
            "[SLEEVE] ERROR line (most likely cause: the VIX/FRED URLs are not yet whitelisted "
            "in Tools>Options>Expert Advisors>Allow WebRequest for listed URL).");
   return(INIT_SUCCEEDED);
  }

void OnDeinit(const int reason)
  {
   EventKillTimer();
  }

void OnTimer()
  {
   ProcessGoldLeg();
   ProcessUS30Leg();
   ProcessSleeve();
  }

void OnTick()
  {
   // Deliberately empty -- all logic runs on the timer (see OnTimer), which
   // decouples this EA from tick frequency/latency on either symbol and
   // keeps the M1/H4 bar-close checks deterministic regardless of how often
   // the chart this EA is attached to actually ticks.
  }
//+------------------------------------------------------------------+
