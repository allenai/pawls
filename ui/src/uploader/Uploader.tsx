import 'antd/dist/antd.css';
import './styles.css';
import { Upload, message, Layout, Row, PageHeader } from 'antd';
import { useHistory } from 'react-router-dom';
import { UploadOutlined } from '@ant-design/icons';
import type { UploadChangeParam } from 'antd/lib/upload/interface';
import type { MessageType } from 'antd/lib/message';
import annotateSvg from './annotate.svg';
import styled from 'styled-components';

const { Content } = Layout;
const { Dragger } = Upload;

interface uploadMessagingState {
    hasLogged: boolean;
    toHide: null | MessageType;
}

const Uploader = () => {
    const history = useHistory();
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
                console.log(info.file.response);
                console.log(state);
                console.log(history);
                if (state.toHide != null) {
                    setTimeout(state.toHide, 0);
                }
                message.success(`${info.file.name} file uploaded successfully! Redirecting...`);
                const redirectUrl = '/pdf/' + info.file.response.pdf_hash;
                history.push(redirectUrl);
                history.go(0);
            } else if (info.file.status === 'error') {
                message.error(`${info.file.name} file upload failed.`);
            }
        },
    };

    return (
        <Layout>
            <Content className="site-layout-background">
                <Row justify="center" align="middle">
                    <Logo src={annotateSvg} alt="My Happy SVG" />
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
                            Please be patient while the PDF is being processed. Once processed, you
                            will automatically redirect you to the annotation page.
                        </div>
                    </Dragger>
                </Row>
            </Content>
        </Layout>
    );
};

const Logo = styled.img`
    margin-top: 3em;
    margin-bottom: 0.5em;
    height: 128px;
`;

export default Uploader;
