import { ComponentType } from 'react';

/**
 * Interface defining the shape of an individual route.
 */
export interface AppRoute {
    /* The url path, i.e. in the url `http://localhost/about`, `/about` is the path. */
    path: string;
    /* The name of the route that's displaed in the navigation. */
    label: string;
    /* The component that's rendered when that route is active. */
    component: ComponentType<any>;
}
