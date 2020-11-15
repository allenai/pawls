import React, {useState} from 'react';
import styled from "styled-components";
import { Input } from "@allenai/varnish";

import { SidebarItem, SidebarItemTitle, SmallButton } from "./common";


interface CommentProps {
    onSave: (s: string) => void
}

export const Comment = ({onSave}: CommentProps) => {

    const [comment, setComment] = useState<string>("")
    return (
        <SidebarItem>
            <SidebarItemTitle>
                Comments
                <SmallButton
                    type="primary"
                    size="small"
                    onClick={() => onSave(comment)}
                >
                    Save
                </SmallButton>
            </SidebarItemTitle>
            <DarkTextArea
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
