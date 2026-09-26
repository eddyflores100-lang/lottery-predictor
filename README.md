# 🎰 LotteryPredictor v4.0

Sistema completo de análisis y predicción de loterías globales con 49 loterías, 10 motores de análisis, Kelly Criterion, EV Calculator, y MCP server.

## 🚀 Quick Start

```bash
# Backend (Python predictor)
cd scripts/lottery_predictor
python3 main.py --list                    # listar 49 loterías
python3 main.py --lottery euromillions --engine markov_chain --predict
python3 main.py --lottery euromillions --backtest all --max-test 100

# Frontend (Next.js web UI)
cd /home/z/my-project
bun run dev                               # http://localhost:3000

# MCP Server (para Claude Desktop / Cursor)
python3 scripts/lottery_predictor/mcp_server.py
# Endpoint: http://localhost:8787/mcp

# Actualizar datos diarios
python3 scripts/lottery_predictor/daily_update.py
```

## 📊 Features

- **49 loterías** de todo el mundo (47 con datos)
- **10 motores de predicción**: frequency, hot_cold, gap_analysis, markov_chain, bayesian, pattern_detection, entropy, monte_carlo, ensemble, LSTM
- **Kelly Criterion + Bankroll Management** con Monte Carlo simulation
- **Backtesting riguroso** con permutation tests, Bonferroni correction, Cohen's d
- **Expected Value Calculator** con break-even analysis
- **MCP Server** productor (expone predictor a Claude Desktop, Cursor, etc.)
- **30 visualizaciones** temporales (heatmaps, timelines, co-ocurrencia)

## 🏗️ Arquitectura

```
scripts/lottery_predictor/
├── lotteries/              # 49 loterías configurables
│   ├── base.py            # Clase abstracta
│   ├── pozo_millonario.py # Ecuador 11/25
│   ├── registry.py        # Registry + factory
│   ├── generic.py         # Lotto genérico + 12 configs
│   └── quicklotto_registry.py  # 31 loterías de quicklotto.io MCP
├── engines/                # 11 motores de análisis
│   ├── frequency.py       # Frecuencia + Z-scores + chi-cuadrado
│   ├── hot_cold.py        # Temperatura + mean reversion
│   ├── gap_analysis.py    # Overdue detection
│   ├── markov_chain.py    # Transiciones 1° y 2° orden
│   ├── bayesian.py        # Beta posterior + credible intervals
│   ├── pattern_detection.py  # Patrones + runs test
│   ├── entropy.py         # Shannon + autocorrelación
│   ├── monte_carlo.py     # 10K simulaciones (mulberry32 PRNG)
│   ├── ensemble.py        # Combina los 8 anteriores
│   ├── lstm_engine.py     # LSTM con TensorFlow 2.21
│   └── kelly_criterion.py # Kelly + bankroll management
├── backtest/              # Framework de validación
│   ├── backtester.py      # Backtest básico
│   └── rigorous_backtester.py  # Permutation tests + p-values
├── data_fetcher/          # Scrapers y converters
│   ├── quicklotto_client.py   # Cliente MCP de quicklotto.io
│   └── convert_csv.py    # CSV → JSON converter
├── main.py                # CLI
├── cli_json.py            # CLI para API web (JSON output)
├── mcp_server.py          # MCP Server productor
├── daily_update.py        # Cron de actualización diaria
├── ev_calculator.py       # Expected Value Calculator
├── visualizations.py      # Generador de gráficos
└── STUDY.md              # Estudio global de loterías
```

## 🎯 Hallazgos clave

### Backtesting riguroso (con p-values)
Solo **markov_chain en EuroMillions** es estadísticamente significativo:
- p-value = 0.0000 (altamente significativo tras Bonferroni)
- Cohen's d = 3.148 (large effect)
- Mejora: +0.280 aciertos (de 0.430 a 0.710)

### Expected Value
Ninguna lotería tiene EV positivo con jackpot mínimo:
- Pozo Millonario: EV -$0.68 por $1 (break-even: $3.5M ✅)
- EuroMillions: EV -$0.79 (break-even: $294M ❌)
- US PowerBall: EV -$0.81 (break-even: $491M ❌)

### Kelly Criterion
Kelly fraction ≈ 0 para todas las loterías. No se recomienda apostar.

## 📡 Fuentes de datos

1. **quicklotto.io MCP** — 39 loterías, gratis, sin auth
2. **bettip.co.za API** — UK49s, SA Lotto, World lotteries
3. **daowa89/lottery-archive** (GitHub) — EuroMillions, German Lotto, Austrian Lotto
4. **pozomillonario.info** — Pozo Millonario Ecuador (scraping)

## ⚠️ Disclaimer

La lotería es matemáticamente desfavorable (EV negativo). Este sistema es para fines educativos y de análisis estadístico. No garantiza ganancias. Juega con responsabilidad.

## 📄 Licencia

MIT
