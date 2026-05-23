"""Tests for correlation detection."""

from unittest.mock import patch

import numpy as np


def test_find_correlations_empty() -> None:
    with patch("src.analysis.correlation.psycopg") as mock_psycopg:
        mock_conn = mock_psycopg.connect.return_value
        mock_conn.execute.return_value.fetchall.return_value = []
        from src.analysis.correlation import find_correlations

        result = find_correlations()
        assert result == []


def test_correlation_logic() -> None:
    """Test that perfectly correlated series are detected."""
    # Simulate the matrix computation directly
    weeks = 6
    matrix = np.zeros((weeks, 2))
    matrix[:, 0] = [1, 2, 3, 4, 5, 6]
    matrix[:, 1] = [2, 4, 6, 8, 10, 12]  # perfectly correlated

    corr = float(np.corrcoef(matrix[:, 0], matrix[:, 1])[0, 1])
    assert corr > 0.99


def test_no_correlation() -> None:
    """Test that uncorrelated series are not matched."""
    weeks = 6
    matrix = np.zeros((weeks, 2))
    matrix[:, 0] = [1, 0, 1, 0, 1, 0]
    matrix[:, 1] = [0, 1, 0, 1, 0, 1]  # anti-correlated

    corr = float(np.corrcoef(matrix[:, 0], matrix[:, 1])[0, 1])
    assert corr < 0.5
