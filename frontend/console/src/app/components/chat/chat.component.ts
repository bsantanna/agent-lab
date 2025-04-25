import { Component } from '@angular/core';
import {CommonModule} from '@angular/common';
import {MarkdownModule} from 'ngx-markdown';
import {Store} from '@ngrx/store';

import {
  selectAll as selectAllMessages,
  selectMessageIsLoading,
} from '../../store/message/message.selectors';

@Component({
  selector: 'console-chat',
  imports: [CommonModule,MarkdownModule],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.scss'
})
export class ChatComponent {

  readonly isProcessing$;
  readonly messages$;

  constructor(private readonly store:Store) {
    this.isProcessing$ = this.store.select(selectMessageIsLoading);
    this.messages$ = this.store.select(selectAllMessages);
  }

}
