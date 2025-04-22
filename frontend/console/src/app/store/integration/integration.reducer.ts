import {createReducer, on} from '@ngrx/store';
import {IntegrationActions} from './integration.actions';
import {integrationAdapter} from './integration.state';
import {EntityState} from '@ngrx/entity';
import {Integration} from '../../openapi';

export const integrationFeatureKey = 'integration';

export interface IntegrationState extends EntityState<Integration> {
    selectedEntityId: string | null;
    loading: boolean;
    error: any;
}

export const initialState: IntegrationState = integrationAdapter.getInitialState({
    selectedEntityId: null,
    loading: false,
    error: null,
});

export const integrationReducer = createReducer(
    initialState,
    on(IntegrationActions.loadIntegrations, state => ({
        ...state,
        loading: true,
        error: null,
    })),
    on(IntegrationActions.loadIntegrationsSuccess, (state, {data}) =>
        integrationAdapter.setAll(data, {...state, loading: false})
    ),
    on(IntegrationActions.loadIntegrationsFailure, (state, {error}) => ({
        ...state,
        loading: false,
        error,
    })),
);
