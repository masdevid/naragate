import { Routes } from '@angular/router';
import { ClaimComponent } from './pages/claim/claim.component';
import { ResultsComponent } from './pages/results/results.component';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { SettingsComponent } from './pages/settings/settings.component';
import { SetupComponent } from './pages/setup/setup.component';
import { UsageComponent } from './pages/usage/usage.component';

export const routes: Routes = [
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  { path: 'claim', component: ClaimComponent },
  { path: 'results/:id', component: ResultsComponent },
  { path: 'settings', component: SettingsComponent },
  { path: 'setup', component: SetupComponent },
  { path: 'usage', component: UsageComponent },
  { path: 'dashboard', component: DashboardComponent },
];
