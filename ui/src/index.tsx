/**
 * This is the main entry point for the UI. You should not need to make any
 * changes here unless you want to update the theme.
 *
 * @see https://github.com/allenai/varnish
 */

import React from 'react';
import ReactDOM from 'react-dom';
import { BrowserRouter, Route } from 'react-router-dom';
import { ThemeProvider } from '@allenai/varnish';
import '@allenai/varnish/dist/varnish.css';

import App from './App';
import Uploader from './uploader/Uploader';

ReactDOM.render(
    <BrowserRouter>
        <ThemeProvider>
            <Route path="/" component={App} />
            <Route path="/upload" component={Uploader} />
        </ThemeProvider>
    </BrowserRouter>,
    document.getElementById('root')
);
