import { Injectable } from '@angular/core';
import {Actions, createEffect, ofType} from '@ngrx/effects';
import {MessageListRequest, MessagesService} from '../../openapi';
import {MessageActions} from './message.actions';
import {catchError, map, mergeMap, of} from 'rxjs';



@Injectable()
export class MessageEffects {

  readonly loadMessages$;
  readonly postMessage$;

  constructor(
    private actions$: Actions,
    private readonly messagesService: MessagesService,
  ) {
    this.loadMessages$ = createEffect(() =>
      this.actions$.pipe(
        ofType(MessageActions.loadMessages),
        mergeMap(action=> this.messagesService.getListMessagesListPost(action.data).pipe(
          map(messages => MessageActions.loadMessagesSuccess({data:messages})),
          catchError(error => of(MessageActions.loadMessagesFailure({error: error.message})))
        ))
      )
    );

    this.postMessage$ = createEffect(() =>
      this.actions$.pipe(
        ofType(MessageActions.postMessage),
        mergeMap(action=>this.messagesService.postMessageMessagesPostPost(action.data).pipe(
          map(message => MessageActions.postMessageSuccess({data: message})),
          catchError(error => of(MessageActions.postMessageFailure({error: error.message})))
        ))
      )
    );
  }
}
