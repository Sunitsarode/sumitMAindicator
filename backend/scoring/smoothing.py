import pandas as pd

def apply_sma_smoothing(scores, sma9=9, sma21=21):
    """Apply SMA smoothing to composite scores"""
    scores['avg_sma9'] = scores['avg_score'].rolling(window=sma9).mean()
    scores['avg_sma21'] = scores['avg_score'].rolling(window=sma21).mean()
    
    scores['weighted_sma9'] = scores['weighted_avg_score'].rolling(window=sma9).mean()
    scores['weighted_sma21'] = scores['weighted_avg_score'].rolling(window=sma21).mean()
    
    return scores
