import {createReducer, on} from '@ngrx/store';
import {AgentActions} from './agent.actions';
import {agentAdapter, AgentState} from './agent.state';

export const agentFeatureKey = 'agent';

export const initialState: AgentState = agentAdapter.getInitialState({
  selectedEntityId: null,
  loading: false,
  error: null,
});

export const agentReducer = createReducer(
  initialState,
  on(AgentActions.loadAgents, state => ({
    ...state,
    loading: true,
    error: null,
  })),
  on(AgentActions.loadAgentsSuccess, (state, {data}) =>
    agentAdapter.setAll(data, {...state, loading: false})
  ),
  on(AgentActions.loadAgentsFailure, (state, {error}) => ({
    ...state,
    loading: false,
    error,
  })),
  on(AgentActions.selectAgent, (state, {id}) => ({
    ...state,
    selectedEntityId: id,
  })),
  on(AgentActions.deselectAgent, state => ({
    ...state,
    selectedEntityId: null,
  }))
);

