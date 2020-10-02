import React, { useState} from 'react';
import { Modal, Row, Col } from '@allenai/varnish';
import { Annotation, RelationGroup } from '../context';
import { ReactSortable } from "react-sortablejs";
import styled from 'styled-components';
import { Label } from '../api';

interface RelationModalProps {
    visible: boolean
    onClick: (group: RelationGroup) => void
    source: Annotation[]
    setSource: (a: Annotation[]) => void
    label: Label
}

export const RelationModal = ({visible, onClick, source, setSource, label}: RelationModalProps) => {
    
    const [target, setTarget] = useState<Annotation[]>([])

    return (
    <Modal
        title="Annotate Relations"
        visible={visible}
        onOk={() => {
            onClick(new RelationGroup(source.map(s => s.id), target.map(t => t.id), label));
            setTarget([])
        }}
    >
    <Row>
        <Col span={12}>
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
        <Col span={12}>
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