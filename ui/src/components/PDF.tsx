import React, { useContext, useRef, useEffect, useState }  from 'react';
import styled from 'styled-components';
import { PDFPageProxy, PDFRenderTask } from 'pdfjs-dist';

import { Annotation, PDFPageInfo, AnnotationStore, PDFStore, Bounds, TokenId, Optional, normalizeBounds, handleNewAnnotations } from '../context';
import { Selection, SelectionBoundary, SelectionTokens } from '../components'

class PDFPageRenderer {
    private currentRenderTask?: PDFRenderTask;
    constructor(
        readonly page: PDFPageProxy,
        readonly canvas: HTMLCanvasElement,
        readonly onError: (e: Error) => void
    ) {}
    cancelCurrentRender() {
        if (this.currentRenderTask === undefined) {
            return;
        }
        this.currentRenderTask.promise.then(
            () => {},
            (err: any) => {
                if (
                    err instanceof Error
                    && err.message.indexOf('Rendering cancelled') !== -1
                ) {
                    // Swallow the error that's thrown when the render is canceled.
                    return;
                }
                const e = err instanceof Error ? err : new Error(err);
                this.onError(e);
            }
        );
        this.currentRenderTask.cancel();
    }
    render(scale: number) {
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
    rescaleAndRender(scale: number) {
        this.cancelCurrentRender();
        return this.render(scale);
    }
}

function getPageBoundsFromCanvas(canvas: HTMLCanvasElement): Bounds {
    if (canvas.parentElement === null) {
        throw new Error('No canvas parent');
    }
    const parent = canvas.parentElement;
    const parentStyles = getComputedStyle(canvas.parentElement);

    const leftPadding = parseFloat(parentStyles.paddingLeft || "0");
    const left = parent.offsetLeft + leftPadding;

    const topPadding = parseFloat(parentStyles.paddingTop || "0");
    const top = parent.offsetTop + topPadding;

    const parentWidth =
        parent.clientWidth - leftPadding - parseFloat(parentStyles.paddingRight || "0");
    const parentHeight =
        parent.clientHeight - topPadding - parseFloat(parentStyles.paddingBottom || "0");
    return {
        left,
        top,
        right: left + parentWidth,
        bottom: top + parentHeight
    };
}

interface PageProps {
    pageInfo: PDFPageInfo;
    onError: (e: Error) => void;
}

const Page = ({ pageInfo, onError }: PageProps) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [ isVisible, setIsVisible ] = useState<boolean>(false);
    const [ scale, setScale ] = useState<number>(1);

    const annotationStore = useContext(AnnotationStore);

    const containerRef = useRef<HTMLDivElement>(null);
    const [ selection, setSelection ] = useState<Bounds>();

    const extraTokens = undefined
    const annotations = annotationStore.pdfAnnotations[pageInfo.page.pageNumber - 1]


    const removeAnnotation = (annotation: Annotation, page: number): void => {
        // TODO(Mark): guarantee uniqueness in tokenSpanAnnotations.
        const store = annotationStore.pdfAnnotations.slice(0)
        const annotationId = annotation.toString()
        const dropped = annotationStore.pdfAnnotations[page].filter(a => a.toString()!== annotationId)
        store[page] = dropped

        if (annotation.linkedAnnotation) {
            // TODO(Mark): Currently this assumes that only individual annotations
            // are linked - if that changes, update this to use an interative modification
            // of `store`, NOT recursive, because the updates to the actual annotationStore
            // context get stomped on by the subsequent updates. We have to collect all the changes
            // locally and update the context one time.
            const page = annotation.linkedAnnotation.page
            const annotationId = annotation.linkedAnnotation.toString()
            const dropped = annotationStore.pdfAnnotations[page].filter(a => a.toString()!== annotationId)
            store[page] = dropped
        }
        annotationStore.setPdfAnnotations(store)
    }

    useEffect(() => {
        try {
            const determinePageVisiblity = () => {
                if (canvasRef.current !== null) {
                    const windowTop = 0;
                    const windowBottom = window.innerHeight;
                    const rect = canvasRef.current.getBoundingClientRect();
                    setIsVisible(
                        (rect.top > windowTop && rect.top < windowBottom) ||
                        (rect.bottom > windowTop && rect.bottom < windowBottom) ||
                        (rect.top < windowTop && rect.bottom > windowTop)
                    );
                }
            };

            if (canvasRef.current === null) {
                onError(new Error('No canvas element'));
                return;
            }

            pageInfo.bounds = getPageBoundsFromCanvas(canvasRef.current);
            const renderer = new PDFPageRenderer(pageInfo.page, canvasRef.current, onError);
            renderer.render(pageInfo.scale);

            determinePageVisiblity();

            const handleResize = () => {
                if (canvasRef.current === null) {
                    onError(new Error('No canvas element'));
                    return;
                }
                pageInfo.bounds = getPageBoundsFromCanvas(canvasRef.current)
                renderer.rescaleAndRender(pageInfo.scale);
                setScale(pageInfo.scale)
                determinePageVisiblity();
            };
            window.addEventListener('resize', handleResize);
            window.addEventListener('scroll', determinePageVisiblity);
            return () => {
                window.removeEventListener('resize', handleResize)
                window.removeEventListener('scroll', determinePageVisiblity);
            };
        } catch (e) {
            onError(e);
        }
    }, [ pageInfo, onError ]); // We deliberately only run this once.

    return (
        <PageAnnotationsContainer
            ref={containerRef}
            onMouseDown={(event) => {
                if (containerRef.current === null) {
                    throw new Error('No Container');
                }
                // Clear the selected annotation, if there is one.
                // TODO (@codeviking): This might change.
                annotationStore.setSelectedAnnotation(undefined);
                if (!selection) {
                    const left = event.pageX - containerRef.current.offsetLeft;
                    const top = event.pageY - containerRef.current.offsetTop;
                    setSelection({
                        left,
                        top,
                        right: left,
                        bottom: top
                    });
                }
            }}
            onMouseMove={selection ? (
                (event) => {
                    if (containerRef.current === null) {
                        throw new Error('No Container');
                    }
                    setSelection({
                        ...selection,
                        right: event.pageX - containerRef.current.offsetLeft,
                        bottom: event.pageY - containerRef.current.offsetTop
                    });
                }
            ) : undefined}
            onMouseUp={selection ? (
                () => {
                    if (annotationStore.activeLabel) {
                        const updatedAnnotations = handleNewAnnotations(
                            //TODO(Mark): Change
                            pageInfo,
                            selection,
                            annotationStore.pdfAnnotations,
                            annotationStore.activeLabel,
                            annotationStore.freeFormAnnotations
                        )
                        annotationStore.setPdfAnnotations(updatedAnnotations)
                    }
                    setSelection(undefined);

                }
            ) : undefined}
        
        >
            <PageCanvas ref={canvasRef} />
            {// We only render the tokens if the page is visible, as rendering them all makes the
             // page slow and/or crash.
                scale && isVisible && annotations.map((annotation) => (
                        <Selection
                            pageInfo={pageInfo}
                            tokens={annotation.tokens}
                            key={annotation.toString()}
                            label={annotation.label}
                            bounds={pageInfo.getScaledBounds(annotation.bounds)}
                            onClickDelete={() => removeAnnotation(annotation, pageInfo.page.pageNumber - 1)}
                        />
                    )
                )
            }
            {extraTokens ? <SelectionTokens pageInfo={pageInfo} tokens={extraTokens}/> : null}
            {selection && annotationStore.activeLabel ? (
                <SelectionBoundary
                   bounds={selection}
                   color={annotationStore.activeLabel.color}
                />
            ) : null}

        </PageAnnotationsContainer>
    );
};


export const PDF = () => {

    const pdfStore = useContext(PDFStore);

    // TODO (@codeviking): Use error boundaries to capture these.
    if (!pdfStore.doc) {
        throw new Error('No Document');
    }
    if (!pdfStore.pages) {
        throw new Error('Document without Pages');
    }

    return (
        <>
            {pdfStore.pages.map((p) => {
                return (
                    <Page
                        key={p.page.pageNumber}
                        pageInfo={p}
                        onError={pdfStore.onError}
                    />
                );
            })}
        </>
    );
};



const PDFAnnotationsContainer = styled.div`
    position: relative;
`;

const PageAnnotationsContainer = styled.div(({ theme }) =>`
    position: relative;
    box-shadow: 2px 2px 4px 0 rgba(0, 0, 0, 0.2);
    margin: 0 0 ${theme.spacing.xs};

    &:last-child {
        margin-bottom: 0;
    }
`);

const PageCanvas = styled.canvas`
    display: block;
`;
