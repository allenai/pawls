/**
 * This is the top-level component that defines your UI application.
 *
 * This is an appropriate spot for application wide components and configuration,
 * stuff like application chrome (headers, footers, navigation, etc), routing
 * (what urls go where), etc.
 *
 * @see https://github.com/reactjs/react-router-tutorial/tree/master/lessons
 */

import React, { useEffect, useState } from 'react';
import { createGlobalStyle } from 'styled-components';
import { Spin } from "@allenai/varnish";
import { BrowserRouter, Route, Redirect} from 'react-router-dom';

import { PDFPage } from './pages';
import { CenterOnPage } from "./components"
import { getAllocatedPaperStatus } from "./api"


const RedirectToFirstPaper = () => {
    const [sha, setSha] = useState<string>();
    useEffect(() => {
        getAllocatedPaperStatus().then((papers) => {
            const first = papers[0]
            setSha(first.sha)
        })
    },[])

    return sha ? <Redirect to={`/pdf/${sha}`} /> : (
        <CenterOnPage>
            <Spin size="large"/>
        </CenterOnPage>
    )
}


const App = () => {
    return (
        <>
            <BrowserRouter>
                <Route path="/" exact component={RedirectToFirstPaper}/>
                <Route path="/pdf/:sha" render={() => <PDFPage email={"markn@allenai.org"}/>} />
            </BrowserRouter>
            <GlobalStyles />
        </>
        )
    };


// Setup the viewport so it takes up all available real-estate.
const GlobalStyles = createGlobalStyle`
    html, body, #root {
        display: flex;
        flex-grow: 1;
    }
`;

export default App;
