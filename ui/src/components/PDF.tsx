import React, { forwardRef, useContext, useRef, useEffect, useState }  from 'react';
import styled from 'styled-components';
import { PDFPageProxy, PDFRenderTask } from 'pdfjs-dist';

import { Token } from '../api';
import { TokenSpanAnnotation, PDFPageInfo, AnnotationStore, PDFStore, Bounds } from '../context';

class PDFPageRenderer {
    private currentRenderTask?: PDFRenderTask;
    public scale: number = 1;
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
                    // We have to use the message because minification in production obfuscates
                    // the error name.
                    if (err.message.indexOf('Rendering cancelled')) {
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
        const parent = this.canvas.parentElement;
        const parentStyles = getComputedStyle(parent);
        const padding =
            parseFloat(parentStyles.paddingLeft || "0") +
            parseFloat(parentStyles.paddingRight || "0");

        this.scale = Math.max((this.canvas.parentElement.clientWidth - padding) / width);
        const viewport = this.page.getViewport({ scale: this.scale });

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

/**
 * Returns the provided bounds adjusted to be relative to the top-left corner of the provided
 * element.
 */
function relativeTo(bounds: Bounds, container: HTMLElement): Bounds {
    return {
        left: bounds.left - container.offsetLeft,
        top: bounds.top - container.offsetTop,
        right: bounds.right - container.offsetLeft,
        bottom: bounds.bottom - container.offsetTop
    };
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

interface PageProps {
    pageInfo: PDFPageInfo;
    selection?: Bounds;
    selectedTokens?: Token[];
    setError: (e: Error) => void;
}

const Page = forwardRef<HTMLDivElement, PageProps>(({ pageInfo, selectedTokens, setError }, ref) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [ isVisible, setIsVisible ] = useState<boolean>(false);

    const pdfStore = useContext(PDFStore);
    const setPageScale = pdfStore.setPageScale;

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

            const renderer = new PDFPageRenderer(pageInfo.page, canvasRef.current);
            renderer.render();
            setPageScale(pageInfo.page.pageNumber - 1, renderer.scale);
            determinePageVisiblity();

            const handleResize = () => {
                renderer.rescaleAndRender(setError)
                setPageScale(pageInfo.page.pageNumber - 1, renderer.scale);
                determinePageVisiblity();
            };
            window.addEventListener('resize', handleResize);
            window.addEventListener('scroll', determinePageVisiblity);
            return () => {
                window.removeEventListener('resize', handleResize)
                window.removeEventListener('scroll', determinePageVisiblity);
            };
        } catch (e) {
            setError(e);
        }
    }, [ pageInfo.page ]); // TODO (@codeviking): Passing `setPageScale` here caused an error.

    return (
        <PageAnnotationsContainer ref={ref}>
            <PageCanvas ref={canvasRef} />
            {// We only render the tokens if the page is visible, as rendering them all makes the
             // page slow and/or crash.
                isVisible && selectedTokens && selectedTokens.map((t, i) => {
                    const b = pageInfo.getScaledTokenBounds(t);
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
                })}
        </PageAnnotationsContainer>
    );
});

interface SelectionProps {
   bounds: Bounds;
}

const Selection = ({ bounds }: SelectionProps) => {
    const width = bounds.right - bounds.left;
    const height = bounds.bottom - bounds.top;
    const rotateY = width < 0 ? -180 : 0;
    const rotateX = height < 0 ? -180 : 0;
    return (
        <SelectionBounds
            style={{
                left: `${bounds.left}px`,
                top: `${bounds.top}px`,
                width: `${Math.abs(width)}px`,
                height: `${Math.abs(height)}px`,
                transform: `rotateY(${rotateY}deg) rotateX(${rotateX}deg)`,
                transformOrigin: 'top left'
            }} />
    );
}

export const PDF = () => {
    const containerRef = useRef<HTMLDivElement>(null);
    const [ selection, setSelection ] = useState<Bounds>();

    const pdfStore = useContext(PDFStore);
    const pageRefs = useRef<HTMLDivElement[]>([]);

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
                    if (pdfStore.doc && pdfStore.pages) {
                        const annotation: TokenSpanAnnotation = [];
                        for (let i = 0; i < pdfStore.doc.numPages; i++) {
                            const p = pdfStore.pages[i];
                            if (pageRefs.current[i] !== null) {
                                annotation.push(
                                    ...p.getIntersectingTokenIds(normalizeBounds(relativeTo(
                                        selection,
                                        pageRefs.current[i]
                                    )))
                                );
                            }
                        }
                        if (annotation.length > 0) {
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
                let selectedTokens: Token[] = [];
                // If the user is selecting something, display that. Otherwise display the
                // currently selection annotation.
                // TODO (@codeviking): We probably eventually want to display both.
                if (selection && pageRefs.current[pageIndex] !== null) {
                    selectedTokens = p.getIntersectingTokens(normalizeBounds(relativeTo(
                        selection,
                        pageRefs.current[pageIndex]
                    )));
                } else if (annotationStore.selectedTokenSpanAnnotation) {
                    // This is an o(n) scan for every page. If this gets too expensive we could
                    // use a dictionary to make the lookup faster. That said I bet it's fine for
                    // the scale we're talking about.
                    for (const tokenId of annotationStore.selectedTokenSpanAnnotation) {
                        if (tokenId.pageIndex === pageIndex) {
                            selectedTokens.push(p.tokens[tokenId.tokenIndex]);
                        }
                    }
                }

                return (
                    <Page
                        key={p.page.pageNumber}
                        ref={e => {
                            if (e !== null) {
                                pageRefs.current = [
                                    ...pageRefs.current.slice(0, pageIndex),
                                    e,
                                    ...pageRefs.current.slice(pageIndex + 1)
                                ];
                            }
                        }}
                        pageInfo={p}
                        selectedTokens={selectedTokens}
                        setError={pdfStore.setError} />
                );
            })}
            {selection ? <Selection bounds={selection} /> : null}
        </PDFAnnotationsContainer>
    );
};



const PDFAnnotationsContainer = styled.div`
    position: relative;
`;

const SelectionBounds = styled.div(({ theme }) => `
    position: absolute;
    border: 1px dotted ${theme.color.G4};
`);

interface TokenSpanProps {
    isSelected?: boolean;
}

const TokenSpan = styled.span<TokenSpanProps>(({ theme, isSelected }) =>`
    position: absolute;
    background: ${isSelected ? theme.color.B6 : 'none'};
    opacity: 0.4;
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

