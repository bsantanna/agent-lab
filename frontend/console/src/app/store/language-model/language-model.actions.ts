import { createActionGroup, emptyProps, props } from '@ngrx/store';
import {LanguageModel} from '../../openapi';

export const LanguageModelActions = createActionGroup({
  source: 'LanguageModel',
  events: {
    'Load LanguageModels': emptyProps(),
    'Load LanguageModels Success': props<{ data: LanguageModel[] }>(),
    'Load LanguageModels Failure': props<{ error: string }>(),
  }
});
