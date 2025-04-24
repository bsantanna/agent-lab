import {Message} from '../../openapi';
import {createEntityAdapter, EntityState} from '@ngrx/entity';

export interface MessageState extends EntityState<Message>{
  selectedEntityId: string | null;
  reply: Message | null | undefined;
  loading: boolean;
  error: any;
}

export const messageAdapter = createEntityAdapter<Message>();
