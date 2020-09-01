import React from 'react';
import styled from 'styled-components';

import { Typography } from '@allenai/varnish';


export const Sidebar = () => {

    return (
        <>
        <div>
        <FixedSidebar>
            <Typography.Title style={{color: "white"}}>
                Pawls
            </Typography.Title>
        👋 Hi. There will be useful stuff here soon.
        </FixedSidebar>
        </div>
        </>
    )
}

const FixedSidebar = styled.div(({ theme }) => `
    position: fixed;
    overflow-y: scroll;
    background: ${theme.color.N10};
    color: ${theme.color.N1};
    padding: ${theme.spacing.lg} ${theme.spacing.xl};
    width: 300px;
    height: 100vh;
`);
