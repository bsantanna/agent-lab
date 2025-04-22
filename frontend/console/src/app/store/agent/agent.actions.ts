import { createActionGroup, emptyProps, props } from '@ngrx/store';
import {Agent} from '../../openapi';

export const AgentActions = createActionGroup({
  source: 'Agent',
  events: {
    'Load Agents': emptyProps(),
    'Load Agents Success': props<{ data: Agent[] }>(),
    'Load Agents Failure': props<{ error: string }>(),
  }
});
