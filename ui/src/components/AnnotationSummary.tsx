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
            .join(" ").slice(0, 20) + "..."

    return (
        <Hoverable>
            <Overflow>
                {text}
            </Overflow>
            <span style={{textAlign: "right"}}>
                    <SmallTag color={annotation.label.color}>
                        {annotation.label.text}
                    </SmallTag>
                    <SmallTag color="grey">
                        Page {pageInfo.page.pageNumber}
                    </SmallTag>
            </span>
        </Hoverable>
    );

}

export const Hoverable = styled.div(({ theme }) => `
    background: ${theme.color.N9};
    padding-bottom: 2px;
    border-radius: 2px;
    display: flex;
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
    line-height: 1;
    white-space: nowrap;
    text-overflow: ellipsis;
    overflow: hidden;   
`