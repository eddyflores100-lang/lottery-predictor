# Contribuir a LotteryPredictor

¡Gracias por tu interés en contribuir! 🎰

## 🚀 Cómo contribuir

### Reportar bugs
1. Ve a [Issues](https://github.com/edgarfloresguerra2011-a11y/lottery-predictor/issues)
2. Abre un nuevo issue con el template de bug
3. Incluye: lotería, motor, error completo, pasos para reproducir

### Agregar una nueva lotería
1. Fork el repo
2. Agrega la config en `scripts/lottery_predictor/lotteries/generic.py`
3. Crea el data fetcher en `scripts/lottery_predictor/data_fetcher/`
4. Ejecuta backtesting: `python3 main.py --lottery nueva --backtest all`
5. Abre un Pull Request

### Agregar un nuevo motor
1. Crea el archivo en `scripts/lottery_predictor/engines/nuevo_motor.py`
2. Implementa `analyze()` y `predict()`
3. Regístralo en `engines/__init__.py`
4. Backtestea contra al menos 2 loterías
5. Abre un Pull Request

## 📋 Código de conducta
- Sé respetuoso
- Aporta evidencia estadística, no opiniones
- Si la lotería es aleatoria, dilo. No prometas milagros.

## ⚠️ Disclaimer
Este proyecto es educativo. NO garantiza ganancias. La lotería tiene EV negativo.
