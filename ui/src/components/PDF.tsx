import React, { useRef, useEffect, useState }  from 'react';
import { PDFPageProxy, PDFDocumentProxy, PDFRenderTask } from 'pdfjs-dist';
import { Result } from '@allenai/varnish';

class PDFPageRenderer {
    private currentRenderTask?: PDFRenderTask;
    constructor(
        readonly page: PDFPageProxy,
        readonly canvas: HTMLCanvasElement | null,
    ) {}
    cancelCurrentRender(onError: (e: Error) => void) {
        if (this.currentRenderTask === undefined) {
            return;
        }
        this.currentRenderTask.promise.then(
            () => {},
            (err: any) => {
                if (err instanceof Error) {
                    if (err.name !== 'RenderingCancelledException') {
                        onError(err);
                    }
                } else {
                    onError(new Error(err));
                }
            }
        );
        this.currentRenderTask.cancel();
    }
    render() {
        if (this.canvas === null) {
            throw new Error('No canvas');
        }
        if (this.canvas.parentElement === null) {
            throw new Error('The canvas element has no parent');
        }
        const width = this.page.view[2] - this.page.view[1];

        // Scale it so the user doesn't have to scroll horizontally
        const scale = Math.max(this.canvas.parentElement.clientWidth / width);

        const viewport = this.page.getViewport({ scale });
        this.canvas.height = viewport.height;
        this.canvas.width = viewport.width;

        const canvasContext = this.canvas.getContext('2d');
        if (canvasContext === null) {
            throw new Error('No canvas context');
        }
        this.currentRenderTask = this.page.render({ canvasContext, viewport });
        return this.currentRenderTask;
    }
    rescaleAndRender(onError: (e: Error) => void) {
        this.cancelCurrentRender(onError);
        return this.render();
    }
}

interface WithErrorCallback {
    onError: (e: Error) => void;
}

interface PageProps extends WithErrorCallback {
    page: PDFPageProxy;
}

const Page = ({ page, onError }: PageProps) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        try {
            const renderer = new PDFPageRenderer(page, canvasRef.current);
            renderer.render();

            const rescalePdf = () => { renderer.rescaleAndRender(onError) };
            window.addEventListener('resize', rescalePdf);
            return () => { window.removeEventListener('resize', rescalePdf) };
        } catch (e) {
            onError(e);
        }
    }, [ page, onError ]);

    return <canvas ref={canvasRef} />;
};

interface PDFProps {
    doc: PDFDocumentProxy;
    page?: number;
}

interface WithPageProps extends PDFProps, WithErrorCallback {
    children: (page: PDFPageProxy) => React.ReactNode;
}

const WithPage = ({ doc, page, onError, children }: WithPageProps) => {
    const [ pdfPage, setPdfPage ] = useState<PDFPageProxy>();
    const pageNo = page || 1;

    useEffect(() => {
        doc.getPage(pageNo).then(
            (page: PDFPageProxy) => {
                setPdfPage(page);
            },
            reason => {
                onError(new Error(reason));
            }
        );
    }, [ doc, pageNo, onError ]);

    // TODO (@codeviking): The `getPage()` call above returns fast enough that we don't have
    // any type of interstitial display here. We probably should put one in place for slower
    // clients.
    return pdfPage ? <>{children(pdfPage)}</> : null;
};

export const PDF = (props: PDFProps) => {
    const [ err, setError ] = useState<Error>();
    if (err) {
        console.error(`Error rendering PDF: `, err);
    }
    return (
        err ? (
            <Result
                status="warning"
                title="Unable to Render PDF" />
        ) : (
            <WithPage {...{...props, onError: setError }}>
                {p => <Page page={p} onError={setError} />}
            </WithPage>
        )
    );
};

