import {createActionGroup, emptyProps, props} from '@ngrx/store';
import {Integration} from '../../openapi';

export const IntegrationActions = createActionGroup({
  source: 'Integration',
  events: {
    'Load Integrations': emptyProps(),
    'Load Integrations Success': props<{ data: Integration[] }>(),
    'Load Integrations Failure': props<{ error: string }>(),
  }
});
