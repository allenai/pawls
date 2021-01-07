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
import { Spin, Result } from "@allenai/varnish";
import { BrowserRouter, Route, Redirect} from 'react-router-dom';

import { PDFPage } from './pages';
import { CenterOnPage } from "./components"
import { getAllocatedPaperStatus } from "./api"


const RedirectToFirstPaper = () => {
    const [sha, setSha] = useState<string>();
    const [authenticated, setAuthenticated] = useState<boolean>(true);
    useEffect(() => {
        getAllocatedPaperStatus().then((allocation) => {
            const first = allocation.papers[0]
            setSha(first.sha)
        }).catch((err) => {
            setAuthenticated(false)
        })
    },[])

    if (!sha && authenticated) {
        return (
            <CenterOnPage>
                <Spin size="large"/>
            </CenterOnPage>
        )
    }
    else if (!sha && !authenticated) {
        return ( 

            <CenterOnPage>
                <Result
                    status="403"
                    title="403"
                    subTitle={
                        <p>
                            Sorry, you are not authorized to access this page.
                            If you believe you should have access, please try logging out 
                            <a href="https://google.login.apps.allenai.org/oauth2/sign_out"> here </a>
                            and reloading this page.
                        </p>
                        }
                />
            </CenterOnPage>
        )}
    else {
        return <Redirect to={`/pdf/${sha}`} /> 
    }
}

const App = () => {
    return (
        <>
            <BrowserRouter>
                <Route path="/" exact component={RedirectToFirstPaper}/>
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
