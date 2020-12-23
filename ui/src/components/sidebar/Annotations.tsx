
import React from 'react';
import styled from "styled-components"
import { SidebarItem, SidebarItemTitle } from "./common";
import { Switch, notification } from '@allenai/varnish';
import { Annotation } from "../../context";

import { CheckOutlined, CloseOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { AnnotationSummary } from "../AnnotationSummary";
import { setPdfJunk, setPdfFinished } from '../../api';

interface AnnotationsProps {
    sha: string
    annotations: Annotation[]
}


export const Annotations = ({sha, annotations}: AnnotationsProps) => {

    const onFinishToggle = (isFinished: boolean) => {

        setPdfFinished(sha, isFinished).then(() => {
            if (isFinished) {
                notification.success({message: "Marked paper as Finished!"})
            } else {
                notification.info({message: "Marked paper as In Progress."})
            }

        })
    }

    const onJunkToggle = (isJunk: boolean) => {

        setPdfJunk(sha, isJunk).then(() => {
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
            </SidebarItemTitle>
            <ExplainerText>
                <InfoCircleOutlined style={{marginRight: "3px"}}/>
                Use CMD + z to undo the last annotation. 
            </ExplainerText>
            <ExplainerText>
                <InfoCircleOutlined style={{marginRight: "3px"}}/>
                Press CTRL to show/hide annotation labels for small annotations.
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