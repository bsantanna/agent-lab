import {Integration} from '../../openapi';
import {createEntityAdapter, EntityState} from '@ngrx/entity';

export interface IntegrationState extends EntityState<Integration> {
  selectedEntityId: string | null;
  loading: boolean;
  error: string | null;
}

export const integrationAdapter = createEntityAdapter<Integration>();
