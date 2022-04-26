/* eslint-disable */

import React, { Component } from 'react';
import styled from 'styled-components';

import { SidebarItem, SidebarItemTitle } from './common';
import { getUsername, UserInfo } from '../../api';



export class DisplayUserInfo extends Component<{}, { user: string, email: string }> {
    constructor(props: any) {
        super(props);
        this.state = {user: '', email: ''};
    }

    componentDidMount() {
        getUsername().then((result: UserInfo) => this.setState({
            user: result.user,
            email: result.email
        }))
    }

    render () {
        const user = this.state.user;
        const email = this.state.email;

        return (
            <CompactSidebarItem>
                <SidebarItemTitle>User Information</SidebarItemTitle>
                <UserInfoBlock>
                    <UserInfoEntry>
                        User: <i>{user}</i>
                    </UserInfoEntry>
                    <UserInfoEntry>
                        Email: <i>{email}</i>
                    </UserInfoEntry>
                </UserInfoBlock>
            </CompactSidebarItem>
        );
    }
}

const CompactSidebarItem = styled(SidebarItem)`
  min-height: 0px;
`

const UserInfoBlock = styled.div`
    margin-bottom: .5em;
`

const UserInfoEntry = styled.div`
    size: 1em;
`;