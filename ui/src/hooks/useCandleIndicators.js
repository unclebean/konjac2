import {format, formatISO} from "date-fns";
import {lossAndProfit} from "../context/forexPairContext";
import {useStrategy} from "./useStrategy";

export const useCandleIndicators = () => {
  const {
    mamaStrategy,
    emaCrossOverStratey,
    sarStrategy,
    vwapStrategy,
    bbandsStrategy,
    bbandsStochStrategy,
    bbandsCCIStrategy,
    almaStrategy,
    ichimokuStrategy,
  } = useStrategy();

  const mapOrderHistory = (symbol, annotations, latestClosePrice) => {
    const annotationMap = annotations.reduce((prev, anots) => {
      prev[anots.x] = anots;
      return prev;
    }, {});
    const orderIds = Object.keys(annotationMap).sort();
    const orders = orderIds.map((act, index) => {
      const action = annotationMap[act].text;
      const orderClosePrice = annotationMap[act].orderPrice;
      const nextOrder = annotationMap[orderIds[index + 1]];
      const strategy = annotationMap[act].strategy;
      const pipCalculator = symbol.indexOf("JPY") > 0 ? 100 : 10000;
      let closePrice = nextOrder ? nextOrder.orderPrice : latestClosePrice;
      if (annotationMap[act].closeOrderPrice) {
        closePrice = annotationMap[act].closeOrderPrice;
      }
      let pips = (closePrice - orderClosePrice) * pipCalculator;

      if (action === "short" && pips !== null) {
        pips = -pips;
      }
      pips = pips >= lossAndProfit.takeProfit ? lossAndProfit.takeProfit : pips;
      pips = pips <= -lossAndProfit.stopLoss ? -lossAndProfit.stopLoss : pips;

      return {
        pips,
        index,
        action,
        strategy,
        date: format(new Date(act), "yyyy-MM-dd HH:mm"),
        orderPricePair: `${orderClosePrice} -> ${closePrice}`,
      };
    });
    return orders;
  };

  const mapSummary = (orders) => {
    const summary = orders.reduce(
      (sumy, order) => {
        sumy.win += order.pips > 0 ? 1 : 0;
        sumy.lose += order.pips < 0 ? 1 : 0;
        sumy.totalPips += order.pips || 0;
        return sumy;
      },
      {win: 0, lose: 0, totalPips: 0}
    );
    summary.totalPips = summary.totalPips.toFixed(2);
    return summary;
  };

  const fetchData = async (currencyPair, date = "", timeFrame = "1h") => {
    const response = await fetch(
      `/chart/${timeFrame}/${currencyPair}?endDate=${date}`
    );
    const resp = await response.json();
    resp.strategies = {};
    resp.orders = {};
    resp.summaries = {};
    return resp;
  };

  return {fetchData, mapSummary};
};
