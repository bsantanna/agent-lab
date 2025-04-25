import {Injectable} from '@angular/core';
import {Actions, createEffect, ofType} from '@ngrx/effects';
import {AgentActions} from './agent.actions';
import {catchError, map, mergeMap, of} from 'rxjs';
import {AgentsService} from '../../openapi';


@Injectable()
export class AgentEffects {

  readonly loadAgents$

  constructor(
    private actions$: Actions,
    private agentsService: AgentsService
  ) {
    this.loadAgents$ = createEffect(() =>
      this.actions$.pipe(
        ofType(AgentActions.loadAgents),
        mergeMap(() => this.agentsService.getListAgentsListGet().pipe(
          map(agents => AgentActions.loadAgentsSuccess({data: agents})),
          catchError(error => of(AgentActions.loadAgentsFailure({error: error.message})))
        ))
      ));
  }
}
