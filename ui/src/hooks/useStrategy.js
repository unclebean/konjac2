import {lossAndProfit} from "../context/forexPairContext";

export const defaultAnnotationValues = {
  xref: "x",
  yref: "y",
  showarrow: true,
  arrowhead: 2,
  ax: -25,
  ay: -40,
  opacity: 0.6,
  font: {
    size: 12,
    color: "white",
  },
};

export const useStrategy = () => {
  const getLongAnnotation = (x, y, orderPrice, name) => {
    return {
      ...defaultAnnotationValues,
      x,
      y,
      text: "long",
      bgcolor: "green",
      arrowcolor: "green",
      orderPrice,
      strategy: name,
    };
  };

  const getShortAnnotation = (x, y, orderPrice, name) => {
    return {
      ...defaultAnnotationValues,
      x,
      y,
      text: "short",
      ay: 40,
      bgcolor: "red",
      arrowcolor: "red",
      orderPrice,
      strategy: name,
    };
  };

  const takePips = (currencyPair, type, orderPrice, closePrice) => {
    const pipCalculator = currencyPair.indexOf("JPY") > 0 ? 100 : 10000;
    if (type === "long") {
      const longPips = (closePrice - orderPrice) * pipCalculator;
      return (
        longPips >= lossAndProfit.takeProfit ||
        longPips <= -lossAndProfit.stopLoss
      );
    }
    const shortPips = (orderPrice - closePrice) * pipCalculator;
    return (
      shortPips >= lossAndProfit.takeProfit ||
      shortPips <= -lossAndProfit.stopLoss
    );
  };

  const mamaStrategy = (currencyPair, marketData, mama, cci34, cci144) => {
    const annos = [];
    mama.mama.forEach((mm, index) => {
      if (
        mm - mama.fama[index] > 0 &&
        mama.mama[index - 1] - mama.fama[index - 1] <= 0 &&
        cci34[index] > cci144[index]
      ) {
        annos.push(
          getLongAnnotation(
            marketData.x[index],
            mm,
            marketData.close[index],
            "mama"
          )
        );
      } else if (
        mm - mama.fama[index] < 0 &&
        mama.mama[index - 1] - mama.fama[index - 1] >= 0 &&
        cci34[index] < cci144[index]
      ) {
        annos.push(
          getShortAnnotation(
            marketData.x[index],
            mm,
            marketData.close[index],
            "mama"
          )
        );
      }
    });
    return annos.filter((a) => a !== null);
  };

  const emaCrossOverStratey = (marketData, ema) => {
    const {ema144, ema169, ema288, ema338} = ema;
    let firstLong = false,
      firstShort = false;
    const annos = ema144.map((ema144Value, index) => {
      if (
        ema144Value > ema288[index] &&
        ema144Value > ema338[index] &&
        ema169[index] > ema288[index] &&
        ema169[index] > ema338[index] &&
        !firstLong
      ) {
        firstLong = true;
        firstShort = false;
        return getLongAnnotation(
          marketData.x[index],
          ema144Value,
          marketData.close[index],
          "ema"
        );
      } else if (
        ema144Value < ema288[index] &&
        ema144Value < ema338[index] &&
        ema169[index] < ema288[index] &&
        ema169[index] < ema338[index] &&
        !firstShort
      ) {
        firstShort = true;
        firstLong = false;
        return getShortAnnotation(
          marketData.x[index],
          ema144Value,
          marketData.close[index],
          "ema"
        );
      } else {
        return null;
      }
    });

    return annos.filter((a) => a !== null);
  };

  const sarStrategy = (marketData, parabolicSAR, ema200) => {
    const annos = parabolicSAR.map((sar, index) => {
      if (
        ema200[index] < marketData.close[index] &&
        ema200[index] < sar &&
        marketData.close[index] > sar &&
        marketData.close[index - 1] < parabolicSAR[index - 1]
      ) {
        return getLongAnnotation(
          marketData.x[index],
          sar,
          marketData.close[index],
          "sar"
        );
      } else if (
        ema200[index] > marketData.close[index] &&
        ema200[index] > sar &&
        marketData.close[index] < sar &&
        marketData.close[index - 1] > parabolicSAR[index - 1]
      ) {
        return getShortAnnotation(
          marketData.x[index],
          sar,
          marketData.close[index],
          "sar"
        );
      } else {
        return null;
      }
    });

    return annos.filter((a) => a !== null);
  };

  const vwapStrategy = (marketData, vwapIndicators, mvwap) => {
    const annos = [];
    vwapIndicators.forEach((vwap, index) => {
      if (
        /*
        marketData.close[index] > vwap &&
        marketData.close[index - 1] >= vwapIndicators[index - 1] &&
        marketData.open[index - 1] < vwapIndicators[index - 1] &&
        marketData.close[index] > marketData.close[index - 5]
        */
       vwap > mvwap[index] && vwapIndicators[index - 1] <= mvwap[index - 1]
      ) {
        annos.push(
          getLongAnnotation(
            marketData.x[index],
            vwap,
            marketData.close[index],
            "vwap"
          )
        );
      } else if (
        /*
        marketData.close[index] < vwap &&
        marketData.close[index - 1] <= vwapIndicators[index - 1] &&
        marketData.open[index - 1] > vwapIndicators[index - 1] &&
        marketData.close[index] < marketData.close[index - 5]
        */
       vwap < mvwap[index] && vwapIndicators[index - 1] >= mvwap[index - 1]
      ) {
        annos.push(
          getShortAnnotation(
            marketData.x[index],
            vwap,
            marketData.close[index],
            "vwap"
          )
        );
      }
    });

    return annos.filter((a) => a !== null);
  };

  const bbandsStrategy = (
    currencyPair,
    marketData,
    bbandsIndicators,
    macdIndicators
  ) => {
    const annos = [];
    const {upper, middle, lower} = bbandsIndicators;
    const {macd, signal, hist} = macdIndicators;
    const touchedUpperLine = (startIndex, highPriceList) => {
      const haveOrNot = highPriceList.filter(
        (hp, index) => hp > upper[startIndex + index]
      );
      return haveOrNot.length > 0;
    };
    const touchedLowerLine = (startIndex, lowPriceList) => {
      const haveOrNot = lowPriceList.filter(
        (lp, index) => lp < lower[startIndex + index]
      );
      return haveOrNot.length > 0;
    };
    hist.forEach((his, index) => {
      if (
        his < 0 &&
        signal[index] > 0 &&
        macd[index] > 0 &&
        signal[index] > macd[index] &&
        signal[index - 1] <= macd[index - 1] &&
        marketData.close[index] >= middle[index] &&
        touchedUpperLine(index - 9, marketData.high.slice(index - 9, index - 1))
      ) {
        annos.push(
          getShortAnnotation(
            marketData.x[index],
            marketData.close[index],
            marketData.close[index],
            "bbands"
          )
        );
      } else if (
        his > 0 &&
        signal[index] < 0 &&
        macd[index] < 0 &&
        signal[index] < macd[index] &&
        signal[index - 1] >= macd[index - 1] &&
        marketData.close[index] <= middle[index] &&
        touchedLowerLine(index - 9, marketData.low.slice(index - 9, index - 1))
      ) {
        annos.push(
          getLongAnnotation(
            marketData.x[index],
            marketData.close[index],
            marketData.close[index],
            "bbands"
          )
        );
      }

      const lastTrade = annos.pop();
      if (
        lastTrade &&
        lastTrade.text === "long" &&
        !lastTrade.closeOrderPrice &&
        (upper[index] <= marketData.high[index] ||
          takePips(
            currencyPair,
            "long",
            lastTrade.orderPrice,
            marketData.close[index]
          ))
      ) {
        lastTrade.closeOrderPrice = marketData.close[index];
      }
      if (
        lastTrade &&
        lastTrade.text === "short" &&
        !lastTrade.closeOrderPrice &&
        (lower[index] >= marketData.low[index] ||
          takePips(
            currencyPair,
            "short",
            lastTrade.orderPrice,
            marketData.close[index]
          ))
      ) {
        lastTrade.closeOrderPrice = marketData.close[index];
      }
      if (lastTrade) {
        annos.push(lastTrade);
      }
    });

    console.log(annos);

    return annos.filter((a) => a !== null);
  };

  const bbandsStochStrategy = (
    currencyPair,
    marketData,
    bbandsIndicators,
    stockIndicators
  ) => {
    const annos = [];
    const {upper, lower} = bbandsIndicators;
    const {slowk, slowd} = stockIndicators;
    const touchedUpperLine = (startIndex, highPriceList) => {
      const haveOrNot = highPriceList.filter(
        (hp, index) => hp > upper[startIndex + index]
      );
      return haveOrNot.length > 0;
    };
    const touchedLowerLine = (startIndex, lowPriceList) => {
      const haveOrNot = lowPriceList.filter(
        (lp, index) => lp < lower[startIndex + index]
      );
      return haveOrNot.length > 0;
    };
    slowk.forEach((sk, index) => {
      if (
        sk > 80 &&
        slowd[index] > 80 &&
        slowd[index] > sk &&
        slowd[index - 1] <= slowk[index - 1] &&
        marketData.close[index] < upper[index] &&
        touchedUpperLine(index - 6, marketData.high.slice(index - 6, index - 1))
      ) {
        annos.push(
          getShortAnnotation(
            marketData.x[index],
            marketData.close[index],
            marketData.close[index],
            "bbands"
          )
        );
      } else if (
        sk < 20 &&
        slowd[index] < 20 &&
        slowd[index] < sk &&
        slowd[index - 1] >= slowk[index - 1] &&
        marketData.close[index] > upper[index] &&
        touchedLowerLine(index - 6, marketData.low.slice(index - 6, index - 1))
      ) {
        annos.push(
          getLongAnnotation(
            marketData.x[index],
            marketData.close[index],
            marketData.close[index],
            "bbands"
          )
        );
      }

      const lastTrade = annos.pop();
      if (
        lastTrade &&
        lastTrade.text === "long" &&
        !lastTrade.closeOrderPrice &&
        (upper[index] <= marketData.high[index] ||
          takePips(
            currencyPair,
            "long",
            lastTrade.orderPrice,
            marketData.close[index]
          ))
      ) {
        lastTrade.closeOrderPrice = marketData.close[index];
      }
      if (
        lastTrade &&
        lastTrade.text === "short" &&
        !lastTrade.closeOrderPrice &&
        (lower[index] >= marketData.low[index] ||
          takePips(
            currencyPair,
            "short",
            lastTrade.orderPrice,
            marketData.close[index]
          ))
      ) {
        lastTrade.closeOrderPrice = marketData.close[index];
      }
      if (lastTrade) {
        annos.push(lastTrade);
      }
    });

    console.log(annos);

    return annos.filter((a) => a !== null);
  };

  const almaStrategy = (marketData, alma50) => {
    const annos = alma50.map((almaValue, index) => {
      if (
        marketData.close[index] > almaValue &&
        marketData.close[index - 1] < alma50[index - 1]
      ) {
        return getLongAnnotation(
          marketData.x[index],
          almaValue,
          marketData.close[index],
          "alma"
        );
      } else if (
        marketData.close[index] < almaValue &&
        marketData.close[index - 1] > alma50[index - 1]
      ) {
        return getShortAnnotation(
          marketData.x[index],
          almaValue,
          marketData.close[index],
          "alma"
        );
      } else {
        return null;
      }
    });

    return annos.filter((a) => a !== null);
  };

  const ichimokuStrategy = (
    marketData,
    tenkan,
    kijun,
    chikou,
    spna_a,
    spna_b
  ) => {
    const annos = [];
    spna_a.forEach((aValue, index) => {
      const closePrice = marketData.close[index]
      if (
        tenkan[index] >= kijun[index] &&
        tenkan[index - 1] < kijun[index - 1] &&
        chikou[index] > marketData.close[index - 26] 
      ) {
        annos.push(
          getLongAnnotation(
            marketData.x[index],
            closePrice,
            closePrice,
            "ichimoku"
          )
        );
      } else if (
        tenkan[index] <= kijun[index] &&
        tenkan[index - 1] > kijun[index - 1] &&
        chikou[index] < marketData.close[index - 26] 
      ) {
        console.log(chikou[index - 26]);
        annos.push(
          getShortAnnotation(
            marketData.x[index],
            closePrice,
            closePrice,
            "ichimoku"
          )
        );
      }
    });

    return annos;
  };

  const bbandsCCIStrategy = (
    currencyPair,
    marketData,
    bbandsIndicators,
    cci21,
    cci55
  ) => {
    const annos = [];
    const {upper, middle, lower} = bbandsIndicators;
    const touchedUpperLine = (startIndex, highPriceList) => {
      const haveOrNot = highPriceList.filter(
        (hp, index) => hp > upper[startIndex + index]
      );
      return haveOrNot.length > 0;
    };
    const touchedLowerLine = (startIndex, lowPriceList) => {
      const haveOrNot = lowPriceList.filter(
        (lp, index) => lp < lower[startIndex + index]
      );
      return haveOrNot.length > 0;
    };
    middle.forEach((md, index) => {
      if (
        cci21[index] < cci55[index] &&
        cci21[index - 1] >= cci55[index - 1] &&
        marketData.close[index] >= md &&
        touchedUpperLine(index - 6, marketData.high.slice(index - 6, index - 1))
      ) {
        annos.push(
          getShortAnnotation(
            marketData.x[index],
            marketData.close[index],
            marketData.close[index],
            "bbands"
          )
        );
      } else if (
        cci21[index] > cci55[index] &&
        cci21[index - 1] <= cci55[index - 1] &&
        marketData.close[index] <= md &&
        touchedLowerLine(index - 6, marketData.low.slice(index - 6, index - 1))
      ) {
        annos.push(
          getLongAnnotation(
            marketData.x[index],
            marketData.close[index],
            marketData.close[index],
            "bbands"
          )
        );
      }

      const lastTrade = annos.pop();
      if (
        lastTrade &&
        lastTrade.text === "long" &&
        !lastTrade.closeOrderPrice &&
        (upper[index] <= marketData.high[index] ||
          takePips(
            currencyPair,
            "long",
            lastTrade.orderPrice,
            marketData.close[index]
          ))
      ) {
        lastTrade.closeOrderPrice = marketData.close[index];
      }
      if (
        lastTrade &&
        lastTrade.text === "short" &&
        !lastTrade.closeOrderPrice &&
        (lower[index] >= marketData.low[index] ||
          takePips(
            currencyPair,
            "short",
            lastTrade.orderPrice,
            marketData.close[index]
          ))
      ) {
        lastTrade.closeOrderPrice = marketData.close[index];
      }
      if (lastTrade) {
        annos.push(lastTrade);
      }
    });

    console.log(annos);

    return annos.filter((a) => a !== null);
  };

  const aiStrategy = (marketData, aiIndicator) => {
    const openPrice = marketData.open[marketData.open.length - 1];
    const closePrice = marketData.open[marketData.close.length - 1];
  };

  return {
    mamaStrategy,
    emaCrossOverStratey,
    sarStrategy,
    vwapStrategy,
    bbandsStrategy,
    bbandsStochStrategy,
    bbandsCCIStrategy,
    almaStrategy,
    ichimokuStrategy,
  };
};
