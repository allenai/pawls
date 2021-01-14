import React from 'react';
import { Logos } from '@allenai/varnish';

import pawlsLogo from "./pawlsLogo.png";
import styled from 'styled-components';

const { AI2Logo } = Logos;

export const Header = () => {

    return (
        <>
            <AI2Logo color="white" size="micro"/>
            <Logo src={pawlsLogo}/>
        </>
    );

};

const Logo = styled.img`
    margin: 20px 4px 10px 0px;
    padding: 4px;
    max-width:100%;
`