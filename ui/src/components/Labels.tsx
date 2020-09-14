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
                if (!annotationStore.activeLabel) {
                    annotationStore.setActiveLabel(annotationStore.labels[0])
                    return;
                }
                const currentIndex = annotationStore.labels.indexOf(annotationStore.activeLabel)
                let next = currentIndex === annotationStore.labels.length - 1 ? 0 : currentIndex + 1
                // Shift + Tab is the other way.
                if (e.shiftKey) {
                    next = currentIndex === 0 ? annotationStore.labels.length - 1 : currentIndex - 1
                }
                annotationStore.setActiveLabel(annotationStore.labels[next])
            }
        }
        window.addEventListener("keydown", onKeyPress)
        return (() => {
            window.removeEventListener("keydown", onKeyPress)
        })
    }, [annotationStore])
    
    // TODO(Mark): Style the tags so it's clear you can select them with the numeric keys.
    return (
        <>
            {annotationStore.labels.map(label => (
                <CheckableTag
                    key={label.text}
                    onClick={() => {annotationStore.setActiveLabel(label)}}
                    checked={label === annotationStore.activeLabel}
                >
                    {label.text}
                </CheckableTag>           
            ))}
        </>
    )
}
