import {createEntityAdapter, EntityState} from '@ngrx/entity';
import {LanguageModel} from '../../openapi';


export interface LanguageModelState extends EntityState<LanguageModel> {
  selectedEntityId: string | null;
  loading: boolean;
  error: string | null;
}

export const languageModelAdapter = createEntityAdapter<LanguageModel>();
