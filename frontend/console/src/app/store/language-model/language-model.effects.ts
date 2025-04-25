import {Injectable} from '@angular/core';
import {Actions, createEffect, ofType} from '@ngrx/effects';
import {LlmsService} from '../../openapi';
import {LanguageModelActions} from './language-model.actions';
import {catchError, map, mergeMap, of} from 'rxjs';


@Injectable()
export class LanguageModelEffects {

  readonly loadLanguageModels$

  constructor(
    private actions$: Actions,
    private llmsService: LlmsService
  ) {
    this.loadLanguageModels$ = createEffect(() =>
      this.actions$.pipe(
        ofType(LanguageModelActions.loadLanguageModels),
        mergeMap(() => this.llmsService.getListLlmsListGet().pipe(
          map(languageModels => LanguageModelActions.loadLanguageModelsSuccess({data: languageModels})),
          catchError(error => of(LanguageModelActions.loadLanguageModelsFailure({error: error.message}))))
        )
      ));
  }
}
