import { createContext } from 'react';

import { Token } from '../api';

export interface TokenSpanAnnotation {
    tokens: Token[];
}

interface _AnnotationStore {
    tokenSpanAnnotations: TokenSpanAnnotation[];
    selectedTokenSpanAnnotation?: TokenSpanAnnotation;
    setSelectedTokenSpanAnnotation: (t?: TokenSpanAnnotation) => void;
    setTokenSpanAnnotations: (t: TokenSpanAnnotation[]) => void;
}

export const AnnotationStore = createContext<_AnnotationStore>({
    tokenSpanAnnotations: [],
    setSelectedTokenSpanAnnotation: (_?: TokenSpanAnnotation) => {
        throw new Error('Unimplemented');
    },
    setTokenSpanAnnotations: (_: TokenSpanAnnotation[]) => {
        throw new Error('Unimplemented');
    }
});
