import {useEffect, useContext} from "react";
import { AnnotationStore } from "../context";
import { saveAnnotations } from "../api";
import { notification } from "@allenai/varnish";


export const UndoAnnotation = () => {

    const annotationStore = useContext(AnnotationStore)
    const {pdfAnnotations, setPdfAnnotations } = annotationStore
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
    const {selectedAnnotations, setSelectedAnnotations, activeRelationLabel} = annotationStore
    useEffect(() => {

        const onShiftUp = (e: KeyboardEvent) => {

            const shift = e.keyCode === 16
            const somethingSelected = selectedAnnotations.length !== 0
            const hasRelations = activeRelationLabel !== undefined
            // Shift key up, the user has selected something,
            // and this annotation project has relation labels.
            if (shift && somethingSelected && hasRelations) {
                setModalVisible(true)
            }
            // Otherwise we just clear the selection,
            // if there is something selected, because
            // there are no relations to annotate.
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



interface WithSha {
    sha: string,
}

export const SaveWithTimeout = ({sha}: WithSha) => {

    const annotationStore = useContext(AnnotationStore)
    const {pdfAnnotations, setPdfAnnotations } = annotationStore

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
            }, 2000)
            return () => clearTimeout(currentTimeout)
        }
    }, [sha, pdfAnnotations])

    return null
}

// TODO(Mark): There is a lot of duplication between these two listeners,
// deduplicate if I need to save at another time as well.

export const SaveBeforeUnload = ({sha}: WithSha) => {

    const annotationStore = useContext(AnnotationStore)
    const {pdfAnnotations, setPdfAnnotations } = annotationStore
    useEffect(() => {

        const beforeUnload = (e: BeforeUnloadEvent) => {

            e.preventDefault()
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
            }).then(() => window.close())
        }
        
        window.addEventListener("beforeunload", beforeUnload)
        return (() => {
            window.removeEventListener("beforeunload", beforeUnload)
        })
    }, [sha, pdfAnnotations])

    return null
}