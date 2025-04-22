import {Injectable} from '@angular/core';
import {Actions, createEffect, ofType} from '@ngrx/effects';
import {catchError, map, mergeMap, of} from 'rxjs';
import {IntegrationsService} from '../../openapi';
import {IntegrationActions} from './integration.actions';


@Injectable()
export class IntegrationEffects {


  loadIntegrations$

  constructor(
    private actions$: Actions,
    private integrationsService: IntegrationsService
  ) {
    this.loadIntegrations$ = createEffect(() =>
      this.actions$.pipe(
        ofType(IntegrationActions.loadIntegrations),
        mergeMap(() => this.integrationsService.getListIntegrationsListGet().pipe(
          map(integrations => IntegrationActions.loadIntegrationsSuccess({data: integrations})),
          catchError(error => of(IntegrationActions.loadIntegrationsFailure({error: error.message}))))
        )
      ));
  }

}
