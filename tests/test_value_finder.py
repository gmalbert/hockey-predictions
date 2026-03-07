"""Tests for the value finder page logic."""

def test_percentage_formatting():
    """Ensure probabilities formatted as percentages multiply by 100."""
    prob = 0.6067
    formatted = f"{prob:.1%}"
    assert formatted == "60.7%"
