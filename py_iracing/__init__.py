"""
py-iracing
==========

A Python 3 implementation of the iRacing SDK.

This package allows you to get session data, live telemetry data, and broadcast messages to the iRacing simulator.
"""

from .client import iRacingClient
from .ibt import IBT
from .constants import VERSION

__version__ = VERSION
__all__ = ['iRacingClient', 'IBT']