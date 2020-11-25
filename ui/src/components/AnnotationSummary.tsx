import React, {useContext} from 'react';
import { Annotation } from '../context';
import { Tag } from "@allenai/varnish";
import styled from 'styled-components';
import { DeleteFilled } from "@ant-design/icons"
import { PDFStore, AnnotationStore } from "../context"

interface AnnotationSummaryProps {
    annotation: Annotation
}

export const AnnotationSummary = ({annotation}: AnnotationSummaryProps) => {

    const pdfStore = useContext(PDFStore)
    const annotationStore = useContext(AnnotationStore)

    const onDelete = () => {
        const filtered = annotationStore.pdfAnnotations
            .filter((a) => a.id !== annotation.id)

        annotationStore.setPdfAnnotations(filtered)
    }

    if (!pdfStore.pages) {
        return null
    }

    const pageInfo = pdfStore.pages[annotation.page]

    const text = annotation.tokens === null ? "Freeform" : 
            annotation.tokens
            .map(t => pageInfo.tokens[t.tokenIndex].text)
            .join(" ")

    return (
        <PaddedRow>
            <Overflow>
                {text}
            </Overflow>
            <SmallTag color={annotation.label.color}>
                {annotation.label.text}
            </SmallTag>
            <SmallTag color="grey">
                Page {pageInfo.page.pageNumber}
            </SmallTag>
            <DeleteFilled onClick={onDelete}/>
        </PaddedRow>
    );

}

const PaddedRow = styled.div(({ theme }) => `
    padding: 4px 0;
    border-radius: 2px;
    display: grid;
    grid-template-columns: minmax(0, 1fr) min-content min-content min-content;

`);


const SmallTag = styled(Tag)`
    font-size: 0.65rem;
    padding: 2px 2px;
    border-radius: 4px;
    color: black;
    line-height: 1;
`
const Overflow = styled.span`
    line-height: 1;
    font-size: 0.8rem;
    white-space: nowrap;
    text-overflow: ellipsis;
    overflow: hidden;   
`