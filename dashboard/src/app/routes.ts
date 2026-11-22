import { Routes } from '@angular/router';
import { AppComponent, PageComponent } from './app.component';

export const routes: Routes = [
  {
    path: '',
    component: AppComponent,
    children: [
      { path: '', component: PageComponent, data: { page: 'overview' } },
      { path: 'live', component: PageComponent, data: { page: 'live' } },
      { path: 'cameras', component: PageComponent, data: { page: 'cameras' } },
      { path: 'analytics', component: PageComponent, data: { page: 'analytics' } },
      { path: 'classes', component: PageComponent, data: { page: 'classes' } },
      { path: 'health', component: PageComponent, data: { page: 'health' } },
      { path: 'reports', component: PageComponent, data: { page: 'reports' } },
      { path: 'models', component: PageComponent, data: { page: 'models' } },
      { path: 'users', component: PageComponent, data: { page: 'users' } },
      { path: 'audit', component: PageComponent, data: { page: 'audit' } },
      { path: 'settings', component: PageComponent, data: { page: 'settings' } },
    ],
  },
  { path: '**', redirectTo: '' },
];
