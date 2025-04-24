import { Injectable } from '@angular/core';
import {Actions, createEffect, ofType} from '@ngrx/effects';
import {Attachment, AttachmentsService} from '../../openapi';
import {AttachmentActions} from './attachment.actions';
import {catchError, map, mergeMap, of} from 'rxjs';
import {HttpClient} from '@angular/common/http';



@Injectable()
export class AttachmentEffects {

  readonly uploadAttachment$;

  constructor(
    private readonly actions$: Actions,
    private readonly httpClient: HttpClient,
  ) {
    this.uploadAttachment$ = createEffect(() =>
      this.actions$.pipe(
        ofType(AttachmentActions.uploadAttachment),
        map(action => new File([action.data], action.filename, { type: action.data.type })),
        mergeMap(file => {
          const formData = new FormData();
          formData.append('file', file, file.name);
          return this.httpClient.post<Attachment>("/attachments/upload", formData).pipe(
            map(attachment => AttachmentActions.uploadAttachmentSuccess({ data: attachment })),
            catchError(error => of(AttachmentActions.uploadAttachmentFailure({ error: error.message })))
          );
        })
      )
    );
  }
}
