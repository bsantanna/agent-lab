import {Component} from '@angular/core';
import {QueryInputComponent} from '../../components/query-input/query-input.component';
import {HeaderComponent} from '../../components/header/header.component';

@Component({
  selector: 'console-start',
  imports: [
    HeaderComponent,
    QueryInputComponent
  ],
  templateUrl: './start.component.html',
  styleUrl: './start.component.scss'
})
export class StartComponent {

}
