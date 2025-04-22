import {AfterViewInit, Component} from '@angular/core';
import {RouterOutlet} from '@angular/router';
import {Store} from '@ngrx/store';
import {IntegrationActions} from './store/integration/integration.actions';
import {LanguageModelActions} from './store/language-model/language-model.actions';
import {AgentActions} from './store/agent/agent.actions';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent implements AfterViewInit{
  title = 'agent-lab-console';

  constructor(private store: Store) {}

  ngAfterViewInit(): void {
    this.store.dispatch(IntegrationActions.loadIntegrations());
    this.store.dispatch(LanguageModelActions.loadLanguageModels());
    this.store.dispatch(AgentActions.loadAgents());
  }

}
