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
import { BrowserRouter, Route, Redirect} from 'react-router-dom';

import { PDFPage } from './pages';
import { getAllocatedPaperInfo } from "./api"

const App = () => {
    const [sha, setSha] = useState<string>();
    useEffect(() => {
        getAllocatedPaperInfo().then((papers) => {
            const first = papers[0]
            setSha(first.sha)
        })
    },[])

    return (
        <>
            <BrowserRouter>
                <Route path="/" exact>
                    {sha ?
                    <Redirect to={`/pdf/${sha}`} />
                    : null
                    }
                </Route>
                <Route path="/pdf/:sha" component={PDFPage} />
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
