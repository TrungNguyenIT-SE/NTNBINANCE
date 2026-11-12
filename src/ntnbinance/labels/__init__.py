"""Versioned point-in-time labeling for Stage G."""

from ntnbinance.labels.engine import label_sample
from ntnbinance.labels.models import Label, LabelConfig, LabelResult

__all__ = ["Label", "LabelConfig", "LabelResult", "label_sample"]
