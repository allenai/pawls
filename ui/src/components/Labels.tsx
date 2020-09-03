import React, { useEffect, useState }  from 'react';
import { Tag } from "@allenai/varnish";

import { getLabels } from '../api';

export const Labels = () => {

    const [labels, setLabels] = useState<string[]>([])

    useEffect(() => {
        getLabels().then(labels => setLabels(labels))
    }, []) 

    // TODO(Mark): Make these Tags checkable on click and with
    // keyboard shortcuts, and pass state to a global context provider.
    return (
        <>
            {labels.map(label => (
                <Tag id={label} color="orange">
                    {label}
                </Tag>           
            ))}
        </>
    )
}
