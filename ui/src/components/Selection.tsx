import React from 'react';
import styled from 'styled-components';

import { Bounds } from '../context';

interface SelectionProps {
    bounds: Bounds
    label?: string

 }
 
export const Selection = ({ bounds, label }: SelectionProps) => {
    const width = bounds.right - bounds.left;
    const height = bounds.bottom - bounds.top;
    const rotateY = width < 0 ? -180 : 0;
    const rotateX = height < 0 ? -180 : 0;
    const border = 3
    return (
         <SelectionBounds
            border={border}
             style={{
                 left: `${bounds.left}px`,
                 top: `${bounds.top}px`,
                 width: `${Math.abs(width)}px`,
                 height: `${Math.abs(height)}px`,
                 transform: `rotateY(${rotateY}deg) rotateX(${rotateX}deg)`,
                 transformOrigin: 'top left',
             }} >
             {label ? (
                 <SelectionLabel
                    border={border}
                 >
                     {label}
                 </SelectionLabel>
             ): null}
         </SelectionBounds>
     );
 }

// TODO(Mark): Set unique colours per label.
// TODO(Mark): Make annotations deleteable on click.

interface WithBorderThickness {
    border: number
}

const SelectionBounds = styled.span<WithBorderThickness>(({ border, theme }) => `
    position: absolute;
    border: ${border}px solid ${theme.color.G4};
    background: rgba(${theme.color.G4.rgb.r}, ${theme.color.G4.rgb.g}, ${theme.color.G4.rgb.b}, 0.1);
`);

// We use transform here because we need to translate the label upward
// to sit on top of the bounds as a function of *its own* height,
// not the height of it's parent.
const SelectionLabel = styled.span<WithBorderThickness>(({ border, theme }) => `
    position: absolute;
    right: -${border}px;
    transform:translateY(-100%);
    border: ${border} solid ${theme.color.G4};
    background: ${theme.color.G4};
    font-weight: bold;
    user-select: none;
`);
