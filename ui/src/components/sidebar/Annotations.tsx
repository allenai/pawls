
import React from 'react';
import { SidebarItem, SidebarItemTitle } from "./common";
import { Button } from '@allenai/varnish';
import { PdfAnnotations } from "../../context";

interface AnnotationsProps {
    onSave: () => void
    annotations: PdfAnnotations
}


export const Annotations = ({onSave, annotations}: AnnotationsProps) => {

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
                <ul>
                    {flatAnnotations.flatMap((annotation, i) => (
                        <li key={annotation.toString()} >
                            Annotation #{i + 1}
                        </li>
                    ))}
                </ul>
            )}
        </SidebarItem>
    );
}