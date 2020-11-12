import React from 'react';
import { SidebarItem, SidebarItemTitle, Contrast } from "./common";
import { PaperInfo } from "../../api";

export const AssignedPaperList = ({papers}: {papers: PaperInfo[]}) => {
    return (
        <SidebarItem>
            <SidebarItemTitle>
                Papers
            </SidebarItemTitle>
            {papers.length !== 0 ? (
                <>
                    {papers.map((info) => (
                        <Contrast key={info.metadata.sha}>
                            <a href={`/pdf/${info.metadata.sha}`}>
                                    {info.metadata.title}
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
