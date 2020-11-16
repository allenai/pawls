import React, {useState} from 'react';
import styled from "styled-components";
import { Input, notification} from "@allenai/varnish";

import { SidebarItem, SidebarItemTitle, SmallButton } from "./common";
import { PaperStatus } from "../../api";

interface CommentProps {
    onStatusChange: (s: PaperStatus, c: () => void) => void
    paperStatus: PaperStatus
}

export const Comment = ({onStatusChange, paperStatus}: CommentProps) => {

    const [comment, setComment] = useState<string>(paperStatus.comments)

    const onCommentSave = () => {
        const newStatus = {
            ...paperStatus,
            comments: comment
        }
        onStatusChange(newStatus, () => {
            notification.info({message: "Comment saved!"})
        })
    }

    return (
        <SidebarItem>
            <SidebarItemTitle>
                Comments
                <SmallButton
                    type="primary"
                    size="small"
                    onClick={onCommentSave}
                >
                    Save
                </SmallButton>
            </SidebarItemTitle>
            <DarkTextArea
                defaultValue={paperStatus.comments}
                onChange={(e) => setComment(e.target.value)}
            />
        </SidebarItem>
    );

};

const DarkTextArea = styled(Input.TextArea)`
    color: black;
    padding: 2px 2px;
    background: lightgrey;
    font-size: 14px;
`
