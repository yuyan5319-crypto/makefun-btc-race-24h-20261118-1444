[![make.fun · btc-race-24h-20261118-1444](https://make.fun/badge/btc-race-24h-20261118-1444.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![rank](https://make.fun/badge/btc-race-24h-20261118-1444/yuyan5319-crypto/makefun-btc-race-24h-20261118-1444/rank.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![reward](https://make.fun/badge/btc-race-24h-20261118-1444/yuyan5319-crypto/makefun-btc-race-24h-20261118-1444/reward.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)

# Dip Pocket — a dip-buying mean-reversion bot for cbBTC

Trades Coinbase Wrapped BTC (cbBTC) against USDC on 1-minute bars, long only,
starting from 1,000 USDC of paper money. It buys only when the close prints at
least 100 bps below its 120-bar (2-hour) moving average — an "air pocket" below
the slow mean — and sells into strength at +220 bps over its entry cost, with
a 100 bps trailing stop and a 150 bps hard stop (followed by a 60-bar cooldown)
to cap the downside. It never enters in the last 60 bars of the window, since
a trade opened there has no time to reach its target before the final flatten.

On the published dev window it nets +$19.75 on a single round trip, with a
0.65% maximum drawdown.

## How to run

Python 3.13, standard library only. The bot speaks `agent-fun/bars-replay/v1`
(newline-delimited JSON on stdin/stdout) via the vendored shim in `vendor/`:

```
python3 -P -s main.py
```

Grade it locally with the kit's command line:

```
node <kit>/cli/makefun.mjs grade-local --kit <kit> --bot .
```

## Layout

- `main.py` — the bot (entrypoint)
- `vendor/makefun_bars.py` — byte-identical copy of the kit's Python SDK shim
- `.makefun/owner.json` — claim file naming the entrant's wallet
