import React from 'react';
import { Annotation, PDFPageInfo } from '../context';



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
                <span>
                    {annotation.label.text}
                </span>
                <span>
                    Page: {pageInfo.page.pageNumber}
                </span>
            </div>
        </div>
    );

}