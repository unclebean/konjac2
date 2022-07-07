import React, {useState, useCallback} from "react";

export const lossAndProfit = {
  stopLoss: 15,
  takeProfit: 25,
};

export const AllForexPairs = [
  {
    key: "ETH-PERP",
    label: "ETH-PERP",
  },
  {
    key: "CEL-PERP",
    label: "CEL-PERP",
  }
];

export const ForexPairContext = React.createContext({
  symbol: {},
  setSymbol: () => {},
  tradingStrategySummary: {},
  setTradingStrategySummary: () => {},
  isBackTest: false,
  onToggleBackTest: () => {},
  refresh: false,
  toggleRefresh: () => {},
  endDate: "",
  setEndDate: () => {},
  timeframe: "",
  setTimeframe: () => {},
  strategy: "",
  setStrategy: () => {},
});

export const useForexPairContext = () => {
  const [symbol, updateSymbol] = useState(AllForexPairs[0]);
  const [summary, updateSummary] = useState({win: 0, lose: 0, totalPips: 0});
  const [isBackTest, updateBackTest] = useState(false);
  const [refresh, updateRefreshFlag] = useState(false);
  const [endDate, updateEndDate] = useState("");
  const [timeframe, updateTimeframe] = useState("H1");
  const [strategy, updateStrategy] = useState("mama");

  const setSymbol = useCallback((symbol) => {
    updateSymbol(symbol);
  }, []);

  const setTradingStrategySummary = useCallback((summary) => {
    updateSummary(summary);
  }, []);

  const onToggleBackTest = useCallback((backTestFlag) => {
    updateBackTest(backTestFlag);
  }, []);

  const toggleRefresh = useCallback((refreshFlag) => {
    updateRefreshFlag(refreshFlag);
  }, []);

  const setEndDate = useCallback((ed) => {
    updateEndDate(ed);
  }, []);

  const setTimeframe = useCallback((tf) => {
    updateTimeframe(tf);
  }, []);

  const setStrategy = useCallback((stg) => {
    updateStrategy(stg);
  }, []);

  return {
    symbol,
    setSymbol,
    tradingStrategySummary: summary,
    setTradingStrategySummary,
    isBackTest,
    onToggleBackTest,
    refresh,
    toggleRefresh,
    endDate,
    setEndDate,
    timeframe,
    setTimeframe,
    strategy,
    setStrategy,
  };
};
