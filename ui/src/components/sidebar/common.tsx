
import styled from "styled-components"
import { Link, Button } from '@allenai/varnish';

interface HasWidth {
    width: string;
}

export const SidebarContainer = styled.div<HasWidth>(({ theme, width }) => `
    width: ${width};
    position: fixed;
    left: 0;
    overflow-y: scroll;
    background: ${theme.color.N10};
    color: ${theme.color.N2};
    padding: ${theme.spacing.md} ${theme.spacing.md};
    height: 100vh;
    * {
        color: ${theme.color.N2};
    }
`);


export const SidebarItem = styled.div(({ theme }) => `
    min-height: 200px;
    max-height: 400px;
    overflow-y: scroll;
    background: ${theme.color.N9};
    margin-bottom: ${theme.spacing.md};
    padding: ${theme.spacing.xxs} ${theme.spacing.sm};
    border-radius: 5px;

`);


// text-transform is necessary because h5 is all caps in antd/varnish.
export const SidebarItemTitle = styled.h5(({ theme }) => `
    margin: ${theme.spacing.xs} 0;
    text-transform: capitalize;
    padding-bottom: ${theme.spacing.xs};
    border-bottom: 2px solid ${theme.color.N8};
`);

export const Contrast = styled.div`
  a[href] {
    ${Link.contrastLinkColorStyles()};
  }
  line-height: 1;
  font-size: 14px;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
`;

export const SmallButton = styled(Button)`
    padding: 2px 4px;
    height: auto;
    font-size: 16px;
    margin-left: 10px;
`