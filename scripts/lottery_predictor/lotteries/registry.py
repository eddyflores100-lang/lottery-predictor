"""
La Primitiva (España) — 6/49 + reintegro (0-9)
Odds: 1 in 13,983,816
Data: from official Spanish lottery site (selae.es) or third-party APIs
"""
from pathlib import Path
from typing import Optional
import json
from .base import Lottery, DrawResult
from .pozo_millonario import PozoMillonario


class LaPrimitiva(Lottery):
    name = "La Primitiva"
    country = "España"
    main_pool_size = 49
    main_picks = 6
    bonus_pool_size = 10  # Reintegro 0-9
    bonus_picks = 1
    draws_per_week = 2  # Jueves y Sábado
    currency = "EUR"
    min_jackpot = 8_000_000  # €8M mínimo
    odds_jackpot = 13_983_816
    
    def load_data(self, source: str) -> None:
        """
        Load from JSON file. Expected format:
        [{"draw_number": int, "date": "YYYY-MM-DD", "main_numbers": [6 ints],
          "bonus_numbers": [1 int] (reintegro), "jackpot_amount": float}, ...]
        """
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Data file not found: {source}")
        
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        
        self.draws = []
        for r in data:
            draw = DrawResult(
                draw_number=r['draw_number'],
                date=r['date'],
                main_numbers=r['main_numbers'],
                bonus_numbers=r.get('bonus_numbers', []),
                jackpot_won=r.get('jackpot_won', False),
                jackpot_amount=r.get('jackpot_amount'),
                raw_data=r.get('raw_data', {})
            )
            self.draws.append(draw)
        
        self.draws.sort(key=lambda d: d.draw_number)


class EuroMillions(Lottery):
    """EuroMillions — 5/50 + 2/12 stars. Odds: 1 in 139,838,160"""
    name = "EuroMillions"
    country = "Europa"
    main_pool_size = 50
    main_picks = 5
    bonus_pool_size = 12
    bonus_picks = 2
    draws_per_week = 2  # Martes y Viernes
    currency = "EUR"
    min_jackpot = 17_000_000
    odds_jackpot = 139_838_160
    
    def load_data(self, source: str) -> None:
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Data file not found: {source}")
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        self.draws = []
        for r in data:
            draw = DrawResult(
                draw_number=r['draw_number'],
                date=r['date'],
                main_numbers=r['main_numbers'],
                bonus_numbers=r.get('bonus_numbers', []),
                jackpot_won=r.get('jackpot_won', False),
                jackpot_amount=r.get('jackpot_amount'),
                raw_data=r.get('raw_data', {})
            )
            self.draws.append(draw)
        self.draws.sort(key=lambda d: d.draw_number)


class EuroJackpot(Lottery):
    """EuroJackpot — 5/50 + 2/10. Odds: 1 in 139,838,160"""
    name = "EuroJackpot"
    country = "Europa"
    main_pool_size = 50
    main_picks = 5
    bonus_pool_size = 10
    bonus_picks = 2
    draws_per_week = 2  # Martes y Viernes
    currency = "EUR"
    min_jackpot = 10_000_000
    odds_jackpot = 139_838_160
    
    def load_data(self, source: str) -> None:
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Data file not found: {source}")
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        self.draws = []
        for r in data:
            draw = DrawResult(
                draw_number=r['draw_number'],
                date=r['date'],
                main_numbers=r['main_numbers'],
                bonus_numbers=r.get('bonus_numbers', []),
                jackpot_won=r.get('jackpot_won', False),
                jackpot_amount=r.get('jackpot_amount'),
                raw_data=r.get('raw_data', {})
            )
            self.draws.append(draw)
        self.draws.sort(key=lambda d: d.draw_number)


class ElGordo(Lottery):
    """El Gordo de la Primitiva — 5/54 + 1/10. Odds: 1 in 31,625,100"""
    name = "El Gordo"
    country = "España"
    main_pool_size = 54
    main_picks = 5
    bonus_pool_size = 10
    bonus_picks = 1
    draws_per_week = 1  # Domingo
    currency = "EUR"
    min_jackpot = 5_000_000
    odds_jackpot = 31_625_100
    
    def load_data(self, source: str) -> None:
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Data file not found: {source}")
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        self.draws = []
        for r in data:
            draw = DrawResult(
                draw_number=r['draw_number'],
                date=r['date'],
                main_numbers=r['main_numbers'],
                bonus_numbers=r.get('bonus_numbers', []),
                jackpot_won=r.get('jackpot_won', False),
                jackpot_amount=r.get('jackpot_amount'),
                raw_data=r.get('raw_data', {})
            )
            self.draws.append(draw)
        self.draws.sort(key=lambda d: d.draw_number)


# Registry
LOTTERY_REGISTRY = {
    'pozo_millonario': PozoMillonario,
    'la_primitiva': LaPrimitiva,
    'euromillions': EuroMillions,
    'eurojackpot': EuroJackpot,
    'el_gordo': ElGordo,
}


def get_lottery(name: str) -> Lottery:
    """Get a lottery instance by name."""
    name = name.lower().replace(' ', '_').replace('-', '_')
    if name not in LOTTERY_REGISTRY:
        raise ValueError(f"Unknown lottery: {name}. Available: {list(LOTTERY_REGISTRY.keys())}")
    return LOTTERY_REGISTRY[name]()
