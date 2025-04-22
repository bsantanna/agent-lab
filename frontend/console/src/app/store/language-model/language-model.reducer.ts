import { createReducer, on } from '@ngrx/store';
import { LanguageModelActions } from './language-model.actions';
import {languageModelAdapter} from './language-model.state';
import {LanguageModel} from '../../openapi';
import {EntityState} from '@ngrx/entity';

export const languageModelFeatureKey = 'languageModel';

export interface LanguageModelState extends EntityState<LanguageModel> {
  selectedEntityId: string | null;
  loading: boolean;
  error: any;
}

export const initialState: LanguageModelState = languageModelAdapter.getInitialState({
  selectedEntityId: null,
  loading: false,
  error: null,
});

export const languageModelReducer = createReducer(
  initialState,
  on(LanguageModelActions.loadLanguageModels, state => ({
    ...state,
    loading: true,
    error: null,
  })),
  on(LanguageModelActions.loadLanguageModelsSuccess, (state, { data }) =>
    languageModelAdapter.setAll(data, {...state, loading: false})
  ),
  on(LanguageModelActions.loadLanguageModelsFailure, (state, { error }) => ({
    ...state,
    loading: false,
    error,
  }))
);

