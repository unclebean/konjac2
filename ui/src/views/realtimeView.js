import React, {useState, useEffect, useContext} from "react";
import Container from "react-bulma-components/lib/components/container";
import Columns from "react-bulma-components/lib/components/columns";
import {CandleAndIndicators} from "../components/candleAndIndicators";
import {useCandleIndicators} from "../hooks/useCandleIndicators";
import {ForexPairContext} from "../context/forexPairContext";

export const RealtimeView = () => {
  const [data, updateData] = useState({});
  const {fetchData} = useCandleIndicators();
  const forexPairContext = useContext(ForexPairContext);

  useEffect(() => {
    const update = async () => {
      const {symbol, endDate, timeframe} = forexPairContext;
      const resp = await fetchData(symbol.key, endDate, timeframe);
      forexPairContext.setTradingStrategySummary(resp.summaries[forexPairContext.strategy]);
      updateData(resp);
    };

    update();

    const pageVisibileEventHandler = () => {
      if (!document.hidden) {
        update();
      }
    };

    document.addEventListener(
      "visibilitychange",
      pageVisibileEventHandler,
      false
    );

    return () => {
      document.removeEventListener(
        "visibilitychange",
        pageVisibileEventHandler
      );
    };
  }, [
    forexPairContext.symbol,
    forexPairContext.refresh,
    forexPairContext.timeframe,
    forexPairContext.endDate,
    forexPairContext.strategy,
  ]);

  const renderOrderHistory = () => {
    if (!data.orders) {
      return null;
    }
    const orders = data.orders[forexPairContext.strategy] || [];
    return orders.map((order) => {
      return (
        <tr key={order.index}>
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
        <Columns.Column>
          <div
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
          </div>
        </Columns.Column>
      </Columns>
    </Container>
  );
};
