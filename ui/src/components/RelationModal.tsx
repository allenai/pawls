import React, { useState, useContext} from 'react';
import { Modal, Tag, Transfer } from '@allenai/varnish';
import { Annotation, RelationGroup, AnnotationStore, PDFPageInfo } from '../context';
import { Label } from '../api';
import { AnnotationSummary } from "./AnnotationSummary";

const { CheckableTag } = Tag;

interface RelationModalProps {
    visible: boolean
    onClick: (group: RelationGroup) => void
    onCancel: () => void
    source: Annotation[]
    label: Label,
    pages: PDFPageInfo[]
}


export const RelationModal = ({visible, onClick, onCancel, source, label, pages}: RelationModalProps) => {
 
    const annotationStore = useContext(AnnotationStore)
    const [targetKeys, setTargetKeys] = useState<string[]>([])
    const transferSource = source.map((a) => ({key: a.id, annotation: a}))

    return (

    <Modal
        title="Annotate Relations"
        width={800}
        visible={visible}
        maskClosable={true}
        onCancel={() => {
            setTargetKeys([])
            onCancel()
        }}
        onOk={() => {

            const sourceIds = source
                .filter(s => !targetKeys.some((k) => k === s.id))
                .map(s => s.id)
            onClick(new RelationGroup(sourceIds, targetKeys, label));
            setTargetKeys([])
        }}
    >
        <h5>Choose a Relation</h5>
        {annotationStore.relationLabels.map(relation => (
            <CheckableTag
                key={relation.text}
                onClick={() => {annotationStore.setActiveRelationLabel(relation)}}
                checked={relation === annotationStore.activeRelationLabel}
            >
                {relation.text}
            </CheckableTag>           
        ))}
        <br/>
        <Transfer
            dataSource={transferSource}
            listStyle={{width: 300, marginTop: "20px"}}
            showSearch={false}
            targetKeys={targetKeys}
            onChange={setTargetKeys}
            render={item => (
                <AnnotationSummary
                    annotation={item.annotation}
                    pageInfo={pages[item.annotation.page]}
                />
            )}
        />
    </Modal>
    )
}
