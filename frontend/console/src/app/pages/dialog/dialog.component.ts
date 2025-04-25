import { Component } from '@angular/core';
import {HeaderComponent} from '../../components/header/header.component';
import {QueryInputComponent} from '../../components/query-input/query-input.component';
import {ChatComponent} from '../../components/chat/chat.component';

@Component({
  selector: 'console-dialog',
  imports: [
    ChatComponent,
    HeaderComponent,
    QueryInputComponent
  ],
  templateUrl: './dialog.component.html',
  styleUrl: './dialog.component.scss'
})
export class DialogComponent {

}
