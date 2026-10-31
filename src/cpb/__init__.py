"""Client portfolio builder: starts from a client profile, not a market signal.

Build order mirrors the advisory conversation:

1. ``profile``         who the client is → risk level 1-5
2. ``allocation``      risk level → model portfolio and 10-year return estimate
3. ``implementation``  asset classes → ETFs and dollar amounts
4. ``stress``          what 2008/2020/2022 would have done, and goal-miss odds
5. ``fx``              the local-currency slice for a LATAM client
6. ``proposal``        one printable page the banker can hand over
"""

__version__ = "0.1.0"
