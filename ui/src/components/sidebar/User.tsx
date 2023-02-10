import React, { Component } from 'react';
import styled from 'styled-components';

import { SidebarItem, SidebarItemTitle } from './common';
import { getUsername, UserInfo } from '../../api';

export class DisplayUserInfo extends Component<{}, { user: string }> {
    constructor(props: any) {
        super(props);
        this.state = { user: '' };
    }

    componentDidMount() {
        getUsername().then((result: UserInfo) =>
            this.setState({
                user: result.user,
            })
        );
    }

    render() {
        const user = this.state.user;

        return (
            <CompactSidebarItem>
                <SidebarItemTitle>User</SidebarItemTitle>
                <UserInfoBlock>{user}</UserInfoBlock>
            </CompactSidebarItem>
        );
    }
}

const CompactSidebarItem = styled(SidebarItem)`
    min-height: 0px;
`;

const UserInfoBlock = styled.div`
    margin-bottom: 0.5em;
`;
