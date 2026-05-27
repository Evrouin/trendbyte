"""Centralized logging configuration."""

from __future__ import annotations

import logging
import sys


class Logger:
    """Application logger factory."""

    _configured = False

    @classmethod
    def setup(cls, level: int = logging.INFO) -> None:
        """Configure root logger once."""
        if cls._configured:
            return
        logging.basicConfig(
            level=level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            stream=sys.stdout,
        )
        cls._configured = True

    @staticmethod
    def get(name: str) -> logging.Logger:
        """Get a named logger instance."""
        return logging.getLogger(name)
