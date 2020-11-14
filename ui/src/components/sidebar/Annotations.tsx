
import React from 'react';
import styled from "styled-components"
import { SidebarItem, SidebarItemTitle } from "./common";
import { Button, Switch } from '@allenai/varnish';
import { PdfAnnotations, PDFPageInfo } from "../../context";

import { CheckOutlined, CloseOutlined } from '@ant-design/icons';
import { AnnotationSummary } from "../AnnotationSummary";
import { Status } from '../../api';

interface AnnotationsProps {
    onSave: () => void
    onStatusChange: (s: Status) => void
    annotations: PdfAnnotations
    pages: PDFPageInfo[]
}


export const Annotations = ({onSave, onStatusChange, annotations, pages}: AnnotationsProps) => {

    const flatAnnotations = annotations.flat()
    return (
        <SidebarItem>
            <SidebarItemTitle>
                Annotations
                <SmallButton
                    type="primary"
                    size="small"
                    onClick={onSave}
                >
                    Save
                </SmallButton>
            </SidebarItemTitle>
            <ToggleDescription>
                Mark as Finished:
            </ToggleDescription>
            <Toggle
                onChange={e => {
                    if (e) {
                        onStatusChange(Status.FINISHED)
                    } else {
                        onStatusChange(Status.INPROGRESS)
                    }
                }}
                checkedChildren={<CheckOutlined />}
                unCheckedChildren={<CloseOutlined />}
            />
            <div>
                {flatAnnotations.length === 0 ? (
                    <>No Annotations Yet :(</>
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
            </div>
        </SidebarItem>
    );
}


const SmallButton = styled(Button)`
    padding: 2px 4px;
    height: auto;
    font-size: 16px;
    margin-left: 10px;
`

const Toggle = styled(Switch)`
  margin: 4px;
`
const ToggleDescription = styled.span`
    font-size: 14px;
    color: ${({ theme }) => theme.color.N6};
`