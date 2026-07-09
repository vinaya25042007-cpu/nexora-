"""
Computer vision service for wound-image analysis.

PRODUCTION NOTE:
  This module exposes a single entry point, `analyze_wound_image(path)`, that
  returns risk scores + a classification. The implementation below is a
  color/texture-heuristic analyzer (HSV redness ratio, contour-based swelling
  proxy, brightness-based discharge/pus proxy) built with Pillow + NumPy so the
  system is fully runnable without a GPU or trained weights.

  To swap in a real trained model (e.g. a fine-tuned CNN / ViT trained on
  labeled wound datasets), replace the body of `analyze_wound_image` with a
  call to your model's inference function, keeping the same return schema:
      {
        "risk_level": "normal" | "mild_concern" | "urgent",
        "redness_score": float 0-1,
        "swelling_score": float 0-1,
        "discharge_score": float 0-1,
        "confidence": float 0-1,
        "findings": [str, ...],
        "recommendation": str
      }
"""
from typing import Dict, Any

import numpy as np
from PIL import Image


def _load_rgb(path: str) -> np.ndarray:
    img = Image.open(path).convert("RGB")
    img = img.resize((256, 256))
    return np.asarray(img).astype(np.float32) / 255.0


def _rgb_to_hsv(rgb: np.ndarray) -> np.ndarray:
    img = Image.fromarray((rgb * 255).astype(np.uint8)).convert("HSV")
    return np.asarray(img).astype(np.float32) / 255.0


def _redness_score(hsv: np.ndarray, rgb: np.ndarray) -> float:
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    # Pixels where red clearly dominates green/blue -> inflamed / red tissue
    redness_mask = (r > g * 1.15) & (r > b * 1.15) & (r > 0.35)
    ratio = float(redness_mask.mean())
    return min(1.0, ratio * 2.2)


def _swelling_score(rgb: np.ndarray) -> float:
    # Proxy: local contrast / edge density around the center region.
    # High local variance around a shiny, taut area can indicate swelling.
    gray = rgb.mean(axis=-1)
    h, w = gray.shape
    center = gray[h // 4 : 3 * h // 4, w // 4 : 3 * w // 4]
    grad_x = np.abs(np.diff(center, axis=1))
    grad_y = np.abs(np.diff(center, axis=0))
    edge_energy = float(grad_x.mean() + grad_y.mean())
    return min(1.0, edge_energy * 6.0)


def _discharge_score(hsv: np.ndarray, rgb: np.ndarray) -> float:
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    # Yellow/white glossy patches -> possible pus / discharge
    yellow_white_mask = (r > 0.65) & (g > 0.6) & (b < 0.55) & (np.abs(r - g) < 0.18)
    ratio = float(yellow_white_mask.mean())
    return min(1.0, ratio * 3.0)


def analyze_wound_image(path: str) -> Dict[str, Any]:
    try:
        rgb = _load_rgb(path)
        hsv = _rgb_to_hsv(rgb)
    except Exception as e:
        return {
            "risk_level": "mild_concern",
            "redness_score": 0.0,
            "swelling_score": 0.0,
            "discharge_score": 0.0,
            "confidence": 0.0,
            "findings": [f"Could not analyze image: {e}"],
            "recommendation": "Please re-upload a clearer photo of the wound in good lighting.",
        }

    redness = _redness_score(hsv, rgb)
    swelling = _swelling_score(rgb)
    discharge = _discharge_score(hsv, rgb)

    composite = redness * 0.4 + swelling * 0.25 + discharge * 0.35

    findings = []
    if redness > 0.5:
        findings.append("Elevated redness detected around the wound area")
    if swelling > 0.5:
        findings.append("Possible swelling / tissue distortion detected")
    if discharge > 0.4:
        findings.append("Possible discharge or exudate detected")
    if not findings:
        findings.append("No significant signs of infection detected")

    if composite >= 0.6 or discharge >= 0.6:
        risk_level = "urgent"
        recommendation = (
            "These signs may indicate infection. Please contact your care team or "
            "visit urgent care as soon as possible."
        )
        confidence = 0.7
    elif composite >= 0.32:
        risk_level = "mild_concern"
        recommendation = (
            "Some changes were noted. Keep monitoring closely over the next 24 hours; "
            "contact your care team if redness, swelling, or discharge increases."
        )
        confidence = 0.6
    else:
        risk_level = "normal"
        recommendation = "Healing appears to be progressing normally. Keep the area clean and dry."
        confidence = 0.75

    return {
        "risk_level": risk_level,
        "redness_score": round(redness, 3),
        "swelling_score": round(swelling, 3),
        "discharge_score": round(discharge, 3),
        "confidence": round(confidence, 3),
        "findings": findings,
        "recommendation": recommendation,
    }
