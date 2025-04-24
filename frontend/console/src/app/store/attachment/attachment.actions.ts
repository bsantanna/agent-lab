import { createActionGroup, props } from '@ngrx/store';
import {Attachment} from '../../openapi';

export const AttachmentActions = createActionGroup({
  source: 'Attachment',
  events: {
    'Upload Attachment': props<{ data: Blob, filename: string }>(),
    'Upload Attachment Success': props<{ data: Attachment }>(),
    'Upload Attachment Failure': props<{ error: string }>(),
  }
});
