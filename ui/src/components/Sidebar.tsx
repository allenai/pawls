
import React, { useContext } from 'react';
import styled from 'styled-components';
import { Link } from '@allenai/varnish';

import { AnnotationStore } from '../context';
import { Labels } from "./Labels";
import { PaperMetadata } from "../api";

import { Logos } from '@allenai/varnish';

const { AI2Logo } = Logos;


interface SidebarProps {
    sidebarWidth: string;
    assignedPapers: PaperMetadata[];
}

export const Sidebar = ({sidebarWidth, assignedPapers}: SidebarProps) => {

    const annotationStore = useContext(AnnotationStore);

    const flatAnnotations = Object.values(annotationStore.pdfAnnotations).flat()

    return(
        <SidebarContainer width={sidebarWidth}>
            <AI2Logo color="white" size="micro"/>
            <h2>Pawls</h2>
            <SidebarItem>
                <SidebarItemTitle>
                    Labels
                </SidebarItemTitle>
                <Labels/>
            </SidebarItem>

            <SidebarItem>
                <SidebarItemTitle>
                    Annotations
                </SidebarItemTitle>
                {flatAnnotations.length === 0 ? (
                    <>None</>
                ) : (
                    <ul>
                        {flatAnnotations.map((annotation, i) => (
                            <li key={annotation.toString()} >
                                Annotation #{i + 1}
                            </li>
                        ))}
                    </ul>
                )}
            </SidebarItem>

            <SidebarItem>
                <SidebarItemTitle>
                    Papers
                </SidebarItemTitle>
                {assignedPapers.length !== 0 ? (
                    <>
                        {assignedPapers.map((metadata) => (
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
        </SidebarContainer>
    )
}

interface HasWidth {
    width: string;
}

const SidebarContainer = styled.div<HasWidth>(({ theme, width }) => `
    width: ${width};
    position: fixed;
    left: 0;
    overflow-y: scroll;
    background: ${theme.color.N10};
    color: ${theme.color.N2};
    padding: ${theme.spacing.md} ${theme.spacing.md};
    height: 100vh;
    * {
        color: ${theme.color.N2};
    }
`);


const SidebarItem = styled.div(({ theme }) => `
    min-height: 200px;
    max-height: 400px;
    overflow-y: scroll;
    background: ${theme.color.N9};
    margin-bottom: ${theme.spacing.md};
    padding: ${theme.spacing.xxs} ${theme.spacing.sm};
    border-radius: 5px;

`);

// text-transform is necessary because h5 is all caps in antd/varnish.
const SidebarItemTitle = styled.h5(({ theme }) => `
    margin: ${theme.spacing.xs} 0;
    text-transform: capitalize;
`);

const Contrast = styled.div`
  a[href] {
    ${Link.contrastLinkColorStyles()};
  }
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
`;