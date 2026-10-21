"""Equitable energy: SERL smart-meter demand, forecasting and tariff analysis.

Modules
-------
config     project paths
dataset    load and slice SERL aggregated statistics (one group, one unit at a time)
labels     readable household-group names and energy-poverty proxies
tariffs    Octopus prices (cached) and bill calculations
plots      shared figure theme from design/tokens.json
reporting  save figures and tables with consistent names
"""
__version__ = "1.0.0"
