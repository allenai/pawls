import React from 'react';
import { Annotation, PDFPageInfo } from '../context';



interface AnnotationSummaryProps {
    annotation: Annotation
    pageInfo: PDFPageInfo;
}

export const AnnotationSummary = ({annotation, pageInfo}: AnnotationSummaryProps) => {

    return (
        <>
        {annotation.tokens === null ? "Freeform" : (
            annotation.tokens.map(t => pageInfo.tokens[t.tokenIndex].text)
        )}
        <div>
            {annotation.label.text}
        </div>
        <div>
            Page: {pageInfo.page.pageNumber}
        </div>
        </>
    );

}