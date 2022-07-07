import React from "react";
import "./App.css";
import Hero from 'react-bulma-components/lib/components/hero';
import Container from 'react-bulma-components/lib/components/container';
import { Navbar } from './components/navbar';
import { RealtimeView } from "./views/realtimeView";
import { BackTestView } from "./views/backTestView";
import { ForexPairContext, useForexPairContext } from './context/forexPairContext';


const App = () => {

	const useForexPair = useForexPairContext();

	return (
		<ForexPairContext.Provider value={useForexPair}>
			<Hero size="fullheight">
				<Hero.Body style={{ paddingTop: "20px" }}>
					<Container breakpoint="widescreen">
						<Container breakpoint="widescreen" style={{ padding: "20px 0" }}>
							<Navbar></Navbar>
						</Container>
						<Container breakpoint="widescreen">
							{!useForexPair.isBackTest && <RealtimeView></RealtimeView>}
							{useForexPair.isBackTest && <BackTestView></BackTestView>}
						</Container>
					</Container>
				</Hero.Body>
				<Hero.Footer>
					<div className="bd-notification is-danger"></div>
				</Hero.Footer>
			</Hero>
		</ForexPairContext.Provider>
	);
};

export default App;
