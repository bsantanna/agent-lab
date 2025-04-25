import {AfterViewInit, Component} from '@angular/core';
import {HeaderComponent} from '../../components/header/header.component';
import {QueryInputComponent} from '../../components/query-input/query-input.component';
import {ChatComponent} from '../../components/chat/chat.component';
import {Store} from '@ngrx/store';
import {selectAll as selectAllMessages, selectMessageIsLoading} from '../../store/message/message.selectors';
import {ActivatedRoute} from '@angular/router';
import {MessageActions} from '../../store/message/message.actions';
import {MessageListRequest} from '../../openapi';
import {AgentActions} from '../../store/agent/agent.actions';
import {IntegrationActions} from '../../store/integration/integration.actions';
import {LanguageModelActions} from '../../store/language-model/language-model.actions';

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
export class DialogComponent implements AfterViewInit {

  readonly isProcessing$;
  readonly messages$;

  constructor(
    private readonly store: Store,
    private readonly activatedRoute: ActivatedRoute,
  ) {
    this.isProcessing$ = this.store.select(selectMessageIsLoading);
    this.messages$ = this.store.select(selectAllMessages);
  }

  ngAfterViewInit(): void {
    const agentId = this.activatedRoute.snapshot.params['agentId'];
    const messageListRequest = {
      agent_id: agentId,
    } as MessageListRequest;
    this.store.dispatch(AgentActions.loadAgents());
    this.store.dispatch(IntegrationActions.loadIntegrations());
    this.store.dispatch(LanguageModelActions.loadLanguageModels());
    this.store.dispatch(AgentActions.selectAgent({id:agentId}));
    this.store.dispatch(MessageActions.loadMessages({data: messageListRequest}));
  }

}
