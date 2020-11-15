import React from 'react';
import { Annotation, PDFPageInfo } from '../context';
import { Tag } from "@allenai/varnish";
import styled from 'styled-components';


interface AnnotationSummaryProps {
    annotation: Annotation
    pageInfo: PDFPageInfo;
}

export const AnnotationSummary = ({annotation, pageInfo}: AnnotationSummaryProps) => {

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
        </PaddedRow>
    );

}

const PaddedRow = styled.div(({ theme }) => `
    padding: 4px 0;
    border-radius: 2px;
    display: grid;
    grid-template-columns: minmax(0, 1fr) min-content min-content;

`);


const SmallTag = styled(Tag)`
    font-size: 10px;
    padding: 2px 2px;
    border-radius: 4px;
    color: black;
    line-height: 1;
`
const Overflow = styled.span`
    line-height: 1;
    font-size: 12px;
    white-space: nowrap;
    text-overflow: ellipsis;
    overflow: hidden;   
`