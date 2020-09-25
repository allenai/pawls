import React from 'react';
import { SidebarItem, SidebarItemTitle, Contrast } from "./common";
import {PaperMetadata} from "../../api";

export const AssignedPaperList = ({papers}: {papers: PaperMetadata[]}) => {
    return (
        <SidebarItem>
            <SidebarItemTitle>
                Papers
            </SidebarItemTitle>
            {papers.length !== 0 ? (
                <>
                    {papers.map((metadata) => (
                        <Contrast key={metadata.sha}>
                            <a href={`/pdf/${metadata.sha}`}>
                                    {metadata.title}
                            </a>
                        </Contrast>
                    ))}
                </>
            ) : (
                <>No Pdfs Allocated!</>
            )}
        </SidebarItem>
    )
}
