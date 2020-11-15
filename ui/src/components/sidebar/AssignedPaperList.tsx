import React, { useState } from 'react';
import styled from "styled-components";
import { SidebarItem, SidebarItemTitle, Contrast } from "./common";
import { PaperInfo, Status } from "../../api";
import { Switch, Tag } from "@allenai/varnish";

import { FileDoneOutlined, CloseOutlined, CommentOutlined, EditFilled } from "@ant-design/icons";


const AssignedPaperRow = ({paper}: {paper: PaperInfo}) => {
    return (
        <PaddedRow>

            <Contrast key={paper.metadata.sha}>
                <a href={`/pdf/${paper.metadata.sha}`}>
                        {paper.metadata.title}
                </a>
            </Contrast>
            <SmallTag color="grey">
                {paper.status.annotations}
                <DarkEditIcon/>
            </SmallTag>
            { paper.status.comments === "" ? null : (
                <CommentOutlined color="black"/>
            )
            }
        </PaddedRow> 
    )
}

export const AssignedPaperList = ({papers}: {papers: PaperInfo[]}) => {

    const [showFinished, setShowFinished] = useState<boolean>(false)

    const unfinished = papers.filter(p => p.status.status !== Status.FINISHED)
    const finished = papers.filter(p => p.status.status === Status.FINISHED)
    const ordered = unfinished.concat(finished)
    const papersToShow = showFinished ? ordered: unfinished

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
                        <AssignedPaperRow key={info.sha} paper={info}/>
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

// TODO(Mark): ask for help figuring out how to style this icon.
const DarkEditIcon = styled(EditFilled)`
    margin-left: 4px;
`

const PaddedRow = styled.div(({ theme }) => `
    padding: 4px 0;
    display: grid;
    grid-template-columns: minmax(0, 1fr) min-content min-content min-content;

`);

const SmallTag = styled(Tag)`
    font-size: 10px;
    padding: 2px 2px;
    margin-left: 4px;
    border-radius: 4px;
    color: black;
    line-height: 1;
`