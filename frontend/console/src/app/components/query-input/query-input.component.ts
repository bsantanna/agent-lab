import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Store } from '@ngrx/store';
import {Observable, tap} from 'rxjs';
import { Agent } from '../../openapi';
import { selectAll as selectAvailableAgents, selectCurrentAgent } from '../../store/agent/agent.selectors';
import { AgentActions } from '../../store/agent/agent.actions';
import {FormBuilder, FormGroup, Validators, AbstractControl, ReactiveFormsModule, FormControl} from '@angular/forms';

@Component({
  selector: 'console-query-input',
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './query-input.component.html',
  styleUrls: ['./query-input.component.scss']
})
export class QueryInputComponent {

  readonly availableAgents$: Observable<Agent[]>;
  readonly currentAgent$: Observable<Agent | null | undefined>;
  readonly form: FormGroup;
  agentSelectorOpen = false;

  constructor(
    private readonly store: Store,
    private readonly fb: FormBuilder
  ) {

    this.currentAgent$ = this.store.select(selectCurrentAgent).pipe(
      tap(agent => {
        if (agent) {
          this.form.get('agentId')?.setValue(agent.id);
        } else {
          this.form.get('agentId')?.setValue(null);
        }
      })
    );
    this.availableAgents$ = this.store.select(selectAvailableAgents);
    this.form = this.fb.group({
      query: ['', [Validators.required, this.noWhitespaceValidator]],
      agentId: ['', [Validators.required, this.noWhitespaceValidator]]
    });
  }

  noWhitespaceValidator(control: AbstractControl) {
    const isWhitespace = (control.value ?? '').trim().length === 0;
    return !isWhitespace ? null : { whitespace: true };
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
    this.store.dispatch(AgentActions.selectAgent({ id: agent.id }));
    this.agentSelectorOpen = false;
  }

  deselectAgent() {
    this.store.dispatch(AgentActions.deselectAgent());
    this.agentSelectorOpen = false;
  }

}
