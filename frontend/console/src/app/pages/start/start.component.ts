import {AfterViewInit, Component} from '@angular/core';
import {QueryInputComponent} from '../../components/query-input/query-input.component';
import {HeaderComponent} from '../../components/header/header.component';
import {IntegrationActions} from '../../store/integration/integration.actions';
import {LanguageModelActions} from '../../store/language-model/language-model.actions';
import {AgentActions} from '../../store/agent/agent.actions';
import {Store} from '@ngrx/store';

@Component({
  selector: 'console-start',
  imports: [
    HeaderComponent,
    QueryInputComponent
  ],
  templateUrl: './start.component.html',
  styleUrl: './start.component.scss'
})
export class StartComponent implements AfterViewInit {

  constructor(private readonly store: Store) {}

  ngAfterViewInit(): void {
    this.store.dispatch(IntegrationActions.loadIntegrations());
    this.store.dispatch(LanguageModelActions.loadLanguageModels());
    this.store.dispatch(AgentActions.loadAgents());
  }

}
