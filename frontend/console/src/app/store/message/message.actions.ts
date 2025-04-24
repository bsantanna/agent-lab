import {createActionGroup, emptyProps, props} from '@ngrx/store';
import {Message, MessageListRequest, MessageRequest} from '../../openapi';

export const MessageActions = createActionGroup({
  source: 'Message',
  events: {
    'Load Messages': props<{ data: MessageListRequest }>(),
    'Load Messages Success': props<{ data: Message[] }>(),
    'Load Messages Failure': props<{ error: string }>(),
    'Post Message': props<{ data: MessageRequest }>(),
    'Post Message Success': props<{ data: Message }>(),
    'Post Message Failure': props<{ error: string }>(),
  }
});
