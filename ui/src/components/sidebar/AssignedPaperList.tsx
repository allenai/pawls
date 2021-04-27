import React, { useState } from 'react';
import styled from 'styled-components';
import { SidebarItem, SidebarItemTitle, Contrast } from './common';
import { PaperStatus } from '../../api';
import { Switch, Tag } from '@allenai/varnish';

import {
    FileDoneOutlined,
    CloseOutlined,
    CommentOutlined,
    EditFilled,
    DeleteFilled,
} from '@ant-design/icons';

const AssignedPaperRow = ({ status }: { status: PaperStatus }) => {
    const getIcon = (status: PaperStatus) => {
        if (status.junk) {
            return <DeleteFilled />;
        } else if (status.comments) {
            return <CommentOutlined />;
        } else {
            return null;
        }
    };

    const getStatusColour = (status: PaperStatus) => {
        if (status.junk) {
            return '#d5a03a';
        }
        if (status.finished) {
            return '#1EC28E';
        }

        return '#AEB7C4';
    };

    return (
        <PaddedRow>
            <Contrast key={status.sha}>
                <a href={`/pdf/${status.sha}`}>{status.name}</a>
            </Contrast>
            <SmallTag color={getStatusColour(status)}>
                {status.annotations}
                <DarkEditIcon />
            </SmallTag>
            {getIcon(status)}
        </PaddedRow>
    );
};

export const AssignedPaperList = ({ papers }: { papers: PaperStatus[] }) => {
    const [showFinished, setShowFinished] = useState<boolean>(false);

    const unfinished = papers.filter((p) => !p.finished);
    const finished = papers.filter((p) => p.finished);
    const ordered = unfinished.concat(finished);
    const papersToShow = showFinished ? ordered : unfinished;

    return (
        <SidebarItem>
            <SidebarItemTitle>Papers</SidebarItemTitle>
            <ToggleDescription>Show Finished Papers:</ToggleDescription>
            <Toggle
                size="small"
                onChange={() => setShowFinished(!showFinished)}
                checkedChildren={<FileDoneOutlined />}
                unCheckedChildren={<CloseOutlined />}
            />
            {papers.length !== 0 ? (
                <>
                    {papersToShow.map((info) => (
                        <AssignedPaperRow key={info.sha} status={info} />
                    ))}
                </>
            ) : (
                <>No Pdfs Allocated!</>
            )}
        </SidebarItem>
    );
};

const Toggle = styled(Switch)`
    margin: 4px;
`;
const ToggleDescription = styled.span`
    font-size: 0.85rem;
    color: ${({ theme }) => theme.color.N6};
`;

// TODO(Mark): ask for help figuring out how to style this icon.
const DarkEditIcon = styled(EditFilled)`
    margin-left: 4px;
    &,
    & * {
        color: ${({ theme }) => theme.color.N9};
    }
`;

const PaddedRow = styled.div`
    padding: 4px 0;
    display: grid;
    grid-template-columns: minmax(0, 1fr) min-content minmax(20px, min-content);
`;

const SmallTag = styled(Tag)`
    font-size: 0.7rem;
    padding: 2px 2px;
    margin-left: 4px;
    border-radius: 4px;
    color: ${({ theme }) => theme.color.N9};
    line-height: 1;
`;
