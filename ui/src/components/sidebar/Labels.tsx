import React, { useContext, useEffect } from 'react';
import styled from 'styled-components';
import { Tag, Switch } from '@allenai/varnish';

import { AnnotationStore } from '../../context';
import { CheckOutlined, CloseOutlined, InfoCircleOutlined } from '@ant-design/icons';

import { SidebarItem, SidebarItemTitle } from './common';

const { CheckableTag } = Tag;

export const Labels = () => {
    const annotationStore = useContext(AnnotationStore);

    const onToggle = () => {
        annotationStore.toggleFreeFormAnnotations(!annotationStore.freeFormAnnotations);
    };

    useEffect(() => {
        const onKeyPress = (e: KeyboardEvent) => {
            // Numeric keys 1-9
            if (e.keyCode >= 49 && e.keyCode <= 57) {
                const index = Number.parseInt(e.key) - 1;
                if (index < annotationStore.labels.length) {
                    annotationStore.setActiveLabel(annotationStore.labels[index]);
                }
            }
            // Left/Right Arrow keys
            if (e.keyCode === 37 || e.keyCode === 39) {
                if (!annotationStore.activeLabel) {
                    annotationStore.setActiveLabel(annotationStore.labels[0]);
                    return;
                }
                const currentIndex = annotationStore.labels.indexOf(annotationStore.activeLabel);
                // Right goes forward
                let next =
                    currentIndex === annotationStore.labels.length - 1 ? 0 : currentIndex + 1;
                // Left goes backward
                if (e.keyCode === 37) {
                    next =
                        currentIndex === 0 ? annotationStore.labels.length - 1 : currentIndex - 1;
                }
                annotationStore.setActiveLabel(annotationStore.labels[next]);
            }
        };
        window.addEventListener('keydown', onKeyPress);
        return () => {
            window.removeEventListener('keydown', onKeyPress);
        };
    }, [annotationStore]);

    // TODO(Mark): Style the tags so it's clear you can select them with the numeric keys.
    return (
        <SidebarItem>
            <SidebarItemTitle>Labels</SidebarItemTitle>
            <ExplainerText>
                <InfoCircleOutlined style={{ marginRight: '3px' }} />
                Use arrow keys to select labels to annotate.
            </ExplainerText>
            <Container>
                <div>
                    {annotationStore.labels.map((label) => (
                        <LabelTag
                            key={label.text}
                            onClick={() => {
                                annotationStore.setActiveLabel(label);
                            }}
                            checked={label === annotationStore.activeLabel}
                            style={{ color: label.color }}>
                            {label.text}
                        </LabelTag>
                    ))}
                </div>
                {annotationStore.relationLabels.length !== 0 ? (
                    <>
                        <SidebarItemTitle>Relations</SidebarItemTitle>
                        <div>
                            {annotationStore.relationLabels.map((relation) => (
                                <LabelTag
                                    key={relation.text}
                                    onClick={() => {
                                        annotationStore.setActiveRelationLabel(relation);
                                    }}
                                    checked={relation === annotationStore.activeRelationLabel}
                                    style={{ color: relation.color }}>
                                    {relation.text}
                                </LabelTag>
                            ))}
                        </div>
                    </>
                ) : null}

                <div>
                    Free Form Annotations
                    <Toggle
                        size="small"
                        onChange={onToggle}
                        checkedChildren={<CheckOutlined />}
                        unCheckedChildren={<CloseOutlined />}
                    />
                </div>
            </Container>
        </SidebarItem>
    );
};

const ExplainerText = styled.div`
    font-size: ${({ theme }) => theme.spacing.sm};

    &,
    & * {
        color: ${({ theme }) => theme.color.N6};
    }
`;

const LabelTag = styled(CheckableTag)`
    &.ant-tag-checkable-checked {
        background-color: #303030;
    }
`;

const Toggle = styled(Switch)`
    margin: 4px;
`;

const Container = styled.div(
    ({ theme }) => `
   margin-top: ${theme.spacing.sm};
   div + div {
       margin-top: ${theme.spacing.md};
   }

`
);
