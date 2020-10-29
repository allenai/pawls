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
            annotation.tokens.map(t => pageInfo.tokens[t.tokenIndex].text).join(" ")

    return (
        <div>
            {text}
            <div>
                <Details>
                    <Tag color={annotation.label.color}>
                        {annotation.label.text}
                    </Tag>
                    <Tag>
                        Page {pageInfo.page.pageNumber}
                    </Tag>
                </Details>
            </div>
        </div>
    );

}

const Details = styled.span`
    font-size: 10px
`