
import React from 'react';
import { SidebarItem, SidebarItemTitle } from "./common";
import { Button } from '@allenai/varnish';
import { PdfAnnotations, PDFPageInfo } from "../../context";

import { AnnotationSummary } from "../AnnotationSummary";

interface AnnotationsProps {
    onSave: () => void
    annotations: PdfAnnotations
    pages: PDFPageInfo[]
}


export const Annotations = ({onSave, annotations, pages}: AnnotationsProps) => {

    const flatAnnotations = annotations.flat()
    return (
        <SidebarItem>
            <SidebarItemTitle>
                Annotations
                <Button
                    type="primary"
                    size="small"
                    onClick={onSave}
                    style={{marginLeft: "8px"}}
                >
                    Save
                </Button>
            </SidebarItemTitle>
            {flatAnnotations.length === 0 ? (
                <>None</>
            ) : (
                <div>
                    {flatAnnotations.flatMap((annotation, i) => (

                        <AnnotationSummary 
                            annotation={annotation}
                            pageInfo={pages[annotation.page]}
                        />


                    ))}
                </div>
            )}
        </SidebarItem>
    );
}