
import React from 'react';
import styled from "styled-components"
import { SidebarItem, SidebarItemTitle, SmallButton} from "./common";
import { Switch, notification } from '@allenai/varnish';
import { PDFPageInfo, Annotation } from "../../context";

import { CheckOutlined, CloseOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { AnnotationSummary } from "../AnnotationSummary";
import { PaperStatus } from '../../api';

interface AnnotationsProps {
    onSave: () => void
    onStatusChange: (s: PaperStatus) => Promise<void>
    annotations: Annotation[]
    pages: PDFPageInfo[]
    paperStatus: PaperStatus
}


export const Annotations = ({onSave, onStatusChange, annotations, pages, paperStatus}: AnnotationsProps) => {

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
            <ExplainerText>
                <InfoCircleOutlined style={{marginRight: "3px"}}/>
                Use CMD + z to undo the last annotation. 
            </ExplainerText>
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
                {annotations.length === 0 ? (
                    <>No Annotations Yet :(</>
                ) : (
                    <div>
                        {annotations.map((annotation, i) => (
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

const ExplainerText = styled.div`
    font-size: ${({ theme }) => theme.spacing.sm};

    &, & * {
        color: ${({ theme }) => theme.color.N6};
    }
`


const Toggle = styled(Switch)`
  margin: 8px 8px;
`
const ToggleDescription = styled.span`
    font-size: 0.85rem;
    color: ${({ theme }) => theme.color.N6};
`