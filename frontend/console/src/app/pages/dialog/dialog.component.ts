import { Component } from '@angular/core';
import {HeaderComponent} from '../../components/header/header.component';
import {QueryInputComponent} from '../../components/query-input/query-input.component';

@Component({
  selector: 'console-dialog',
  imports: [
    HeaderComponent,
    QueryInputComponent
  ],
  templateUrl: './dialog.component.html',
  styleUrl: './dialog.component.scss'
})
export class DialogComponent {

}
