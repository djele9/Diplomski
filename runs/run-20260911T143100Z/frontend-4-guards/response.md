FILE: frontend/src/app/guards/auth.guard.ts

```typescript
// Guards are a convenience for the user, not a security boundary.
// Anyone can edit the bundle. The server is what enforces access,
// and the specification's authorization scenarios test the server
// independently of anything the browser does.

import { inject } from '@angular/core';
import { CanActivateFn, Router, UrlTree } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = (route, state): boolean | UrlTree => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isAuthenticated()) {
    return true;
  }

  const returnUrl = state.url;
  return router.createUrlTree(['/login'], { queryParams: { returnUrl } });
};
```

FILE: frontend/src/app/guards/role.guard.ts

```typescript
// Guards are a convenience for the user, not a security boundary.
// Anyone can edit the bundle. The server is what enforces access,
// and the specification's authorization scenarios test the server
// independently of anything the browser does.

import { inject } from '@angular/core';
import { CanActivateFn, Router, UrlTree } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { UserRole } from '../models/user-role.enum';

export const roleGuard: CanActivateFn = (route, state): boolean | UrlTree => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (!authService.isAuthenticated()) {
    const returnUrl = state.url;
    return router.createUrlTree(['/login'], { queryParams: { returnUrl } });
  }

  const allowedRoles = route.data['roles'] as UserRole[] | undefined;

  if (!allowedRoles || allowedRoles.length === 0) {
    return true;
  }

  const userRole = authService.userRole();

  if (userRole && allowedRoles.includes(userRole)) {
    return true;
  }

  return router.createUrlTree(['/']);
};
```

FILE: frontend/src/app/guards/guest.guard.ts

```typescript
// Guards are a convenience for the user, not a security boundary.
// Anyone can edit the bundle. The server is what enforces access,
// and the specification's authorization scenarios test the server
// independently of anything the browser does.

import { inject } from '@angular/core';
import { CanActivateFn, Router, UrlTree } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const guestGuard: CanActivateFn = (): boolean | UrlTree => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (!authService.isAuthenticated()) {
    return true;
  }

  const userRole = authService.userRole();

  if (userRole === 'ADMIN') {
    return router.createUrlTree(['/admin/dashboard']);
  }

  if (userRole === 'MANAGER') {
    return router.createUrlTree(['/manager/dashboard']);
  }

  return router.createUrlTree(['/member/dashboard']);
};
```

FILE: frontend/src/app/interceptors/auth.interceptor.ts

```typescript
import { inject } from '@angular/core';
import { HttpInterceptorFn, HttpRequest, HttpHandlerFn } from '@angular/common/http';
import { AuthService } from '../services/auth.service';
import { environment } from '../../environments/environment';

export const authInterceptor: HttpInterceptorFn = (req: HttpRequest<unknown>, next: HttpHandlerFn) => {
  const authService = inject(AuthService);
  const apiUrl = environment.apiUrl;

  if (!req.url.startsWith(apiUrl)) {
    return next(req);
  }

  const accessToken = authService.getAccessToken();

  if (!accessToken) {
    return next(req);
  }

  const authReq = req.clone({
    setHeaders: {
      Authorization: `Bearer ${accessToken}`
    }
  });

  return next(authReq);
};
```

FILE: frontend/src/app/interceptors/error.interceptor.ts

```typescript
import { inject } from '@angular/core';
import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { catchError, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';
import { Router } from '@angular/router';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 401) {
        authService.clearSession();
        router.navigate(['/login'], { queryParams: { returnUrl: router.url } });
        return throwError(() => new Error('Your session has expired. Please sign in again.'));
      }

      let message = 'An unexpected error occurred.';

      if (error.error?.message) {
        message = error.error.message;
      } else if (error.status === 403) {
        message = 'You do not have permission to perform this action.';
      } else if (error.status === 404) {
        message = 'The requested resource was not found.';
      } else if (error.status === 409) {
        message = error.error?.message || 'A conflict occurred.';
      } else if (error.status === 400 && error.error?.fieldErrors?.length) {
        message = error.error.fieldErrors.map((fe: { field: string; message: string }) => `${fe.field}: ${fe.message}`).join('; ');
      } else if (error.status === 0) {
        message = 'Unable to reach the server. Please check your connection.';
      } else if (error.status >= 500) {
        message = 'A server error occurred. Please try again later.';
      }

      return throwError(() => new Error(message));
    })
  );
};
```