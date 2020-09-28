import React, { useContext, useEffect }  from 'react';
import styled from "styled-components";
import { Tag, Switch} from "@allenai/varnish";

import { AnnotationStore } from "../../context";
import { CheckOutlined, CloseOutlined } from '@ant-design/icons';

import { SidebarItem, SidebarItemTitle } from "./common";

const { CheckableTag } = Tag;

export const Labels = () => {

    const annotationStore = useContext(AnnotationStore)

    const onToggle = () => {
        annotationStore.toggleFreeFormAnnotations(
            !annotationStore.freeFormAnnotations
        )
    }

    useEffect(() => {

        const onKeyPress = (e: KeyboardEvent) => {
            // Numeric keys 1-9
            if (49 <= e.keyCode && e.keyCode <= 57) {

                const index = Number.parseInt(e.key) - 1
                if (index < annotationStore.labels.length) {
                    annotationStore.setActiveLabel(annotationStore.labels[index])
                }
            }
            // Tab key
            if (e.keyCode === 9) {
                if (!annotationStore.activeLabel) {
                    annotationStore.setActiveLabel(annotationStore.labels[0])
                    return;
                }
                const currentIndex = annotationStore.labels.indexOf(annotationStore.activeLabel)
                let next = currentIndex === annotationStore.labels.length - 1 ? 0 : currentIndex + 1
                // Shift + Tab is the other way.
                if (e.shiftKey) {
                    next = currentIndex === 0 ? annotationStore.labels.length - 1 : currentIndex - 1
                }
                annotationStore.setActiveLabel(annotationStore.labels[next])
            }
        }
        window.addEventListener("keydown", onKeyPress)
        return (() => {
            window.removeEventListener("keydown", onKeyPress)
        })
    }, [annotationStore])

    // TODO(Mark): Style the tags so it's clear you can select them with the numeric keys.
    return (
        <SidebarItem> 
          <SidebarItemTitle>
              Labels
          </SidebarItemTitle>
          <Container>
            <div>
                {annotationStore.labels.map(label => (
                    <CheckableTag
                        key={label.text}
                        onClick={() => {annotationStore.setActiveLabel(label)}}
                        checked={label === annotationStore.activeLabel}
                    >
                        {label.text}
                    </CheckableTag>           
                ))}
            </div>
            <SidebarItemTitle>
                Relations
            </SidebarItemTitle>
            <div>
                {annotationStore.relations.map(relation => (
                    <CheckableTag
                        key={relation.text}
                        onClick={() => {annotationStore.setActiveRelation(relation)}}
                        checked={relation === annotationStore.activeRelation}
                    >
                        {relation.text}
                    </CheckableTag>           
                ))}
            </div>

            <div>
                Free Form Annotations
                <Toggle 
                    onChange={onToggle}
                    checkedChildren={<CheckOutlined />}
                    unCheckedChildren={<CloseOutlined />}
                />
            </div>
          </Container>
        </SidebarItem>
    )
}


const Toggle = styled(Switch)`
  margin: 4px;
`

const Container = styled.div(({ theme }) => `
   margin-top: ${theme.spacing.md};
   div + div {
       margin-top: ${theme.spacing.md};
   }

`);
