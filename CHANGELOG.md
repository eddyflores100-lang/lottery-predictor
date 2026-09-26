# Changelog

## [4.0.0] — 2026-09-26

### Added
- 🎰 49 loterías globales (de 6 originales)
- 🧠 Motor LSTM con TensorFlow 2.21
- 💰 Kelly Criterion + Bankroll Management
- 📊 Expected Value Calculator con break-even analysis
- 🔬 Backtesting riguroso (permutation tests, Bonferroni, Cohen's d)
- 📡 MCP Server productor (6 tools)
- 🎨 30 visualizaciones temporales (heatmaps, timelines, co-ocurrencia)
- 🌐 Web UI con 49 loterías en dropdown
- 📅 Cron de actualización diaria automática
- 🔍 Cliente quicklotto.io MCP (39 loterías en vivo)
- 📈 9 reportes Excel profesionales

### Key findings
- Markov Chain en EuroMillions: p=0.0000, Cohen's d=3.148 (estadísticamente significativo)
- Ninguna lotería tiene EV positivo con jackpot mínimo
- Kelly fraction ≈ 0 para todas las loterías
- Pozo Millonario: 35% de sorteos sospechosos
- EuroMillions: 4 números no aleatorios (6, 30, 33, 41)

## [3.0.0] — 2026-09-25

### Added
- Búsqueda exhaustiva en 15 registries MCP mundiales
- Integración quicklotto.io MCP (39 loterías)
- 31 nuevas loterías (SuperEnalotto, Mega-Sena, Lotofácil, etc.)
- MCP Server productor

## [2.0.0] — 2026-09-25

### Added
- 12 loterías nuevas vía bettip.co.za API
- Motor LSTM con TensorFlow
- Backtesting de 8 loterías
- Web UI Next.js 16

## [1.0.0] — 2026-09-24

### Added
- Sistema inicial con 6 loterías
- 9 motores estadísticos + ensemble
- Backtesting framework
- Análisis forense (chi-cuadrado, runs test, autocorrelación)
- Pozo Millonario Ecuador (308 sorteos scraped)
