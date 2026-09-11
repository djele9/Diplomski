FILE: frontend/src/app/app.routes.ts

```typescript
import { Routes } from '@angular/router';
import { authGuard } from './guards/auth.guard';
import { guestGuard } from './guards/guest.guard';
import { roleGuard } from './guards/role.guard';
import { UserRole } from './models/user-role.enum';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./components/landing/landing.component').then(m => m.LandingComponent),
    title: 'Coworking Network'
  },
  {
    path: 'login',
    loadComponent: () => import('./components/login/login.component').then(m => m.LoginComponent),
    canActivate: [guestGuard],
    title: 'Sign In'
  },
  {
    path: 'admin/login',
    loadComponent: () => import('./components/admin-login/admin-login.component').then(m => m.AdminLoginComponent),
    canActivate: [guestGuard],
    title: 'Administrator Sign In'
  },
  {
    path: 'register',
    loadComponent: () => import('./components/register/register.component').then(m => m.RegisterComponent),
    canActivate: [guestGuard],
    title: 'Register'
  },
  {
    path: 'forgot-password',
    loadComponent: () => import('./components/forgot-password/forgot-password.component').then(m => m.ForgotPasswordComponent),
    canActivate: [guestGuard],
    title: 'Forgotten Password'
  },
  {
    path: 'reset-password/:token',
    loadComponent: () => import('./components/reset-password/reset-password.component').then(m => m.ResetPasswordComponent),
    canActivate: [guestGuard],
    title: 'Reset Password'
  },
  {
    path: 'member',
    canActivate: [authGuard, roleGuard],
    data: { roles: [UserRole.MEMBER, UserRole.MANAGER, UserRole.ADMIN] },
    children: [
      {
        path: 'dashboard',
        loadComponent: () => import('./components/member-dashboard/member-dashboard.component').then(m => m.MemberDashboardComponent),
        title: 'Member Dashboard'
      },
      {
        path: 'profile',
        loadComponent: () => import('./components/profile/profile.component').then(m => m.ProfileComponent),
        title: 'Profile'
      },
      {
        path: 'search',
        loadComponent: () => import('./components/space-search/space-search.component').then(m => m.SpaceSearchComponent),
        title: 'Search and Reserve'
      },
      {
        path: 'reservations',
        loadComponent: () => import('./components/member-reservations/member-reservations.component').then(m => m.MemberReservationsComponent),
        title: 'My Reservations'
      },
      {
        path: '',
        redirectTo: 'dashboard',
        pathMatch: 'full'
      }
    ]
  },
  {
    path: 'manager',
    canActivate: [authGuard, roleGuard],
    data: { roles: [UserRole.MANAGER, UserRole.ADMIN] },
    children: [
      {
        path: 'dashboard',
        loadComponent: () => import('./components/manager-dashboard/manager-dashboard.component').then(m => m.ManagerDashboardComponent),
        title: 'Manager Dashboard'
      },
      {
        path: 'spaces',
        loadComponent: () => import('./components/manager-spaces/manager-spaces.component').then(m => m.ManagerSpacesComponent),
        title: 'Spaces'
      },
      {
        path: 'spaces/create',
        loadComponent: () => import('./components/space-form/space-form.component').then(m => m.SpaceFormComponent),
        title: 'Create Space'
      },
      {
        path: 'spaces/:id/edit',
        loadComponent: () => import('./components/space-form/space-form.component').then(m => m.SpaceFormComponent),
        title: 'Edit Space'
      },
      {
        path: 'reservations',
        loadComponent: () => import('./components/manager-reservations/manager-reservations.component').then(m => m.ManagerReservationsComponent),
        title: 'Reservations'
      },
      {
        path: 'calendar',
        loadComponent: () => import('./components/manager-calendar/manager-calendar.component').then(m => m.ManagerCalendarComponent),
        title: 'Calendar'
      },
      {
        path: 'reports',
        loadComponent: () => import('./components/manager-reports/manager-reports.component').then(m => m.ManagerReportsComponent),
        title: 'Reports'
      },
      {
        path: 'import',
        loadComponent: () => import('./components/manager-import/manager-import.component').then(m => m.ManagerImportComponent),
        title: 'Import from File'
      },
      {
        path: 'profile',
        loadComponent: () => import('./components/profile/profile.component').then(m => m.ProfileComponent),
        title: 'Profile'
      },
      {
        path: '',
        redirectTo: 'dashboard',
        pathMatch: 'full'
      }
    ]
  },
  {
    path: 'admin',
    canActivate: [authGuard, roleGuard],
    data: { roles: [UserRole.ADMIN] },
    children: [
      {
        path: 'dashboard',
        loadComponent: () => import('./components/admin-dashboard/admin-dashboard.component').then(m => m.AdminDashboardComponent),
        title: 'Administrator Dashboard'
      },
      {
        path: 'users',
        loadComponent: () => import('./components/admin-users/admin-users.component').then(m => m.AdminUsersComponent),
        title: 'User Management'
      },
      {
        path: 'registration-requests',
        loadComponent: () => import('./components/admin-registration-requests/admin-registration-requests.component').then(m => m.AdminRegistrationRequestsComponent),
        title: 'Registration Requests'
      },
      {
        path: 'spaces/pending',
        loadComponent: () => import('./components/admin-pending-spaces/admin-pending-spaces.component').then(m => m.AdminPendingSpacesComponent),
        title: 'Pending Spaces'
      },
      {
        path: 'statistics',
        loadComponent: () => import('./components/admin-statistics/admin-statistics.component').then(m => m.AdminStatisticsComponent),
        title: 'Statistics'
      },
      {
        path: 'companies',
        loadComponent: () => import('./components/admin-companies/admin-companies.component').then(m => m.AdminCompaniesComponent),
        title: 'Companies'
      },
      {
        path: 'reservations',
        loadComponent: () => import('./components/admin-reservations/admin-reservations.component').then(m => m.AdminReservationsComponent),
        title: 'All Reservations'
      },
      {
        path: '',
        redirectTo: 'dashboard',
        pathMatch: 'full'
      }
    ]
  },
  {
    path: '**',
    loadComponent: () => import('./components/not-found/not-found.component').then(m => m.NotFoundComponent),
    title: 'Page Not Found'
  }
];
```

FILE: frontend/src/app/app.config.ts

```typescript
import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { routes } from './app.routes';
import { authInterceptor } from './interceptors/auth.interceptor';
import { errorInterceptor } from './interceptors/error.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes, withComponentInputBinding()),
    provideHttpClient(withInterceptors([authInterceptor, errorInterceptor]))
  ]
};
```

FILE: frontend/src/app/app.ts

```typescript
import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AuthService } from './services/auth.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class AppComponent {
  protected readonly authService = inject(AuthService);
}
```

FILE: frontend/src/app/app.html

```html
<header class="navbar navbar-expand-lg navbar-dark bg-primary fixed-top" role="banner">
  <div class="container">
    <a class="navbar-brand fw-bold" href="/" aria-label="Coworking Network Home">
      <i class="bi bi-building me-2" aria-hidden="true"></i>
      Coworking Network
    </a>
    <button
      class="navbar-toggler"
      type="button"
      data-bs-toggle="collapse"
      data-bs-target="#mainNavigation"
      aria-controls="mainNavigation"
      aria-expanded="false"
      aria-label="Toggle navigation"
    >
      <span class="navbar-toggler-icon"></span>
    </button>

    <nav id="mainNavigation" class="collapse navbar-collapse" role="navigation" aria-label="Main navigation">
      <ul class="navbar-nav me-auto mb-2 mb-lg-0">
        @if (!authService.isAuthenticated()) {
          <li class="nav-item">
            <a class="nav-link" routerLink="/login" routerLinkActive="active" aria-current="page">Sign In</a>
          </li>
          <li class="nav-item">
            <a class="nav-link" routerLink="/register" routerLinkActive="active" aria-current="page">Register</a>
          </li>
        } @else {
          @if (authService.isMember() || authService.isManager() || authService.isAdmin()) {
            <li class="nav-item">
              <a class="nav-link" routerLink="/member/dashboard" routerLinkActive="active" aria-current="page">Dashboard</a>
            </li>
          }
          @if (authService.isMember()) {
            <li class="nav-item">
              <a class="nav-link" routerLink="/member/search" routerLinkActive="active" aria-current="page">Search and Reserve</a>
            </li>
            <li class="nav-item">
              <a class="nav-link" routerLink="/member/reservations" routerLinkActive="active" aria-current="page">My Reservations</a>
            </li>
          }
          @if (authService.isManager() || authService.isAdmin()) {
            <li class="nav-item dropdown">
              <a
                class="nav-link dropdown-toggle"
                href="#"
                role="button"
                data-bs-toggle="dropdown"
                aria-expanded="false"
                aria-label="Spaces management"
              >
                Spaces
              </a>
              <ul class="dropdown-menu" role="menu">
                <li>
                  <a class="dropdown-item" routerLink="/manager/spaces" routerLinkActive="active" aria-current="page">Manage Spaces</a>
                </li>
                <li>
                  <a class="dropdown-item" routerLink="/manager/spaces/create" routerLinkActive="active" aria-current="page">Create Space</a>
                </li>
              </ul>
            </li>
            <li class="nav-item">
              <a class="nav-link" routerLink="/manager/reservations" routerLinkActive="active" aria-current="page">Reservations</a>
            </li>
            <li class="nav-item">
              <a class="nav-link" routerLink="/manager/calendar" routerLinkActive="active" aria-current="page">Calendar</a>
            </li>
            <li class="nav-item">
              <a class="nav-link" routerLink="/manager/reports" routerLinkActive="active" aria-current="page">Reports</a>
            </li>
            <li class="nav-item">
              <a class="nav-link" routerLink="/manager/import" routerLinkActive="active" aria-current="page">Import from File</a>
            </li>
          }
          @if (authService.isAdmin()) {
            <li class="nav-item dropdown">
              <a
                class="nav-link dropdown-toggle"
                href="#"
                role="button"
                data-bs-toggle="dropdown"
                aria-expanded="false"
                aria-label="Administration"
              >
                Administration
              </a>
              <ul class="dropdown-menu" role="menu">
                <li>
                  <a class="dropdown-item" routerLink="/admin/dashboard" routerLinkActive="active" aria-current="page">Dashboard</a>
                </li>
                <li>
                  <a class="dropdown-item" routerLink="/admin/users" routerLinkActive="active" aria-current="page">Users</a>
                </li>
                <li>
                  <a class="dropdown-item" routerLink="/admin/registration-requests" routerLinkActive="active" aria-current="page">Registration Requests</a>
                </li>
                <li>
                  <a class="dropdown-item" routerLink="/admin/spaces/pending" routerLinkActive="active" aria-current="page">Pending Spaces</a>
                </li>
                <li>
                  <a class="dropdown-item" routerLink="/admin/companies" routerLinkActive="active" aria-current="page">Companies</a>
                </li>
                <li>
                  <a class="dropdown-item" routerLink="/admin/statistics" routerLinkActive="active" aria-current="page">Statistics</a>
                </li>
                <li>
                  <a class="dropdown-item" routerLink="/admin/reservations" routerLinkActive="active" aria-current="page">All Reservations</a>
                </li>
              </ul>
            </li>
          }
          <li class="nav-item">
            <a class="nav-link" routerLink="/member/profile" routerLinkActive="active" aria-current="page">Profile</a>
          </li>
        }
      </ul>

      <ul class="navbar-nav ms-auto">
        @if (authService.isAuthenticated()) {
          <li class="nav-item dropdown">
            <a
              class="nav-link dropdown-toggle"
              href="#"
              role="button"
              data-bs-toggle="dropdown"
              aria-expanded="false"
              aria-label="User menu"
            >
              <i class="bi bi-person-circle me-1" aria-hidden="true"></i>
              {{ authService.currentUser()?.username }}
            </a>
            <ul class="dropdown-menu dropdown-menu-end" role="menu">
              <li>
                <a class="dropdown-item" routerLink="/member/profile" routerLinkActive="active" aria-current="page">
                  <i class="bi bi-person me-2" aria-hidden="true"></i>
                  Profile
                </a>
              </li>
              <li><hr class="dropdown-divider" /></li>
              <li>
                <button
                  class="dropdown-item text-danger"
                  (click)="signOut()"
                  type="button"
                >
                  <i class="bi bi-box-arrow-right me-2" aria-hidden="true"></i>
                  Sign Out
                </button>
              </li>
            </ul>
          </li>
        }
      </ul>
    </nav>
  </div>
</header>

<main class="container pt-5" role="main" id="mainContent">
  <router-outlet />
</main>

<footer class="footer mt-auto py-3 bg-light border-top" role="contentinfo">
  <div class="container text-center text-muted small">
    &copy; {{ currentYear }} Coworking Network. All rights reserved.
  </div>
</footer>
```

FILE: frontend/src/app/app.css

```css
:root {
  --bs-primary-rgb: 13, 110, 253;
}

html {
  position: relative;
  min-height: 100%;
}

body {
  margin-bottom: 60px;
}

.footer {
  position: absolute;
  bottom: 0;
  width: 100%;
  height: 60px;
  line-height: 60px;
}

.navbar-brand {
  font-size: 1.25rem;
}

.nav-link {
  font-weight: 500;
}

.dropdown-item {
  font-weight: 500;
}

.dropdown-item i {
  width: 1.25rem;
  text-align: center;
}

@media (max-width: 991.98px) {
  .navbar-nav .dropdown-menu {
    position: static;
    transform: none;
    border: none;
    box-shadow: none;
    padding-left: 1rem;
  }

  .navbar-nav .dropdown-menu-end {
    text-align: left;
  }
}

main {
  min-height: calc(100vh - 120px);
}

#mainContent {
  padding-top: 1rem;
  padding-bottom: 2rem;
}
```