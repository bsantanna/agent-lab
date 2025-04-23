import {Routes} from '@angular/router';
import {StartComponent} from './pages/start/start.component';

export const routes: Routes = [
  {path: '', redirectTo: '/pages/start', pathMatch: 'full'},
  {path: 'pages/start', component: StartComponent}
];
