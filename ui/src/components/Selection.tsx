import React, { useContext } from 'react';
import styled, { ThemeContext } from 'styled-components';

import { Bounds } from '../context';
import { Label } from '../api'

interface SelectionProps {
    bounds: Bounds
    label?: Label
    isActiveSelection: boolean

 }

 function hexToRgb(hex: string) {
    var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    if (!result) {
        throw new Error("Unable to parse color.")
    }
    return {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16)
    }
  }
  

export const Selection = ({ bounds, label, isActiveSelection }: SelectionProps) => {

    const theme = useContext(ThemeContext)
    let color;
    if (!label) {
        color = theme.color.N4.hex // grey as the default.
    } else {
        color = label.color
    }

    const width = bounds.right - bounds.left;
    const height = bounds.bottom - bounds.top;
    const rotateY = width < 0 ? -180 : 0;
    const rotateX = height < 0 ? -180 : 0;
    const border = 3

    const rgbColor = hexToRgb(color)

    return (
         <span
             style={{
                 position: "absolute",
                 left: `${bounds.left}px`,
                 top: `${bounds.top}px`,
                 width: `${Math.abs(width)}px`,
                 height: `${Math.abs(height)}px`,
                 transform: `rotateY(${rotateY}deg) rotateX(${rotateX}deg)`,
                 transformOrigin: 'top left',
                 border: `${border}px solid ${color}`,
                 background: `rgba(${rgbColor.r}, ${rgbColor.g}, ${rgbColor.b}, 0.1)`

             }} >
             {label && !isActiveSelection ? (
                 <SelectionLabel
                    border={border}
                    color={color}
                 >
                     {label.text}
                 </SelectionLabel>
             ): null}
         </span>
     );
 }

// TODO(Mark): Make annotations deleteable on click.

// We use transform here because we need to translate the label upward
// to sit on top of the bounds as a function of *its own* height,
// not the height of it's parent.
interface SelectionLabelProps {
    border: number
    color: string
}
const SelectionLabel = styled.span<SelectionLabelProps>(({ border, color }) => `
    position: absolute;
    right: -${border}px;
    transform:translateY(-100%);
    border: ${border} solid  ${color};
    background: ${color};
    font-weight: bold;
    user-select: none;
`);
