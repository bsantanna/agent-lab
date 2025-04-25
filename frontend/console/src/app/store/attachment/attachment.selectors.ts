import {createFeatureSelector, createSelector} from '@ngrx/store';
import {AttachmentState} from './attachment.reducer';

export const selectAttachmentState = createFeatureSelector<AttachmentState>('attachment');

export const selectCurrentAttachment = createSelector(
  selectAttachmentState,
  state => state.attachment
)
