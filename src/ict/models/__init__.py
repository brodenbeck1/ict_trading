"""
Composite trading models, organized by author/source.

- ict/      — ICT (Inner Circle Trader) models: 2022 model, FVG sweep, daily bias, ...
- romeo/    — Romeo's Candle Range Theory (CRT) models
- merchant/ — The Currency Merchant (Kishane) models

Each model composes primitives from `ict.concepts`. The conceptual spec for every
model lives in `knowledge/<author>/models/`; model classes should reference the
concept slug they implement.
"""
