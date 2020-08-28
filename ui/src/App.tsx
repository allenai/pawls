/**
 * This is the top-level component that defines your UI application.
 *
 * This is an appropriate spot for application wide components and configuration,
 * stuff like application chrome (headers, footers, navigation, etc), routing
 * (what urls go where), etc.
 *
 * @see https://github.com/reactjs/react-router-tutorial/tree/master/lessons
 */

import * as React from 'react';
import { createGlobalStyle } from 'styled-components';
import { BrowserRouter, Route, Redirect } from 'react-router-dom';

import { PDFPage } from './pages';

const App = () => (
    <>
        <BrowserRouter>
            <Route path="/" exact>
                {/* TODO (@codeviking): This is temporary. */}
                <Redirect to="/pdf/34f25a8704614163c4095b3ee2fc969b60de4698" />
            </Route>
            <Route path="/pdf/:sha" component={PDFPage} />
        </BrowserRouter>
        <GlobalStyles />
    </>
);


// Setup the viewport so it takes up all available real-estate.
const GlobalStyles = createGlobalStyle`
    html, body, #root {
        display: flex;
        flex-grow: 1;
    }
`;

export default App;
