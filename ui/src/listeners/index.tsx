import {useEffect, useContext} from "react";
import { AnnotationStore, PdfAnnotations } from "../context";
import { saveAnnotations, setPaperStatus, PaperInfo } from "../api";
import { notification } from "@allenai/varnish";


export const UndoAnnotation = () => {

    const annotationStore = useContext(AnnotationStore)
    const pdfAnnotations = annotationStore.pdfAnnotations
    const setPdfAnnotations = annotationStore.setPdfAnnotations
    useEffect(() => {
        const handleUndo = (e: KeyboardEvent) => {

            if (e.metaKey && e.keyCode === 90) {
                    setPdfAnnotations(pdfAnnotations.undoAnnotation())
                }
        }

        window.addEventListener('keydown', handleUndo);
        return () => {
            window.removeEventListener('keydown', handleUndo)
        };
    }, [pdfAnnotations, setPdfAnnotations])

    return null

}


interface HandleAnnotationSelectionProps {
    setModalVisible: (v: boolean) => void
}
export const HandleAnnotationSelection = ({setModalVisible}: HandleAnnotationSelectionProps) => {

    const annotationStore = useContext(AnnotationStore)
    const selectedAnnotations = annotationStore.selectedAnnotations
    const setSelectedAnnotations = annotationStore.setSelectedAnnotations
    const activeRelationLabel = annotationStore.activeRelationLabel
    useEffect(() => {

        const onShiftUp = (e: KeyboardEvent) => {

            const shift = e.keyCode === 16
            const somethingSelected = selectedAnnotations.length !== 0
            const hasRelations = activeRelationLabel !== undefined
            // Shift key up
            if (shift && somethingSelected && hasRelations) {
                setModalVisible(true)
            }
            else if (shift && somethingSelected) {
                setSelectedAnnotations([])
            }
        }

        window.addEventListener("keyup", onShiftUp)
        return (() => {
            window.removeEventListener("keyup", onShiftUp)
        })
    }, [activeRelationLabel, selectedAnnotations, setModalVisible])

    return null
}



interface SaveWithTimeoutProps {
    sha: string,
    assignedPaperInfo: PaperInfo[]
}

export const SaveWithTimeout = ({sha, assignedPaperInfo}: SaveWithTimeoutProps) => {

    const annotationStore = useContext(AnnotationStore)
    const pdfAnnotations = annotationStore.pdfAnnotations
    const setPdfAnnotations = annotationStore.setPdfAnnotations

    useEffect(() => {
        // We only save annotations once the annotations have
        // been fetched, because otherwise we save when the
        // annotations and relations are empty.
        if (pdfAnnotations.unsavedChanges) {

            const currentTimeout = setTimeout(() => {
                saveAnnotations(sha, pdfAnnotations).then(() => {
                    setPdfAnnotations(
                        pdfAnnotations.saved()
                    )
                }).catch((err) => {
        
                    notification.error({
                        message: "Sorry, something went wrong!",
                        description: "Try re-doing your previous annotation, or contact someone on the Semantic Scholar team."
                    })
                    console.log("Failed to save annotations: ", err)
                })
                const current = assignedPaperInfo.filter(x => x.sha === sha)[0]
                setPaperStatus(sha, {
                    ...current.status,
                    annotations: pdfAnnotations.annotations.length,
                    relations: pdfAnnotations.relations.length
                })
            }, 2000)
            return () => clearTimeout(currentTimeout)
        }
    }, [sha, pdfAnnotations, assignedPaperInfo])

    return null
}

// TODO(Mark): There is a lot of duplication between these two listeners,
// deduplicate if I need to save at another time as well.
interface SaveBeforeUnloadProps {
    sha: string,
    assignedPaperInfo: PaperInfo[]
}

export const SaveBeforeUnload = ({sha, assignedPaperInfo}: SaveBeforeUnloadProps) => {

    const annotationStore = useContext(AnnotationStore)
    const pdfAnnotations = annotationStore.pdfAnnotations
    const setPdfAnnotations = annotationStore.setPdfAnnotations

    useEffect(() => {

        const beforeUnload = (e: BeforeUnloadEvent) => {
            console.log("hi")
            saveAnnotations(sha, pdfAnnotations).then(() => {
                setPdfAnnotations(
                    pdfAnnotations.saved()
                )
            }).catch((err) => {
    
                notification.error({
                    message: "Sorry, something went wrong!",
                    description: "Try re-doing your previous annotation, or contact someone on the Semantic Scholar team."
                })
                console.log("Failed to save annotations: ", err)
            })
            const current = assignedPaperInfo.filter(x => x.sha === sha)[0]
            setPaperStatus(sha, {
                ...current.status,
                annotations: pdfAnnotations.annotations.length,
                relations: pdfAnnotations.relations.length
            })
        }
        window.addEventListener("beforeunload", beforeUnload)
        return (() => {
            window.removeEventListener("beforeunload", beforeUnload)
        })
    }, [pdfAnnotations.unsavedChanges])

    return null
}