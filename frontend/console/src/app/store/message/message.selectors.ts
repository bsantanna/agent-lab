import { createFeatureSelector, createSelector } from '@ngrx/store';
import {messageAdapter, MessageState} from './message.state';

export const selectMessageState = createFeatureSelector<MessageState>('message');

const {selectAll, selectEntities} = messageAdapter.getSelectors(selectMessageState);

export const selectCurrentMessage = createSelector(
  selectEntities,
  selectMessageState,
  (entities, state) => (state.selectedEntityId ? entities[state.selectedEntityId] : null)
);

export const selectMessageRequest = createSelector(
  selectMessageState,
  state => state.request
);

export const selectMessageReply = createSelector(
  selectMessageState,
  state => state.reply
);

export const selectMessageIsLoading = createSelector(
  selectMessageState,
  state => state.loading
)
