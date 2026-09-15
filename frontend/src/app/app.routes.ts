import { Routes } from '@angular/router';
import { authGuard } from './auth.guard';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () => import('./pages/login/login.component').then(m => m.LoginComponent),
  },
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  {
    path: 'claim',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/claim/claim.component').then(m => m.ClaimComponent),
  },
  {
    path: 'results/:id',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/results/results.component').then(m => m.ResultsComponent),
  },
  {
    path: 'settings',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/settings/settings.component').then(m => m.SettingsComponent),
  },
  {
    path: 'llm-connector',
    canActivate: [authGuard],
    loadComponent: () => import('./components/llm-connector/llm-connector.component').then(m => m.LlmConnectorComponent),
  },
  {
    path: 'setup',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/setup/setup.component').then(m => m.SetupComponent),
  },
  {
    path: 'usage',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/usage/usage.component').then(m => m.UsageComponent),
  },
  {
    path: 'history',
    canActivate: [authGuard],
    loadComponent: () => import('./pages/history/history.component').then(m => m.HistoryComponent),
  },
  {
    // Landing page: viewable without login, but analysis is gated (the page
    // shows a "log in first" notice and redirects on use).
    path: 'dashboard',
    loadComponent: () => import('./pages/dashboard/dashboard.component').then(m => m.DashboardComponent),
  },
];
