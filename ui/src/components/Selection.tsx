import React, { useContext, useState, useEffect} from 'react';
import styled, { ThemeContext } from 'styled-components';

import { Bounds, TokenId, PDFPageInfo, AnnotationStore } from '../context';
import { Label } from '../api'
import { CloseCircleFilled } from '@ant-design/icons';

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
  

interface SelectionBoundaryProps {
    color: string
    bounds: Bounds
    children?: React.ReactNode
    annotationId?: string
    onClick?: () => void
}

export const SelectionBoundary = ({color, bounds, children, onClick}: SelectionBoundaryProps) => {

    const width = bounds.right - bounds.left;
    const height = bounds.bottom - bounds.top;
    const rotateY = width < 0 ? -180 : 0;
    const rotateX = height < 0 ? -180 : 0;
    const border = 3
    const rgbColor = hexToRgb(color)
    // TODO(Mark): This should be stateless, currently it
    // doesn't drop the darker background after relations are done.
    const [selected, setSelected] = useState(false)

    return (
        <span
          onClick={(e) => {
              // Here we are preventing the default PdfAnnotationsContainer
              // behaviour of drawing a new bounding box if the shift key
              // is pressed in order to allow users to select multiple
              // annotations and associate them together with a relation.
              if (e.shiftKey && onClick) {
                e.stopPropagation();
                onClick()
                setSelected(!selected)
                
            }
          }}
          onMouseDown={(e) => {
            if (e.shiftKey) {
                e.stopPropagation()
            }
        }}    
          style={{
            position: "absolute",
            left: `${bounds.left}px`,
            top: `${bounds.top}px`,
            width: `${Math.abs(width)}px`,
            height: `${Math.abs(height)}px`,
            transform: `rotateY(${rotateY}deg) rotateX(${rotateX}deg)`,
            transformOrigin: 'top left',
            border: `${border}px solid ${color}`,
            background: `rgba(${rgbColor.r}, ${rgbColor.g}, ${rgbColor.b}, ${selected ? 0.3: 0.1})`,
        }}
        >
            {children ? children: null}
        </span>
    )
}


interface TokenSpanProps {
    isSelected?: boolean;
}

const TokenSpan = styled.span<TokenSpanProps>(({ theme, isSelected }) =>`
    position: absolute;
    background: ${isSelected ? theme.color.B6 : 'none'};
    opacity: 0.2;
    border-radius: 3px;
`);

interface SelectionTokenProps {
    pageInfo: PDFPageInfo
    tokens: TokenId[]
}
export const SelectionTokens = ({pageInfo, tokens}: SelectionTokenProps) => {

    return (
        <>
        {tokens && tokens.map((t, i) => {
            const b = pageInfo.getScaledTokenBounds(pageInfo.tokens[t.tokenIndex]);
            return (
                <TokenSpan
                    key={i}
                    isSelected={true}
                    style={{
                        left: `${b.left}px`,
                        top: `${b.top}px`,
                        width: `${b.right - b.left}px`,
                        height: `${b.bottom - b.top}px`,
                        // Tokens don't respond to pointerEvents because
                        // they are ontop of the bounding boxes and the canvas,
                        // which do respond to pointer events.
                        pointerEvents: 'none'
                    }} />
                )

          })}
        </>
    )
}

interface SelectionProps {
    pageInfo: PDFPageInfo
    bounds: Bounds
    tokens?: TokenId[]
    label: Label
    onClickDelete?: () => void
    onClick?: () => void
    showInfo?: boolean
    isSelected?: boolean
 }

export const Selection = ({
    pageInfo, 
    tokens,
    bounds,
    label,
    onClickDelete,
    onClick,
    showInfo = true,
    isSelected = false
}: SelectionProps) => {
    const theme = useContext(ThemeContext)
    let color;
    if (!label) {
        color = theme.color.N4.hex // grey as the default.
    } else {
        color = label.color
    }
    const border = 3

    return (
        <>
          <SelectionBoundary color={color} bounds={bounds} onClick={onClick}>
            {showInfo ? (
                <SelectionInfo border={border} color={color}>
                <span>
                    {label.text}
                </span>
                <CloseCircleFilled
                    onClick={(e) => {
                        e.stopPropagation();
                        if (onClickDelete){
                            onClickDelete()
                        }
                    }}
                    // We have to prevent the default behaviour for
                    // the pdf canvas here, in order to be able to capture
                    // the click event.
                    onMouseDown={(e) => {e.stopPropagation()}}
                />
                </SelectionInfo>
            ): null}
          </SelectionBoundary>
          { 
            // NOTE: It's important that the parent element of the tokens
            // is the PDF canvas, because we need their absolute position
            // to be relative to that and not another absolute/relatively
            // positioned element. This is why SelectionTokens are not inside
            // SelectionBoundary.
            tokens ? <SelectionTokens pageInfo={pageInfo} tokens={tokens}/>: null
          }
        </>
     );
 }

// We use transform here because we need to translate the label upward
// to sit on top of the bounds as a function of *its own* height,
// not the height of it's parent.
interface SelectionInfoProps {
    border: number
    color: string
}
const SelectionInfo = styled.div<SelectionInfoProps>(({ border, color }) => `
    position: absolute;
    right: -${border}px;
    transform:translateY(-100%);
    border: ${border} solid  ${color};
    background: ${color};
    font-weight: bold;
    user-select: none;
    * {
        margin: 2px;
        vertical-align: text-bottom;
    }
`);
