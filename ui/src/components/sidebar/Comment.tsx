import React, {useState} from 'react';
import styled from "styled-components";
import { Input} from "@allenai/varnish";

import { SidebarItem, SidebarItemTitle } from "./common";
import { PaperStatus } from "../../api";

interface CommentProps {
    onStatusChange: (s: PaperStatus) => Promise<void>
    paperStatus: PaperStatus
}

export const Comment = ({onStatusChange, paperStatus}: CommentProps) => {

    const [comment, setComment] = useState<string>(paperStatus.comments)

    const onCommentSave = () => {
        const newStatus = {
            ...paperStatus,
            comments: comment
        }
        onStatusChange(newStatus)
    }

    return (
        <SidebarItem>
            <SidebarItemTitle>
                Comments
            </SidebarItemTitle>
            <DarkTextArea
                defaultValue={paperStatus.comments}
                onChange={(e) => setComment(e.target.value)}
                onBlur={onCommentSave}
                autoSize={{minRows: 6}}
            />
        </SidebarItem>
    );
};

const DarkTextArea = styled(Input.TextArea)`
    color: black;
    padding: 2px 2px;
    background: lightgrey;
    font-size: 0.8rem;
`
