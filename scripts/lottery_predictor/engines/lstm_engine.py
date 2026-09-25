"""
Engine 10: LSTM Neural Network
Deep learning prediction using TensorFlow/Keras.

Adapted from KittenCN/predict_Lottery_ticket (LSTM multicapa) and
cpeoples/powerpredict (Bidirectional LSTM/GRU hybrid).

Requires: tensorflow, numpy
Optional - falls back to frequency engine if TF not available.
"""
import math
from typing import List, Dict
from collections import Counter

# Try to import TF
try:
    import numpy as np
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional
    from tensorflow.keras.optimizers import Adam
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False


def is_available() -> bool:
    """Check if TensorFlow is available."""
    return TF_AVAILABLE


def _prepare_sequences(lottery, window_size: int = 10):
    """
    Prepare sequences for LSTM training.
    
    For each draw at position t, X = previous `window_size` draws (one-hot encoded),
    y = current draw (multi-label binary vector).
    """
    pool_size = lottery.main_pool_size
    draws = lottery.draws
    
    if len(draws) < window_size + 1:
        return None, None
    
    X, y = [], []
    for i in range(window_size, len(draws)):
        # Input: previous window_size draws, each as multi-hot vector
        seq = []
        for j in range(i - window_size, i):
            multi_hot = np.zeros(pool_size)
            for n in draws[j].main_numbers:
                if 1 <= n <= pool_size:
                    multi_hot[n - 1] = 1
            seq.append(multi_hot)
        X.append(np.array(seq))
        
        # Output: current draw as multi-hot
        target = np.zeros(pool_size)
        for n in draws[i].main_numbers:
            if 1 <= n <= pool_size:
                target[n - 1] = 1
        y.append(target)
    
    return np.array(X), np.array(y)


def _build_model(pool_size: int, window_size: int) -> 'Sequential':
    """Build LSTM model."""
    model = Sequential([
        Bidirectional(LSTM(64, return_sequences=True), input_shape=(window_size, pool_size)),
        Dropout(0.2),
        LSTM(32),
        Dropout(0.2),
        Dense(pool_size, activation='sigmoid')
    ])
    model.compile(
        optimizer=Adam(learning_rate=0.001),
        loss='binary_crossentropy',
        metrics=['accuracy']
    )
    return model


def train_model(lottery, window_size: int = 10, epochs: int = 30,
                verbose: int = 0, model_path: str = None) -> Dict:
    """
    Train an LSTM model on the lottery data.
    
    Returns:
        {model, history, training_size, window_size, pool_size}
    """
    if not TF_AVAILABLE:
        raise RuntimeError("TensorFlow not available. Install with: pip install tensorflow")
    
    pool_size = lottery.main_pool_size
    X, y = _prepare_sequences(lottery, window_size)
    if X is None:
        raise ValueError(f"Not enough data. Need >{window_size} draws, have {lottery.total_draws()}")
    
    model = _build_model(pool_size, window_size)
    
    # Log to stderr (not stdout, which is used for JSON output)
    import sys
    print(f"  Training LSTM on {len(X)} sequences, {epochs} epochs...", file=sys.stderr, flush=True)
    history = model.fit(X, y, epochs=epochs, batch_size=32, verbose=verbose, validation_split=0.1)
    
    # Save model if path provided
    if model_path:
        model.save(model_path)
        print(f"  Model saved to {model_path}", file=sys.stderr, flush=True)
    
    return {
        'model': model,
        'history': history.history,
        'training_size': len(X),
        'window_size': window_size,
        'pool_size': pool_size,
    }


def predict_next(lottery, model=None, window_size: int = 10) -> List[int]:
    """
    Predict next draw using trained LSTM model.
    """
    if not TF_AVAILABLE:
        # Fallback to frequency
        from .frequency import predict as freq_predict
        return freq_predict(lottery)
    
    if model is None:
        # Train a quick model on the fly
        result = train_model(lottery, window_size=window_size, epochs=20, verbose=0)
        model = result['model']
    
    pool_size = lottery.main_pool_size
    draws = lottery.draws
    
    # Build input from last window_size draws
    if len(draws) < window_size:
        from .frequency import predict as freq_predict
        return freq_predict(lottery)
    
    seq = []
    for j in range(len(draws) - window_size, len(draws)):
        multi_hot = np.zeros(pool_size)
        for n in draws[j].main_numbers:
            if 1 <= n <= pool_size:
                multi_hot[n - 1] = 1
        seq.append(multi_hot)
    
    X = np.array([seq])
    prediction = model.predict(X, verbose=0)[0]
    
    # Get top picks
    ranked_indices = np.argsort(prediction)[::-1]
    return [int(idx + 1) for idx in ranked_indices[:lottery.main_picks]]


def analyze(lottery, window_size: int = 10, epochs: int = 20) -> Dict:
    """
    Train and analyze with LSTM. Returns prediction + training info.
    """
    if not TF_AVAILABLE:
        return {
            'error': 'TensorFlow not available',
            'fallback': 'Use frequency engine instead',
        }
    
    try:
        result = train_model(lottery, window_size=window_size, epochs=epochs, verbose=0)
        prediction = predict_next(lottery, model=result['model'], window_size=window_size)
        
        return {
            'tf_available': True,
            'training_size': result['training_size'],
            'window_size': result['window_size'],
            'final_loss': result['history'].get('loss', [None])[-1],
            'final_val_loss': result['history'].get('val_loss', [None])[-1],
            'final_accuracy': result['history'].get('accuracy', [None])[-1],
            'prediction': prediction,
            'total_draws': lottery.total_draws(),
        }
    except Exception as e:
        return {'error': str(e)}


def predict(lottery, window_size: int = 10) -> List[int]:
    """Predict using LSTM. Falls back to frequency if TF unavailable."""
    if not TF_AVAILABLE:
        from .frequency import predict as freq_predict
        return freq_predict(lottery)
    
    try:
        # Use fewer epochs for live prediction (faster)
        result = train_model(lottery, window_size=window_size, epochs=10, verbose=0)
        return predict_next(lottery, model=result['model'], window_size=window_size)
    except Exception as e:
        # Fallback
        from .frequency import predict as freq_predict
        return freq_predict(lottery)
