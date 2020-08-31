import React, { useContext, useState, useEffect } from 'react';
import styled, { ThemeContext } from 'styled-components';
import { useParams } from 'react-router-dom';
import pdfjs from 'pdfjs-dist';
import { Result, Progress } from '@allenai/varnish';
import { QuestionCircleOutlined } from '@ant-design/icons';

import { PDF, CenterOnPage } from '../components';

// This tells PDF.js the URL the code to load for it's webworker, which handles heavy-handed
// tasks in a background thread. Ideally we'd load this from the application itself rather
// than from the CDN to keep things local.
// TODO (@codeviking): Figure out how to get webpack to package up the PDF.js webworker code.
pdfjs.GlobalWorkerOptions.workerSrc =
    `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.js`;

// This callback exists in the source code, but not in the TypeScript types. So we mix it in
// to make TypeScript happy.
// See: https://github.com/mozilla/pdf.js/blob/master/src/display/api.js#L510
interface PDFLoadingTask extends pdfjs.PDFLoadingTask<pdfjs.PDFDocumentProxy> {
    onProgress?: (p: pdfjs.PDFProgressData) => void;
}

enum ViewState {
    LOADING, LOADED, NOT_FOUND, ERROR
}

export const PDFPage = () => {
    const { sha } = useParams<{ sha: string }>();
    const [ viewState, setViewState ] = useState<ViewState>(ViewState.LOADING);
    const [ doc, setDocument ] = useState<pdfjs.PDFDocumentProxy>();
    const [ progress, setProgress ] = useState(0);
    const theme = useContext(ThemeContext);

    useEffect(() => {
        setDocument(undefined);
        const pdfUrl = `/api/pdf/${sha}`;
        const loadingTask: PDFLoadingTask = pdfjs.getDocument(pdfUrl)
        loadingTask.onProgress = (p: pdfjs.PDFProgressData) => {
            setProgress(Math.round(p.loaded / p.total * 100));
        };
        loadingTask.promise.then(
            doc => {
                setDocument(doc);
                setViewState(ViewState.LOADED);
            },
            (reason: any) => {
                if (reason instanceof Error) {
                    if (reason.name === 'MissingPDFException') {
                        setViewState(ViewState.NOT_FOUND);
                        return;
                    }
                }
                setViewState(ViewState.ERROR);
            }
        );
    }, [ sha ]);

    switch (viewState) {
        case ViewState.LOADING:
            return (
                <CenterOnPage>
                    <Progress
                        type="circle"
                        percent={progress}
                        strokeColor={{ '0%': theme.color.T6, '100%': theme.color.G6 }} />
                </CenterOnPage>
            );
        case ViewState.NOT_FOUND:
            return (
                <CenterOnPage>
                    <Result
                        icon={<QuestionCircleOutlined />}
                        title="PDF Not Found" />
                </CenterOnPage>
            );
        case ViewState.LOADED:
            if (doc) {
                return (
                    <WithSidebar>
                        <Sidebar>
                            👋 Hi. There will be useful stuff here soon.
                        </Sidebar>
                        <PDFContainer>
                            <PDF doc={doc} />
                        </PDFContainer>
                    </WithSidebar>
                );
            }
        // eslint-disable-line: no-fallthrough
        case ViewState.ERROR:
            return (
                <CenterOnPage>
                    <Result
                        status="warning"
                        title="Unable to Render Document" />
                </CenterOnPage>
            );
    }
};

const WithSidebar = styled.div`
    display: grid;
    flex-grow: 1;
    grid-template-columns: 300px auto;
`;

const Sidebar = styled.div(({ theme }) => `
    background: ${theme.color.N10};
    color: ${theme.color.N1};
    padding: ${theme.spacing.lg} ${theme.spacing.xl};
`);

const PDFContainer = styled.div(({ theme }) => `
    overflow: scroll;
    background: ${theme.color.N4};
    padding: ${theme.spacing.sm};
`);
