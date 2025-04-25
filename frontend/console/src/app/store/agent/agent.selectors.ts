import {createFeatureSelector, createSelector} from '@ngrx/store';
import {agentAdapter, AgentState} from './agent.state';

export const selectAgentState = createFeatureSelector<AgentState>('agent');

const {selectAll, selectEntities} = agentAdapter.getSelectors(selectAgentState);

export const selectCurrentAgent = createSelector(
  selectEntities,
  selectAgentState,
  (entities, state) => (state.selectedEntityId ? entities[state.selectedEntityId] : null)
);

export {selectAll, selectEntities};
