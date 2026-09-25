# Estudio Global de Loterías Comprables Online

## Criterios de selección
- ✅ Comprables online desde cualquier país (vía thelotter.com, multilotto, lottoland, etc.)
- ✅ Sorteos frecuentes (≥2 por semana) para acumular datos históricos rápido
- ✅ Pool de números pequeño-mediano (mejor relación señal/ruido en análisis estadístico)
- ✅ Datos históricos públicos y accesibles
- ✅ Premio mínimo garantizado > $1M USD

## Ranking de loterías analizadas

| # | Lotería | País | Formato | Probabilidad Jackpot | Sorteos/sem | Pool | Comprable online |
|---|---------|------|---------|----------------------|-------------|------|------------------|
| 1 | **Pozo Millonario** | Ecuador | 11/25 + mascota | 1 en 4,457,400 | 2 | Pequeño | Sí (nacional) |
| 2 | **La Primitiva** | España | 6/49 + reintegro | 1 en 13,983,816 | 2 | Medio | Sí |
| 3 | **El Gordo** | España | 5/54 + 1/10 | 1 en 31,625,100 | 1 | Medio | Sí |
| 4 | **UK Lotto** | UK | 6/59 | 1 en 45,057,474 | 2 | Medio | Sí |
| 5 | **Oz Lotto** | Australia | 7/47 | 1 en 45,379,620 | 1 | Medio | Sí |
| 6 | **EuroJackpot** | Europa | 5/50 + 2/10 | 1 en 139,838,160 | 2 | Medio | Sí |
| 7 | **EuroMillions** | Europa | 5/50 + 2/12 | 1 en 139,838,160 | 2 | Medio | Sí |
| 8 | **Powerball Australia** | Australia | 7/35 + 1/20 | 1 en 133,780,000 | 1 | Medio | Sí |
| 9 | **Powerball USA** | USA | 5/69 + 1/26 | 1 en 292,201,338 | 3 | Grande | Sí |
| 10 | **Mega Millions** | USA | 5/70 + 1/25 | 1 en 302,575,350 | 2 | Grande | Sí |
| 11 | **SuperEnalotto** | Italia | 6/90 | 1 en 622,614,630 | 3 | Enorme | Sí |

## 🎯 Top 5 loterías recomendadas para predecir

### 1. **Pozo Millonario (Ecuador)** ⭐⭐⭐⭐⭐
- **Por qué:** Mejor probabilidad global (1:4.5M), pool pequeño (25 números), 2 sorteos/semana
- **Datos:** Ya tenemos 308 sorteos locales (5 años)
- **Limitación:** Solo comprable dentro de Ecuador

### 2. **La Primitiva (España)** ⭐⭐⭐⭐⭐
- **Por qué:** 6/49 (probabilidad 1:14M), datos desde 1985 (40+ años, >4,000 sorteos)
- **Comprable online:** Sí, vía thelotter.com desde cualquier país
- **Sorteos:** Jueves y sábado

### 3. **EuroMillions** ⭐⭐⭐⭐
- **Por qué:** 5/50 + 2/12, 2 sorteos/semana, datos desde 2004 (>2,000 sorteos)
- **Comprable online:** Sí, mundialmente
- **Premios:** Mínimo €17M, acumula rápido

### 4. **EuroJackpot** ⭐⭐⭐⭐
- **Por qué:** Similar a EuroMillions pero mejores odds secundarias, 18 países europeos
- **Comprable online:** Sí, mundialmente
- **Sorteos:** Martes y viernes

### 5. **El Gordo de la Primitiva** ⭐⭐⭐⭐
- **Por qué:** 5/54 + 1/10, 1 sorteo/semana pero probabilidades decentes (1:31M)
- **Comprable online:** Sí
- **Premios:** Mínimo €5M

## ❌ Loterías a EVITAR para predicción
- **SuperEnalotto (Italia):** 6/90, probabilidad 1:622M. Pool demasiado grande.
- **Mega Millions / Powerball USA:** Pool 69-70 números. Probabilidad 1:300M. Mucho ruido.
- **UK Lotto:** Cambió de formato en 2015 (de 6/49 a 6/59). Datos históricos fragmentados.

## 📊 Análisis de "predecibilidad"

| Lotería | Combinaciones | Sorteos históricos | Ratio datos/combs |
|---------|---------------|---------------------|-------------------|
| Pozo Millonario | 4,457,400 | 308 (local) / ~1,250 (desde 2012) | 0.00028 |
| La Primitiva | 13,983,816 | ~4,200 | 0.00030 |
| El Gordo | 31,625,100 | ~1,700 | 0.00005 |
| EuroMillions | 139,838,160 | ~2,200 | 0.00002 |
| Powerball USA | 292,201,338 | ~3,300 | 0.00001 |

**Conclusión:** Pozo Millonario y La Primitiva son las más "predecibles" estadísticamente.

## 🏗️ Arquitectura del predictor (lo mejor de los 3 repos)

### 9 motores de análisis (de `lotto-max-ml-predictor`):
1. Frequency Analysis (con Z-scores y chi-cuadrado)
2. Hot/Cold Tracker (con mean reversion)
3. Gap Analysis (overdue detection)
4. Markov Chain (1° y 2° orden)
5. Bayesian Inference (con Beta priors)
6. Pattern Detection (consecutivos, sumas, par/impar)
7. Entropy Scoring (Shannon + autocorrelación)
8. Monte Carlo Simulation (10K iteraciones)
9. Ensemble (combina los 8 anteriores con pesos)

### Extras adaptados:
- **Backtesting framework** (validación histórica de cada motor)
- **Multi-lotería** (config YAML por lotería)
- **Reporte Excel** con justificación de cada número
- **CLI** con flags --lottery, --engine, --backtest

### Dependencias mínimas
- **Core:** Solo Python 3.8+ stdlib (random, math, statistics, json, collections, datetime, itertools, argparse)
- **Opcional (LSTM):** TensorFlow 2.x + numpy
- **Visualización:** matplotlib (ya instalado)
