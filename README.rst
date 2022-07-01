For trading strategy strategy & back testing
============================================


Convert tradingview strategy to python and running back testing to verirfy the strategy

Target is that to build visualized backtesting tools with useful trading strategy.

.. image:: ./docs/backtest_ui.gif
  :width: 400
  :alt: backtest ui

```sql
select sum(result), strftime('%m-%Y', create_date) from trade GROUP BY strftime('%m-%Y', create_date);
```