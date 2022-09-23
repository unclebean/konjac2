import React, {useState, useEffect, useRef} from "react";
import Plot from "react-plotly.js";

const traceConfig = {
  decreasing: {line: {color: "#f44336"}},
  increasing: {line: {color: "#26a69a"}},
  line: {color: "rgba(31,119,180,1)"},
  type: "candlestick",
  xaxis: "x",
  yaxis: "y",
  name: "",
  mode: "lines",
};

const layout = {
  width: 800,
  height: 550,
  showlegend: false,
  responsive: true,
  spikedistance: 1,
  margin: {
    l: 50,
    r: 20,
    b: 0,
    t: 40,
  },
  xaxis1: {
    type: "category",
    showticklabels: false,
    rangeslider: {
      visible: false,
    },
    spikemode: "across",
    spikethickness: 2,
    side: "top",
    fixedrange: true,
  },
  yaxis1: {
    domain: [0.3, 1],
    fixedrange: true,
  },
  yaxis2: {
    domain: [0.1, 0.3],
    fixedrange: true,
  },
  grid: {rows: 2, columns: 1, pattern: "independent"},
  annotations: [],
};

export const CandleAndIndicators = ({candlesAndIndicators, strategy}) => {
  const chartWrapper = useRef(null);
  const [chartWidth, updateChartWidth] = useState(800);
  const [trace, updateTrace] = useState(traceConfig);
  const [histTrace, updateHistTrace] = useState({
    type: "bar",
    yaxis: "y2",
    name: "HIST",
  });
  const [macdTrace, updateMacdTrace] = useState({
    type: "scatter",
    yaxis: "y2",
    name: "MACD",
  });
  const [signalTrace, updateSignalTrace] = useState({
    type: "scatter",
    yaxis: "y2",
    name: "SIGNAL",
  });

  const [senkouATrace, updateSenkouATrace] = useState({
    type: "scatter",
    name: "SENKOU_A",
    fill: "none",
    marker: {
      color: "green",
    },
    // stackgroup: "ichimoku",
  });

  const [senkouBTrace, updateSenkouBTrace] = useState({
    type: "scatter",
    name: "SENKOU_B",
    fill: "tonexty",
    fillcolor: "rgba(198,231,255,0.5)",
    // stackgroup: "ichimoku",
  });

  const [tenkanTrace, updateTenkanTrace] = useState({
    type: "scatter",
    name: "Tenkan Sen",
  });

  const [kijunTrace, updateKijunTrace] = useState({
    type: "scatter",
    name: "Kijun Sen",
  });

  const [chikouTrace, updateChikouTrace] = useState({
    type: "scatter",
    name: "Chikou Span",
  });

  const [rsiVwapTrace, updateRsiVwapTrace] = useState({
    type: "scatter",
    yaxis: "y2",
    name: "RSI VWAP",
  });

  useEffect(() => {
    const {marketData, macd, ichimoku, threadholder, volatility, rsi_vwap} = candlesAndIndicators;
    const wrapperWidth = chartWrapper.current.offsetWidth;
    updateChartWidth(wrapperWidth);
    if (!marketData) {
      return () => {};
    }
    updateTrace({...trace, ...marketData});

    updateHistTrace({...histTrace, x: marketData.x, y: macd.hist});
    updateMacdTrace({...macdTrace, x: marketData.x, y: threadholder});
    updateSignalTrace({...signalTrace, x: marketData.x, y: volatility});

    updateSenkouATrace({
      ...senkouATrace,
      x: marketData.x,
      y: ichimoku.senkou_a,
    });

    updateSenkouBTrace({
      ...senkouBTrace,
      x: marketData.x,
      y: ichimoku.senkou_b,
    });
    updateTenkanTrace({...tenkanTrace, x: marketData.x, y: ichimoku.tenkan});
    updateKijunTrace({...kijunTrace, x: marketData.x, y: ichimoku.kijun});
    updateRsiVwapTrace({...rsiVwapTrace, x: marketData.x, y: rsi_vwap});
    // updateChikouTrace({
    //   ...chikouTrace,
    //   x: marketData.x,
    //   y: ichimoku.chikou.slice(26),
    // });
  }, [candlesAndIndicators]);

  return (
    <div
      id="chart"
      ref={chartWrapper}
      style={{border: "1px solid lightgray", overflow: "hidden"}}
    >
      <Plot
        data={[
          trace,
          senkouATrace,
          senkouBTrace,
          tenkanTrace,
          kijunTrace,
          // chikouTrace,
          // histTrace,
          rsiVwapTrace,
        ]}
        layout={{...layout, width: chartWidth}}
        config={{displaylogo: false, responsive: true}}
      />
    </div>
  );
};
