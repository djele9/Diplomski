FILE: frontend/src/app/components/register/register.ts

```typescript
import { Component, effect, inject, signal, OnInit, takeUntilDestroyed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators, AbstractControl, ValidationErrors } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { RegistrationService } from '../../services/registration.service';
import { UserRole } from '../../models/user-role.enum';
import { RegistrationResponse } from '../../models/registration-request.model';
import { ErrorResponse } from '../../models/api.model';

type AccountType = 'MEMBER' | 'MANAGER';

interface RegisterFormValue {
  username: string;
  password: string;
  confirmPassword: string;
  firstName: string;
  lastName: string;
  phone: string;
  email: string;
  companyName: string;
  headquartersAddress: string;
  companyNumber: string;
  taxId: string;
}

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './register.html',
  styleUrl: './register.css'
})
export class RegisterComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly registrationService = inject(RegistrationService);
  private readonly router = inject(Router);

  readonly accountType = signal<AccountType>('MEMBER');
  readonly isSubmitting = signal(false);
  readonly submitSuccess = signal(false);
  readonly submitError = signal<string | null>(null);
  readonly fieldErrors = signal<Record<string, string>>({});
  readonly previewImage = signal<string | null>(null);
  readonly selectedFile = signal<File | null>(null);
  readonly imageError = signal<string | null>(null);

  readonly form = this.fb.nonNullable.group({
    username: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(50)]],
    password: ['', [Validators.required, this.passwordPolicyValidator]],
    confirmPassword: ['', [Validators.required]],
    firstName: ['', [Validators.required, Validators.maxLength(100)]],
    lastName: ['', [Validators.required, Validators.maxLength(100)]],
    phone: ['', [Validators.required, this.phoneValidator]],
    email: ['', [Validators.required, Validators.email]],
    companyName: [''],
    headquartersAddress: [''],
    companyNumber: ['', [this.companyNumberValidator]],
    taxId: ['', [this.taxIdValidator]]
  }, { validators: this.passwordMatchValidator });

  readonly passwordRequirements = [
    { label: '8–12 characters', test: (v: string) => v.length >= 8 && v.length <= 12 },
    { label: 'At least one uppercase letter', test: (v: string) => /[A-Z]/.test(v) },
    { label: 'At least one digit', test: (v: string) => /\d/.test(v) },
    { label: 'At least one special character', test: (v: string) => /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(v) },
    { label: 'Must begin with a letter', test: (v: string) => /^[A-Za-z]/.test(v) }
  ];

  ngOnInit(): void {
    this.updateCompanyValidators();
    this.form.controls.accountType?.valueChanges?.subscribe(() => this.updateCompanyValidators());
  }

  private updateCompanyValidators(): void {
    const isManager = this.accountType() === 'MANAGER';
    const companyFields = ['companyName', 'headquartersAddress', 'companyNumber', 'taxId'] as const;

    companyFields.forEach(field => {
      const control = this.form.controls[field];
      if (isManager) {
        control.setValidators([Validators.required, ...control.validator ? [control.validator] : []]);
      } else {
        control.clearValidators();
        control.setValue('');
      }
      control.updateValueAndValidity({ emitEvent: false });
    });
  }

  private passwordPolicyValidator = (control: AbstractControl): ValidationErrors | null => {
    const value = control.value as string;
    if (!value) return null;

    const errors: ValidationErrors = {};
    if (value.length < 8 || value.length > 12) errors['length'] = true;
    if (!/[A-Z]/.test(value)) errors['uppercase'] = true;
    if (!/\d/.test(value)) errors['digit'] = true;
    if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(value)) errors['special'] = true;
    if (!/^[A-Za-z]/.test(value)) errors['startsWithLetter'] = true;

    return Object.keys(errors).length ? errors : null;
  };

  private phoneValidator = (control: AbstractControl): ValidationErrors | null => {
    const value = control.value as string;
    if (!value) return null;
    const cleaned = value.replace(/[\s\-\(\)]/g, '');
    if (!/^\+?\d{8,15}$/.test(cleaned)) return { phone: true };
    return null;
  };

  private companyNumberValidator = (control: AbstractControl): ValidationErrors | null => {
    const value = control.value as string;
    if (!value) return null;
    if (!/^\d{8}$/.test(value)) return { companyNumber: true };
    return null;
  };

  private taxIdValidator = (control: AbstractControl): ValidationErrors | null => {
    const value = control.value as string;
    if (!value) return null;
    if (!/^\d{9}$/.test(value)) return { taxIdLength: true };
    if (value.startsWith('0')) return { taxIdLeadingZero: true };
    return null;
  };

  private passwordMatchValidator = (group: AbstractControl): ValidationErrors | null => {
    const password = group.get('password')?.value;
    const confirm = group.get('confirmPassword')?.value;
    return password && confirm && password !== confirm ? { passwordMismatch: true } : null;
  };

  onAccountTypeChange(type: AccountType): void {
    this.accountType.set(type);
    this.submitError.set(null);
    this.fieldErrors.set({});
    this.updateCompanyValidators();
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    this.imageError.set(null);

    if (!file) {
      this.selectedFile.set(null);
      this.previewImage.set(null);
      return;
    }

    if (!['image/jpeg', 'image/png'].includes(file.type)) {
      this.imageError.set('Only JPG and PNG images are accepted.');
      this.selectedFile.set(null);
      this.previewImage.set(null);
      input.value = '';
      return;
    }

    const img = new Image();
    const url = URL.createObjectURL(file);
    img.onload = () => {
      URL.revokeObjectURL(url);
      if (img.width < 100 || img.width > 300 || img.height < 100 || img.height > 300) {
        this.imageError.set('The image must be between 100x100 and 300x300 pixels.');
        this.selectedFile.set(null);
        this.previewImage.set(null);
      } else {
        this.selectedFile.set(file);
        this.previewImage.set(url);
      }
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      this.imageError.set('Invalid image file.');
      this.selectedFile.set(null);
      this.previewImage.set(null);
    };
    img.src = url;
  }

  removeImage(): void {
    this.selectedFile.set(null);
    this.previewImage.set(null);
    this.imageError.set(null);
    const fileInput = document.getElementById('profileImage') as HTMLInputElement;
    if (fileInput) fileInput.value = '';
  }

  getFieldError(fieldName: string): string | null {
    const control = this.form.get(fieldName);
    if (control?.touched && control?.invalid) {
      const errors = control.errors;
      if (errors) {
        if (errors['required']) return this.getRequiredMessage(fieldName);
        if (errors['minlength']) return `${this.getFieldLabel(fieldName)} must be at least ${errors['minlength'].requiredLength} characters.`;
        if (errors['maxlength']) return `${this.getFieldLabel(fieldName)} must not exceed ${errors['maxlength'].requiredLength} characters.`;
        if (errors['email']) return 'Enter a valid email address.';
        if (errors['phone']) return 'Enter a valid contact phone number.';
        if (errors['companyNumber']) return 'Company number must be exactly 8 digits.';
        if (errors['taxIdLength']) return 'Tax ID must be exactly 9 digits.';
        if (errors['taxIdLeadingZero']) return 'Tax ID must not begin with zero.';
        if (errors['length']) return 'Password must be between 8 and 12 characters.';
        if (errors['uppercase']) return 'Password must contain at least one uppercase letter.';
        if (errors['digit']) return 'Password must contain at least one digit.';
        if (errors['special']) return 'Password must contain at least one special character.';
        if (errors['startsWithLetter']) return 'Password must begin with a letter.';
      }
    }
    if (this.form.hasError('passwordMismatch') && fieldName === 'confirmPassword' && this.form.get('confirmPassword')?.touched) {
      return 'The two passwords do not match.';
    }
    return this.fieldErrors()[fieldName] ?? null;
  }

  private getRequiredMessage(fieldName: string): string {
    const messages: Record<string, string> = {
      username: 'Username is required.',
      password: 'Password is required.',
      confirmPassword: 'Please confirm your password.',
      firstName: 'First name is required.',
      lastName: 'Last name is required.',
      phone: 'Contact phone is required.',
      email: 'Email address is required.',
      companyName: 'Company name is required.',
      headquartersAddress: 'Headquarters address is required.',
      companyNumber: 'Company number is required.',
      taxId: 'Tax ID is required.'
    };
    return messages[fieldName] ?? 'This field is required.';
  }

  private getFieldLabel(fieldName: string): string {
    const labels: Record<string, string> = {
      username: 'Username',
      password: 'Password',
      firstName: 'First name',
      lastName: 'Last name',
      phone: 'Phone',
      email: 'Email',
      companyName: 'Company name',
      headquartersAddress: 'Headquarters address',
      companyNumber: 'Company number',
      taxId: 'Tax ID'
    };
    return labels[fieldName] ?? fieldName;
  }

  async onSubmit(): Promise<void> {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.isSubmitting.set(true);
    this.submitError.set(null);
    this.fieldErrors.set({});

    const value = this.form.getRawValue();
    const formData = new FormData();

    const baseData = {
      username: value.username,
      password: value.password,
      firstName: value.firstName,
      lastName: value.lastName,
      phone: value.phone,
      email: value.email
    };

    if (this.accountType() === 'MEMBER') {
      Object.entries(baseData).forEach(([key, val]) => formData.append(key, val));
      if (this.selectedFile()) {
        formData.append('profileImage', this.selectedFile()!);
      }

      this.registrationService.registerMember(baseData as any).pipe(takeUntilDestroyed()).subscribe({
        next: (response: RegistrationResponse) => this.handleSuccess(response),
        error: (err: ErrorResponse) => this.handleError(err)
      });
    } else {
      const managerData = {
        ...baseData,
        companyName: value.companyName,
        headquartersAddress: value.headquartersAddress,
        companyNumber: value.companyNumber,
        taxId: value.taxId
      };
      Object.entries(managerData).forEach(([key, val]) => formData.append(key, val));
      if (this.selectedFile()) {
        formData.append('profileImage', this.selectedFile()!);
      }

      this.registrationService.registerManager(managerData as any).pipe(takeUntilDestroyed()).subscribe({
        next: (response: RegistrationResponse) => this.handleSuccess(response),
        error: (err: ErrorResponse) => this.handleError(err)
      });
    }
  }

  private handleSuccess(response: RegistrationResponse): void {
    this.isSubmitting.set(false);
    this.submitSuccess.set(true);
    this.form.reset();
    this.removeImage();
    this.accountType.set('MEMBER');
  }

  private handleError(err: ErrorResponse): void {
    this.isSubmitting.set(false);
    if (err.fieldErrors?.length) {
      const errors: Record<string, string> = {};
      err.fieldErrors.forEach(fe => errors[fe.field] = fe.message);
      this.fieldErrors.set(errors);
      this.form.markAllAsTouched();
    } else if (err.message) {
      this.submitError.set(err.message);
    } else {
      this.submitError.set('Registration failed. Please try again.');
    }
  }

  getPasswordRequirementClass(req: { test: (v: string) => boolean }, index: number): string {
    const value = this.form.get('password')?.value ?? '';
    return req.test(value) ? 'text-success' : 'text-muted';
  }

  getPasswordRequirementIcon(req: { test: (v: string) => boolean }, index: number): string {
    const value = this.form.get('password')?.value ?? '';
    return req.test(value) ? 'bi-check-circle-fill' : 'bi-x-circle-fill';
  }
}
```

FILE: frontend/src/app/components/register/register.html

```html
<div class="container py-5">
  <div class="row justify-content-center">
    <div class="col-12 col-md-10 col-lg-8 col-xl-7">
      <div class="card shadow-sm border-0">
        <div class="card-header bg-white border-0 pb-0">
          <h1 class="h3 mb-1">Create an account</h1>
          <p class="text-muted mb-0">Choose your account type and fill in your details.</p>
        </div>
        <div class="card-body">
          @if (submitSuccess()) {
            <div class="alert alert-success border-0 shadow-sm" role="alert">
              <i class="bi bi-check-circle-fill me-2"></i>
              <strong>Registration submitted!</strong>
              <p class="mb-0 mt-2">Your registration request has been submitted and is awaiting approval. You will be able to sign in once an administrator approves your account.</p>
            </div>
            <div class="text-center mt-3">
              <a routerLink="/login" class="btn btn-primary">Go to sign in</a>
            </div>
          } @else {
            <div class="mb-4">
              <label class="form-label fw-semibold">Account type</label>
              <div class="btn-group w-100" role="group" aria-label="Account type selection">
                <button
                  type="button"
                  class="btn btn-outline-primary"
                  [class.active]="accountType() === 'MEMBER'"
                  [class.btn-primary]="accountType() === 'MEMBER'"
                  (click)="onAccountTypeChange('MEMBER')"
                  aria-pressed="accountType() === 'MEMBER'">
                  <i class="bi bi-person me-1"></i> Member
                </button>
                <button
                  type="button"
                  class="btn btn-outline-primary"
                  [class.active]="accountType() === 'MANAGER'"
                  [class.btn-primary]="accountType() === 'MANAGER'"
                  (click)="onAccountTypeChange('MANAGER')"
                  aria-pressed="accountType() === 'MANAGER'">
                  <i class="bi bi-building me-1"></i> Space Manager
                </button>
              </div>
              <div class="form-text mt-2">
                @if (accountType() === 'MEMBER') {
                  <i class="bi bi-info-circle me-1"></i> Members can search and reserve workspaces after approval.
                } @else {
                  <i class="bi bi-info-circle me-1"></i> Space Managers publish and manage spaces for their company after approval.
                }
              </div>
            </div>

            <form [formGroup]="form" (ngSubmit)="onSubmit()" novalidate>
              <div class="row g-3">
                <div class="col-12 col-md-6">
                  <label for="username" class="form-label fw-semibold">Username <span class="text-danger">*</span></label>
                  <input
                    type="text"
                    id="username"
                    class="form-control"
                    formControlName="username"
                    placeholder="Choose a username"
                    autocomplete="username"
                    [class.is-invalid]="form.get('username')?.touched && form.get('username')?.invalid"
                    [disabled]="isSubmitting()" />
                  @if (getFieldError('username'); as err) {
                    <div class="invalid-feedback d-block">{{ err }}</div>
                  }
                </div>

                <div class="col-12 col-md-6">
                  <label for="email" class="form-label fw-semibold">Email <span class="text-danger">*</span></label>
                  <input
                    type="email"
                    id="email"
                    class="form-control"
                    formControlName="email"
                    placeholder="you@example.com"
                    autocomplete="email"
                    [class.is-invalid]="form.get('email')?.touched && form.get('email')?.invalid"
                    [disabled]="isSubmitting()" />
                  @if (getFieldError('email'); as err) {
                    <div class="invalid-feedback d-block">{{ err }}</div>
                  }
                </div>

                <div class="col-12 col-md-6">
                  <label for="password" class="form-label fw-semibold">Password <span class="text-danger">*</span></label>
                  <div class="input-group">
                    <input
                      type="password"
                      id="password"
                      class="form-control"
                      formControlName="password"
                      placeholder="Create a password"
                      autocomplete="new-password"
                      [class.is-invalid]="form.get('password')?.touched && form.get('password')?.invalid"
                      [disabled]="isSubmitting()" />
                    <button
                      type="button"
                      class="btn btn-outline-secondary"
                      (click)="form.get('password')?.setValue('')"
                      [disabled]="isSubmitting()"
                      aria-label="Clear password">
                      <i class="bi bi-x-lg"></i>
                    </button>
                  </div>
                  @if (getFieldError('password'); as err) {
                    <div class="invalid-feedback d-block">{{ err }}</div>
                  }
                  @if (form.get('password')?.value) {
                    <div class="mt-2">
                      <small class="fw-semibold d-block mb-1">Password requirements:</small>
                      <ul class="list-unstyled small mb-0 ps-3">
                        @for (req of passwordRequirements; track $index) {
                          <li class="d-flex align-items-center gap-2 mb-1">
                            <i class="bi" [class]="getPasswordRequirementIcon(req, $index)" [class]="getPasswordRequirementClass(req, $index)"></i>
                            <span [class]="getPasswordRequirementClass(req, $index)">{{ req.label }}</span>
                          </li>
                        }
                      </ul>
                    </div>
                  }
                </div>

                <div class="col-12 col-md-6">
                  <label for="confirmPassword" class="form-label fw-semibold">Confirm password <span class="text-danger">*</span></label>
                  <input
                    type="password"
                    id="confirmPassword"
                    class="form-control"
                    formControlName="confirmPassword"
                    placeholder="Confirm your password"
                    autocomplete="new-password"
                    [class.is-invalid]="form.get('confirmPassword')?.touched && (form.get('confirmPassword')?.invalid || form.hasError('passwordMismatch'))"
                    [disabled]="isSubmitting()" />
                  @if (getFieldError('confirmPassword'); as err) {
                    <div class="invalid-feedback d-block">{{ err }}</div>
                  }
                </div>

                <div class="col-12 col-md-6">
                  <label for="firstName" class="form-label fw-semibold">First name <span class="text-danger">*</span></label>
                  <input
                    type="text"
                    id="firstName"
                    class="form-control"
                    formControlName="firstName"
                    placeholder="First name"
                    autocomplete="given-name"
                    [class.is-invalid]="form.get('firstName')?.touched && form.get('firstName')?.invalid"
                    [disabled]="isSubmitting()" />
                  @if (getFieldError('firstName'); as err) {
                    <div class="invalid-feedback d-block">{{ err }}</div>
                  }
                </div>

                <div class="col-12 col-md-6">
                  <label for="lastName" class="form-label fw-semibold">Last name <span class="text-danger">*</span></label>
                  <input
                    type="text"
                    id="lastName"
                    class="form-control"
                    formControlName="lastName"
                    placeholder="Last name"
                    autocomplete="family-name"
                    [class.is-invalid]="form.get('lastName')?.touched && form.get('lastName')?.invalid"
                    [disabled]="isSubmitting()" />
                  @if (getFieldError('lastName'); as err) {
                    <div class="invalid-feedback d-block">{{ err }}</div>
                  }
                </div>

                <div class="col-12 col-md-6">
                  <label for="phone" class="form-label fw-semibold">Contact phone <span class="text-danger">*</span></label>
                  <input
                    type="tel"
                    id="phone"
                    class="form-control"
                    formControlName="phone"
                    placeholder="+381 64 123 4567"
                    autocomplete="tel"
                    [class.is-invalid]="form.get('phone')?.touched && form.get('phone')?.invalid"
                    [disabled]="isSubmitting()" />
                  @if (getFieldError('phone'); as err) {
                    <div class="invalid-feedback d-block">{{ err }}</div>
                  }
                </div>

                @if (accountType() === 'MANAGER') {
                  <div class="col-12">
                    <hr class="my-3" />
                    <h5 class="mb-3"><i class="bi bi-building me-2"></i>Company details</h5>
                  </div>

                  <div class="col-12 col-md-6">
                    <label for="companyName" class="form-label fw-semibold">Company name <span class="text-danger">*</span></label>
                    <input
                      type="text"
                      id="companyName"
                      class="form-control"
                      formControlName="companyName"
                      placeholder="Company name"
                      [class.is-invalid]="form.get('companyName')?.touched && form.get('companyName')?.invalid"
                      [disabled]="isSubmitting()" />
                    @if (getFieldError('companyName'); as err) {
                      <div class="invalid-feedback d-block">{{ err }}</div>
                    }
                  </div>

                  <div class="col-12">
                    <label for="headquartersAddress" class="form-label fw-semibold">Headquarters address <span class="text-danger">*</span></label>
                    <input
                      type="text"
                      id="headquartersAddress"
                      class="form-control"
                      formControlName="headquartersAddress"
                      placeholder="Street, number, city, postal code"
                      [class.is-invalid]="form.get('headquartersAddress')?.touched && form.get('headquartersAddress')?.invalid"
                      [disabled]="isSubmitting()" />
                    @if (getFieldError('headquartersAddress'); as err) {
                      <div class="invalid-feedback d-block">{{ err }}</div>
                    }
                  </div>

                  <div class="col-12 col-md-6">
                    <label for="companyNumber" class="form-label fw-semibold">Company number (PIB) <span class="text-danger">*</span></label>
                    <input
                      type="text"
                      id="companyNumber"
                      class="form-control"
                      formControlName="companyNumber"
                      placeholder="8 digits, e.g. 12345678"
                      maxlength="8"
                      [class.is-invalid]="form.get('companyNumber')?.touched && form.get('companyNumber')?.invalid"
                      [disabled]="isSubmitting()" />
                    @if (getFieldError('companyNumber'); as err) {
                      <div class="invalid-feedback d-block">{{ err }}</div>
                    }
                    <div class="form-text">Exactly 8 digits. Leading zeros are allowed.</div>
                  </div>

                  <div class="col-12 col-md-6">
                    <label for="taxId" class="form-label fw-semibold">Tax ID (Matični broj) <span class="text-danger">*</span></label>
                    <input
                      type="text"
                      id="taxId"
                      class="form-control"
                      formControlName="taxId"
                      placeholder="9 digits, e.g. 101234567"
                      maxlength="9"
                      [class.is-invalid]="form.get('taxId')?.touched && form.get('taxId')?.invalid"
                      [disabled]="isSubmitting()" />
                    @if (getFieldError('taxId'); as err) {
                      <div class="invalid-feedback d-block">{{ err }}</div>
                    }
                    <div class="form-text">Exactly 9 digits. Must not begin with zero.</div>
                  </div>
                }
              </div>

              <div class="row g-3 mt-1">
                <div class="col-12">
                  <label class="form-label fw-semibold">Profile image</label>
                  <div class="d-flex flex-column flex-md-row gap-3 align-items-md-center">
                    <div class="position-relative" style="width: 120px; height: 120px; flex-shrink: 0;">
                      @if (previewImage()) {
                        <img [src]="previewImage()" alt="Profile preview" class="rounded border img-thumbnail" style="width: 100%; height: 100%; object-fit: cover;" />
                        <button
                          type="button"
                          class="btn btn-sm btn-danger position-absolute top-0 end-0 m-1"
                          (click)="removeImage()"
                          [disabled]="isSubmitting()"
                          aria-label="Remove profile image">
                          <i class="bi bi-x-lg"></i>
                        </button>
                      } @else {
                        <div class="rounded border bg-light d-flex align-items-center justify-content-center" style="width: 100%; height: 100%;">
                          <i class="bi bi-person-circle text-muted" style="font-size: 3rem;"></i>
                        </div>
                      }
                    </div>
                    <div class="flex-grow-1">
                      <input
                        type="file"
                        id="profileImage"
                        class="form-control"
                        accept="image/jpeg,image/png"
                        (change)="onFileSelected($event)"
                        [disabled]="isSubmitting()"
                        hidden
                        #fileInput />
                      <button
                        type="button"
                        class="btn btn-outline-secondary"
                        (click)="fileInput.click()"
                        [disabled]="isSubmitting() || !!selectedFile()">
                        <i class="bi bi-upload me-1"></i> Choose image
                      </button>
                      <button
                        type="button"
                        class="btn btn-outline-danger ms-2"
                        (click)="removeImage()"
                        [disabled]="isSubmitting() || !selectedFile()">
                        <i class="bi bi-trash me-1"></i> Remove
                      </button>
                      @if (imageError()) {
                        <div class="text-danger small mt-1">{{ imageError() }}</div>
                      }
                      <div class="form-text mt-1">JPG or PNG, 100×100 to 300×300 pixels. Optional — a default image will be used if omitted.</div>
                    </div>
                  </div>
                </div>
              </div>

              @if (submitError()) {
                <div class="alert alert-danger border-0 shadow-sm mt-3" role="alert">
                  <i class="bi bi-exclamation-triangle-fill me-2"></i>{{ submitError() }}
                </div>
              }

              <div class="d-grid gap-2 mt-4">
                <button
                  type="submit"
                  class="btn btn-primary btn-lg"
                  [disabled]="isSubmitting() || form.invalid">
                  @if (isSubmitting()) {
                    <span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>
                    Submitting…
                  } @else {
                    <i class="bi bi-person-plus me-1"></i> Submit registration
                  }
                </button>
              </div>
            </form>

            <p class="text-center text-muted mt-4 mb-0">
              Already have an account? <a routerLink="/login" class="fw-semibold">Sign in</a>
            </p>
          }
        </div>
      </div>
    </div>
  </div>
</div>
```

FILE: frontend/src/app/components/register/register.css

```css
.card {
  border-radius: 0.75rem;
}

.card-header {
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.btn-group .btn {
  border-radius: 0.5rem !important;
  margin: 0 2px;
}

.btn-group .btn:first-child {
  margin-left: 0;
  border-top-right-radius: 0 !important;
  border-bottom-right-radius: 0 !important;
}

.btn-group .btn:last-child {
  margin-right: 0;
  border-top-left-radius: 0 !important;
  border-bottom-left-radius: 0 !important;
}

.btn-group .btn.active {
  z-index: 1;
}

.form-label {
  font-size: 0.875rem;
}

.form-control:focus,
.form-select:focus {
  border-color: #86b7fe;
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.15);
}

.invalid-feedback {
  font-size: 0.8125rem;
}

.form-text {
  font-size: 0.8125rem;
}

.input-group .btn-outline-secondary {
  border-left: none;
  border-top-left-radius: 0;
  border-bottom-left-radius: 0;
}

.list-unstyled li i {
  font-size: 0.875rem;
  width: 1em;
  text-align: center;
}

.text-success {
  color: #198754 !important;
}

.text-muted {
  color: #6c757d !important;
}

@media (max-width: 575.98px) {
  .card-body {
    padding: 1.25rem;
  }

  .btn-group .btn {
    padding: 0.5rem 0.75rem;
    font-size: 0.875rem;
  }

  .btn-group .btn i {
    display: none;
  }
}

@media (min-width: 576px) {
  .card-body {
    padding: 2rem;
  }
}

.spinner-border-sm {
  width: 1rem;
  height: 1rem;
}

.img-thumbnail {
  border-width: 2px;
}

.position-relative .btn {
  opacity: 0;
  transition: opacity 0.2s ease;
}

.position-relative:hover .btn,
.position-relative:focus-within .btn {
  opacity: 1;
}

.alert {
  border-radius: 0.5rem;
}

.alert-success {
  background-color: #d1e7dd;
  color: #0f5132;
}

.alert-danger {
  background-color: #f8d7da;
  color: #842029;
}
```