import { createReducer, on } from '@ngrx/store';
import { AttachmentActions } from './attachment.actions';
import {Attachment} from '../../openapi';

export const attachmentFeatureKey = 'attachment';

export interface AttachmentState {
  attachment: Attachment | null;
  loading: boolean;
  error: string | null;
}

export const initialState: AttachmentState = {
  attachment:null,
  loading: false,
  error: null,
};

export const attachmentReducer = createReducer(
  initialState,
  on(AttachmentActions.uploadAttachment, state => ({
    ...state,
    loading: true,
    error: null,
  })),
  on(AttachmentActions.uploadAttachmentSuccess, (state, {data}) => ({
    ...state,
    attachment: data,
    loading: false,
    error: null,
  })),
  on(AttachmentActions.uploadAttachmentFailure, (state, {error}) => ({
    ...state,
    loading: false,
    error,
  })),
  on(AttachmentActions.deselectAttachment, state => ({
    ...state,
    attachment: null,
  }))

);

