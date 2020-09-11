import React, { useContext, useEffect }  from 'react';
import { Tag } from "@allenai/varnish";

import { AnnotationStore } from "../context";


const { CheckableTag } = Tag;


export const Labels = () => {

    const annotationStore = useContext(AnnotationStore)

    useEffect(() => {

        const onKeyPress = (e: KeyboardEvent) => {
            // Numeric keys 1-9
            if (49 <= e.keyCode && e.keyCode <= 57) {

                const index = Number.parseInt(e.key) - 1
                if (index < annotationStore.labels.length) {
                    annotationStore.setActiveLabel(annotationStore.labels[index])
                }

            }

            // Tab key
            if (e.keyCode === 9) {
                const currentIndex = annotationStore.labels.indexOf(annotationStore.activeLabel)
                const next = currentIndex === annotationStore.labels.length - 1 ? 0 : currentIndex + 1
                annotationStore.setActiveLabel(annotationStore.labels[next])

            }
            // TODO(Mark): Shift + tab should go backward in the label list.
        }
        window.addEventListener("keydown", onKeyPress)

        return (() => {
            window.removeEventListener("keydown", onKeyPress)
        })

    }, [annotationStore])
    
    return (
        <>
            {annotationStore.labels.map(label => (
                <CheckableTag
                    key={label}
                    onClick={() => {annotationStore.setActiveLabel(label)}}
                    checked={label === annotationStore.activeLabel}
                >
                    {label}
                </CheckableTag>           
            ))}
        </>
    )
}
