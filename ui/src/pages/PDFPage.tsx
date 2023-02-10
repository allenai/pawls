import React, { useContext, useCallback, useState, useEffect } from 'react';
import styled, { ThemeContext } from 'styled-components';
import { useParams } from 'react-router-dom';
import * as pdfjs from 'pdfjs-dist';
import { PDFDocumentProxy, PDFDocumentLoadingTask } from 'pdfjs-dist/types/display/api';
import { Result, Progress, notification } from '@allenai/varnish';

import { QuestionCircleOutlined } from '@ant-design/icons';

import { PDF, CenterOnPage, RelationModal } from '../components';
import {
    SidebarContainer,
    Labels,
    Annotations,
    Relations,
    AssignedPaperList,
    Header,
    Comment,
    DisplayUserInfo,
} from '../components/sidebar';
import {
    pdfURL,
    getTokens,
    PageTokens,
    PaperStatus,
    getAllocatedPaperStatus,
    getLabels,
    Label,
    getAnnotations,
    getRelations,
} from '../api';
import {
    PDFPageInfo,
    Annotation,
    AnnotationStore,
    PDFStore,
    RelationGroup,
    PdfAnnotations,
} from '../context';

import * as listeners from '../listeners';

// This tells PDF.js the URL the code to load for it's webworker, which handles heavy-handed
// tasks in a background thread. Ideally we'd load this from the application itself rather
// than from the CDN to keep things local.
// TODO (@codeviking): Figure out how to get webpack to package up the PDF.js webworker code.
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.js`;

enum ViewState {
    LOADING,
    LOADED,
    NOT_FOUND,
    ERROR,
}

export const PDFPage = () => {
    const { sha } = useParams<{ sha: string }>();
    const [viewState, setViewState] = useState<ViewState>(ViewState.LOADING);

    const [doc, setDocument] = useState<PDFDocumentProxy>();
    const [progress, setProgress] = useState(0);
    const [pages, setPages] = useState<PDFPageInfo[]>();
    const [pdfAnnotations, setPdfAnnotations] = useState<PdfAnnotations>(
        new PdfAnnotations([], [])
    );

    const [selectedAnnotations, setSelectedAnnotations] = useState<Annotation[]>([]);

    const [assignedPaperStatuses, setAssignedPaperStatuses] = useState<PaperStatus[]>([]);
    const [activePaperStatus, setActivePaperStatus] = useState<PaperStatus>();
    const [activeLabel, setActiveLabel] = useState<Label>();
    const [labels, setLabels] = useState<Label[]>([]);
    const [relationLabels, setRelationLabels] = useState<Label[]>([]);
    const [activeRelationLabel, setActiveRelationLabel] = useState<Label>();
    const [freeFormAnnotations, toggleFreeFormAnnotations] = useState<boolean>(false);
    const [hideLabels, setHideLabels] = useState<boolean>(false);

    const [relationModalVisible, setRelationModalVisible] = useState<boolean>(false);

    // React's Error Boundaries don't work for us because a lot of work is done by pdfjs in
    // a background task (a web worker). We instead setup a top level error handler that's
    // passed around as needed so we can display a nice error to the user when something
    // goes wrong.
    //
    // We have to use the `useCallback` hook here so that equality checks in child components
    // don't trigger unintentional rerenders.
    const onError = useCallback(
        (err: Error) => {
            console.error('Unexpected Error rendering PDF', err);
            setViewState(ViewState.ERROR);
        },
        [setViewState]
    );

    const theme = useContext(ThemeContext);

    const onRelationModalOk = (group: RelationGroup) => {
        setPdfAnnotations(pdfAnnotations.withNewRelation(group));
        setRelationModalVisible(false);
        setSelectedAnnotations([]);
    };

    const onRelationModalCancel = () => {
        setRelationModalVisible(false);
        setSelectedAnnotations([]);
    };

    useEffect(() => {
        getLabels().then((labels) => {
            setLabels(labels);
            setActiveLabel(labels[0]);
        });
    }, []);

    useEffect(() => {
        getRelations().then((relations) => {
            setRelationLabels(relations);
            setActiveRelationLabel(relations[0]);
        });
    }, [sha]);

    useEffect(() => {
        getAllocatedPaperStatus()
            .then((allocation) => {
                setAssignedPaperStatuses(allocation.papers);
                const foundActivePaperStatus = allocation.papers.filter((p) => p.sha === sha)[0];
                setActivePaperStatus(foundActivePaperStatus);

                /* eslint-disable */
                const description = (
                    (
                        allocation.hasAllocatedPapers
                            ? 'This paper is not assigned to you in this project. '
                            : 'This project has no assigned papers for your email address. '
                    ) + "Your annotations won't be saved. If you think this is a mistake, contact the Semantic Scholar research team."
                );
                /* eslint-enable */

                console.log(allocation);
                console.log(foundActivePaperStatus);
                console.log(sha);

                if (!allocation.hasAllocatedPapers || foundActivePaperStatus == null) {
                    notification.warn({
                        message: 'Read Only Mode!',
                        duration: 0, // do not dismiss
                        description: description,
                    });
                }
            })
            .catch((err: any) => {
                setViewState(ViewState.ERROR);
                console.log(err);
            });
    }, [sha]);

    useEffect(() => {
        setDocument(undefined);
        setViewState(ViewState.LOADING);
        const loadingTask: PDFDocumentLoadingTask = pdfjs.getDocument(pdfURL(sha));
        loadingTask.onProgress = (p: { loaded: number; total: number }) => {
            setProgress(Math.round((p.loaded / p.total) * 100));
        };
        Promise.all([
            // PDF.js uses their own `Promise` type, which according to TypeScript doesn't overlap
            // with the base `Promise` interface. To resolve this we (unsafely) cast the PDF.js
            // specific `Promise` back to a generic one. This works, but might have unexpected
            // side-effects, so we should remain wary of this code.
            (loadingTask.promise as unknown) as Promise<PDFDocumentProxy>,
            getTokens(sha),
        ])
            .then(([doc, resp]: [PDFDocumentProxy, PageTokens[]]) => {
                setDocument(doc);

                // Load all the pages too. In theory this makes things a little slower to startup,
                // as fetching and rendering them asynchronously would make it faster to render the
                // first, visible page. That said it makes the code simpler, so we're ok with it for
                // now.
                const loadPages: Promise<PDFPageInfo>[] = [];
                for (let i = 1; i <= doc.numPages; i++) {
                    // See line 50 for an explanation of the cast here.
                    loadPages.push(
                        (doc.getPage(i).then((p) => {
                            const pageIndex = p.pageNumber - 1;
                            const pageTokens = resp[pageIndex].tokens;
                            return new PDFPageInfo(p, pageTokens);
                        }) as unknown) as Promise<PDFPageInfo>
                    );
                }
                return Promise.all(loadPages);
            })
            .then((pages) => {
                setPages(pages);
                // Get any existing annotations for this pdf.
                getAnnotations(sha)
                    .then((paperAnnotations) => {
                        setPdfAnnotations(paperAnnotations);

                        setViewState(ViewState.LOADED);
                    })
                    .catch((err: any) => {
                        console.error(`Error Fetching Existing Annotations: `, err);
                        setViewState(ViewState.ERROR);
                    });
            })
            .catch((err: any) => {
                if (err instanceof Error) {
                    // We have to use the message because minification in production obfuscates
                    // the error name.
                    if (err.message === 'Request failed with status code 404') {
                        setViewState(ViewState.NOT_FOUND);
                        return;
                    }
                }
                console.error(`Error Loading PDF: `, err);
                setViewState(ViewState.ERROR);
            });
    }, [sha]);

    const sidebarWidth = '300px';
    switch (viewState) {
        case ViewState.LOADING:
            return (
                <WithSidebar width={sidebarWidth}>
                    <SidebarContainer width={sidebarWidth}>
                        <Header />
                        <AssignedPaperList papers={assignedPaperStatuses} />
                    </SidebarContainer>
                    <CenterOnPage>
                        <Progress
                            type="circle"
                            percent={progress}
                            strokeColor={{ '0%': theme.color.T6, '100%': theme.color.G6 }}
                        />
                    </CenterOnPage>
                </WithSidebar>
            );
        case ViewState.NOT_FOUND:
            return (
                <WithSidebar width={sidebarWidth}>
                    <SidebarContainer width={sidebarWidth}>
                        <Header />
                        <AssignedPaperList papers={assignedPaperStatuses} />
                    </SidebarContainer>
                    <CenterOnPage>
                        <Result icon={<QuestionCircleOutlined />} title="PDF Not Found" />
                    </CenterOnPage>
                </WithSidebar>
            );
        case ViewState.LOADED:
            if (doc && pages && pdfAnnotations) {
                return (
                    <PDFStore.Provider
                        value={{
                            doc,
                            pages,
                            onError,
                        }}>
                        <AnnotationStore.Provider
                            value={{
                                labels,
                                activeLabel,
                                setActiveLabel,
                                relationLabels,
                                activeRelationLabel,
                                setActiveRelationLabel,
                                pdfAnnotations,
                                setPdfAnnotations,
                                selectedAnnotations,
                                setSelectedAnnotations,
                                freeFormAnnotations,
                                toggleFreeFormAnnotations,
                                hideLabels,
                                setHideLabels,
                            }}>
                            <listeners.UndoAnnotation />
                            <listeners.HandleAnnotationSelection
                                setModalVisible={setRelationModalVisible}
                            />
                            <listeners.SaveWithTimeout sha={sha} />
                            <listeners.SaveBeforeUnload sha={sha} />
                            <listeners.HideAnnotationLabels />
                            <WithSidebar width={sidebarWidth}>
                                <SidebarContainer width={sidebarWidth}>
                                    <Header />
                                    <DisplayUserInfo />
                                    <Labels />
                                    <AssignedPaperList papers={assignedPaperStatuses} />
                                    {activePaperStatus ? (
                                        <Annotations
                                            sha={sha}
                                            annotations={pdfAnnotations.annotations}
                                        />
                                    ) : null}
                                    {activeRelationLabel ? (
                                        <Relations relations={pdfAnnotations.relations} />
                                    ) : null}
                                    {activePaperStatus ? (
                                        <Comment sha={sha} paperStatus={activePaperStatus} />
                                    ) : null}
                                </SidebarContainer>
                                <PDFContainer>
                                    {activeRelationLabel ? (
                                        <RelationModal
                                            visible={relationModalVisible}
                                            onClick={onRelationModalOk}
                                            onCancel={onRelationModalCancel}
                                            source={selectedAnnotations}
                                            label={activeRelationLabel}
                                        />
                                    ) : null}
                                    <PDF />
                                </PDFContainer>
                            </WithSidebar>
                        </AnnotationStore.Provider>
                    </PDFStore.Provider>
                );
            } else {
                return null;
            }
        // eslint-disable-line: no-fallthrough
        case ViewState.ERROR:
            return (
                <WithSidebar width={sidebarWidth}>
                    <SidebarContainer width={sidebarWidth}>
                        <Header />
                        <AssignedPaperList papers={assignedPaperStatuses} />
                    </SidebarContainer>
                    <CenterOnPage>
                        <Result status="warning" title="Unable to Render Document" />
                    </CenterOnPage>
                </WithSidebar>
            );
    }
};

interface HasWidth {
    width: string;
}

const WithSidebar = styled.div<HasWidth>(
    ({ width }) => `
    display: grid;
    flex-grow: 1;
    grid-template-columns: minmax(0, 1fr);
    padding-left: ${width};
`
);

const PDFContainer = styled.div(
    ({ theme }) => `
    background: ${theme.color.N4};
    padding: ${theme.spacing.sm};
`
);
