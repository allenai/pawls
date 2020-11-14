import React, { useState } from 'react';
import styled from "styled-components";
import { SidebarItem, SidebarItemTitle, Contrast } from "./common";
import { PaperInfo, Status } from "../../api";
import { Switch } from "@allenai/varnish";

import { FileDoneOutlined, CloseOutlined } from "@ant-design/icons";


const AssignedPaperRow = ({paper}: {paper: PaperInfo}) => {

    return (
        <Contrast key={paper.metadata.sha}>
            <a href={`/pdf/${paper.metadata.sha}`}>
                    {paper.metadata.title}
            </a>
        </Contrast>
    )
}

export const AssignedPaperList = ({papers}: {papers: PaperInfo[]}) => {

    const [showFinished, setShowFinished] = useState<boolean>(false)

    const finished = papers.filter(p => p.status.status === Status.FINISHED)
    const unfinished = papers.filter(p => p.status.status !== Status.FINISHED)
    const papersToShow = showFinished ? finished: unfinished
    
    return (
        <SidebarItem>
            <SidebarItemTitle>
                Papers
            </SidebarItemTitle>
            <ToggleDescription>
                Show Finished Papers:
            </ToggleDescription>
            <Toggle
                onChange={() => setShowFinished(!showFinished)}
                checkedChildren={<FileDoneOutlined />}
                unCheckedChildren={<CloseOutlined />}
            />
            {papers.length !== 0 ? (
                <>
                    {papersToShow.map((info) => (
                        <AssignedPaperRow paper={info}/>
                    ))}
                </>
            ) : (
                <>No Pdfs Allocated!</>
            )}
        </SidebarItem>
    )
}

const Toggle = styled(Switch)`
  margin: 4px;
`
const ToggleDescription = styled.span`
    font-size: 14px;
    color: ${({ theme }) => theme.color.N6};

`