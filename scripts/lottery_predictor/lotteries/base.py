"""
Lottery base class — Abstract interface for all lotteries.
Each lottery defines its own rules (pool size, picks, format).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
import json
from pathlib import Path


@dataclass
class DrawResult:
    """A single draw result."""
    draw_number: int                    # Sorteo number
    date: str                           # ISO date YYYY-MM-DD
    main_numbers: List[int]             # Main numbers drawn
    bonus_numbers: List[int] = field(default_factory=list)  # Bonus/extra numbers
    jackpot_won: bool = False           # Was the jackpot won?
    jackpot_amount: Optional[float] = None  # Jackpot amount (if known)
    raw_data: Dict = field(default_factory=dict)  # Extra metadata


class Lottery(ABC):
    """Abstract base class for all lotteries."""
    
    name: str = "Base Lottery"
    country: str = ""
    main_pool_size: int = 0       # e.g. 25 for Pozo Millonario
    main_picks: int = 0           # e.g. 11 for Pozo Millonario
    bonus_pool_size: int = 0      # e.g. 12 for EuroMillions stars
    bonus_picks: int = 0          # e.g. 2 for EuroMillions stars
    draws_per_week: int = 1
    currency: str = "USD"
    min_jackpot: float = 0
    odds_jackpot: int = 0         # 1 in N
    
    def __init__(self, data_file: Optional[str] = None):
        self.draws: List[DrawResult] = []
        if data_file:
            self.load_data(data_file)
    
    @abstractmethod
    def load_data(self, source: str) -> None:
        """Load historical draw data from file or URL."""
        pass
    
    def add_draw(self, draw: DrawResult) -> None:
        """Add a draw to history."""
        self.draws.append(draw)
        # Keep sorted by draw number
        self.draws.sort(key=lambda d: d.draw_number)
    
    def get_main_numbers_history(self) -> List[List[int]]:
        """Get list of all main number sets."""
        return [d.main_numbers for d in self.draws]
    
    def get_bonus_numbers_history(self) -> List[List[int]]:
        """Get list of all bonus number sets."""
        return [d.bonus_numbers for d in self.draws]
    
    def get_recent_draws(self, n: int = 50) -> List[DrawResult]:
        """Get the N most recent draws."""
        return self.draws[-n:] if len(self.draws) >= n else self.draws
    
    def get_last_draw(self) -> Optional[DrawResult]:
        """Get the most recent draw."""
        return self.draws[-1] if self.draws else None
    
    def total_draws(self) -> int:
        """Total number of draws loaded."""
        return len(self.draws)
    
    def date_range(self) -> Optional[tuple]:
        """Returns (earliest_date, latest_date) as strings."""
        if not self.draws:
            return None
        return (self.draws[0].date, self.draws[-1].date)
    
    def describe(self) -> str:
        """Human-readable description of this lottery."""
        return (f"{self.name} ({self.country})\n"
                f"  Format: {self.main_picks}/{self.main_pool_size}"
                + (f" + {self.bonus_picks}/{self.bonus_pool_size}" if self.bonus_picks else "")
                + f"\n  Draws/week: {self.draws_per_week}\n"
                f"  Currency: {self.currency}\n"
                f"  Min jackpot: {self.currency} {self.min_jackpot:,.0f}\n"
                f"  Jackpot odds: 1 in {self.odds_jackpot:,}\n"
                f"  Total draws loaded: {self.total_draws()}")
    
    def to_dict(self) -> Dict:
        """Serialize lottery state to dict."""
        return {
            'name': self.name,
            'country': self.country,
            'main_pool_size': self.main_pool_size,
            'main_picks': self.main_picks,
            'bonus_pool_size': self.bonus_pool_size,
            'bonus_picks': self.bonus_picks,
            'draws_per_week': self.draws_per_week,
            'currency': self.currency,
            'min_jackpot': self.min_jackpot,
            'odds_jackpot': self.odds_jackpot,
            'draws': [
                {
                    'draw_number': d.draw_number,
                    'date': d.date,
                    'main_numbers': d.main_numbers,
                    'bonus_numbers': d.bonus_numbers,
                    'jackpot_won': d.jackpot_won,
                    'jackpot_amount': d.jackpot_amount,
                    'raw_data': d.raw_data,
                } for d in self.draws
            ]
        }
    
    def save_json(self, path: str) -> None:
        """Save lottery state to JSON file."""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
