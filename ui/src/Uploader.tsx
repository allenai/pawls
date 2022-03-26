// import React from 'react';
// import ReactDOM from 'react-dom';
import 'antd/dist/antd.css';
import { Upload, message, Button } from 'antd';
import { CenterOnPage } from './components';
import type { UploadChangeParam } from 'antd/lib/upload';
import { UploadOutlined } from '@ant-design/icons';

const props = {
    name: 'file',
    action: '/api/upload',
    headers: {
        authorization: 'authorization-text',
    },
    onChange(info: UploadChangeParam) {
        if (info.file.status !== 'uploading') {
            console.log(info.file, info.fileList);
        }
        if (info.file.status === 'done') {
            message.success(`${info.file.name} file uploaded successfully`);
        } else if (info.file.status === 'error') {
            message.error(`${info.file.name} file upload failed.`);
        }
    },
};
const Uploader = () => {
    return (
        <CenterOnPage>
            <Upload {...props} accept=".pdf">
                <Button size="large" shape="round" icon={<UploadOutlined />}>
                    Click to Upload PDF File
                </Button>
            </Upload>
        </CenterOnPage>
    );
};

export default Uploader;
