/**
 * This file is meant for shared display components that you use throughout
 * your application.
 *
 * Components with a lot of logic, or those that are particularly complicated
 * should probably be put in their own file. This file is meant for the
 * re-usable, simple things used in a lot of different spots in your UI.
 */
import * as React from 'react';
import styled from 'styled-components';
import { WarningOutlined } from '@ant-design/icons';

export const Error: React.SFC<{ message: string }> = ({ message }) => (
    <ErrorGrid>
        <WarningOutlined />
        {message}
    </ErrorGrid>
);

const TwoColumnGrid = styled.div`
    display: grid;
    grid-template-columns: auto max-content;
    grid-gap: ${({ theme }) => `${theme.spacing.xs}`};
    align-items: center;
`;

const ErrorGrid = styled(TwoColumnGrid as any)`
    /* The 'any' type here fixes a bug, https://github.com/microsoft/TypeScript/issues/37597 */
    color: ${({ theme }) => theme.palette.text.error.hex};
`;
