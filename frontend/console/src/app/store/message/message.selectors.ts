import { createFeatureSelector, createSelector } from '@ngrx/store';
import {messageAdapter, MessageState} from './message.state';

export const selectMessageState = createFeatureSelector<MessageState>('message');

const {selectAll, selectEntities} = messageAdapter.getSelectors(selectMessageState);

const selectCurrentMessage = createSelector(
  selectEntities,
  selectMessageState,
  (entities, state) => (state.selectedEntityId ? entities[state.selectedEntityId] : null)
);

const selectMessageRequest = createSelector(
  selectMessageState,
  state => state.request
);

const selectMessageReply = createSelector(
  selectMessageState,
  state => state.reply
);

const selectMessageIsLoading = createSelector(
  selectMessageState,
  state => state.loading
)

export {selectAll, selectEntities, selectCurrentMessage, selectMessageRequest, selectMessageReply, selectMessageIsLoading};
