import React, { useState } from 'react';
import styled from 'styled-components';
import { Input } from '@allenai/varnish';

import { SidebarItem, SidebarItemTitle } from './common';
import { PaperStatus, setPdfComment } from '../../api';

interface CommentProps {
    sha: string;
    paperStatus: PaperStatus;
}

export const Comment = ({ sha, paperStatus }: CommentProps) => {
    const [comment, setComment] = useState<string>(paperStatus.comments);

    return (
        <SidebarItem>
            <SidebarItemTitle>Fields</SidebarItemTitle>
            <DarkTextArea
                defaultValue={paperStatus.comments}
                onChange={(e) => setComment(e.target.value)}
                onBlur={() => setPdfComment(sha, comment)}
                autoSize={{ minRows: 6 }}
            />
        </SidebarItem>
    );
};

const DarkTextArea = styled(Input.TextArea)`
    color: black;
    padding: 2px 2px;
    background: lightgrey;
    font-size: 0.8rem;
`;
