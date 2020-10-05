import React, { useState, useContext} from 'react';
import { Modal, Row, Col, Tag } from '@allenai/varnish';
import { Annotation, RelationGroup, AnnotationStore } from '../context';
import { ReactSortable } from "react-sortablejs";
import styled from 'styled-components';
import { Label } from '../api';

const { CheckableTag } = Tag;

interface RelationModalProps {
    visible: boolean
    onClick: (group: RelationGroup) => void
    onCancel: () => void
    source: Annotation[]
    setSource: (a: Annotation[]) => void
    target: Annotation[]
    setTarget: (a: Annotation[]) => void
    label: Label
}


export const RelationModal = ({visible, onClick, onCancel, source, setSource, target, setTarget, label}: RelationModalProps) => {
 
    const annotationStore = useContext(AnnotationStore)

    return (
    <Modal
        title="Annotate Relations"
        width={600}
        visible={visible}
        maskClosable={true}
        onCancel={onCancel}
        onOk={() => {
            onClick(new RelationGroup(source.map(s => s.id), target.map(t => t.id), label));
            setTarget([])
        }}
    >
    <Row>
        <Col span={10}>
            <h5>Source</h5>
            <Sortable
                list={source} 
                setList={setSource}
                animation={200}
                delay={2}
                group="relations"
            >
                {source.map((item, i) => (
                    <div key={item.id}>
                        <div key={i} id={item.id}>
                            {item.id}
                        </div>
                    </div>
                        )
                    )
                }
            </Sortable>
        </Col>

        <Col span={4}>
            <h5>Relation</h5>
            {annotationStore.relationLabels.map(relation => (
                        <CheckableTag
                            key={relation.text}
                            onClick={() => {annotationStore.setActiveRelationLabel(relation)}}
                            checked={relation === annotationStore.activeRelationLabel}
                        >
                            {relation.text}
                        </CheckableTag>           
                    ))}
        </Col>
        <Col span={10}>
        <h5>Target</h5>
        <Sortable
            list={target} 
            setList={setTarget}
            animation={200}
            delay={2}
            group="relations"
        >
            {target.map((item) => (<div key={item.id}>{item.id}</div>))}
        </Sortable>
        </Col>
    </Row>

    </Modal>
    )
}


const Sortable = styled(ReactSortable)`
    min-height: 100px;
    width: 100%;
    border: 3px solid black;

`