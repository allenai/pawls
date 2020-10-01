import React, { useState} from 'react';
import { Modal, Row, Col } from '@allenai/varnish';
import { Annotation } from '../context';
import { ReactSortable } from "react-sortablejs";
import styled from 'styled-components';

interface RelationModalProps {
    visible: boolean
    onClick: () => void
    source: Annotation[]
    setSource: (a: Annotation[]) => void
}

export const RelationModal = ({visible, onClick, source, setSource}: RelationModalProps) => {
    
    const [target, setTarget] = useState<Annotation[]>([])

    return (
    <Modal
        title="Annotate Relations"
        visible={visible}
        onOk={() => {onClick(); setTarget([])}}
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