import {Component} from '@angular/core';
import {Router} from '@angular/router';
import {CommonModule} from '@angular/common';
import {Store} from '@ngrx/store';
import {Observable, tap} from 'rxjs';
import {Agent, Attachment, MessageRequest} from '../../openapi';
import {selectAll as selectAvailableAgents, selectCurrentAgent} from '../../store/agent/agent.selectors';
import {AgentActions} from '../../store/agent/agent.actions';
import {AbstractControl, FormBuilder, FormGroup, ReactiveFormsModule, Validators} from '@angular/forms';
import {AudioRecorderComponent} from '../audio-recorder/audio-recorder.component';
import {AttachmentActions} from '../../store/attachment/attachment.actions';
import {selectCurrentAttachment} from '../../store/attachment/attachment.selectors';
import globalConfig from '../../../agent-lab-console.json';
import {MessageActions} from '../../store/message/message.actions';
import {selectMessageIsLoading} from '../../store/message/message.selectors';

@Component({
  selector: 'console-query-input',
  imports: [CommonModule, ReactiveFormsModule, AudioRecorderComponent],
  templateUrl: './query-input.component.html',
  styleUrls: ['./query-input.component.scss']
})
export class QueryInputComponent {

  readonly availableAgents$: Observable<Agent[]>;
  readonly currentAgent$: Observable<Agent | null | undefined>;
  readonly currentAttachment$: Observable<Attachment | null | undefined>;
  readonly isProcessing$: Observable<boolean>;
  readonly form: FormGroup;
  agentSelectorOpen = false;

  constructor(
    private readonly store: Store,
    private readonly fb: FormBuilder,
    private readonly router: Router
  ) {
    this.availableAgents$ = this.store.select(selectAvailableAgents);

    this.currentAgent$ = this.store.select(selectCurrentAgent).pipe(
      tap(agent => {
        if (agent) {
          this.form.get('agentId')?.setValue(agent.id);
        } else {
          this.form.get('agentId')?.setValue(null);
        }
      })
    );

    this.currentAttachment$ = this.store.select(selectCurrentAttachment).pipe(
      tap(attachment => {
        if (attachment) {
          this.form.get('attachmentId')?.setValue(attachment.id);
        } else {
          this.form.get('attachmentId')?.setValue(null);
        }
      })
    );

    this.isProcessing$ = this.store.select(selectMessageIsLoading);

    this.form = this.fb.group({
      query: ['', [Validators.required, this.noWhitespaceValidator]],
      agentId: ['', [Validators.required, this.noWhitespaceValidator]],
      attachmentId: [null]
    });
  }

  noWhitespaceValidator(control: AbstractControl) {
    const isWhitespace = (control.value ?? '').trim().length === 0;
    return !isWhitespace ? null : {whitespace: true};
  }

  voiceInputEnabled(agent: Agent | null | undefined): boolean {
    return agent != null && ['voice_memos', 'azure_entra_id_voice_memos'].includes(agent.agent_type);
  }

  imageAttachmentEnabled(agent: Agent | null | undefined): boolean {
    return agent != null && ['vision_document'].includes(agent.agent_type);
  }

  toggleAgentSelector(): void {
    this.agentSelectorOpen = !this.agentSelectorOpen;
  }

  setCurrentAgent(agent: Agent) {
    this.store.dispatch(AgentActions.selectAgent({id: agent.id}));
    this.agentSelectorOpen = false;
  }

  deselectAgent() {
    this.store.dispatch(AgentActions.deselectAgent());
    this.store.dispatch(AttachmentActions.deselectAttachment());
    this.store.dispatch(MessageActions.cleanReply())
    this.agentSelectorOpen = false;
    this.router.navigate(['/pages/start']);
  }

  getAttachmentUrl(attachment: Attachment): string {
    return `${globalConfig.apiUrl}/attachments/download/${attachment.id}`;
  }

  postMessageRequest(
    query: string,
    agentId: string,
    attachmentId: string | null | undefined,
  ): void {
    if (!this.form.invalid) {
      const data = {
        'message_role': 'human',
        'message_content': query,
        'agent_id': agentId,
        'attachment_id': attachmentId,
      } as MessageRequest;

      this.store.dispatch(MessageActions.postMessage({data}));
      this.router.navigate(['/pages/dialog', agentId]);
    }
  }

}
