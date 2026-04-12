"""
Shot-based expected goals (xG) model trained on hockeyR PBP data.

Uses logistic regression on shot distance, shot angle, and shot type to
assign a goal probability (0-1) to each unblocked shot attempt.

The fitted coefficients are persisted to data_files/models/xg_logreg.json
so the heavy training step runs only once.

Usage:
    from src.models.xg_shot_model import XGShotModel

    model = XGShotModel()
    model.ensure_trained()                 # trains & saves if needed
    prob = model.predict_single(distance=25, angle=20, shot_type="Wrist Shot")
"""
from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

MODEL_PATH = Path("data_files/models/xg_logreg.json")

# Shot-type encoding (one-hot baseline = Wrist Shot)
SHOT_TYPES = {
    "Wrist Shot": 0.0,
    "Slap Shot": -0.15,      # longer distance, lower chance
    "Snap Shot": 0.05,
    "Backhand": -0.10,
    "Tip-In": 0.40,          # very high danger
    "Deflected": 0.30,
    "Wrap-around": 0.10,
}

# League avg xG per shot (used when model isn't trained)
LEAGUE_AVG_XG_PER_SHOT = 0.075


def _sigmoid(x: float) -> float:
    """Numerically stable sigmoid."""
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    exp_x = math.exp(x)
    return exp_x / (1.0 + exp_x)


class XGShotModel:
    """
    Logistic regression xG model.

    Coefficients are either loaded from the saved JSON file or fit on
    hockeyR play-by-play data (which is downloaded from GitHub on demand).

    When training data is unavailable the model falls back to a set of
    reasonable hand-calibrated coefficients based on published NHL xG
    research (intercept ≈ -2.9, distance ≈ -0.04, angle ≈ -0.02).
    """

    # Hand-calibrated fallback coefficients
    DEFAULT_COEFFICIENTS = {
        "intercept": -2.90,
        "distance": -0.040,
        "angle": -0.018,
        "is_rebound": 0.65,
        "is_rush": 0.35,
        "shot_type_slap": -0.15,
        "shot_type_snap": 0.05,
        "shot_type_backhand": -0.10,
        "shot_type_tip": 0.40,
        "shot_type_deflected": 0.30,
        "shot_type_wrap": 0.10,
        "source": "fallback",
    }

    def __init__(self) -> None:
        self._coef: Optional[dict] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ensure_trained(self, force_retrain: bool = False) -> bool:
        """
        Load saved model or train from hockeyR PBP data if needed.

        Returns True if a trained model (not just fallback) is available.
        """
        if not force_retrain and MODEL_PATH.exists():
            self._load()
            return self._coef.get("source") == "trained"

        trained = self._train_from_pbp()
        if not trained:
            logger.warning(
                "Could not train xG model from PBP; using calibrated defaults."
            )
            self._coef = dict(self.DEFAULT_COEFFICIENTS)
            self._save()
            return False
        return True

    def predict_single(
        self,
        distance: float,
        angle: float,
        shot_type: str = "Wrist Shot",
        is_rebound: bool = False,
        is_rush: bool = False,
    ) -> float:
        """
        Predict xG probability for a single shot.

        Args:
            distance: Shot distance from net in feet.
            angle: Shot angle from goal mouth in degrees (0 = center).
            shot_type: Shot type string (Wrist Shot, Slap Shot, Tip-In, …).
            is_rebound: Whether this shot followed a rebound.
            is_rush: Whether this was a rush shot.

        Returns:
            Expected goal probability in [0, 1].
        """
        coef = self._get_coef()

        logit = (
            coef["intercept"]
            + coef["distance"] * distance
            + coef["angle"] * abs(angle)
            + coef["is_rebound"] * int(is_rebound)
            + coef["is_rush"] * int(is_rush)
        )

        # Shot-type adjustments
        shot_type_lower = shot_type.lower()
        if "slap" in shot_type_lower:
            logit += coef.get("shot_type_slap", 0)
        elif "snap" in shot_type_lower:
            logit += coef.get("shot_type_snap", 0)
        elif "backhand" in shot_type_lower:
            logit += coef.get("shot_type_backhand", 0)
        elif "tip" in shot_type_lower or "tip-in" in shot_type_lower:
            logit += coef.get("shot_type_tip", 0)
        elif "deflect" in shot_type_lower:
            logit += coef.get("shot_type_deflected", 0)
        elif "wrap" in shot_type_lower:
            logit += coef.get("shot_type_wrap", 0)

        return round(_sigmoid(logit), 4)

    def predict_batch(self, shots: list[dict]) -> list[float]:
        """
        Predict xG for a list of shot dicts.

        Each dict should have keys: distance, angle, shot_type (optional),
        is_rebound (optional), is_rush (optional).
        """
        return [
            self.predict_single(
                distance=s.get("distance", 30),
                angle=s.get("angle", 0),
                shot_type=s.get("shot_type", "Wrist Shot"),
                is_rebound=s.get("is_rebound", False),
                is_rush=s.get("is_rush", False),
            )
            for s in shots
        ]

    def is_trained(self) -> bool:
        """Return True if a trained (not just fallback) model is loaded."""
        return (
            self._coef is not None
            and self._coef.get("source") == "trained"
        )

    def get_coef_summary(self) -> dict:
        """Return the model coefficients for display."""
        return {k: v for k, v in self._get_coef().items() if k != "source"}

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def _train_from_pbp(self) -> bool:
        """
        Attempt training from hockeyR PBP data.

        Uses sklearn LogisticRegression if available.
        Returns True on success.
        """
        try:
            import numpy as np
            from sklearn.linear_model import LogisticRegression
            from sklearn.preprocessing import StandardScaler
        except ImportError:
            logger.warning("scikit-learn not installed; skipping PBP model training.")
            return False

        try:
            from src.api.pbp_client import load_most_recent_season
        except ImportError:
            from api.pbp_client import load_most_recent_season  # type: ignore

        pbp = load_most_recent_season()
        if pbp is None or pbp.empty:
            return False

        shot_events = {"SHOT", "MISSED_SHOT", "GOAL"}
        shots = pbp[pbp["event_type"].isin(shot_events)].copy()

        # Need distance and angle columns
        for col in ("shot_distance", "shot_angle"):
            if col not in shots.columns:
                logger.warning("Column %s missing from PBP; skipping training.", col)
                return False

        shots = shots.dropna(subset=["shot_distance", "shot_angle"])
        if len(shots) < 1000:
            return False

        # Build feature matrix
        shots["_distance"] = shots["shot_distance"].clip(0, 89)
        shots["_angle"] = shots["shot_angle"].abs().clip(0, 90)

        # Shot type one-hot (vs Wrist Shot baseline)
        shot_col = "secondaryType" if "secondaryType" in shots.columns else "shot_type"
        if shot_col in shots.columns:
            shots["_slap"] = shots[shot_col].str.contains("Slap", na=False).astype(int)
            shots["_snap"] = shots[shot_col].str.contains("Snap", na=False).astype(int)
            shots["_backhand"] = shots[shot_col].str.contains("Backhand", na=False).astype(int)
            shots["_tip"] = shots[shot_col].str.contains("Tip", na=False).astype(int)
            shots["_deflect"] = shots[shot_col].str.contains("Deflect", na=False).astype(int)
        else:
            for c in ("_slap", "_snap", "_backhand", "_tip", "_deflect"):
                shots[c] = 0

        feature_cols = [
            "_distance", "_angle", "_slap", "_snap",
            "_backhand", "_tip", "_deflect",
        ]
        X = shots[feature_cols].values
        y = (shots["event_type"] == "GOAL").astype(int).values

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        model = LogisticRegression(max_iter=1000, C=1.0, solver="lbfgs")
        model.fit(X_scaled, y)

        # Extract unscaled coefficients by backing out the scaler
        means = scaler.mean_
        stds = scaler.scale_
        raw_coef = model.coef_[0] / stds
        intercept = model.intercept_[0] - float(np.dot(model.coef_[0], means / stds))

        coef_names = feature_cols
        coef_map = {
            "intercept": float(round(intercept, 5)),
            "distance": float(round(raw_coef[coef_names.index("_distance")], 5)),
            "angle": float(round(raw_coef[coef_names.index("_angle")], 5)),
            "is_rebound": self.DEFAULT_COEFFICIENTS["is_rebound"],  # keep prior
            "is_rush": self.DEFAULT_COEFFICIENTS["is_rush"],
            "shot_type_slap": float(round(raw_coef[coef_names.index("_slap")], 5)),
            "shot_type_snap": float(round(raw_coef[coef_names.index("_snap")], 5)),
            "shot_type_backhand": float(
                round(raw_coef[coef_names.index("_backhand")], 5)
            ),
            "shot_type_tip": float(round(raw_coef[coef_names.index("_tip")], 5)),
            "shot_type_deflected": float(
                round(raw_coef[coef_names.index("_deflect")], 5)
            ),
            "shot_type_wrap": self.DEFAULT_COEFFICIENTS["shot_type_wrap"],
            "source": "trained",
            "n_shots": int(len(shots)),
            "goal_rate": float(round(y.mean(), 4)),
        }

        self._coef = coef_map
        self._save()
        logger.info(
            "Trained xG model on %d shots (goal rate %.1f%%)",
            len(shots),
            y.mean() * 100,
        )
        return True

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _save(self) -> None:
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(MODEL_PATH, "w") as f:
            json.dump(self._coef, f, indent=2)

    def _load(self) -> None:
        with open(MODEL_PATH) as f:
            self._coef = json.load(f)

    def _get_coef(self) -> dict:
        if self._coef is None:
            if MODEL_PATH.exists():
                self._load()
            else:
                self._coef = dict(self.DEFAULT_COEFFICIENTS)
        return self._coef


# ---------------------------------------------------------------------------
# Module-level convenience accessor (singleton)
# ---------------------------------------------------------------------------

_model_instance: Optional[XGShotModel] = None


def get_xg_model() -> XGShotModel:
    """Return a module-level singleton XGShotModel (loads saved model)."""
    global _model_instance
    if _model_instance is None:
        _model_instance = XGShotModel()
        _model_instance.ensure_trained()
    return _model_instance
