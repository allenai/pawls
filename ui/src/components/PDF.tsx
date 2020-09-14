import React, { useContext, useRef, useEffect, useState }  from 'react';
import styled from 'styled-components';
import { PDFPageProxy, PDFRenderTask } from 'pdfjs-dist';

import { TokenSpanAnnotation, PDFPageInfo, AnnotationStore, PDFStore, Bounds } from '../context';
import { Selection } from '../components'

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

/**
 * Returns the provided bounds in their normalized form. Normalized means that the left
 * coordinate is always less than the right coordinate, and that the top coordinate is always
 * left than the bottom coordinate.
 *
 * This is required because objects in the DOM are positioned and sized by setting their top-left
 * corner, width and height. This means that when a user composes a selection and moves to the left,
 * or up, from where they started might result in a negative width and/or height. We don't normalize
 * these values as we're tracking the mouse as it'd result in the wrong visual effect. Instead we
 * rotate the bounds we render on the appropriate axis. This means we need to account for this
 * later when calculating what tokens the bounds intersect with.
 */
function normalizeBounds(b: Bounds): Bounds {
    const normalized = Object.assign({}, b);
    if (b.right < b.left) {
        const l = b.left;
        normalized.left = b.right;
        normalized.right = l;
    }
    if (b.bottom < b.top) {
        const t = b.top;
        normalized.top = b.bottom;
        normalized.bottom = t;
    }
    return normalized;
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
    annotations: TokenSpanAnnotation[];
    onError: (e: Error) => void;
}

const Page = ({ pageInfo, annotations, onError }: PageProps) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [ isVisible, setIsVisible ] = useState<boolean>(false);

    const annotationStore = useContext(AnnotationStore);

    const removeAnnotationCallback = (annotation: TokenSpanAnnotation): (() => void) => {
        return () => {
            // TODO(Mark): guarantee uniqueness in tokenSpanAnnotations.
            const annotationId = annotation.toString()
            const dropped = annotationStore.tokenSpanAnnotations.filter(a => a.toString()!== annotationId)
            annotationStore.setTokenSpanAnnotations(dropped)
        }
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
        <PageAnnotationsContainer>
            <PageCanvas ref={canvasRef} />
            {// We only render the tokens if the page is visible, as rendering them all makes the
             // page slow and/or crash.

                isVisible && annotations.map((annotation) => {
                    const tokens = annotation.tokens.map((t, i) => {
                        const b = pageInfo.getScaledTokenBounds(pageInfo.tokens[t.tokenIndex]);
                        return (
                            <TokenSpan
                                key={i}
                                isSelected={true}
                                style={{
                                    left: `${b.left}px`,
                                    top: `${b.top}px`,
                                    width: `${b.right - b.left}px`,
                                    height: `${b.bottom - b.top}px`
                                }} />
                            )
                        })
                    const selections = annotation.bounds.map((bound, i) => (
                            <Selection
                               key={annotation.toString()}
                               label={annotation.label}
                               bounds={pageInfo.getScaledBounds(bound)}
                               isActiveSelection={false}
                               onClickDelete={removeAnnotationCallback(annotation)}
                            />
                          )
                        )
                    return (
                        <div key={annotation.toString()}>
                            {tokens}
                            {selections}
                        </div>
                        )
                    }
                )
            }
        </PageAnnotationsContainer>
    );
};


export const PDF = () => {
    const containerRef = useRef<HTMLDivElement>(null);
    const [ selection, setSelection ] = useState<Bounds>();

    const pdfStore = useContext(PDFStore);
    const annotationStore = useContext(AnnotationStore);

    // TODO (@codeviking): Use error boundaries to capture these.
    if (!pdfStore.doc) {
        throw new Error('No Document');
    }
    if (!pdfStore.pages) {
        throw new Error('Document without Pages');
    }

    return (
        <PDFAnnotationsContainer
            ref={containerRef}
            onMouseDown={(event) => {
                if (containerRef.current === null) {
                    throw new Error('No Container');
                }
                // Clear the selected annotation, if there is one.
                // TODO (@codeviking): This might change.
                annotationStore.setSelectedTokenSpanAnnotation(undefined);
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
                    if (pdfStore.doc && pdfStore.pages && annotationStore.activeLabel) {
                        let annotation = new TokenSpanAnnotation([], [], [], annotationStore.activeLabel)

                        // Loop over all pages to find tokens that intersect with the current
                        // selection, since we allow selections to cross page boundaries.
                        for (let i = 0; i < pdfStore.doc.numPages; i++) {
                            const p = pdfStore.pages[i];
                            const next = p.getTokenSpanAnnotationForBounds(normalizeBounds(selection), annotationStore.activeLabel)
                            if (next.tokens.length > 0) {
                                annotation = annotation.mergeWith(next)
                            }
                        }
                        if (annotation.tokens.length > 0) {
                            const withNewAnnotation =
                                annotationStore.tokenSpanAnnotations.concat([ annotation ])
                            annotationStore.setTokenSpanAnnotations(withNewAnnotation);
                        }
                    }
                    setSelection(undefined);

                }
            ) : undefined}
        >
            {pdfStore.pages.map((p, pageIndex) => {
                // If the user is selecting something, display that. Otherwise display the
                // currently selection annotation.
                const existingAnnotations = annotationStore.tokenSpanAnnotations.map(a => a.annotationsForPage(pageIndex))
                if (selection && annotationStore.activeLabel) {
                    const annotation = p.getTokenSpanAnnotationForBounds(normalizeBounds(selection), annotationStore.activeLabel)
                    // When the user is actively making a selection, we render the
                    // bounds below rather than in the page, for 2 reasons:
                    // 1) The bounds might go across pages
                    // 2) The computed bounds for the annotation encapsulate it,
                    //    but this is a weird experience when you are trying to accurately
                    //    select tokens.
                    annotation.bounds = []
                    existingAnnotations.push(annotation)
                }

                return (
                    <Page
                        key={p.page.pageNumber}
                        pageInfo={p}
                        annotations={existingAnnotations}
                        onError={pdfStore.onError} />
                );
            })}
            {selection && annotationStore.activeLabel ? (
                <Selection
                   bounds={selection}
                   label={annotationStore.activeLabel}
                   isActiveSelection={true}
                />
            ) : null}
        </PDFAnnotationsContainer>
    );
};



const PDFAnnotationsContainer = styled.div`
    position: relative;
`;

interface TokenSpanProps {
    isSelected?: boolean;
}

const TokenSpan = styled.span<TokenSpanProps>(({ theme, isSelected }) =>`
    position: absolute;
    background: ${isSelected ? theme.color.B6 : 'none'};
    opacity: 0.2;
    border-radius: 3px;
`);

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
