"""
Austrian Lotto 6 aus 45 — 6/45 + Zusatzzahl
Odds: 1 in 8,145,060 (better than La Primitiva!)
"""
from pathlib import Path
import json
from .base import Lottery, DrawResult


class LottoAustrian(Lottery):
    name = "Lotto 6 aus 45 (Austria)"
    country = "Austria"
    main_pool_size = 45
    main_picks = 6
    bonus_pool_size = 45  # Zusatzzahl is from same pool
    bonus_picks = 1
    draws_per_week = 2  # Wednesday and Sunday
    currency = "EUR"
    min_jackpot = 1_500_000
    odds_jackpot = 8_145_060
    
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
