import {createReducer, on} from '@ngrx/store';
import {MessageActions} from './message.actions';
import {messageAdapter, MessageState} from './message.state';

export const messageFeatureKey = 'message';

export const initialState: MessageState = messageAdapter.getInitialState({
  selectedEntityId: null,
  request: null,
  reply: null,
  loading: false,
  error: null,
});

export const messageReducer = createReducer(
  initialState,
  on(MessageActions.loadMessages, state => ({
    ...state,
    loading: true,
    error: null,
  })),
  on(MessageActions.loadMessagesSuccess, (state, {data}) =>
    messageAdapter.setAll(data, {...state, loading: false})
  ),
  on(MessageActions.loadMessagesFailure, (state, {error}) => ({
    ...state,
    loading: false,
    error,
  })),
  on(MessageActions.postMessage, (state, {data}) => ({
    ...state,
    request: data,
    loading: true,
    error: null,
  })),
  on(MessageActions.postMessageSuccess, (state, {data}) => ({
    ...state,
    reply: data,
    loading: false,
    error: null,
  })),
  on(MessageActions.postMessageFailure, (state, {error}) => ({
    ...state,
    loading: false,
    error,
  })),
  on(MessageActions.cleanReply, state => ({
    ...state,
    request: null,
    reply: null,
  }))
);

