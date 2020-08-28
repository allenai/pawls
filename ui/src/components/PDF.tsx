import React, { useRef, useEffect, useState }  from 'react';
import { PDFPageProxy, PDFDocumentProxy } from 'pdfjs-dist';
import { Result } from '@allenai/varnish';

import { CenterOnPage } from '../components';

enum ViewState {
    INITIALIZING, INITIALIZED, RENDERED, ERROR
}

export const PDF = ({ doc, page }: { doc: PDFDocumentProxy, page?: number }) => {
    const [ viewState, setViewState ] = useState<ViewState>(ViewState.INITIALIZING);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const pageNo = page || 1;

    useEffect(() => {
        doc.getPage(pageNo).then(
            (page: PDFPageProxy) => {
                setViewState(ViewState.INITIALIZED);
                const canvas = canvasRef.current;
                if (canvas === null) {
                    console.error('Error: No canvas element.');
                    setViewState(ViewState.ERROR);
                    return;
                }
                if (canvas.parentElement === null) {
                    console.error('Error: The canvas element does not have a valid parent element.');
                    setViewState(ViewState.ERROR);
                    return;
                }
                // Calculate the width of the document.
                // See: https://github.com/mozilla/pdf.js/blob/7edc5cb79fe829d45fed85e2b4b6d8594522cc10/src/display/api.js#L1039
                const width = page.view[2] - page.view[1];

                // Scale it so the user doesn't have to scroll horizontally
                const scale = Math.max(canvas.parentElement.clientWidth / width);

                // TODO (@codeviking): Add an event listener for adjusting the canvas dimensions and
                // the viewport scale when the window is resized.
                const viewport = page.getViewport({ scale });
                canvas.height = viewport.height;
                canvas.width = viewport.width;

                const canvasContext = canvas.getContext('2d');
                if (canvasContext === null) {
                    console.error('Error: No valid canvas context.');
                    setViewState(ViewState.ERROR);
                    return;
                }
                page.render({
                    canvasContext,
                    viewport: viewport
                });
                setViewState(ViewState.RENDERED);
            },
            reason => {
                console.error(`Error rendering PDF: `, reason);
                setViewState(ViewState.ERROR);
            }
        );
    }, [ doc, pageNo ]);

    return (
        viewState === ViewState.ERROR ? (
            <Result
                status="warning"
                title="Error Rendering PDF" />
        ) : (
            <canvas ref={canvasRef} />
        )
    );
};
