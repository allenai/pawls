
import React from 'react';
import styled from "styled-components"
import { SidebarItem, SidebarItemTitle, SmallButton} from "./common";
import { Switch, notification } from '@allenai/varnish';
import { PdfAnnotations, PDFPageInfo } from "../../context";

import { CheckOutlined, CloseOutlined } from '@ant-design/icons';
import { AnnotationSummary } from "../AnnotationSummary";
import { PaperStatus, Status } from '../../api';

interface AnnotationsProps {
    onSave: () => void
    onStatusChange: (s: PaperStatus) => Promise<void>
    annotations: PdfAnnotations
    pages: PDFPageInfo[]
    paperStatus: PaperStatus
}


export const Annotations = ({onSave, onStatusChange, annotations, pages, paperStatus}: AnnotationsProps) => {

    const flatAnnotations = annotations.flat()

    const onChange = (s: Status) => {

        const newPaperStatus = {
            ...paperStatus,
            status: s
        }
        onStatusChange(newPaperStatus).then(() => {
            if (s === Status.INPROGRESS) {
                notification.info({message: "Marked paper as In Progress."})
            } else {
                notification.success({message: "Marked paper as Finshed!"})
            }

        })
    }

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
                        onChange(Status.FINISHED)
                    } else {
                        onChange(Status.INPROGRESS)
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
                                key={annotation.id}
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

const Toggle = styled(Switch)`
  margin: 4px;
`
const ToggleDescription = styled.span`
    font-size: 0.85rem;
    color: ${({ theme }) => theme.color.N6};
`