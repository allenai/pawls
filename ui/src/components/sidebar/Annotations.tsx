import React, { useContext, useState, useEffect } from 'react';
import styled from 'styled-components';
import { SidebarItem, SidebarItemTitle } from './common';
import { Switch, notification } from '@allenai/varnish';
import { Annotation, PDFStore } from '../../context';

import { CheckOutlined, CloseOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { AnnotationSummary } from '../AnnotationSummary';
import { setPdfJunk, getPdfJunk, setPdfFinished, getPdfFinished } from '../../api';

interface AnnotationsProps {
    sha: string;
    annotations: Annotation[];
}

export const Annotations = ({ sha, annotations }: AnnotationsProps) => {
    const [finishedButtonState, setFinishedButtonState] = useState<boolean>(false);
    const [junkButtonState, setJunkButtonState] = useState<boolean>(false);

    useEffect(() => {
        getPdfFinished(sha).then((isFinished) => setFinishedButtonState(isFinished));
    }, [sha]);
    useEffect(() => {
        getPdfJunk(sha).then((isJunk) => setJunkButtonState(isJunk));
    }, [sha]);

    // eslint-disable-next-line
    const onFinishToggle = (isFinished: boolean) => {
        setPdfFinished(sha, isFinished).then(() => {
            if (isFinished) {
                notification.success({ message: 'Marked paper as Finished!' });
            } else {
                notification.info({ message: 'Marked paper as In Progress.' });
            }
            setFinishedButtonState(isFinished);
        });
    };

    const onJunkToggle = (isJunk: boolean) => {
        setPdfJunk(sha, isJunk).then(() => {
            if (isJunk) {
                notification.warning({ message: 'Marked paper as Junk!' });
            } else {
                notification.info({ message: 'Marked paper as In Progress.' });
            }
            setJunkButtonState(isJunk);
        });
    };

    const pdfStore = useContext(PDFStore);

    // total number of PDF tokens of any type
    const totalPdfTokens =
        pdfStore.pages?.map((page) => page?.tokens.length || 0).reduce((a, b) => a + b, 0) || 100;

    // counting the number of total annotated tokens is much easier;
    // it's the length of each span.
    const totalAnnotatedTokens = annotations
        .map((annotation) => annotation.tokens?.length || 0)
        .reduce((a, b) => a + b, 0);

    // finally we want the percentage of annotated tokens.
    const ratioTokenAnnotated = ((totalAnnotatedTokens / totalPdfTokens) * 100).toFixed(2);

    const totalAnnotatedTokensFormatted = totalAnnotatedTokens.toLocaleString();
    const totalPdfTokensFormatted = totalPdfTokens.toLocaleString();

    return (
        <SidebarItem>
            <SidebarItemTitle>Annotations</SidebarItemTitle>
            <AnnotationStatusInfoBlock>
                <AnnotationStatusInfo>
                    Percent annotated:
                    <AnnotationStatusInfoCount>{ratioTokenAnnotated}%</AnnotationStatusInfoCount>
                </AnnotationStatusInfo>
                <AnnotationStatusInfo>
                    Annotated words:
                    <AnnotationStatusInfoCount>
                        {totalAnnotatedTokensFormatted}
                    </AnnotationStatusInfoCount>
                </AnnotationStatusInfo>
                <AnnotationStatusInfo>
                    Total words:
                    <AnnotationStatusInfoCount>{totalPdfTokensFormatted}</AnnotationStatusInfoCount>
                </AnnotationStatusInfo>
            </AnnotationStatusInfoBlock>
            <ExplainerText>
                <InfoCircleOutlined style={{ marginRight: '3px' }} />
                Use CMD + z to undo the last annotation.
            </ExplainerText>
            <ExplainerText>
                <InfoCircleOutlined style={{ marginRight: '3px' }} />
                Press CTRL to show/hide annotation labels for small annotations.
            </ExplainerText>
            <span>
                <ToggleDescription>Finished?</ToggleDescription>
                <Toggle
                    size="small"
                    checked={finishedButtonState}
                    onChange={(e) => onFinishToggle(e)}
                    checkedChildren={<CheckOutlined />}
                    unCheckedChildren={<CloseOutlined />}
                />
            </span>
            <span>
                <ToggleDescription>Junk</ToggleDescription>
                <Toggle
                    size="small"
                    defaultChecked={false}
                    checked={junkButtonState}
                    onChange={(e) => onJunkToggle(e)}
                    checkedChildren={<CheckOutlined />}
                    unCheckedChildren={<CloseOutlined />}
                />
            </span>
            <div>
                {annotations.length === 0 ? (
                    <>No Annotations Yet :(</>
                ) : (
                    <div>
                        {annotations.map((annotation) => (
                            <AnnotationSummary key={annotation.id} annotation={annotation} />
                        ))}
                    </div>
                )}
            </div>
        </SidebarItem>
    );
};

const AnnotationStatusInfoBlock = styled.div(
    ({ theme }) => `
        margin-bottom: 1em;
        padding-bottom: .5em;
        border-bottom: 1px solid ${theme.color.N8};
    `
);

const AnnotationStatusInfo = styled.div`
    size: 1em;
`;

const AnnotationStatusInfoCount = styled.span`
    font-weight: bold;
    margin-left: 0.5em;
`;

const ExplainerText = styled.div`
    font-size: ${({ theme }) => theme.spacing.sm};

    &,
    & * {
        color: ${({ theme }) => theme.color.N6};
    }
`;

const Toggle = styled(Switch)`
    margin: 8px 8px;
`;
const ToggleDescription = styled.span`
    font-size: 0.85rem;
    color: ${({ theme }) => theme.color.N6};
`;
