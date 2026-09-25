"""
Pozo Millonario (Ecuador) — 11/25 + mascota
Odds: 1 in 4,457,400
"""
from pathlib import Path
from typing import Optional
import json
from .base import Lottery, DrawResult


class PozoMillonario(Lottery):
    name = "Pozo Millonario"
    country = "Ecuador"
    main_pool_size = 25
    main_picks = 11
    bonus_pool_size = 0
    bonus_picks = 0
    draws_per_week = 2
    currency = "USD"
    min_jackpot = 500_000
    odds_jackpot = 4_457_400
    
    def load_data(self, source: str) -> None:
        """
        Load from our pre-parsed JSON file at /home/z/my-project/data/pozo_data.json
        Format: list of {sorteo_num, fecha, dia_semana, numeros, mascota, premios, ...}
        """
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Data file not found: {source}")
        
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        
        self.draws = []
        for r in data:
            # Normalize prize keys to int
            premios = {}
            for k, v in r.get('premios', {}).items():
                if isinstance(k, str) and k.isdigit():
                    premios[int(k)] = v
                else:
                    premios[k] = v
            
            # Determine if jackpot was won (ganadores 11 > 0)
            p11 = premios.get(11, {})
            jackpot_won = bool(p11.get('ganadores') and p11['ganadores'] > 0)
            jackpot_amount = p11.get('premio_indiv') if jackpot_won else None
            
            draw = DrawResult(
                draw_number=r['sorteo_num'],
                date=r['fecha'],
                main_numbers=r['numeros'],
                bonus_numbers=[],  # mascot is metadata, not a bonus number
                jackpot_won=jackpot_won,
                jackpot_amount=jackpot_amount,
                raw_data={
                    'mascota': r.get('mascota'),
                    'dia_semana': r.get('dia_semana'),
                    'premios': premios,
                    'revancha': r.get('revancha', {}),
                    'proximo': r.get('proximo', {}),
                }
            )
            self.draws.append(draw)
        
        self.draws.sort(key=lambda d: d.draw_number)
    
    def get_mascots_history(self):
        """Get list of (draw_number, mascot) tuples."""
        return [(d.draw_number, d.raw_data.get('mascota')) for d in self.draws]
