import React from 'react';
import { SidebarItem, SidebarItemTitle } from './common';
import { RelationGroup } from '../../context';

interface RelationProps {
    relations: RelationGroup[];
}

// TODO(Mark): Improve the UX of this component.
export const Relations = ({ relations }: RelationProps) => {
    return (
        <SidebarItem>
            <SidebarItemTitle>Relations</SidebarItemTitle>
            {relations.length === 0 ? (
                <>None</>
            ) : (
                <ul>
                    {relations.map((relation, i) => (
                        <li key={relation.toString()}>Relation #{i + 1}</li>
                    ))}
                </ul>
            )}
        </SidebarItem>
    );
};
