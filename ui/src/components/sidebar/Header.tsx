import React from 'react';
import { Logos } from '@allenai/varnish';

const { AI2Logo } = Logos;

export const Header = () => {

    return (
        <>
            <AI2Logo color="white" size="micro"/>
            <h2>Pawls</h2>
        </>
    );

};