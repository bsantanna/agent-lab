import {Agent} from '../../openapi';
import {createEntityAdapter, EntityState} from '@ngrx/entity';

export interface AgentState extends EntityState<Agent>{
  selectedEntityId: string | null;
  loading: boolean;
  error: string | null;
}

export const agentAdapter = createEntityAdapter<Agent>();
