"""
poisson_model.py - Poisson-based scoreline probability model (Dixon-Coles style)

Provides utilities to fit team attack/defense strengths from historical dataset
and to compute scoreline probabilities for a given match-up.
"""

from __future__ import annotations

import os
import pickle
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from math import exp, factorial

DATASET_PATH = 'master_dataset.csv'
CACHE_PATH = 'poisson_strengths.pkl'


def _poisson_pmf(lmbda: float, k: int) -> float:
    return (lmbda ** k) * exp(-lmbda) / factorial(k)


def compute_strengths(df: pd.DataFrame) -> Tuple[Dict[str, Dict[str, float]], float, float]:
    """
    Compute team attack/defense strengths using league averages.
    Returns (strengths, mu_home, mu_away)
    strengths[team] = {
       'home_attack', 'home_defense', 'away_attack', 'away_defense'
    }
    """
    # Filter needed columns
    cols = ['HomeTeam', 'AwayTeam', 'FTHG', 'FTAG']
    df = df.dropna(subset=cols)[cols].copy()

    # League averages
    mu_home = df['FTHG'].mean()
    mu_away = df['FTAG'].mean()

    strengths: Dict[str, Dict[str, float]] = {}

    teams = pd.unique(pd.concat([df['HomeTeam'], df['AwayTeam']]))

    for team in teams:
        home_matches = df[df['HomeTeam'] == team]
        away_matches = df[df['AwayTeam'] == team]

        # Avoid division by zero
        home_count = max(1, len(home_matches))
        away_count = max(1, len(away_matches))

        home_gf = home_matches['FTHG'].sum() / home_count
        home_ga = home_matches['FTAG'].sum() / home_count
        away_gf = away_matches['FTAG'].sum() / away_count
        away_ga = away_matches['FTHG'].sum() / away_count

        strengths[team] = {
            'home_attack': (home_gf / mu_home) if mu_home > 0 else 1.0,
            'home_defense': (home_ga / mu_away) if mu_away > 0 else 1.0,
            'away_attack': (away_gf / mu_away) if mu_away > 0 else 1.0,
            'away_defense': (away_ga / mu_home) if mu_home > 0 else 1.0,
        }

    return strengths, mu_home, mu_away


def load_or_fit_strengths(force: bool = False) -> Tuple[Dict[str, Dict[str, float]], float, float]:
    if not force and os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, 'rb') as f:
                data = pickle.load(f)
                return data['strengths'], data['mu_home'], data['mu_away']
        except Exception:
            pass

    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError('master_dataset.csv not found')

    df = pd.read_csv(DATASET_PATH)
    strengths, mu_home, mu_away = compute_strengths(df)

    try:
        with open(CACHE_PATH, 'wb') as f:
            pickle.dump({'strengths': strengths, 'mu_home': mu_home, 'mu_away': mu_away}, f)
    except Exception:
        pass

    return strengths, mu_home, mu_away


def expected_goals(home_team: str, away_team: str, strengths: Dict[str, Dict[str, float]], mu_home: float, mu_away: float) -> Tuple[float, float]:
    """Compute lambda_home and lambda_away using strengths; fallback to league avgs if team not found."""
    sh = strengths.get(home_team)
    sa = strengths.get(away_team)
    if sh and sa:
        lam_home = mu_home * sh['home_attack'] * sa['away_defense']
        lam_away = mu_away * sa['away_attack'] * sh['home_defense']
        return max(lam_home, 0.05), max(lam_away, 0.05)
    # Fallback: slight home advantage
    return max(mu_home, 0.05), max(mu_away, 0.05)


def score_matrix(lam_home: float, lam_away: float, max_goals: int = 6) -> np.ndarray:
    """Return matrix P[i,j] = P(home=i, away=j)"""
    i = np.arange(0, max_goals + 1)
    ph = np.array([_poisson_pmf(lam_home, k) for k in i])
    pa = np.array([_poisson_pmf(lam_away, k) for k in i])
    return np.outer(ph, pa)


def ou_probabilities(prob: np.ndarray, line: float) -> Tuple[float, float, float]:
    """Return (P(Over line), P(Under line), P(Push)) using discrete totals."""
    max_goals = prob.shape[0] - 1
    # Total goals distribution
    totals = np.zeros(2 * max_goals + 1)
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            totals[h + a] += prob[h, a]
    # Over/Under computation
    over = sum(totals[int(line) + 1:]) if line.is_integer() else sum(totals[int(np.floor(line)) + 1:])
    under = 1.0 - over
    push = 0.0
    if line.is_integer():
        push = totals[int(line)]
        under = max(0.0, under - push)
    return float(over), float(under), float(push)


def top_scorelines(prob: np.ndarray, n: int = 5) -> list[Tuple[str, float]]:
    pairs = []
    max_goals = prob.shape[0] - 1
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            pairs.append((f"{h}-{a}", float(prob[h, a])))
    pairs.sort(key=lambda x: x[1], reverse=True)
    return pairs[:n]
