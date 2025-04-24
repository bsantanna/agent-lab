import {Routes} from '@angular/router';
import {StartComponent} from './pages/start/start.component';
import {DialogComponent} from './pages/dialog/dialog.component';

export const routes: Routes = [
  {path: '', redirectTo: '/pages/start', pathMatch: 'full'},
  {path: 'pages/start', component: StartComponent},
  {path: 'pages/dialog/:agentId', component: DialogComponent}
];
