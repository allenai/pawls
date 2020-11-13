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
        <Hoverable>
            <Overflow>
                {text}
            </Overflow>
                <SmallTag color={annotation.label.color}>
                    {annotation.label.text}
                </SmallTag>
                <SmallTag color="grey">
                    Page {pageInfo.page.pageNumber}
                </SmallTag>
        </Hoverable>
    );

}

export const Hoverable = styled.div(({ theme }) => `
    background: ${theme.color.N9};
    padding: 4px 0;
    border-radius: 2px;
    display: grid;
    grid-template-columns: minmax(0, 1fr) min-content min-content;

    :hover {
        background: ${theme.color.N8}
    }
`);


const SmallTag = styled(Tag)`
    font-size: 10px;
    padding: 2px 2px;
    border-radius: 4px;
    color: black;
    line-height: 1;
`
const Overflow = styled.span`
    font-size: 12px;
    white-space: nowrap;
    text-overflow: ellipsis;
    overflow: hidden;   
`