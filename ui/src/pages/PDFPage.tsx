import React, { useContext, useCallback, useState, useEffect } from 'react';
import styled, { ThemeContext } from 'styled-components';
import { useParams } from 'react-router-dom';
import pdfjs from 'pdfjs-dist';
import { Result, Progress, notification } from '@allenai/varnish';

import { QuestionCircleOutlined } from '@ant-design/icons';

import { PDF, CenterOnPage, RelationModal } from '../components';
import {SidebarContainer, Labels, Annotations, Relations, AssignedPaperList, Header, Comment} from "../components/sidebar";
import { SourceId, pdfURL, getTokens, Token, TokensResponse, PaperInfo, getAllocatedPaperInfo, setPaperStatus, getLabels, Label, getAnnotations, saveAnnotations, getRelations, PaperStatus } from '../api';
import { PDFPageInfo, Annotation, AnnotationStore, PDFStore, PdfAnnotations, RelationGroup } from '../context';


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
    const [ pages, setPages ] = useState<PDFPageInfo[]>();
    const [ pdfAnnotations, setPdfAnnotations ] = useState<PdfAnnotations>();
    const [ pdfRelations, setPdfRelations ] = useState<RelationGroup[]>([]);

    const [ selectedAnnotations, setSelectedAnnotations ] = useState<Annotation[]>([])

    const [ assignedPaperInfo, setAssignedPaperInfo] = useState<PaperInfo[]>([])
    const [ activePaperInfo, setActivePaperInfo] = useState<PaperInfo>()
    const [ activeLabel, setActiveLabel] = useState<Label>();
    const [ labels, setLabels] = useState<Label[]>([]);
    const [ relationLabels, setRelationLabels] = useState<Label[]>([]);
    const [ activeRelationLabel, setActiveRelationLabel] = useState<Label>();
    const [ freeFormAnnotations, toggleFreeFormAnnotations] = useState<boolean>(false);

    const [ relationModalVisible, setRelationModalVisible] = useState<boolean>(false);

    // React's Error Boundaries don't work for us because a lot of work is done by pdfjs in
    // a background task (a web worker). We instead setup a top level error handler that's
    // passed around as needed so we can display a nice error to the user when something
    // goes wrong.
    //
    // We have to use the `useCallback` hook here so that equality checks in child components
    // don't trigger unintentional rerenders.
    const onError = useCallback((err: Error) => {
        console.error('Unexpected Error rendering PDF', err);
        setViewState(ViewState.ERROR);
    }, [ setViewState ]);

    const theme = useContext(ThemeContext);

   function onStatusChange(status: PaperStatus): Promise<void> {
        if (activePaperInfo) {
            const idx = assignedPaperInfo.indexOf(activePaperInfo)
        
            return setPaperStatus(sha, status).then(() => {
                const newInfo = {
                    metadata: activePaperInfo.metadata,
                    status: status,
                    sha: activePaperInfo.sha
                }

                return new Promise<any>((resolved, rejected) => {
                    setAssignedPaperInfo([
                        ...assignedPaperInfo.slice(0, idx),
                        newInfo,
                        ...assignedPaperInfo.slice(idx + 1)

                    ])
                    setActivePaperInfo(newInfo)
                    resolved()
                })
            })
        } else {
            setViewState(ViewState.ERROR)
            throw new Error("No active Paper!")
        }
    }

    const onSave = () => {

        if (pdfAnnotations) {
            saveAnnotations(sha, pdfAnnotations.flat(), pdfRelations).then(() => {
                notification.success({message: "Saved Annotations!"})
            }).catch((err) => {

                notification.error({
                    message: "Sorry, something went wrong!",
                    description: "Try saving your annotations again in a second, or contact someone on the Semantic Scholar team."
                })
                console.log("Failed to save annotations: ", err)
            })
            const current = assignedPaperInfo.filter(x => x.sha === sha)[0]
            setPaperStatus(sha, {
                ...current.status,
                annotations: pdfAnnotations.flat().length,
                relations: pdfRelations.length
            })
        }
    }

    const onRelationModalOk = (group: RelationGroup) => {

        pdfRelations.push(group)
        setPdfRelations(pdfRelations)
        setRelationModalVisible(false)
        setSelectedAnnotations([])
    }

    const onRelationModalCancel = () => {

        setRelationModalVisible(false)
        setSelectedAnnotations([])
    }


    useEffect(() => {
        getLabels().then(labels => {
            setLabels(labels)
            setActiveLabel(labels[0])
        })
    }, []) 

    useEffect(() => {
        getRelations().then(relations => {
            setRelationLabels(relations)
            setActiveRelationLabel(
                relations.length === 0 ? undefined : relations[0]
                )
        })
    }, []) 
    
    useEffect(() => {

        const onShiftUp = (e: KeyboardEvent) => {

            // Shift key up
            if (e.keyCode === 16 && selectedAnnotations.length !== 0) {
                setRelationModalVisible(true)
            }
        }

        window.addEventListener("keyup", onShiftUp)
        return (() => {
            window.removeEventListener("keyup", onShiftUp)
        })
    }, [])



    useEffect( () => {
        getAllocatedPaperInfo().then((paperInfo) => {
            setAssignedPaperInfo(paperInfo)
            setActivePaperInfo(
                paperInfo.filter(p => p.sha === sha)[0]
            )

        }).catch((err: any) => {
            setViewState(ViewState.ERROR);
            console.log(err)
        })
    }, [])

    useEffect(() => {
        setDocument(undefined);
        const loadingTask: PDFLoadingTask = pdfjs.getDocument(pdfURL(sha))
        loadingTask.onProgress = (p: pdfjs.PDFProgressData) => {
            setProgress(Math.round(p.loaded / p.total * 100));
        };
        Promise.all([
            // PDF.js uses their own `Promise` type, which according to TypeScript doesn't overlap
            // with the base `Promise` interface. To resolve this we (unsafely) cast the PDF.js
            // specific `Promise` back to a generic one. This works, but might have unexpected
            // side-effects, so we should remain wary of this code.
            loadingTask.promise as unknown as Promise<pdfjs.PDFDocumentProxy>,
            getTokens(sha)
        ]).then(([ doc, resp ]: [ pdfjs.PDFDocumentProxy, TokensResponse ]) => {
            setDocument(doc);

            // Load all the pages too. In theory this makes things a little slower to startup,
            // as fetching and rendering them asynchronously would make it faster to render the
            // first, visible page. That said it makes the code simpler, so we're ok with it for
            // now.
            const loadPages: Promise<PDFPageInfo>[] = [];
            for (let i = 1; i <= doc.numPages; i++) {
                // See line 50 for an explanation of the cast here.
                loadPages.push(
                    doc.getPage(i).then(p => {
                        let pageTokens: Token[] = [];
                        if (resp.tokens) {
                            const grobidTokensByPage = resp.tokens.sources[SourceId.GROBID].pages;
                            const pageIndex = p.pageNumber - 1;
                            if (pageIndex in grobidTokensByPage) {
                                pageTokens = grobidTokensByPage[pageIndex].tokens;
                            }
                        }
                        return new PDFPageInfo(p, pageTokens);
                    }) as unknown as Promise<PDFPageInfo>
                );
            }
            return Promise.all(loadPages);
        }).then(pages => {
            setPages(pages);
            // Initialize the store for keeping our per-page annotations.
            const initialPageAnnotations: PdfAnnotations = []
            pages.forEach((p) => {
                initialPageAnnotations.push([])
            })
            // Get any existing annotations for this pdf.
            getAnnotations(sha).then(paperAnnotations => {
                paperAnnotations.annotations.forEach((annotation) => {
                    initialPageAnnotations[annotation.page].push(annotation)
                })
                setPdfRelations(paperAnnotations.relations)
                setPdfAnnotations(initialPageAnnotations)

            }).catch((err: any) => {
                console.error(`Error Fetching Existing Annotations: `, err);
                setViewState(ViewState.ERROR);
            })

            setViewState(ViewState.LOADED);
        }).catch((err: any) => {
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
    }, [ sha ]);

    const sidebarWidth = "300px";
    switch (viewState) {
        case ViewState.LOADING:
            return (
                <WithSidebar width={sidebarWidth}>
                    <SidebarContainer width={sidebarWidth}>
                        <Header/>
                        <AssignedPaperList papers={assignedPaperInfo}/>
                    </SidebarContainer>
                    <CenterOnPage>
                        <Progress
                            type="circle"
                            percent={progress}
                            strokeColor={{ '0%': theme.color.T6, '100%': theme.color.G6 }} />
                    </CenterOnPage>
                </WithSidebar>
            );
        case ViewState.NOT_FOUND:
            return (
                <WithSidebar width={sidebarWidth}>
                    <SidebarContainer width={sidebarWidth}>
                        <Header/>
                        <AssignedPaperList papers={assignedPaperInfo}/>
                    </SidebarContainer>
                    <CenterOnPage>
                        <Result
                            icon={<QuestionCircleOutlined />}
                            title="PDF Not Found" />
                    </CenterOnPage>
                </WithSidebar>
            );
        case ViewState.LOADED:
            if (doc && pdfAnnotations && pages) {
                return (
                    <PDFStore.Provider value={{
                        doc,
                        pages,
                        onError
                    }}>
                        <AnnotationStore.Provider
                            value={{
                                labels,
                                activeLabel,
                                setActiveLabel,
                                relationLabels,
                                activeRelationLabel,
                                setActiveRelationLabel,
                                pdfRelations,
                                setPdfRelations,
                                pdfAnnotations,
                                setPdfAnnotations,
                                selectedAnnotations,
                                setSelectedAnnotations,
                                freeFormAnnotations,
                                toggleFreeFormAnnotations
                            }}
                        >
                            <WithSidebar width={sidebarWidth}>
                                <SidebarContainer width={sidebarWidth}>
                                    <Header/>
                                    <Labels/>
                                    <AssignedPaperList papers={assignedPaperInfo}/>
                                    {activePaperInfo ?
                                    <Annotations 
                                        onSave={onSave}
                                        onStatusChange={onStatusChange}
                                        annotations={pdfAnnotations}
                                        pages={pages}
                                        paperStatus={activePaperInfo.status}
                                    /> : null}
                                    {activeRelationLabel ? 
                                    <Relations relations={pdfRelations}/>
                                    : null
                                    }
                                    {activePaperInfo ?
                                        <Comment
                                            onStatusChange={onStatusChange}
                                            paperStatus={activePaperInfo.status}
                                        />
                                        : null
                                    }
                                </SidebarContainer>
                                <PDFContainer>
                                    {activeRelationLabel ? 
                                        <RelationModal 
                                            visible={relationModalVisible}
                                            onClick={onRelationModalOk}
                                            onCancel={onRelationModalCancel}
                                            source={selectedAnnotations}
                                            label={activeRelationLabel}
                                            pages={pages}
                                            />
                                        : null}
                                    <PDF />
                                </PDFContainer>
                            </WithSidebar>
                        </AnnotationStore.Provider>
                    </PDFStore.Provider>
                );
            } else {
                return (null);
            }
        // eslint-disable-line: no-fallthrough
        case ViewState.ERROR:
            return (
                <WithSidebar width={sidebarWidth}>
                    <SidebarContainer width={sidebarWidth}>
                        <Header/>
                        <AssignedPaperList papers={assignedPaperInfo}/>
                    </SidebarContainer>
                    <CenterOnPage>
                        <Result
                            status="warning"
                            title="Unable to Render Document" />
                    </CenterOnPage>
                </WithSidebar>
            );
    }
};

interface HasWidth {
    width: string;
}

const WithSidebar = styled.div<HasWidth>(({ width }) =>`
    display: grid;
    flex-grow: 1;
    grid-template-columns: minmax(0, 1fr);
    padding-left: ${width};
`);


const PDFContainer = styled.div(({ theme }) => `
    background: ${theme.color.N4};
    padding: ${theme.spacing.sm};
`);
