"""
Generate temporal visualizations for lottery analysis.

Creates:
1. Heatmap of number frequency over time (years × numbers)
2. Timeline of suspicious draws
3. Hot/cold evolution per number
4. Sum distribution evolution
5. Par/impar distribution over time
6. Autocorrelation plots

Saves as PNG to /home/z/my-project/download/charts/
"""
import sys, os, json, math
sys.path.insert(0, '/home/z/my-project/scripts/lottery_predictor')
sys.path.insert(0, '/home/z/my-project/skills/xlsx/templates')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

# Register Chinese font (also covers Spanish characters)
try:
    fm.fontManager.addfont('/usr/share/fonts/truetype/chinese/NotoSansSC-Regular.ttf')
except:
    pass
plt.rcParams['font.sans-serif'] = ['Noto Sans SC', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

from lotteries import get_lottery, NEW_LOTTERIES

OUTPUT_DIR = Path('/home/z/my-project/download/charts')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DATA_PATHS = {
    'pozo_millonario': '/home/z/my-project/data/pozo_data.json',
    'euromillions': '/home/z/my-project/data/euromillions.json',
    'la_primitiva': '/home/z/my-project/data/la_primitiva.json',
    'lotto_austrian': '/home/z/my-project/data/lotto_austrian.json',
    'uk49s': '/home/z/my-project/data/uk49s.json',
}
for k, v in NEW_LOTTERIES.items():
    DATA_PATHS[k] = v['data_file']


def load_lottery(key):
    lot = get_lottery(key)
    lot.load_data(DATA_PATHS[key])
    return lot


def plot_frequency_heatmap(lottery, output_path=None):
    """
    Heatmap: years (rows) × numbers (cols), color = frequency.
    Shows how each number's frequency evolved over time.
    """
    if not lottery.draws:
        return None
    
    # Group draws by year
    year_data = defaultdict(lambda: Counter())
    for d in lottery.draws:
        try:
            year = int(d.date[:4])
            for n in d.main_numbers:
                year_data[year][n] += 1
        except:
            continue
    
    if not year_data:
        return None
    
    years = sorted(year_data.keys())
    pool_size = lottery.main_pool_size
    
    # Build matrix
    matrix = np.zeros((len(years), pool_size))
    for i, year in enumerate(years):
        for n in range(1, pool_size + 1):
            matrix[i, n-1] = year_data[year].get(n, 0)
    
    # Normalize per year (since some years have more draws)
    row_sums = matrix.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    matrix_norm = matrix / row_sums * pool_size  # expected = 1.0 if uniform
    
    fig, ax = plt.subplots(figsize=(16, 6), constrained_layout=True)
    im = ax.imshow(matrix_norm, aspect='auto', cmap='RdYlGn_r', vmin=0.5, vmax=1.5)
    
    ax.set_xticks(range(pool_size))
    ax.set_xticklabels([str(n) for n in range(1, pool_size + 1)], fontsize=7)
    ax.set_yticks(range(len(years)))
    ax.set_yticklabels(years, fontsize=9)
    ax.set_xlabel('Número', fontsize=11)
    ax.set_ylabel('Año', fontsize=11)
    ax.set_title(f'{lottery.name} — Frecuencia por Año (1.0 = uniforme)\nVerde = más frecuente, Rojo = menos frecuente', fontsize=12)
    
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('Frecuencia normalizada', fontsize=10)
    
    path = output_path or OUTPUT_DIR / f'{lottery.name}_heatmap.png'
    plt.savefig(path, dpi=120)
    plt.close()
    return str(path)


def plot_hot_cold_evolution(lottery, output_path=None, top_n=10):
    """
    Line chart showing how the top-N most frequent numbers evolved over time.
    X-axis: draw number, Y-axis: rolling frequency (last 100 draws).
    """
    if len(lottery.draws) < 100:
        return None
    
    pool_size = lottery.main_pool_size
    window = 100
    
    # Compute overall top N most frequent numbers
    counter = Counter()
    for d in lottery.draws:
        for n in d.main_numbers:
            counter[n] += 1
    top_numbers = [n for n, _ in counter.most_common(top_n)]
    
    # Compute rolling frequency for each top number
    fig, ax = plt.subplots(figsize=(16, 8), constrained_layout=True)
    
    for n in top_numbers:
        rolling_freq = []
        for i in range(window, len(lottery.draws) + 1):
            count = sum(1 for d in lottery.draws[i-window:i] if n in d.main_numbers)
            rolling_freq.append(count / window)
        ax.plot(range(window, len(lottery.draws) + 1), rolling_freq, label=f'#{n:02d}', alpha=0.7, linewidth=1)
    
    # Expected frequency line
    expected = lottery.main_picks / pool_size
    ax.axhline(y=expected, color='black', linestyle='--', alpha=0.5, label=f'Esperado ({expected:.2f})')
    
    ax.set_xlabel('Sorteo #', fontsize=11)
    ax.set_ylabel('Frecuencia rolling (últimos 100 sorteos)', fontsize=11)
    ax.set_title(f'{lottery.name} — Evolución Hot/Cold (top {top_n} números)', fontsize=12)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8, ncol=2)
    ax.grid(True, alpha=0.3)
    
    path = output_path or OUTPUT_DIR / f'{lottery.name}_hot_cold_evolution.png'
    plt.savefig(path, dpi=120)
    plt.close()
    return str(path)


def plot_sum_distribution_evolution(lottery, output_path=None):
    """
    Box plot showing how sum of numbers evolved over time (by year).
    Reveals if sums are drifting or stable.
    """
    if not lottery.draws:
        return None
    
    year_sums = defaultdict(list)
    for d in lottery.draws:
        try:
            year = int(d.date[:4])
            unique_nums = list(set(d.main_numbers))
            year_sums[year].append(sum(unique_nums))
        except:
            continue
    
    if not year_sums:
        return None
    
    years = sorted(year_sums.keys())
    data = [year_sums[y] for y in years]
    
    fig, ax = plt.subplots(figsize=(14, 6), constrained_layout=True)
    bp = ax.boxplot(data, labels=years, patch_artist=True, showmeans=True)
    
    # Color boxes
    for patch in bp['boxes']:
        patch.set_facecolor('#4C72B0')
        patch.set_alpha(0.6)
    
    ax.set_xlabel('Año', fontsize=11)
    ax.set_ylabel('Suma de números', fontsize=11)
    ax.set_title(f'{lottery.name} — Distribución de sumas por año', fontsize=12)
    ax.grid(True, alpha=0.3, axis='y')
    
    path = output_path or OUTPUT_DIR / f'{lottery.name}_sum_evolution.png'
    plt.savefig(path, dpi=120)
    plt.close()
    return str(path)


def plot_parity_evolution(lottery, output_path=None):
    """
    Stacked area chart: % pares vs impares over time.
    """
    if len(lottery.draws) < 50:
        return None
    
    window = 50
    pares_pct = []
    impares_pct = []
    x = []
    
    for i in range(window, len(lottery.draws) + 1):
        pares = 0
        impares = 0
        for d in lottery.draws[i-window:i]:
            for n in d.main_numbers:
                if n % 2 == 0:
                    pares += 1
                else:
                    impares += 1
        total = pares + impares
        if total > 0:
            pares_pct.append(pares / total * 100)
            impares_pct.append(impares / total * 100)
            x.append(i)
    
    fig, ax = plt.subplots(figsize=(14, 6), constrained_layout=True)
    ax.fill_between(x, 0, pares_pct, alpha=0.6, color='#4C72B0', label='Pares')
    ax.fill_between(x, pares_pct, 100, alpha=0.6, color='#C44E52', label='Impares')
    ax.axhline(y=50, color='black', linestyle='--', alpha=0.5)
    ax.set_xlabel('Sorteo #', fontsize=11)
    ax.set_ylabel('% (rolling 50 sorteos)', fontsize=11)
    ax.set_title(f'{lottery.name} — Evolución Pares vs Impares', fontsize=12)
    ax.legend(loc='upper right')
    ax.set_ylim(0, 100)
    ax.grid(True, alpha=0.3)
    
    path = output_path or OUTPUT_DIR / f'{lottery.name}_parity_evolution.png'
    plt.savefig(path, dpi=120)
    plt.close()
    return str(path)


def plot_suspicious_timeline(lottery, output_path=None):
    """
    Timeline of suspicious draws (4+ consecutive, all same parity, etc.).
    Each event plotted as a dot on the timeline.
    """
    if not lottery.draws:
        return None
    
    suspicious = []
    for d in lottery.draws:
        nums = sorted(set(d.main_numbers))
        reasons = []
        
        # 4+ consecutive
        max_consec = 1
        consec = 1
        for i in range(1, len(nums)):
            if nums[i] == nums[i-1] + 1:
                consec += 1
                max_consec = max(max_consec, consec)
            else:
                consec = 1
        if max_consec >= 4:
            reasons.append(f'{max_consec} consec')
        
        # All same parity
        pares = sum(1 for n in nums if n % 2 == 0)
        if pares == 0 or pares == len(nums):
            reasons.append('all same parity')
        
        if reasons:
            try:
                dt = datetime.strptime(d.date, '%Y-%m-%d')
                suspicious.append((dt, reasons, d.draw_number))
            except:
                pass
    
    if not suspicious:
        return None
    
    fig, ax = plt.subplots(figsize=(16, 6), constrained_layout=True)
    
    # Plot all draws as a faint baseline
    all_dates = []
    for d in lottery.draws:
        try:
            all_dates.append(datetime.strptime(d.date, '%Y-%m-%d'))
        except:
            pass
    if all_dates:
        ax.scatter(all_dates, [0]*len(all_dates), alpha=0.1, s=10, color='gray')
    
    # Plot suspicious
    for dt, reasons, draw_num in suspicious:
        ax.scatter([dt], [1], color='red', s=80, zorder=5, edgecolors='darkred')
    
    ax.set_xlabel('Fecha', fontsize=11)
    ax.set_ylabel('', fontsize=11)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(['Normal', 'Sospechoso'])
    ax.set_title(f'{lottery.name} — Timeline de sorteos sospechosos ({len(suspicious)} eventos)', fontsize=12)
    ax.grid(True, alpha=0.3, axis='x')
    
    plt.xticks(rotation=45)
    
    path = output_path or OUTPUT_DIR / f'{lottery.name}_suspicious_timeline.png'
    plt.savefig(path, dpi=120)
    plt.close()
    return str(path)


def plot_number_co_occurrence_matrix(lottery, output_path=None):
    """
    Heatmap of co-occurrence: how often each pair of numbers appears together.
    """
    pool_size = lottery.main_pool_size
    matrix = np.zeros((pool_size, pool_size))
    
    for d in lottery.draws:
        nums = sorted(set(d.main_numbers))
        for i in range(len(nums)):
            for j in range(i+1, len(nums)):
                a, b = nums[i]-1, nums[j]-1
                matrix[a, b] += 1
                matrix[b, a] += 1
    
    # Normalize
    total_draws = len(lottery.draws)
    if total_draws > 0:
        matrix_norm = matrix / total_draws * 100  # percentage
    else:
        matrix_norm = matrix
    
    fig, ax = plt.subplots(figsize=(12, 10), constrained_layout=True)
    im = ax.imshow(matrix_norm, cmap='YlOrRd', aspect='auto')
    
    ax.set_xticks(range(pool_size))
    ax.set_xticklabels([str(n) for n in range(1, pool_size + 1)], fontsize=7)
    ax.set_yticks(range(pool_size))
    ax.set_yticklabels([str(n) for n in range(1, pool_size + 1)], fontsize=7)
    ax.set_xlabel('Número', fontsize=11)
    ax.set_ylabel('Número', fontsize=11)
    ax.set_title(f'{lottery.name} — Matriz de co-ocurrencia (% de sorteos)', fontsize=12)
    
    cbar = plt.colorbar(im, ax=ax, shrink=0.7)
    cbar.set_label('% co-ocurrencia', fontsize=10)
    
    path = output_path or OUTPUT_DIR / f'{lottery.name}_cooccurrence.png'
    plt.savefig(path, dpi=120)
    plt.close()
    return str(path)


def generate_all_visualizations(lottery_key: str):
    """Generate all 6 visualizations for a lottery."""
    lottery = load_lottery(lottery_key)
    print(f"\n📊 Generating visualizations for {lottery.name} ({lottery.total_draws()} draws)...")
    
    paths = []
    
    print("  1. Frequency heatmap...")
    p = plot_frequency_heatmap(lottery)
    if p: paths.append(p)
    
    print("  2. Hot/cold evolution...")
    p = plot_hot_cold_evolution(lottery)
    if p: paths.append(p)
    
    print("  3. Sum distribution evolution...")
    p = plot_sum_distribution_evolution(lottery)
    if p: paths.append(p)
    
    print("  4. Parity evolution...")
    p = plot_parity_evolution(lottery)
    if p: paths.append(p)
    
    print("  5. Suspicious timeline...")
    p = plot_suspicious_timeline(lottery)
    if p: paths.append(p)
    
    print("  6. Co-occurrence matrix...")
    p = plot_number_co_occurrence_matrix(lottery)
    if p: paths.append(p)
    
    print(f"  ✓ Generated {len(paths)} charts in {OUTPUT_DIR}")
    return paths


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--lottery', default='euromillions')
    parser.add_argument('--all', action='store_true')
    args = parser.parse_args()
    
    if args.all:
        for key in ['euromillions', 'la_primitiva', 'lotto_austrian', 'pozo_millonario', 'uk49s']:
            try:
                generate_all_visualizations(key)
            except Exception as e:
                print(f"  ✗ {key}: {e}")
    else:
        generate_all_visualizations(args.lottery)
