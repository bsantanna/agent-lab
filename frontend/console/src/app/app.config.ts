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

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({eventCoalescing: true}),
    provideRouter(routes),
    provideStore({
      router: routerReducer,
      integration: integrationReducer
    }),
    provideStoreDevtools({maxAge: 25, logOnly: !isDevMode()}),
    provideHttpClient(),
    provideEffects([IntegrationEffects]),
    provideRouterStore(),
  ]
};
