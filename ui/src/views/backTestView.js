import React, {useState, useEffect, useContext} from "react";
import Container from "react-bulma-components/lib/components/container";
import Columns from "react-bulma-components/lib/components/columns";
import {
  subHours,
  isWeekend,
  isValid,
  parseISO,
  formatISO,
  subMinutes,
} from "date-fns";
import {CandleAndIndicators} from "../components/candleAndIndicators";
import {useCandleIndicators} from "../hooks/useCandleIndicators";
import {ForexPairContext} from "../context/forexPairContext";

export const BackTestView = () => {
  const [data, updateData] = useState({});
  const [allOrders, updateAllOrders] = useState([]);
  const {fetchData, mapSummary} = useCandleIndicators();
  const forexPairContext = useContext(ForexPairContext);

  const getDateTime = (startDate, timeframe) => {
    switch (timeframe) {
      case "M5":
        return subMinutes(startDate, 5);
      case "M15":
        return subMinutes(startDate, 15);
      case "H1":
        return subHours(startDate, 1);
      case "H4":
        return subHours(startDate, 4);
      case "D":
        return subHours(startDate, 24);
      default:
        return subHours(startDate, 1);
    }
  };

  useEffect(() => {
    const {symbol, endDate, timeframe} = forexPairContext;
    const endDateObj = parseISO(endDate);
    let endDateList = [];
    let date = isValid(endDateObj) ? endDateObj : new Date();
    let isDestoried = false;
    let orders = {};
    while (endDateList.length < 1000) {
      date = getDateTime(date, timeframe);
      if (isWeekend(date)) continue;
      endDateList.push(formatISO(date));
    }
    endDateList.reverse();

    const launchBackTesting = async () => {
      while (endDateList.length !== 0 && !isDestoried) {
        const date = endDateList.shift();
        const resp = await fetchData(symbol.key, date, timeframe);
        orders = resp.orders[forexPairContext.strategy].reduce((pre, order) => {
          pre[order.date] = order;
          return pre;
        }, orders);
        const orderList = [];
        Object.keys(orders)
          .sort()
          .forEach((key) => {
            if (orderList.length > 0) {
              const prevOrder = orderList[orderList.length - 1];
              // if (prevOrder.action !== orders[key].action) {
              orderList.push(orders[key]);
              // }
            } else {
                orderList.push(orders[key]);
            }
          });
        updateAllOrders(orderList.reverse());
        forexPairContext.setTradingStrategySummary(mapSummary(orderList));
        updateData(resp);
      }
    };

    launchBackTesting();

    return () => {
      isDestoried = true;
    };
  }, [
    forexPairContext.symbol,
    forexPairContext.refresh,
    forexPairContext.timeframe,
    forexPairContext.endDate,
    forexPairContext.strategy,
  ]);

  const renderOrderHistory = () => {
    return allOrders.map((order, index) => {
      return (
        <tr key={index}>
          <td>{order.date}</td>
          <td>
            <div>{order.action}</div>
            <div style={{fontSize: "12px"}}>{order.orderPricePair}</div>
          </td>
          <td>{order.pips && order.pips.toFixed(2)}</td>
        </tr>
      );
    });
  };

  return (
    <Container breakpoint="widescreen">
      <Columns>
        <Columns.Column size="two-thirds">
          <CandleAndIndicators
            candlesAndIndicators={data}
            strategy={forexPairContext.strategy}
          ></CandleAndIndicators>
        </Columns.Column>
        <Columns.Column
          style={{
            maxHeight: "559px",
            overflow: "auto",
            border: "1px solid lightgray",
          }}
        >
          <table className="table is-fullwidth is-striped">
            <thead>
              <tr>
                <td>Date</td>
                <td>Action</td>
                <td>Take Pips</td>
              </tr>
            </thead>
            <tbody>{renderOrderHistory()}</tbody>
          </table>
        </Columns.Column>
      </Columns>
    </Container>
  );
};
