"""Dip-buy mean-reversion bot for the BTC 24h race (agent-fun/bars-replay/v1).

Idea: cbBTC on 1-minute bars spends most of its time chopping around a slow
2-hour mean, with occasional 1-2% air pockets below it and sharp recoveries.
This bot only buys those air pockets and only sells into strength:

  - Entry: the close prints at least 100 bps below the 120-bar simple moving
    average of closes, and the bot is flat. It spends all its cash (long only,
    one position, no leverage).
  - Exit, whichever comes first:
      * take profit: the close is 220 bps above the entry's average fill cost;
      * trailing stop: the close falls 100 bps below the highest close seen
        since the entry;
      * hard stop: the close falls 150 bps below the entry cost (after a hard
        stop the bot sits out for 60 bars, so a waterfall cannot stop it out
        over and over).
  - No new entry in the last 60 bars of the window: a trade opened there has
    no time to reach its target before the final flatten, so it would only
    pay the round-trip cost.

Everything is integer arithmetic on the bar closes (price_scale 5), so the
same bars always give the same orders. No clock, no network, no files, no
randomness: the only state is the close history, the running peak since the
entry, and the stop-loss cooldown. Orders are capped at 200 bps of slippage
from the latest close; the largest 1-minute move in the dev window is 64 bps.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))

import makefun_bars

SYMBOL = "CBBTC"
# The window is 1,440 one-minute bars (see RULES.txt, "Windows").
WINDOW_BARS = 1440
# The mean the bot buys dips below: 120 closes, i.e. two hours.
SMA_BARS = 120
# Entry: close at least this far below the 120-bar mean, in basis points.
DIP_BPS = 100
# Exit: close this far above the entry's average fill cost, in basis points.
TAKE_PROFIT_BPS = 220
# Exit: close this far below the entry's average fill cost, in basis points.
STOP_LOSS_BPS = 150
# Exit: close this far below the highest close since the entry, in basis points.
TRAIL_BPS = 100
# Orders are refused if they would fill further than this from the latest close.
MAX_SLIPPAGE_BPS = 200
# No new entry this close to the end of the window.
NO_ENTRY_LAST_BARS = 60
# Bars to sit out after a hard stop-loss exit.
COOLDOWN_BARS = 60
# Price and quantity scales of CBBTC in hello (price_scale 5, qty_scale 8,
# quote_scale 6): entry price = cost * 10**(8+5) // (qty * 10**6).
_ENTRY_NUM = 10 ** (8 + 5)
_ENTRY_DEN = 10 ** 6

_closes = []
_peak = 0
_cool_until = -1


def _entry_price(state):
    held = state.positions.get(SYMBOL)
    if held is None or held.qty == 0:
        return None
    return held.cost * _ENTRY_NUM // (held.qty * _ENTRY_DEN)


def _sell_all(state):
    held = state.positions.get(SYMBOL)
    if held is None or held.qty == 0:
        return []
    return [{
        "side": "sell",
        "symbol": SYMBOL,
        "qty": held.qty,
        "max_slippage_bps": MAX_SLIPPAGE_BPS,
    }]


def on_batch(state, batch):
    global _peak, _cool_until
    for bar in batch["bars"]:
        if bar["symbol"] == SYMBOL:
            _closes.append(int(bar["c"]))
    if state.warming_up:
        return []
    if len(_closes) < SMA_BARS + 1:
        return []
    close = _closes[-1]
    sma = sum(_closes[-SMA_BARS:]) // SMA_BARS
    entry = _entry_price(state)
    if entry is None:
        _peak = 0
        last_entry_seq = state.warmup_bars + WINDOW_BARS - NO_ENTRY_LAST_BARS
        if state.seq >= last_entry_seq:
            return []
        if state.seq < _cool_until:
            return []
        if close * 10000 < sma * (10000 - DIP_BPS):
            amount = state.cash
            if amount >= int(state.hello["fees"]["min_notional_quote_units"]):
                return [{
                    "side": "buy",
                    "symbol": SYMBOL,
                    "notional_quote_units": amount,
                    "max_slippage_bps": MAX_SLIPPAGE_BPS,
                }]
        return []
    if close > _peak:
        _peak = close
    if close * 10000 >= entry * (10000 + TAKE_PROFIT_BPS):
        return _sell_all(state)
    if close * 10000 <= entry * (10000 - STOP_LOSS_BPS):
        _cool_until = state.seq + COOLDOWN_BARS
        return _sell_all(state)
    if _peak > 0 and close * 10000 <= _peak * (10000 - TRAIL_BPS):
        return _sell_all(state)
    return []


makefun_bars.run(on_batch)
