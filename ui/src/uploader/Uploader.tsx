/* eslint-disable */

import 'antd/dist/antd.css';
import './styles.css';
import  React, { Component } from 'react';
import { Upload, message, Layout, Row, PageHeader } from 'antd/es';
import { useHistory } from 'react-router-dom';
import { UploadOutlined } from '@ant-design/icons';
import type { UploadChangeParam } from 'antd/lib/upload/interface';
import type { MessageType } from 'antd/lib/message';
import annotateSvg from './annotate.svg';
import styled from 'styled-components';

// eslint-disable-next-line
import { UnauthorizedInterface } from '../App';
// eslint-disable-next-line
import { isAuthorized } from '../api';

const { Content } = Layout;
const { Dragger } = Upload;

interface uploadMessagingState {
    hasLogged: boolean;
    toHide: null | MessageType;
}

const UploaderInterface = (props: any) => {
    return (
        <Layout>
            <Content className="site-layout-background">
                <Row justify="center" align="middle">
                    <Logo src={annotateSvg} alt="PAWLS uploader logo" />
                </Row>
                <Row justify="center" align="middle">
                    <PageHeader title="PAWLS PDF Uploading Tool" backIcon={false}></PageHeader>
                </Row>
                <Row justify="center" align="middle">
                    <Dragger {...props} accept=".pdf">
                        <div className="ant-upload-drag-icon">
                            <Row justify="center" align="middle">
                                <UploadOutlined />
                            </Row>
                        </div>
                        <div className="ant-upload-text">
                            Click or drag a PDF to this area to begin annotation.
                        </div>
                        <div className="ant-upload-hint">
                            Please be patient while the PDF is being processed. Once done, you will
                            be automatically redirected to the annotation page.
                        </div>
                    </Dragger>
                </Row>
            </Content>
        </Layout>
    );
};

const AuthorizedUploader = () => {
    const history = useHistory();
    // eslint-disable-next-line
    var state: uploadMessagingState = { toHide: null, hasLogged: false };

    const props = {
        name: 'file',
        action: '/api/upload',
        showUploadList: false,
        headers: {
            authorization: 'authorization-text',
        },
        state: state,
        onChange(info: UploadChangeParam) {
            if (info.file.status === 'uploading' && state.hasLogged === false) {
                const toHide = message.loading('Processing PDF, be patient...', 0);
                state.toHide = toHide;
                state.hasLogged = true;
            }
            if (info.file.status === 'done') {
                if (state.toHide != null) {
                    setTimeout(state.toHide, 0);
                }
                message.success(`${info.file.name} file uploaded successfully! Redirecting...`);
                const redirectUrl = '/pdf/' + info.file.response.pdf_hash;
                history.push(redirectUrl);
                history.go(0);
            } else if (info.file.status === 'error') {
                if (state.toHide != null) {
                    setTimeout(state.toHide, 0);
                }
                message.error(`${info.file.name} file upload failed.`);
            }
        },
    };

    return UploaderInterface(props);
};

const Logo = styled.img`
    margin-top: 3em;
    margin-bottom: 0.5em;
    height: 128px;
`;



class Uploader extends Component<{}, { authorized: boolean }> {
    constructor(props: any) {
        super(props);
        this.state = {authorized: true};
    }

    componentDidMount() {
        isAuthorized().then(result => this.setState({
            authorized: result
        }))
    }

    render () {
        const authorized = this.state.authorized;

        console.log(authorized);

        if (authorized) {
            return <AuthorizedUploader></AuthorizedUploader>
        } else {
            return <UnauthorizedInterface></UnauthorizedInterface>
        }
    }
}

export default Uploader;