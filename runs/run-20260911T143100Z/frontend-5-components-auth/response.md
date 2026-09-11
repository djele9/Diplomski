FILE: frontend/src/app/components/login/login.ts

```typescript
import { Component, inject, signal, computed, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators, FormGroup } from '@angular/forms';
import { Router, RouterLink, ActivatedRoute } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { AuthService } from '../../services/auth.service';
import { LoginData } from '../../models/auth.model';
import { FieldError, ErrorResponse } from '../../models/api.model';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './login.html',
  styleUrl: './login.css'
})
export class LoginComponent implements OnInit, OnDestroy {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  readonly returnUrl = signal<string>('/member/dashboard');
  readonly isLoading = signal(false);
  readonly serverError = signal<string | null>(null);
  readonly fieldErrors = signal<FieldError[]>([]);

  readonly loginForm: FormGroup = this.fb.nonNullable.group({
    username: ['', [Validators.required]],
    password: ['', [Validators.required]]
  });

  readonly usernameControl = this.loginForm.get('username')!;
  readonly passwordControl = this.loginForm.get('password')!;

  readonly showPassword = signal(false);

  ngOnInit(): void {
    this.route.queryParams.pipe(takeUntilDestroyed()).subscribe(params => {
      if (params['returnUrl']) {
        this.returnUrl.set(params['returnUrl']);
      }
    });
  }

  ngOnDestroy(): void {}

  togglePasswordVisibility(): void {
    this.showPassword.update(v => !v);
  }

  onSubmit(): void {
    if (this.loginForm.invalid) {
      this.loginForm.markAllAsTouched();
      return;
    }

    this.isLoading.set(true);
    this.serverError.set(null);
    this.fieldErrors.set([]);

    const data: LoginData = this.loginForm.getRawValue();

    this.authService.login(data).pipe(takeUntilDestroyed()).subscribe({
      next: () => {
        this.isLoading.set(false);
        this.router.navigateByUrl(this.returnUrl());
      },
      error: (err: ErrorResponse) => {
        this.isLoading.set(false);
        if (err.fieldErrors?.length) {
          this.fieldErrors.set(err.fieldErrors);
          this.applyFieldErrors(err.fieldErrors);
        } else if (err.message) {
          this.serverError.set(err.message);
        } else {
          this.serverError.set('An unexpected error occurred. Please try again.');
        }
      }
    });
  }

  private applyFieldErrors(errors: FieldError[]): void {
    errors.forEach(fe => {
      const control = this.loginForm.get(fe.field);
      if (control) {
        control.setErrors({ server: fe.message });
      }
    });
  }

  getFieldError(controlName: string): string | null {
    const control = this.loginForm.get(controlName);
    if (control?.touched && control?.errors) {
      if (control.errors['required']) {
        return `${controlName === 'username' ? 'Username' : 'Password'} is required.`;
      }
      if (control.errors['server']) {
        return control.errors['server'];
      }
    }
    return null;
  }
}
```

FILE: frontend/src/app/components/login/login.html

```html
<div class="container d-flex align-items-center justify-content-center min-vh-100 px-3">
  <div class="card shadow-sm w-100" style="max-width: 420px;">
    <div class="card-body p-4 p-md-5">
      <div class="text-center mb-4">
        <i class="bi bi-building text-primary" style="font-size: 2.5rem;"></i>
        <h2 class="mt-3 mb-1">Sign in</h2>
        <p class="text-muted small">Member or Space Manager access</p>
      </div>

      @if (serverError()) {
        <div class="alert alert-danger alert-dismissible fade show small py-2" role="alert">
          {{ serverError() }}
          <button type="button" class="btn-close btn-close-white" (click)="serverError.set(null)" aria-label="Close"></button>
        </div>
      }

      <form [formGroup]="loginForm" (ngSubmit)="onSubmit()" novalidate>
        <div class="mb-3">
          <label for="username" class="form-label fw-medium">Username</label>
          <input
            id="username"
            type="text"
            class="form-control"
            formControlName="username"
            autocomplete="username"
            [class.is-invalid]="usernameControl.touched && usernameControl.invalid"
            [disabled]="isLoading()"
            placeholder="Enter your username"
          />
          @if (getFieldError('username'); as err) {
            <div class="invalid-feedback d-block">{{ err }}</div>
          }
        </div>

        <div class="mb-3">
          <label for="password" class="form-label fw-medium">Password</label>
          <div class="input-group">
            <input
              id="password"
              [type]="showPassword() ? 'text' : 'password'"
              class="form-control"
              formControlName="password"
              autocomplete="current-password"
              [class.is-invalid]="passwordControl.touched && passwordControl.invalid"
              [disabled]="isLoading()"
              placeholder="Enter your password"
            />
            <button
              type="button"
              class="btn btn-outline-secondary"
              (click)="togglePasswordVisibility()"
              [disabled]="isLoading()"
              [attr.aria-label]="showPassword() ? 'Hide password' : 'Show password'"
              [attr.aria-pressed]="showPassword()"
            >
              <i class="bi" [class.bi-eye-fill]="showPassword()" [class.bi-eye-slash-fill]="!showPassword()"></i>
            </button>
          </div>
          @if (getFieldError('password'); as err) {
            <div class="invalid-feedback d-block">{{ err }}</div>
          }
        </div>

        <div class="d-grid gap-2 mt-4">
          <button
            type="submit"
            class="btn btn-primary btn-lg"
            [disabled]="isLoading() || loginForm.invalid"
          >
            @if (isLoading()) {
              <span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>
              Signing in…
            } @else {
              Sign in
            }
          </button>
        </div>
      </form>

      <div class="text-center mt-3">
        <a routerLink="/forgot-password" class="text-decoration-none small">Forgotten password?</a>
      </div>

      <hr class="my-3" />

      <div class="text-center">
        <p class="small text-muted mb-1">Administrator?</p>
        <a routerLink="/admin/login" class="btn btn-outline-secondary btn-sm">Administrator sign in</a>
      </div>
    </div>
  </div>
</div>
```

FILE: frontend/src/app/components/login/login.css

```css
.min-vh-100 {
  min-height: 100vh;
}

.card {
  border: none;
  border-radius: 0.75rem;
}

.form-control:focus {
  border-color: #86b7fe;
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
}

.btn-primary:disabled {
  opacity: 0.65;
}

.input-group .btn-outline-secondary {
  border-left: none;
  border-top-left-radius: 0;
  border-bottom-left-radius: 0;
}

@media (max-width: 375px) {
  .card-body {
    padding: 1.5rem !important;
  }
}
```

FILE: frontend/src/app/components/admin-login/admin-login.ts

```typescript
import { Component, inject, signal, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators, FormGroup } from '@angular/forms';
import { Router, RouterLink, ActivatedRoute } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { AuthService } from '../../services/auth.service';
import { LoginData } from '../../models/auth.model';
import { FieldError, ErrorResponse } from '../../models/api.model';

@Component({
  selector: 'app-admin-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './admin-login.html',
  styleUrl: './admin-login.css'
})
export class AdminLoginComponent implements OnInit, OnDestroy {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  readonly returnUrl = signal<string>('/admin/dashboard');
  readonly isLoading = signal(false);
  readonly serverError = signal<string | null>(null);
  readonly fieldErrors = signal<FieldError[]>([]);

  readonly loginForm: FormGroup = this.fb.nonNullable.group({
    username: ['', [Validators.required]],
    password: ['', [Validators.required]]
  });

  readonly usernameControl = this.loginForm.get('username')!;
  readonly passwordControl = this.loginForm.get('password')!;

  readonly showPassword = signal(false);

  ngOnInit(): void {
    this.route.queryParams.pipe(takeUntilDestroyed()).subscribe(params => {
      if (params['returnUrl']) {
        this.returnUrl.set(params['returnUrl']);
      }
    });
  }

  ngOnDestroy(): void {}

  togglePasswordVisibility(): void {
    this.showPassword.update(v => !v);
  }

  onSubmit(): void {
    if (this.loginForm.invalid) {
      this.loginForm.markAllAsTouched();
      return;
    }

    this.isLoading.set(true);
    this.serverError.set(null);
    this.fieldErrors.set([]);

    const data: LoginData = this.loginForm.getRawValue();

    this.authService.adminLogin(data).pipe(takeUntilDestroyed()).subscribe({
      next: () => {
        this.isLoading.set(false);
        this.router.navigateByUrl(this.returnUrl());
      },
      error: (err: ErrorResponse) => {
        this.isLoading.set(false);
        if (err.fieldErrors?.length) {
          this.fieldErrors.set(err.fieldErrors);
          this.applyFieldErrors(err.fieldErrors);
        } else if (err.message) {
          this.serverError.set(err.message);
        } else {
          this.serverError.set('An unexpected error occurred. Please try again.');
        }
      }
    });
  }

  private applyFieldErrors(errors: FieldError[]): void {
    errors.forEach(fe => {
      const control = this.loginForm.get(fe.field);
      if (control) {
        control.setErrors({ server: fe.message });
      }
    });
  }

  getFieldError(controlName: string): string | null {
    const control = this.loginForm.get(controlName);
    if (control?.touched && control?.errors) {
      if (control.errors['required']) {
        return `${controlName === 'username' ? 'Username' : 'Password'} is required.`;
      }
      if (control.errors['server']) {
        return control.errors['server'];
      }
    }
    return null;
  }
}
```

FILE: frontend/src/app/components/admin-login/admin-login.html

```html
<div class="container d-flex align-items-center justify-content-center min-vh-100 px-3">
  <div class="card shadow-sm w-100" style="max-width: 420px;">
    <div class="card-body p-4 p-md-5">
      <div class="text-center mb-4">
        <i class="bi bi-shield-lock text-danger" style="font-size: 2.5rem;"></i>
        <h2 class="mt-3 mb-1">Administrator sign in</h2>
        <p class="text-muted small">Restricted access — not linked from public pages</p>
      </div>

      @if (serverError()) {
        <div class="alert alert-danger alert-dismissible fade show small py-2" role="alert">
          {{ serverError() }}
          <button type="button" class="btn-close btn-close-white" (click)="serverError.set(null)" aria-label="Close"></button>
        </div>
      }

      <form [formGroup]="loginForm" (ngSubmit)="onSubmit()" novalidate>
        <div class="mb-3">
          <label for="username" class="form-label fw-medium">Username</label>
          <input
            id="username"
            type="text"
            class="form-control"
            formControlName="username"
            autocomplete="username"
            [class.is-invalid]="usernameControl.touched && usernameControl.invalid"
            [disabled]="isLoading()"
            placeholder="Enter administrator username"
          />
          @if (getFieldError('username'); as err) {
            <div class="invalid-feedback d-block">{{ err }}</div>
          }
        </div>

        <div class="mb-3">
          <label for="password" class="form-label fw-medium">Password</label>
          <div class="input-group">
            <input
              id="password"
              [type]="showPassword() ? 'text' : 'password'"
              class="form-control"
              formControlName="password"
              autocomplete="current-password"
              [class.is-invalid]="passwordControl.touched && passwordControl.invalid"
              [disabled]="isLoading()"
              placeholder="Enter administrator password"
            />
            <button
              type="button"
              class="btn btn-outline-secondary"
              (click)="togglePasswordVisibility()"
              [disabled]="isLoading()"
              [attr.aria-label]="showPassword() ? 'Hide password' : 'Show password'"
              [attr.aria-pressed]="showPassword()"
            >
              <i class="bi" [class.bi-eye-fill]="showPassword()" [class.bi-eye-slash-fill]="!showPassword()"></i>
            </button>
          </div>
          @if (getFieldError('password'); as err) {
            <div class="invalid-feedback d-block">{{ err }}</div>
          }
        </div>

        <div class="d-grid gap-2 mt-4">
          <button
            type="submit"
            class="btn btn-danger btn-lg"
            [disabled]="isLoading() || loginForm.invalid"
          >
            @if (isLoading()) {
              <span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>
              Signing in…
            } @else {
              Sign in as Administrator
            }
          </button>
        </div>
      </form>

      <div class="text-center mt-3">
        <a routerLink="/login" class="btn btn-link btn-sm p-0">← Back to public sign in</a>
      </div>
    </div>
  </div>
</div>
```

FILE: frontend/src/app/components/admin-login/admin-login.css

```css
.min-vh-100 {
  min-height: 100vh;
}

.card {
  border: none;
  border-radius: 0.75rem;
}

.form-control:focus {
  border-color: #86b7fe;
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
}

.btn-danger:disabled {
  opacity: 0.65;
}

.input-group .btn-outline-secondary {
  border-left: none;
  border-top-left-radius: 0;
  border-bottom-left-radius: 0;
}

@media (max-width: 375px) {
  .card-body {
    padding: 1.5rem !important;
  }
}
```

FILE: frontend/src/app/components/forgot-password/forgot-password.ts

```typescript
import { Component, inject, signal, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators, FormGroup } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { AuthService } from '../../services/auth.service';
import { RequestPasswordResetData } from '../../models/password-reset.model';
import { FieldError, ErrorResponse } from '../../models/api.model';

@Component({
  selector: 'app-forgot-password',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './forgot-password.html',
  styleUrl: './forgot-password.css'
})
export class ForgotPasswordComponent implements OnDestroy {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  readonly isLoading = signal(false);
  readonly serverError = signal<string | null>(null);
  readonly successMessage = signal<string | null>(null);
  readonly fieldErrors = signal<FieldError[]>([]);

  readonly resetForm: FormGroup = this.fb.nonNullable.group({
    identifier: ['', [Validators.required, Validators.email]]
  });

  readonly identifierControl = this.resetForm.get('identifier')!;

  ngOnDestroy(): void {}

  onSubmit(): void {
    if (this.resetForm.invalid) {
      this.resetForm.markAllAsTouched();
      return;
    }

    this.isLoading.set(true);
    this.serverError.set(null);
    this.successMessage.set(null);
    this.fieldErrors.set([]);

    const data: RequestPasswordResetData = this.resetForm.getRawValue();

    this.authService.requestPasswordReset(data).pipe(takeUntilDestroyed()).subscribe({
      next: (response) => {
        this.isLoading.set(false);
        this.successMessage.set(response.message || 'If an account exists for that identifier, a password reset link has been sent to the associated email address.');
        this.resetForm.reset();
      },
      error: (err: ErrorResponse) => {
        this.isLoading.set(false);
        if (err.fieldErrors?.length) {
          this.fieldErrors.set(err.fieldErrors);
          this.applyFieldErrors(err.fieldErrors);
        } else if (err.message) {
          this.serverError.set(err.message);
        } else {
          this.serverError.set('An unexpected error occurred. Please try again.');
        }
      }
    });
  }

  private applyFieldErrors(errors: FieldError[]): void {
    errors.forEach(fe => {
      const control = this.resetForm.get(fe.field);
      if (control) {
        control.setErrors({ server: fe.message });
      }
    });
  }

  getFieldError(controlName: string): string | null {
    const control = this.resetForm.get(controlName);
    if (control?.touched && control?.errors) {
      if (control.errors['required']) {
        return 'Email address or username is required.';
      }
      if (control.errors['email']) {
        return 'Enter a valid email address or username.';
      }
      if (control.errors['server']) {
        return control.errors['server'];
      }
    }
    return null;
  }
}
```

FILE: frontend/src/app/components/forgot-password/forgot-password.html

```html
<div class="container d-flex align-items-center justify-content-center min-vh-100 px-3">
  <div class="card shadow-sm w-100" style="max-width: 420px;">
    <div class="card-body p-4 p-md-5">
      <div class="text-center mb-4">
        <i class="bi bi-key text-primary" style="font-size: 2.5rem;"></i>
        <h2 class="mt-3 mb-1">Forgotten password?</h2>
        <p class="text-muted small">Enter your email address or username and we'll send you a link to reset your password.</p>
      </div>

      @if (serverError()) {
        <div class="alert alert-danger alert-dismissible fade show small py-2" role="alert">
          {{ serverError() }}
          <button type="button" class="btn-close btn-close-white" (click)="serverError.set(null)" aria-label="Close"></button>
        </div>
      }

      @if (successMessage()) {
        <div class="alert alert-success alert-dismissible fade show small py-2" role="alert">
          {{ successMessage() }}
          <button type="button" class="btn-close" (click)="successMessage.set(null)" aria-label="Close"></button>
        </div>
      }

      <form [formGroup]="resetForm" (ngSubmit)="onSubmit()" novalidate>
        <div class="mb-3">
          <label for="identifier" class="form-label fw-medium">Email address or username</label>
          <input
            id="identifier"
            type="text"
            class="form-control"
            formControlName="identifier"
            autocomplete="email"
            [class.is-invalid]="identifierControl.touched && identifierControl.invalid"
            [disabled]="isLoading()"
            placeholder="Enter your email or username"
          />
          @if (getFieldError('identifier'); as err) {
            <div class="invalid-feedback d-block">{{ err }}</div>
          }
        </div>

        <div class="d-grid gap-2 mt-4">
          <button
            type="submit"
            class="btn btn-primary btn-lg"
            [disabled]="isLoading() || resetForm.invalid"
          >
            @if (isLoading()) {
              <span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>
              Sending…
            } @else {
              Send reset link
            }
          </button>
        </div>
      </form>

      <div class="text-center mt-3">
        <a routerLink="/login" class="btn btn-link btn-sm p-0">← Back to sign in</a>
      </div>
    </div>
  </div>
</div>
```

FILE: frontend/src/app/components/forgot-password/forgot-password.css

```css
.min-vh-100 {
  min-height: 100vh;
}

.card {
  border: none;
  border-radius: 0.75rem;
}

.form-control:focus {
  border-color: #86b7fe;
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
}

.btn-primary:disabled {
  opacity: 0.65;
}

@media (max-width: 375px) {
  .card-body {
    padding: 1.5rem !important;
  }
}
```

FILE: frontend/src/app/components/reset-password/reset-password.ts

```typescript
import { Component, inject, signal, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators, FormGroup } from '@angular/forms';
import { Router, RouterLink, ActivatedRoute } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { AuthService } from '../../services/auth.service';
import { ConfirmPasswordResetData } from '../../models/password-reset.model';
import { FieldError, ErrorResponse } from '../../models/api.model';
import { VerifyPasswordResetTokenResponse } from '../../models/password-reset.model';

@Component({
  selector: 'app-reset-password',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './reset-password.html',
  styleUrl: './reset-password.css'
})
export class ResetPasswordComponent implements OnInit, OnDestroy {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  readonly token = signal<string>('');
  readonly isLoading = signal(false);
  readonly verifying = signal(true);
  readonly tokenValid = signal(false);
  readonly serverError = signal<string | null>(null);
  readonly successMessage = signal<string | null>(null);
  readonly fieldErrors = signal<FieldError[]>([]);

  readonly resetForm: FormGroup = this.fb.nonNullable.group({
    newPassword: ['', [
      Validators.required,
      Validators.minLength(8),
      Validators.maxLength(12),
      Validators.pattern(/^[A-Za-z]/),
      Validators.pattern(/.*[A-Z].*/),
      Validators.pattern(/.*\d.*/),
      Validators.pattern(/.*[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?].*/)
    ]],
    confirmPassword: ['', [Validators.required]]
  }, { validators: this.passwordsMatchValidator });

  readonly newPasswordControl = this.resetForm.get('newPassword')!;
  readonly confirmPasswordControl = this.resetForm.get('confirmPassword')!;

  readonly showNewPassword = signal(false);
  readonly showConfirmPassword = signal(false);

  ngOnInit(): void {
    this.route.paramMap.pipe(takeUntilDestroyed()).subscribe(params => {
      const token = params.get('token');
      if (token) {
        this.token.set(token);
        this.verifyToken(token);
      } else {
        this.verifying.set(false);
        this.tokenValid.set(false);
        this.serverError.set('Invalid reset link. No token provided.');
      }
    });
  }

  ngOnDestroy(): void {}

  private verifyToken(token: string): void {
    this.authService.verifyResetToken(token).pipe(takeUntilDestroyed()).subscribe({
      next: (response: VerifyPasswordResetTokenResponse) => {
        this.verifying.set(false);
        if (response.valid) {
          this.tokenValid.set(true);
        } else {
          this.tokenValid.set(false);
          this.serverError.set('This reset link is invalid or has already been used.');
        }
      },
      error: (err: ErrorResponse) => {
        this.verifying.set(false);
        this.tokenValid.set(false);
        if (err.status === 410) {
          this.serverError.set(err.message || 'This reset link has expired or has already been used. Please request a new one.');
        } else {
          this.serverError.set('An unexpected error occurred. Please request a new reset link.');
        }
      }
    });
  }

  private passwordsMatchValidator(group: FormGroup): { mismatch: boolean } | null {
    const newPass = group.get('newPassword')?.value;
    const confirmPass = group.get('confirmPassword')?.value;
    return newPass && confirmPass && newPass !== confirmPass ? { mismatch: true } : null;
  }

  toggleNewPasswordVisibility(): void {
    this.showNewPassword.update(v => !v);
  }

  toggleConfirmPasswordVisibility(): void {
    this.showConfirmPassword.update(v => !v);
  }

  onSubmit(): void {
    if (this.resetForm.invalid) {
      this.resetForm.markAllAsTouched();
      return;
    }

    this.isLoading.set(true);
    this.serverError.set(null);
    this.fieldErrors.set([]);

    const data: ConfirmPasswordResetData = this.resetForm.getRawValue();

    this.authService.confirmPasswordReset(this.token(), data).pipe(takeUntilDestroyed()).subscribe({
      next: (response) => {
        this.isLoading.set(false);
        this.successMessage.set(response.message || 'Your password has been reset successfully. You can now sign in with your new password.');
        this.resetForm.reset();
        this.tokenValid.set(false);
      },
      error: (err: ErrorResponse) => {
        this.isLoading.set(false);
        if (err.fieldErrors?.length) {
          this.fieldErrors.set(err.fieldErrors);
          this.applyFieldErrors(err.fieldErrors);
        } else if (err.message) {
          this.serverError.set(err.message);
        } else {
          this.serverError.set('An unexpected error occurred. Please try again.');
        }
      }
    });
  }

  private applyFieldErrors(errors: FieldError[]): void {
    errors.forEach(fe => {
      const control = this.resetForm.get(fe.field);
      if (control) {
        control.setErrors({ server: fe.message });
      }
    });
  }

  getFieldError(controlName: string): string | null {
    const control = this.resetForm.get(controlName);
    if (control?.touched && control?.errors) {
      if (control.errors['required']) {
        return controlName === 'newPassword' ? 'New password is required.' : 'Please confirm your new password.';
      }
      if (controlName === 'newPassword') {
        if (control.errors['minlength']) {
          return 'Password must be between 8 and 12 characters.';
        }
        if (control.errors['maxlength']) {
          return 'Password must be between 8 and 12 characters.';
        }
        if (control.errors['pattern']) {
          const value = control.value || '';
          if (!/^[A-Za-z]/.test(value)) {
            return 'Password must begin with a letter.';
          }
          if (!/[A-Z]/.test(value)) {
            return 'Password must contain at least one uppercase letter.';
          }
          if (!/\d/.test(value)) {
            return 'Password must contain at least one digit.';
          }
          if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(value)) {
            return 'Password must contain at least one special character.';
          }
        }
      }
      if (control.errors['server']) {
        return control.errors['server'];
      }
      if (controlName === 'confirmPassword' && this.resetForm.errors?.['mismatch'] && control.touched) {
        return 'The two passwords do not match.';
      }
    }
    return null;
  }

  getFormError(errorName: string): boolean {
    return this.resetForm.hasError(errorName) && (this.confirmPasswordControl.touched || this.newPasswordControl.touched);
  }
}
```

FILE: frontend/src/app/components/reset-password/reset-password.html

```html
<div class="container d-flex align-items-center justify-content-center min-vh-100 px-3">
  <div class="card shadow-sm w-100" style="max-width: 420px;">
    <div class="card-body p-4 p-md-5">
      @if (verifying()) {
        <div class="text-center py-4">
          <div class="spinner-border text-primary" role="status" aria-live="polite">
            <span class="visually-hidden">Verifying reset link…</span>
          </div>
          <p class="mt-2 text-muted small">Verifying your reset link…</p>
        </div>
      } @else if (!tokenValid()) {
        <div class="text-center py-4">
          <i class="bi bi-exclamation-triangle text-warning" style="font-size: 3rem;"></i>
          <h3 class="mt-3 mb-2">Invalid or expired link</h3>
          @if (serverError()) {
            <p class="text-muted small">{{ serverError() }}</p>
          } @else {
            <p class="text-muted small">This password reset link is invalid, has expired, or has already been used.</p>
          }
          <div class="mt-3">
            <a routerLink="/forgot-password" class="btn btn-primary">Request a new reset link</a>
          </div>
        </div>
      } @else {
        <div class="text-center mb-4">
          <i class="bi bi-key-fill text-primary" style="font-size: 2.5rem;"></i>
          <h2 class="mt-3 mb-1">Set new password</h2>
          <p class="text-muted small">Your new password must be 8–12 characters, start with a letter, and include uppercase, lowercase, a number, and a special character.</p>
        </div>

        @if (serverError()) {
          <div class="alert alert-danger alert-dismissible fade show small py-2" role="alert">
            {{ serverError() }}
            <button type="button" class="btn-close btn-close-white" (click)="serverError.set(null)" aria-label="Close"></button>
          </div>
        }

        @if (successMessage()) {
          <div class="alert alert-success alert-dismissible fade show small py-2" role="alert">
            {{ successMessage() }}
            <button type="button" class="btn-close" (click)="successMessage.set(null)" aria-label="Close"></button>
          </div>
        }

        <form [formGroup]="resetForm" (ngSubmit)="onSubmit()" novalidate>
          <div class="mb-3">
            <label for="newPassword" class="form-label fw-medium">New password</label>
            <div class="input-group">
              <input
                id="newPassword"
                [type]="showNewPassword() ? 'text' : 'password'"
                class="form-control"
                formControlName="newPassword"
                autocomplete="new-password"
                [class.is-invalid]="newPasswordControl.touched && newPasswordControl.invalid"
                [disabled]="isLoading()"
                placeholder="Enter new password"
              />
              <button
                type="button"
                class="btn btn-outline-secondary"
                (click)="toggleNewPasswordVisibility()"
                [disabled]="isLoading()"
                [attr.aria-label]="showNewPassword() ? 'Hide password' : 'Show password'"
                [attr.aria-pressed]="showNewPassword()"
              >
                <i class="bi" [class.bi-eye-fill]="showNewPassword()" [class.bi-eye-slash-fill]="!showNewPassword()"></i>
              </button>
            </div>
            @if (getFieldError('newPassword'); as err) {
              <div class="invalid-feedback d-block">{{ err }}</div>
            }
          </div>

          <div class="mb-3">
            <label for="confirmPassword" class="form-label fw-medium">Confirm new password</label>
            <div class="input-group">
              <input
                id="confirmPassword"
                [type]="showConfirmPassword() ? 'text' : 'password'"
                class="form-control"
                formControlName="confirmPassword"
                autocomplete="new-password"
                [class.is-invalid]="confirmPasswordControl.touched && confirmPasswordControl.invalid || getFormError('mismatch')"
                [disabled]="isLoading()"
                placeholder="Confirm new password"
              />
              <button
                type="button"
                class="btn btn-outline-secondary"
                (click)="toggleConfirmPasswordVisibility()"
                [disabled]="isLoading()"
                [attr.aria-label]="showConfirmPassword() ? 'Hide password' : 'Show password'"
                [attr.aria-pressed]="showConfirmPassword()"
              >
                <i class="bi" [class.bi-eye-fill]="showConfirmPassword()" [class.bi-eye-slash-fill]="!showConfirmPassword()"></i>
              </button>
            </div>
            @if (getFieldError('confirmPassword'); as err) {
              <div class="invalid-feedback d-block">{{ err }}</div>
            }
            @if (getFormError('mismatch') && !getFieldError('confirmPassword')) {
              <div class="invalid-feedback d-block">The two passwords do not match.</div>
            }
          </div>

          <div class="d-grid gap-2 mt-4">
            <button
              type="submit"
              class="btn btn-primary btn-lg"
              [disabled]="isLoading() || resetForm.invalid"
            >
              @if (isLoading()) {
                <span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>
                Resetting…
              } @else {
                Reset password
              }
            </button>
          </div>
        </form>

        <div class="text-center mt-3">
          <a routerLink="/login" class="btn btn-link btn-sm p-0">← Back to sign in</a>
        </div>
      }
    </div>
  </div>
</div>
```

FILE: frontend/src/app/components/reset-password/reset-password.css

```css
.min-vh-100 {
  min-height: 100vh;
}

.card {
  border: none;
  border-radius: 0.75rem;
}

.form-control:focus {
  border-color: #86b7fe;
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
}

.btn-primary:disabled {
  opacity: 0.65;
}

.input-group .btn-outline-secondary {
  border-left: none;
  border-top-left-radius: 0;
  border-bottom-left-radius: 0;
}

@media (max-width: 375px) {
  .card-body {
    padding: 1.5rem !important;
  }
}
```

FILE: frontend/src/app/components/register/register.ts

```typescript
import { Component, inject, signal, computed, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators, FormGroup, FormArray } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { AuthService } from '../../services/auth.service';
import { RegisterMemberData, RegisterManagerData } from '../../models/registration-request.model';
import { FieldError, ErrorResponse } from '../../models/api.model';
import { UserRole } from '../../models/user-role.enum';

type AccountType = 'member' | 'manager';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './register.html',
  styleUrl: './register.css'
})
export class RegisterComponent implements OnDestroy {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  readonly accountType = signal<AccountType>('member');
  readonly isLoading = signal(false);
  readonly serverError = signal<string | null>(null);
  readonly successMessage = signal<string | null>(null);
  readonly fieldErrors = signal<FieldError[]>([]);
  readonly previewImage = signal<string | null>(null);
  readonly selectedFile = signal<File | null>(null);

  readonly registerForm: FormGroup = this.fb.nonNullable.group({
    username: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(50), Validators.pattern(/^[a-zA-Z0-9._-]+$/)]],
    password: ['', [
      Validators.required,
      Validators.minLength(8),
      Validators.maxLength(12),
      Validators.pattern(/^[A-Za-z]/),
      Validators.pattern(/.*[A-Z].*/),
      Validators.pattern(/.*\d.*/),
      Validators.pattern(/.*[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?].*/)
    ]],
    firstName: ['', [Validators.required, Validators.maxLength(50)]],
    lastName: ['', [Validators.required, Validators.maxLength(50)]],
    phone: ['', [Validators.required, Validators.pattern(/^[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,3}[)]?[-\s\.]?[0-9]{4,10}$/)]],
    email: ['', [Validators.required, Validators.email, Validators.maxLength(100)]],
    companyName: [''],
    headquartersAddress: [''],
    companyNumber: ['', [Validators.pattern(/^\d{8}$/)]],
    taxId: ['', [Validators.pattern(/^[1-9]\d{8}$/)]]
  });

  readonly usernameControl = this.registerForm.get('username')!;
  readonly passwordControl = this.registerForm.get('password')!;
  readonly firstNameControl = this.registerForm.get('firstName')!;
  readonly lastNameControl = this.registerForm.get('lastName')!;
  readonly phoneControl = this.registerForm.get('phone')!;
  readonly emailControl = this.registerForm.get('email')!;
  readonly companyNameControl = this.registerForm.get('companyName')!;
  readonly headquartersAddressControl = this.registerForm.get('headquartersAddress')!;
  readonly companyNumberControl = this.registerForm.get('companyNumber')!;
  readonly taxIdControl = this.registerForm.get('taxId')!;

  readonly showPassword = signal(false);

  readonly managerFields = computed(() => [
    { control: this.companyNameControl, label: 'Company name', name: 'companyName', required: true },
    { control: this.headquartersAddressControl, label: 'Headquarters address', name: 'headquartersAddress', required: true },
    { control: this.companyNumberControl, label: 'Company number (8 digits)', name: 'companyNumber', required: true },
    { control: this.taxIdControl, label: 'Tax ID (9 digits, not starting with 0)', name: 'taxId', required: true }
  ]);

  ngOnDestroy(): void {}

  setAccountType(type: AccountType): void {
    this.accountType.set(type);
    this.serverError.set(null);
    this.successMessage.set(null);
    this.fieldErrors.set([]);
    this.clearManagerFieldsValidators();
    if (type === 'manager') {
      this.setManagerFieldsValidators();
    }
    this.registerForm.updateValueAndValidity();
  }

  private setManagerFieldsValidators(): void {
    this.companyNameControl.setValidators([Validators.required, Validators.maxLength(100)]);
    this.headquartersAddressControl.setValidators([Validators.required, Validators.maxLength(200)]);
    this.companyNumberControl.setValidators([Validators.required, Validators.pattern(/^\d{8}$/)]);
    this.taxIdControl.setValidators([Validators.required, Validators.pattern(/^[1-9]\d{8}$/)]);
  }

  private clearManagerFieldsValidators(): void {
    this.companyNameControl.clearValidators();
    this.headquartersAddressControl.clearValidators();
    this.companyNumberControl.clearValidators();
    this.taxIdControl.clearValidators();
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      const file = input.files[0];
      this.validateImageFile(file).then(valid => {
        if (valid) {
          this.selectedFile.set(file);
          const reader = new FileReader();
          reader.onload = (e) => {
            this.previewImage.set(e.target?.result as string);
          };
          reader.readAsDataURL(file);
        } else {
          input.value = '';
        }
      });
    }
  }

  private async validateImageFile(file: File): Promise<boolean> {
    if (!['image/jpeg', 'image/png'].includes(file.type)) {
      this.serverError.set('Only JPG and PNG images are accepted.');
      return false;
    }
    if (file.size > 5 * 1024 * 1024) {
      this.serverError.set('The uploaded file is too large. Maximum size is 5 MB.');
      return false;
    }
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => {
        if (img.width < 100 || img.width > 300 || img.height < 100 || img.height > 300) {
          this.serverError.set('The image must be between 100x100 and 300x300 pixels.');
          resolve(false);
        } else {
          this.serverError.set(null);
          resolve(true);
        }
      };
      img.onerror = () => {
        this.serverError.set('Invalid image file.');
        resolve(false);
      };
      img.src = URL.createObjectURL(file);
    });
  }

  removeImage(): void {
    this.previewImage.set(null);
    this.selectedFile.set(null);
    const fileInput = document.getElementById('profileImage') as HTMLInputElement;
    if (fileInput) {
      fileInput.value = '';
    }
  }

  togglePasswordVisibility(): void {
    this.showPassword.update(v => !v);
  }

  onSubmit(): void {
    if (this.registerForm.invalid) {
      this.registerForm.markAllAsTouched();
      return;
    }

    this.isLoading.set(true);
    this.serverError.set(null);
    this.fieldErrors.set([]);

    const formValue = this.registerForm.getRawValue();
    const baseData = {
      username: formValue.username,
      password: formValue.password,
      firstName: formValue.firstName,
      lastName: formValue.lastName,
      phone: formValue.phone,
      email: formValue.email,
      profileImage: this.previewImage() || undefined
    };

    let request$: any;
    if (this.accountType() === 'member') {
      const data: RegisterMemberData = baseData;
      request$ = this.authService.registerMember(data);
    } else {
      const data: RegisterManagerData = {
        ...baseData,
        companyName: formValue.companyName,
        headquartersAddress: formValue.headquartersAddress,
        companyNumber: formValue.companyNumber,
        taxId: formValue.taxId
      };
      request$ = this.authService.registerManager(data);
    }

    request$.pipe(takeUntilDestroyed()).subscribe({
      next: (response) => {
        this.isLoading.set(false);
        this.successMessage.set(response.message || 'Your registration request has been submitted and is awaiting approval.');
        this.registerForm.reset();
        this.previewImage.set(null);
        this.selectedFile.set(null);
      },
      error: (err: ErrorResponse) => {
        this.isLoading.set(false);
        if (err.fieldErrors?.length) {
          this.fieldErrors.set(err.fieldErrors);
          this.applyFieldErrors(err.fieldErrors);
        } else if (err.message) {
          this.serverError.set(err.message);
        } else {
          this.serverError.set('An unexpected error occurred. Please try again.');
        }
      }
    });
  }

  private applyFieldErrors(errors: FieldError[]): void {
    errors.forEach(fe => {
      const control = this.registerForm.get(fe.field);
      if (control) {
        control.setErrors({ server: fe.message });
      }
    });
  }

  getFieldError(controlName: string): string | null {
    const control = this.registerForm.get(controlName);
    if (control?.touched && control?.errors) {
      if (control.errors['required']) {
        const labels: Record<string, string> = {
          username: 'Username',
          password: 'Password',
          firstName: 'First name',
          lastName: 'Last name',
          phone: 'Contact phone',
          email: 'Email address',
          companyName: 'Company name',
          headquartersAddress: 'Headquarters address',
          companyNumber: 'Company number',
          taxId: 'Tax ID'
        };
        return `${labels[controlName] || controlName} is required.`;
      }
      if (control.errors['minlength']) {
        return 'Must be at least 3 characters.';
      }
      if (control.errors['maxlength']) {
        if (controlName === 'password') {
          return 'Password must be between 8 and 12 characters.';
        }
        return 'Value is too long.';
      }
      if (control.errors['pattern']) {
        if (controlName === 'username') {
          return 'Username may only contain letters, numbers, dots, underscores, and hyphens.';
        }
        if (controlName === 'password') {
          const value = control.value || '';
          if (!/^[A-Za-z]/.test(value)) {
            return 'Password must begin with a letter.';
          }
          if (!/[A-Z]/.test(value)) {
            return 'Password must contain at least one uppercase letter.';
          }
          if (!/\d/.test(value)) {
            return 'Password must contain at least one digit.';
          }
          if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(value)) {
            return 'Password must contain at least one special character.';
          }
        }
        if (controlName === 'email') {
          return 'Enter a valid email address.';
        }
        if (controlName === 'phone') {
          return 'Enter a valid contact phone number.';
        }
        if (controlName === 'companyNumber') {
          return 'Company number must be exactly 8 digits.';
        }
        if (controlName === 'taxId') {
          const value = control.value || '';
          if (!/^\d{9}$/.test(value)) {
            return 'Tax ID must be exactly 9 digits.';
          }
          if (/^0/.test(value)) {
            return 'Tax ID must not begin with zero.';
          }
        }
      }
      if (control.errors['email']) {
        return 'Enter a valid email address.';
      }
      if (control.errors['server']) {
        return control.errors['server'];
      }
    }
    return null;
  }

  getManagerFieldError(fieldName: string): string | null {
    return this.getFieldError(fieldName);
  }
}
```

FILE: frontend/src/app/components/register/register.html

```html
<div class="container py-4 px-3">
  <div class="row justify-content-center">
    <div class="col-12 col-md-10 col-lg-8">
      <div class="card shadow-sm">
        <div class="card-body p-4 p-md-5">
          <div class="text-center mb-4">
            <i class="bi bi-person-plus text-primary" style="font-size: 2.5rem;"></i>
            <h2 class="mt-3 mb-1">Create an account</h2>
            <p class="text-muted small">Choose your account type and fill in the details below.</p>
          </div>

          <div class="mb-4">
            <div class="btn-group w-100" role="group" aria-label="Account type selection">
              <button
                type="button"
                class="btn btn-outline-primary"
                [class.active]="accountType() === 'member'"
                [class.btn-primary]="accountType() === 'member'"
                (click)="setAccountType('member')"
                [disabled]="isLoading()"
              >
                <i class="bi bi-person me-1"></i> Member
              </button>
              <button
                type="button"
                class="btn btn-outline-primary"
                [class.active]="accountType() === 'manager'"
                [class.btn-primary]="accountType() === 'manager'"
                (click)="setAccountType('manager')"
                [disabled]="isLoading()"
              >
                <i class="bi bi-building me-1"></i> Space Manager
              </button>
            </div>
            <div class="form-text text-center mt-2">
              @if (accountType() === 'member') {
                Members can search and reserve workspaces.
              } @else {
                Space Managers publish and manage spaces on behalf of a company.
              }
            </div>
          </div>

          @if (serverError()) {
            <div class="alert alert-danger alert-dismissible fade show small py-2" role="alert">
              {{ serverError() }}
              <button type="button" class="btn-close btn-close-white" (click)="serverError.set(null)" aria-label="Close"></button>
            </div>
          }

          @if (successMessage()) {
            <div class="alert alert-success alert-dismissible fade show small py-2" role="alert">
              {{ successMessage() }}
              <button type="button" class="btn-close" (click)="successMessage.set(null)" aria-label="Close"></button>
            </div>
          }

          <form [formGroup]="registerForm" (ngSubmit)="onSubmit()" novalidate enctype="multipart/form-data">
            <div class="row g-3">
              <div class="col-12 col-md-6">
                <label for="username" class="form-label fw-medium">Username <span class="text-danger">*</span></label>
                <input
                  id="username"
                  type="text"
                  class="form-control"
                  formControlName="username"
                  autocomplete="username"
                  [class.is-invalid]="usernameControl.touched && usernameControl.invalid"
                  [disabled]="isLoading()"
                  placeholder="Enter username"
                />
                @if (getFieldError('username'); as err) {
                  <div class="invalid-feedback d-block">{{ err }}</div>
                }
              </div>

              <div class="col-12 col-md-6">
                <label for="email" class="form-label fw-medium">Email address <span class="text-danger">*</span></label>
                <input
                  id="email"
                  type="email"
                  class="form-control"
                  formControlName="email"
                  autocomplete="email"
                  [class.is-invalid]="emailControl.touched && emailControl.invalid"
                  [disabled]="isLoading()"
                  placeholder="Enter email"
                />
                @if (getFieldError('email'); as err) {
                  <div class="invalid-feedback d-block">{{ err }}</div>
                }
              </div>

              <div class="col-12 col-md-6">
                <label for="firstName" class="form-label fw-medium">First name <span class="text-danger">*</span></label>
                <input
                  id="firstName"
                  type="text"
                  class="form-control"
                  formControlName="firstName"
                  autocomplete="given-name"
                  [class.is-invalid]="firstNameControl.touched && firstNameControl.invalid"
                  [disabled]="isLoading()"
                  placeholder="Enter first name"
                />
                @if (getFieldError('firstName'); as err) {
                  <div class="invalid-feedback d-block">{{ err }}</div>
                }
              </div>

              <div class="col-12 col-md-6">
                <label for="lastName" class="form-label fw-medium">Last name <span class="text-danger">*</span></label>
                <input
                  id="lastName"
                  type="text"
                  class="form-control"
                  formControlName="lastName"
                  autocomplete="family-name"
                  [class.is-invalid]="lastNameControl.touched && lastNameControl.invalid"
                  [disabled]="isLoading()"
                  placeholder="Enter last name"
                />
                @if (getFieldError('lastName'); as err) {
                  <div class="invalid-feedback d-block">{{ err }}</div>
                }
              </div>

              <div class="col-12 col-md-6">
                <label for="phone" class="form-label fw-medium">Contact phone <span class="text-danger">*</span></label>
                <input
                  id="phone"
                  type="tel"
                  class="form-control"
                  formControlName="phone"
                  autocomplete="tel"
                  [class.is-invalid]="phoneControl.touched && phoneControl.invalid"
                  [disabled]="isLoading()"
                  placeholder="+381 64 123 4567"
                />
                @if (getFieldError('phone'); as err) {
                  <div class="invalid-feedback d-block">{{ err }}</div>
                }
              </div>

              <div class="col-12 col-md-6">
                <label for="password" class="form-label fw-medium">Password <span class="text-danger">*</span></label>
                <div class="input-group">
                  <input
                    id="password"
                    [type]="showPassword() ? 'text' : 'password'"
                    class="form-control"
                    formControlName="password"
                    autocomplete="new-password"
                    [class.is-invalid]="passwordControl.touched && passwordControl.invalid"
                    [disabled]="isLoading()"
                    placeholder="Enter password"
                  />
                  <button
                    type="button"
                    class="btn btn-outline-secondary"
                    (click)="togglePasswordVisibility()"
                    [disabled]="isLoading()"
                    [attr.aria-label]="showPassword() ? 'Hide password' : 'Show password'"
                    [attr.aria-pressed]="showPassword()"
                  >
                    <i class="bi" [class.bi-eye-fill]="showPassword()" [class.bi-eye-slash-fill]="!showPassword()"></i>
                  </button>
                </div>
                @if (getFieldError('password'); as err) {
                  <div class="invalid-feedback d-block">{{ err }}</div>
                }
              </div>
            </div>

            @if (accountType() === 'manager') {
              <hr class="my-3" />
              <h5 class="mb-3"><i class="bi bi-building me-2"></i>Company details</h5>
              <div class="row g-3">
                <div class="col-12">
                  <label for="companyName" class="form-label fw-medium">Company name <span class="text-danger">*</span></label>
                  <input
                    id="companyName"
                    type="text"
                    class="form-control"
                    formControlName="companyName"
                    [class.is-invalid]="companyNameControl.touched && companyNameControl.invalid"
                    [disabled]="isLoading()"
                    placeholder="Enter company name"
                  />
                  @if (getManagerFieldError('companyName'); as err) {
                    <div class="invalid-feedback d-block">{{ err }}</div>
                  }
                </div>

                <div class="col-12">
                  <label for="headquartersAddress" class="form-label fw-medium">Headquarters address <span class="text-danger">*</span></label>
                  <input
                    id="headquartersAddress"
                    type="text"
                    class="form-control"
                    formControlName="headquartersAddress"
                    [class.is-invalid]="headquartersAddressControl.touched && headquartersAddressControl.invalid"
                    [disabled]="isLoading()"
                    placeholder="Enter headquarters address"
                  />
                  @if (getManagerFieldError('headquartersAddress'); as err) {
                    <div class="invalid-feedback d-block">{{ err }}</div>
                  }
                </div>

                <div class="col-12 col-md-6">
                  <label for="companyNumber" class="form-label fw-medium">Company number <span class="text-danger">*</span></label>
                  <input
                    id="companyNumber"
                    type="text"
                    class="form-control"
                    formControlName="companyNumber"
                    [class.is-invalid]="companyNumberControl.touched && companyNumberControl.invalid"
                    [disabled]="isLoading()"
                    placeholder="8 digits (e.g., 12345678)"
                    maxlength="8"
                  />
                  @if (getManagerFieldError('companyNumber'); as err) {
                    <div class="invalid-feedback d-block">{{ err }}</div>
                  }
                </div>

                <div class="col-12 col-md-6">
                  <label for="taxId" class="form-label fw-medium">Tax ID <span class="text-danger">*</span></label>
                  <input
                    id="taxId"
                    type="text"
                    class="form-control"
                    formControlName="taxId"
                    [class.is-invalid]="taxIdControl.touched && taxIdControl.invalid"
                    [disabled]="isLoading()"
                    placeholder="9 digits, not starting with 0"
                    maxlength="9"
                  />
                  @if (getManagerFieldError('taxId'); as err) {
                    <div class="invalid-feedback d-block">{{ err }}</div>
                  }
                </div>
              </div>
            }

            <hr class="my-3" />
            <h5 class="mb-3"><i class="bi bi-image me-2"></i>Profile image (optional)</h5>
            <div class="mb-3">
              <label for="profileImage" class="form-label fw-medium">Upload a photo (JPG or PNG, 100×100 to 300×300 px)</label>
              <div class="d-flex align-items-center gap-3">
                <div class="position-relative" style="width: 80px; height: 80px; flex-shrink: 0;">
                  @if (previewImage()) {
                    <img [src]="previewImage()" alt="Profile preview" class="rounded border" style="width: 100%; height: 100%; object-fit: cover;" />
                    <button
                      type="button"
                      class="btn btn-sm btn-danger position-absolute top-0 end-0 m-1"
                      (click)="removeImage()"
                      [disabled]="isLoading()"
                      aria-label="Remove image"
                    >
                      <i class="bi bi-x"></i>
                    </button>
                  } @else {
                    <div class="rounded border d-flex align-items-center justify-content-center bg-light" style="width: 100%; height: 100%;">
                      <i class="bi bi-person text-muted" style="font-size: 2rem;"></i>
                    </div>
                  }
                </div>
                <div class="flex-grow-1">
                  <input
                    id="profileImage"
                    type="file"
                    class="form-control"
                    accept="image/jpeg,image/png"
                    (change)="onFileSelected($event)"
                    [disabled]="isLoading()"
                    aria-describedby="profileImageHelp"
                  />
                  <div id="profileImageHelp" class="form-text">JPG or PNG, 100×100 to 300×300 pixels, max 5 MB.</div>
                </div>
              </div>
            </div>

            <div class="d-grid gap-2 mt-4">
              <button
                type="submit"
                class="btn btn-primary btn-lg"
                [disabled]="isLoading() || registerForm.invalid"
              >
                @if (isLoading()) {
                  <span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>
                  Submitting…
                } @else {
                  Submit registration
                }
              </button>
            </div>
          </form>

          <div class="text-center mt-3">
            <a routerLink="/login" class="btn btn-link btn-sm p-0">Already have an account? Sign in</a>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
```

FILE: frontend/src/app/components/register/register.css

```css
.min-vh-100 {
  min-height: 100vh;
}

.card {
  border: none;
  border-radius: 0.75rem;
}

.form-control:focus {
  border-color: #86b7fe;
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
}

.btn-primary:disabled {
  opacity: 0.65;
}

.input-group .btn-outline-secondary {
  border-left: none;
  border-top-left-radius: 0;
  border-bottom-left-radius: 0;
}

.btn-group .btn.active {
  color: #fff;
}

@media (max-width: 375px) {
  .card-body {
    padding: 1.5rem !important;
  }

  .btn-group .btn {
    padding: 0.5rem 0.75rem;
    font-size: 0.875rem;
  }
}
```