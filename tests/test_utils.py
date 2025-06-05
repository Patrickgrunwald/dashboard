import os
import sys
import pytest

# Ensure the application module can be imported when tests are executed
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import deg_to_cardinal


def test_deg_to_cardinal_zero():
    assert deg_to_cardinal(0) == "N"


def test_deg_to_cardinal_90():
    assert deg_to_cardinal(90) == "O"


def test_deg_to_cardinal_225():
    assert deg_to_cardinal(225) == "SW"
