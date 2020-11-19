
import React from 'react';
import styled from "styled-components"
import { SidebarItem, SidebarItemTitle, SmallButton} from "./common";
import { Switch, notification } from '@allenai/varnish';
import { PdfAnnotations, PDFPageInfo } from "../../context";

import { CheckOutlined, CloseOutlined } from '@ant-design/icons';
import { AnnotationSummary } from "../AnnotationSummary";
import { PaperStatus } from '../../api';

interface AnnotationsProps {
    onSave: () => void
    onStatusChange: (s: PaperStatus) => Promise<void>
    annotations: PdfAnnotations
    pages: PDFPageInfo[]
    paperStatus: PaperStatus
}


export const Annotations = ({onSave, onStatusChange, annotations, pages, paperStatus}: AnnotationsProps) => {

    const flatAnnotations = annotations.flat()

    const onFinishToggle = (isFinished: boolean) => {

        const newPaperStatus = {
            ...paperStatus,
            finished: isFinished
        }
        onStatusChange(newPaperStatus).then(() => {
            if (isFinished) {
                notification.success({message: "Marked paper as Finished!"})
            } else {
                notification.info({message: "Marked paper as In Progress."})
            }

        })
    }

    const onJunkToggle = (isJunk: boolean) => {

        const newPaperStatus = {
            ...paperStatus,
            junk: isJunk,
            // Hide junk papers in UI by default.
            finished: isJunk
        }
        onStatusChange(newPaperStatus).then(() => {
            if (isJunk) {
                notification.warning({message: "Marked paper as Junk!"})
            } else {
                notification.info({message: "Marked paper as In Progress."})
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
            <span>
                <ToggleDescription>
                    Finished?
                </ToggleDescription>
                <Toggle
                    size="small"
                    onChange={e => onFinishToggle(e)}
                    checkedChildren={<CheckOutlined />}
                    unCheckedChildren={<CloseOutlined />}
                />
            </span>
            <span>
                <ToggleDescription>
                    Junk
                </ToggleDescription>
                <Toggle
                    size="small"
                    onChange={e => onJunkToggle(e)}
                    checkedChildren={<CheckOutlined />}
                    unCheckedChildren={<CloseOutlined />}
                />
            </span>
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
  margin: 8px 8px;
`
const ToggleDescription = styled.span`
    font-size: 0.85rem;
    color: ${({ theme }) => theme.color.N6};
`