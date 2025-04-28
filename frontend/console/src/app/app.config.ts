import {ApplicationConfig, isDevMode, provideZoneChangeDetection} from '@angular/core';
import {provideRouter} from '@angular/router';

import {routes} from './app.routes';
import {provideStore} from '@ngrx/store';
import {provideStoreDevtools} from '@ngrx/store-devtools';
import {provideEffects} from '@ngrx/effects';
import {provideRouterStore, routerReducer} from '@ngrx/router-store';
import {IntegrationEffects} from './store/integration/integration.effects';
import {integrationReducer} from './store/integration/integration.reducer';
import {provideHttpClient} from '@angular/common/http';
import {languageModelReducer} from './store/language-model/language-model.reducer';
import {agentReducer} from './store/agent/agent.reducer';
import {LanguageModelEffects} from './store/language-model/language-model.effects';
import {AgentEffects} from './store/agent/agent.effects';
import {AttachmentEffects} from './store/attachment/attachment.effects';
import {attachmentReducer} from './store/attachment/attachment.reducer';
import {messageReducer} from './store/message/message.reducer';
import {MessageEffects} from './store/message/message.effects';
import {provideMarkdown} from 'ngx-markdown';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({eventCoalescing: true}),
    provideRouter(routes),
    provideStore({
      agent: agentReducer,
      attachment: attachmentReducer,
      integration: integrationReducer,
      languageModel: languageModelReducer,
      message: messageReducer,
      router: routerReducer,
    }),
    provideStoreDevtools({maxAge: 25, logOnly: !isDevMode()}),
    provideHttpClient(),
    provideEffects([
      AgentEffects,
      AttachmentEffects,
      IntegrationEffects,
      LanguageModelEffects,
      MessageEffects,
    ]),
    provideRouterStore(),
    provideMarkdown()
  ]
};
