import React, {useState, useContext, useEffect, useRef} from "react";
import Dropdown from "react-bulma-components/lib/components/dropdown";
import Level from "react-bulma-components/lib/components/level";
import Box from "react-bulma-components/lib/components/box";
import Heading from "react-bulma-components/lib/components/heading";
import bulmaCalendar from "bulma-calendar/dist/js/bulma-calendar";
import "bulma-calendar/dist/css/bulma-calendar.min.css";
import Icon from "@mdi/react";
import {mdiRefreshCircle} from "@mdi/js";
import {mdiCalendarRangeOutline} from "@mdi/js";
import {ForexPairContext, AllForexPairs} from "../context/forexPairContext";
import {parse, formatISO, isToday} from "date-fns";

export const Navbar = () => {
  const style = {textAlign: "center"};
  const calendar = useRef(null);
  const [isBackTest, updateBaskTestFalg] = useState(false);
  const [showCalendar, toggleShowCalendar] = useState(false);
  const [timeframe, updateTimeframe] = useState("H1");
  const [endDate, updateEndDate] = useState("");
  const forexPairContext = useContext(ForexPairContext);
  const [strategy, updateStrategy] = useState("mama");

  useEffect(() => {
    if (calendar.current) {
      bulmaCalendar.attach(calendar.current, {displayMode: "dialog"});
      calendar.current.bulmaCalendar.on("select", function (datepicker) {
        const selectedEndDate = parse(
          datepicker.data.value(),
          "MM/dd/yyyy",
          new Date()
        );
        updateEndDate(`end date: ${datepicker.data.value()}`);
        const newEndDate = isToday(selectedEndDate)
          ? ""
          : formatISO(selectedEndDate);
        forexPairContext.setEndDate(newEndDate);
      });
    }
  }, []);

  useEffect(() => {
    toggleShowCalendar(false);
  }, [endDate]);

  const changeCurrencyPair = (selected) => {
    forexPairContext.setSymbol(selected);
  };

  const changeTimeframe = (selected) => {
    updateTimeframe(selected);
    forexPairContext.setTimeframe(selected);
  };

  const toggleBackTest = () => {
    const toggleFlag = !isBackTest;
    updateBaskTestFalg(toggleFlag);
    forexPairContext.onToggleBackTest(toggleFlag);
  };

  const toggleRefresh = () => {
    forexPairContext.toggleRefresh(!forexPairContext.refresh);
  };

  const toggleCalendar = () => {
    const toggleFlag = !showCalendar;
    if (toggleFlag) {
      calendar.current.bulmaCalendar.show();
    }
    toggleShowCalendar(toggleFlag);
  };

  const changeStrategy = (selected) => {
    updateStrategy(selected);
    forexPairContext.setStrategy(selected);
  };

  return (
    <Box>
      <Level renderAs="nav">
        <Level.Item style={style}>
          <div>
            <Heading renderAs="div" heading>
              Symbol
              <Icon
                path={mdiRefreshCircle}
                size={0.6}
                onClick={toggleRefresh}
                style={{cursor: "pointer"}}
              />
            </Heading>
            <Heading renderAs="div" style={{textAlign: "left"}}>
              <Dropdown
                label={forexPairContext.symbol.label}
                onChange={changeCurrencyPair}
              >
                {AllForexPairs.map((fp, index) => (
                  <Dropdown.Item key={index} value={fp}>
                    {fp.label}
                  </Dropdown.Item>
                ))}
              </Dropdown>
            </Heading>
          </div>
        </Level.Item>
        <Level.Item style={style}>
          <div>
            <Heading renderAs="div" heading>
              time interval
            </Heading>
            <Heading renderAs="div">
              <Dropdown
                label={timeframe}
                onChange={changeTimeframe}
                style={{textAlign: "left"}}
              >
                <Dropdown.Item value={"M5"}>M5</Dropdown.Item>
                <Dropdown.Item value={"M15"}>M15</Dropdown.Item>
                <Dropdown.Item value={"M30"}>M30</Dropdown.Item>
                <Dropdown.Item value={"H1"}>H1</Dropdown.Item>
                <Dropdown.Item value={"H4"}>H4</Dropdown.Item>
                <Dropdown.Item value={"H6"}>H6</Dropdown.Item>
                <Dropdown.Item value={"D"}>D</Dropdown.Item>
              </Dropdown>
            </Heading>
          </div>
        </Level.Item>
        <Level.Item style={style}>
          <div>
            <Heading renderAs="div" heading>
              {!endDate && "today"}
              {endDate && endDate}
            </Heading>
            <div>
              {!showCalendar && (
                <Icon
                  path={mdiCalendarRangeOutline}
                  size={1.2}
                  style={{cursor: "pointer", marginTop: "6px"}}
                  onClick={toggleCalendar}
                />
              )}
              <div style={{display: showCalendar ? "block" : "none"}}>
                <input ref={calendar} className="input" type="date" />
              </div>
            </div>
          </div>
        </Level.Item>
        <Level.Item style={style}>
          <div>
            <Heading renderAs="div" heading>
              Win
            </Heading>
            <Heading renderAs="div">
            </Heading>
          </div>
        </Level.Item>
        <Level.Item style={style}>
          <div>
            <Heading renderAs="div" heading>
              Lose
            </Heading>
            <Heading renderAs="div">
            </Heading>
          </div>
        </Level.Item>
        <Level.Item style={style}>
          <div>
            <Heading renderAs="div" heading>
              Total take pips
            </Heading>
            <Heading renderAs="div">
            </Heading>
          </div>
        </Level.Item>
        <Level.Item style={style}>
          <div>
            <Heading renderAs="div" heading>
              stragety
            </Heading>
            <Heading renderAs="div">
              <Dropdown
                label={strategy}
                onChange={changeStrategy}
                style={{textAlign: "left"}}
              >
                <Dropdown.Item value={"mama"}>mama</Dropdown.Item>
                <Dropdown.Item value={"ema"}>ema</Dropdown.Item>
                <Dropdown.Item value={"sar"}>sar</Dropdown.Item>
                <Dropdown.Item value={"vwap"}>vwap</Dropdown.Item>
                <Dropdown.Item value={"bbands"}>bbands</Dropdown.Item>
                <Dropdown.Item value={"alma"}>alma</Dropdown.Item>
                <Dropdown.Item value={"ichimoku"}>ichimoku</Dropdown.Item>
              </Dropdown>
            </Heading>
          </div>
        </Level.Item>
        <Level.Item style={style}>
          <div>
            <Heading renderAs="div" heading>
              Back Testing
            </Heading>
            <Heading renderAs="div">
              <label className="switch">
                <input type="checkbox" />
                <span className="slider round" onClick={toggleBackTest}></span>
              </label>
            </Heading>
          </div>
        </Level.Item>
      </Level>
    </Box>
  );
};
