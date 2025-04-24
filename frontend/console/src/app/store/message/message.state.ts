import {Message, MessageRequest} from '../../openapi';
import {createEntityAdapter, EntityState} from '@ngrx/entity';

export interface MessageState extends EntityState<Message> {
  selectedEntityId: string | null;
  request: MessageRequest | null | undefined;
  reply: Message | null | undefined;
  loading: boolean;
  error: any;
}

export const messageAdapter = createEntityAdapter<Message>();
