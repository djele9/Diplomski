FILE: frontend/src/app/services/auth.service.ts

```typescript
import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, tap, catchError, throwError } from 'rxjs';
import { environment } from '../../environments/environment';
import {
  LoginData,
  LoginResult,
  RefreshTokenData,
  RefreshTokenResult,
  JwtPayload,
  TokenPair,
  MeResponse,
  LogoutResponse,
  UserRole
} from '../models/auth.model';
import { RequestPasswordResetData, RequestPasswordResetResponse, VerifyPasswordResetTokenResponse, ConfirmPasswordResetData, ConfirmPasswordResetResponse } from '../models/password-reset.model';
import { RegisterMemberData, RegisterManagerData, RegistrationResponse, CheckAvailabilityResponse } from '../models/registration-request.model';
import { User } from '../models/user.model';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = environment.apiUrl;

  private readonly accessTokenKey = 'access_token';
  private readonly refreshTokenKey = 'refresh_token';
  private readonly userKey = 'current_user';

  private readonly _currentUser = signal<User | null>(null);
  readonly currentUser = this._currentUser.asReadonly();

  readonly isAuthenticated = computed(() => this._currentUser() !== null);
  readonly userRole = computed(() => this._currentUser()?.role ?? null);
  readonly isAdmin = computed(() => this._currentUser()?.role === UserRole.ADMIN);
  readonly isManager = computed(() => this._currentUser()?.role === UserRole.MANAGER);
  readonly isMember = computed(() => this._currentUser()?.role === UserRole.MEMBER);

  constructor() {
    this.restoreSession();
  }

  private restoreSession(): void {
    const accessToken = localStorage.getItem(this.accessTokenKey);
    const refreshToken = localStorage.getItem(this.refreshTokenKey);
    const userJson = localStorage.getItem(this.userKey);

    if (accessToken && refreshToken && userJson) {
      try {
        const user = JSON.parse(userJson) as User;
        this._currentUser.set(user);
      } catch {
        this.clearSession();
      }
    }
  }

  private saveSession(tokens: TokenPair, user: User): void {
    localStorage.setItem(this.accessTokenKey, tokens.accessToken);
    localStorage.setItem(this.refreshTokenKey, tokens.refreshToken);
    localStorage.setItem(this.userKey, JSON.stringify(user));
    this._currentUser.set(user);
  }

  private clearSession(): void {
    localStorage.removeItem(this.accessTokenKey);
    localStorage.removeItem(this.refreshTokenKey);
    localStorage.removeItem(this.userKey);
    this._currentUser.set(null);
  }

  getAccessToken(): string | null {
    return localStorage.getItem(this.accessTokenKey);
  }

  getRefreshToken(): string | null {
    return localStorage.getItem(this.refreshTokenKey);
  }

  login(data: LoginData): Observable<LoginResult> {
    return this.http.post<LoginResult>(`${this.apiUrl}/auth/login`, data).pipe(
      tap(result => this.saveSession({ accessToken: result.accessToken, refreshToken: result.refreshToken }, {
        id: result.user.id,
        username: result.user.username,
        firstName: '',
        lastName: '',
        phone: '',
        email: '',
        role: result.user.role,
        status: 'APPROVED' as any,
        profileImage: '',
        createdAt: '',
        updatedAt: ''
      }))
    );
  }

  adminLogin(data: LoginData): Observable<LoginResult> {
    return this.http.post<LoginResult>(`${this.apiUrl}/auth/admin/login`, data).pipe(
      tap(result => this.saveSession({ accessToken: result.accessToken, refreshToken: result.refreshToken }, {
        id: result.user.id,
        username: result.user.username,
        firstName: '',
        lastName: '',
        phone: '',
        email: '',
        role: result.user.role,
        status: 'APPROVED' as any,
        profileImage: '',
        createdAt: '',
        updatedAt: ''
      }))
    );
  }

  logout(): Observable<LogoutResponse> {
    const refreshToken = this.getRefreshToken();
    return this.http.post<LogoutResponse>(`${this.apiUrl}/auth/logout`, { refreshToken } as RefreshTokenData).pipe(
      tap(() => this.clearSession()),
      catchError(err => {
        this.clearSession();
        return throwError(() => err);
      })
    );
  }

  refreshToken(): Observable<RefreshTokenResult> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      return throwError(() => new Error('No refresh token available'));
    }
    return this.http.post<RefreshTokenResult>(`${this.apiUrl}/auth/refresh`, { refreshToken } as RefreshTokenData).pipe(
      tap(result => {
        localStorage.setItem(this.accessTokenKey, result.accessToken);
        localStorage.setItem(this.refreshTokenKey, result.refreshToken);
      })
    );
  }

  me(): Observable<MeResponse> {
    return this.http.get<MeResponse>(`${this.apiUrl}/auth/me`);
  }

  registerMember(data: RegisterMemberData): Observable<RegistrationResponse> {
    return this.http.post<RegistrationResponse>(`${this.apiUrl}/auth/register/member`, data);
  }

  registerManager(data: RegisterManagerData): Observable<RegistrationResponse> {
    return this.http.post<RegistrationResponse>(`${this.apiUrl}/auth/register/manager`, data);
  }

  checkUsernameAvailability(username: string): Observable<CheckAvailabilityResponse> {
    const params = new HttpParams().set('username', username);
    return this.http.get<CheckAvailabilityResponse>(`${this.apiUrl}/auth/check-username`, { params });
  }

  checkEmailAvailability(email: string): Observable<CheckAvailabilityResponse> {
    const params = new HttpParams().set('email', email);
    return this.http.get<CheckAvailabilityResponse>(`${this.apiUrl}/auth/check-email`, { params });
  }

  requestPasswordReset(data: RequestPasswordResetData): Observable<RequestPasswordResetResponse> {
    return this.http.post<RequestPasswordResetResponse>(`${this.apiUrl}/auth/forgot-password`, data);
  }

  verifyResetToken(token: string): Observable<VerifyPasswordResetTokenResponse> {
    return this.http.get<VerifyPasswordResetTokenResponse>(`${this.apiUrl}/auth/reset-password/${token}`);
  }

  confirmPasswordReset(token: string, data: ConfirmPasswordResetData): Observable<ConfirmPasswordResetResponse> {
    return this.http.post<ConfirmPasswordResetResponse>(`${this.apiUrl}/auth/reset-password/${token}`, data);
  }

  hasRole(role: UserRole): boolean {
    return this._currentUser()?.role === role;
  }

  hasAnyRole(roles: UserRole[]): boolean {
    const userRole = this._currentUser()?.role;
    return userRole ? roles.includes(userRole) : false;
  }
}
```

FILE: frontend/src/app/services/admin.service.ts

```typescript
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { AdminStatistics, ApproveRegistrationResult, RejectRegistrationResult, DeleteResult, PaginationParams, PaginatedResult } from '../models/api.model';
import { RegistrationRequest } from '../models/registration-request.model';
import { User } from '../models/user.model';
import { Company } from '../models/company.model';
import { Space } from '../models/space.model';
import { ReservationWithDetails } from '../models/reservation.model';

@Injectable({ providedIn: 'root' })
export class AdminService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = environment.apiUrl;

  getStatistics(): Observable<AdminStatistics> {
    return this.http.get<AdminStatistics>(`${this.apiUrl}/admin/statistics`);
  }

  getRegistrationRequests(params?: PaginationParams): Observable<PaginatedResult<RegistrationRequest>> {
    let httpParams = new HttpParams();
    if (params) {
      if (params.page !== undefined) httpParams = httpParams.set('page', params.page);
      if (params.limit !== undefined) httpParams = httpParams.set('limit', params.limit);
      if (params.sortBy) httpParams = httpParams.set('sortBy', params.sortBy);
      if (params.sortOrder) httpParams = httpParams.set('sortOrder', params.sortOrder);
    }
    return this.http.get<PaginatedResult<RegistrationRequest>>(`${this.apiUrl}/admin/registration-requests`, { params: httpParams });
  }

  approveRegistrationRequest(requestId: string): Observable<ApproveRegistrationResult> {
    return this.http.post<ApproveRegistrationResult>(`${this.apiUrl}/admin/registration-requests/${requestId}/approve`, {});
  }

  rejectRegistrationRequest(requestId: string): Observable<RejectRegistrationResult> {
    return this.http.post<RejectRegistrationResult>(`${this.apiUrl}/admin/registration-requests/${requestId}/reject`, {});
  }

  getUsers(params?: PaginationParams): Observable<PaginatedResult<User>> {
    let httpParams = new HttpParams();
    if (params) {
      if (params.page !== undefined) httpParams = httpParams.set('page', params.page);
      if (params.limit !== undefined) httpParams = httpParams.set('limit', params.limit);
      if (params.sortBy) httpParams = httpParams.set('sortBy', params.sortBy);
      if (params.sortOrder) httpParams = httpParams.set('sortOrder', params.sortOrder);
    }
    return this.http.get<PaginatedResult<User>>(`${this.apiUrl}/admin/users`, { params: httpParams });
  }

  getUser(userId: string): Observable<User> {
    return this.http.get<User>(`${this.apiUrl}/admin/users/${userId}`);
  }

  updateUserStatus(userId: string, status: string): Observable<User> {
    return this.http.put<User>(`${this.apiUrl}/admin/users/${userId}/status`, { status });
  }

  updateUserRole(userId: string, role: string): Observable<User> {
    return this.http.put<User>(`${this.apiUrl}/admin/users/${userId}/role`, { role });
  }

  deleteUser(userId: string): Observable<DeleteResult> {
    return this.http.delete<DeleteResult>(`${this.apiUrl}/admin/users/${userId}`);
  }

  getCompanies(params?: PaginationParams): Observable<PaginatedResult<Company>> {
    let httpParams = new HttpParams();
    if (params) {
      if (params.page !== undefined) httpParams = httpParams.set('page', params.page);
      if (params.limit !== undefined) httpParams = httpParams.set('limit', params.limit);
      if (params.sortBy) httpParams = httpParams.set('sortBy', params.sortBy);
      if (params.sortOrder) httpParams = httpParams.set('sortOrder', params.sortOrder);
    }
    return this.http.get<PaginatedResult<Company>>(`${this.apiUrl}/admin/companies`, { params: httpParams });
  }

  getSpaces(params?: PaginationParams): Observable<PaginatedResult<Space>> {
    let httpParams = new HttpParams();
    if (params) {
      if (params.page !== undefined) httpParams = httpParams.set('page', params.page);
      if (params.limit !== undefined) httpParams = httpParams.set('limit', params.limit);
      if (params.sortBy) httpParams = httpParams.set('sortBy', params.sortBy);
      if (params.sortOrder) httpParams = httpParams.set('sortOrder', params.sortOrder);
    }
    return this.http.get<PaginatedResult<Space>>(`${this.apiUrl}/admin/spaces`, { params: httpParams });
  }

  getReservations(params?: PaginationParams): Observable<PaginatedResult<ReservationWithDetails>> {
    let httpParams = new HttpParams();
    if (params) {
      if (params.page !== undefined) httpParams = httpParams.set('page', params.page);
      if (params.limit !== undefined) httpParams = httpParams.set('limit', params.limit);
      if (params.sortBy) httpParams = httpParams.set('sortBy', params.sortBy);
      if (params.sortOrder) httpParams = httpParams.set('sortOrder', params.sortOrder);
    }
    return this.http.get<PaginatedResult<ReservationWithDetails>>(`${this.apiUrl}/admin/reservations`, { params: httpParams });
  }
}
```

FILE: frontend/src/app/services/company.service.ts

```typescript
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { Company, CompanyData, CompanyManagersCount, CompanyPendingManagersCount } from '../models/company.model';
import { PaginationParams, PaginatedResult } from '../models/api.model';

@Injectable({ providedIn: 'root' })
export class CompanyService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = environment.apiUrl;

  createCompany(data: CompanyData): Observable<Company> {
    return this.http.post<Company>(`${this.apiUrl}/companies/companies`, data);
  }

  getCompany(companyId: string): Observable<Company> {
    return this.http.get<Company>(`${this.apiUrl}/companies/companies/${companyId}`);
  }

  getAdminCompanies(params?: PaginationParams): Observable<PaginatedResult<Company>> {
    let httpParams = new HttpParams();
    if (params) {
      if (params.page !== undefined) httpParams = httpParams.set('page', params.page);
      if (params.limit !== undefined) httpParams = httpParams.set('limit', params.limit);
      if (params.sortBy) httpParams = httpParams.set('sortBy', params.sortBy);
      if (params.sortOrder) httpParams = httpParams.set('sortOrder', params.sortOrder);
    }
    return this.http.get<PaginatedResult<Company>>(`${this.apiUrl}/companies/admin/companies`, { params: httpParams });
  }

  updateCompany(companyId: string, data: Partial<CompanyData>): Observable<Company> {
    return this.http.put<Company>(`${this.apiUrl}/companies/admin/companies/${companyId}`, data);
  }

  deleteCompany(companyId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/companies/admin/companies/${companyId}`);
  }

  getManagersCount(companyId: string): Observable<CompanyManagersCount> {
    return this.http.get<CompanyManagersCount>(`${this.apiUrl}/companies/companies/${companyId}/managers/count`);
  }

  getPendingManagersCount(companyNumber: string): Observable<CompanyPendingManagersCount> {
    return this.http.get<CompanyPendingManagersCount>(`${this.apiUrl}/companies/admin/companies/${companyNumber}/pending-managers/count`);
  }
}
```

FILE: frontend/src/app/services/registration.service.ts

```typescript
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { RegistrationRequest, RegisterMemberData, RegisterManagerData, RegistrationResponse, CheckAvailabilityResponse } from '../models/registration-request.model';
import { PaginationParams, PaginatedResult } from '../models/api.model';

@Injectable({ providedIn: 'root' })
export class RegistrationService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = environment.apiUrl;

  registerMember(data: RegisterMemberData): Observable<RegistrationResponse> {
    return this.http.post<RegistrationResponse>(`${this.apiUrl}/auth/register/member`, data);
  }

  registerManager(data: RegisterManagerData): Observable<RegistrationResponse> {
    return this.http.post<RegistrationResponse>(`${this.apiUrl}/auth/register/manager`, data);
  }

  getAdminRegistrationRequests(params?: PaginationParams): Observable<PaginatedResult<RegistrationRequest>> {
    let httpParams = new HttpParams();
    if (params) {
      if (params.page !== undefined) httpParams = httpParams.set('page', params.page);
      if (params.limit !== undefined) httpParams = httpParams.set('limit', params.limit);
      if (params.sortBy) httpParams = httpParams.set('sortBy', params.sortBy);
      if (params.sortOrder) httpParams = httpParams.set('sortOrder', params.sortOrder);
    }
    return this.http.get<PaginatedResult<RegistrationRequest>>(`${this.apiUrl}/auth/admin/registration-requests`, { params: httpParams });
  }

  approveRegistrationRequest(requestId: string): Observable<RegistrationResponse> {
    return this.http.post<RegistrationResponse>(`${this.apiUrl}/auth/admin/registration-requests/${requestId}/approve`, {});
  }

  rejectRegistrationRequest(requestId: string): Observable<RegistrationResponse> {
    return this.http.post<RegistrationResponse>(`${this.apiUrl}/auth/admin/registration-requests/${requestId}/reject`, {});
  }

  checkUsernameAvailability(username: string): Observable<CheckAvailabilityResponse> {
    const params = new HttpParams().set('username', username);
    return this.http.get<CheckAvailabilityResponse>(`${this.apiUrl}/auth/check-username`, { params });
  }

  checkEmailAvailability(email: string): Observable<CheckAvailabilityResponse> {
    const params = new HttpParams().set('email', email);
    return this.http.get<CheckAvailabilityResponse>(`${this.apiUrl}/auth/check-email`, { params });
  }
}
```

FILE: frontend/src/app/services/reservation.service.ts

```typescript
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { Reservation, ReservationWithDetails, CreateReservationData, ReservationFilters } from '../models/reservation.model';
import { SpaceAvailabilityResponse } from '../models/space.model';
import { PaginationParams, PaginatedResult } from '../models/api.model';

@Injectable({ providedIn: 'root' })
export class ReservationService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = environment.apiUrl;

  createReservation(data: CreateReservationData): Observable<Reservation> {
    return this.http.post<Reservation>(`${this.apiUrl}/reservations/reservations`, data);
  }

  getReservations(filters?: ReservationFilters): Observable<PaginatedResult<ReservationWithDetails>> {
    let httpParams = new HttpParams();
    if (filters) {
      if (filters.page !== undefined) httpParams = httpParams.set('page', filters.page);
      if (filters.limit !== undefined) httpParams = httpParams.set('limit', filters.limit);
      if (filters.sortBy) httpParams = httpParams.set('sortBy', filters.sortBy);
      if (filters.sortOrder) httpParams = httpParams.set('sortOrder', filters.sortOrder);
      if (filters.status) httpParams = httpParams.set('status', filters.status);
    }
    return this.http.get<PaginatedResult<ReservationWithDetails>>(`${this.apiUrl}/reservations/reservations`, { params: httpParams });
  }

  getReservation(reservationId: string): Observable<ReservationWithDetails> {
    return this.http.get<ReservationWithDetails>(`${this.apiUrl}/reservations/reservations/${reservationId}`);
  }

  getCompanyReservations(filters?: ReservationFilters): Observable<PaginatedResult<ReservationWithDetails>> {
    let httpParams = new HttpParams();
    if (filters) {
      if (filters.page !== undefined) httpParams = httpParams.set('page', filters.page);
      if (filters.limit !== undefined) httpParams = httpParams.set('limit', filters.limit);
      if (filters.sortBy) httpParams = httpParams.set('sortBy', filters.sortBy);
      if (filters.sortOrder) httpParams = httpParams.set('sortOrder', filters.sortOrder);
      if (filters.status) httpParams = httpParams.set('status', filters.status);
    }
    return this.http.get<PaginatedResult<ReservationWithDetails>>(`${this.apiUrl}/reservations/reservations/company`, { params: httpParams });
  }

  cancelReservation(reservationId: string): Observable<Reservation> {
    return this.http.post<Reservation>(`${this.apiUrl}/reservations/reservations/${reservationId}/cancel`, {});
  }

  confirmReservation(reservationId: string): Observable<Reservation> {
    return this.http.post<Reservation>(`${this.apiUrl}/reservations/reservations/${reservationId}/confirm`, {});
  }

  completeReservation(reservationId: string): Observable<Reservation> {
    return this.http.post<Reservation>(`${this.apiUrl}/reservations/reservations/${reservationId}/complete`, {});
  }

  checkSpaceAvailability(spaceId: string, startTime: string, endTime: string): Observable<SpaceAvailabilityResponse> {
    const params = new HttpParams()
      .set('startTime', startTime)
      .set('endTime', endTime);
    return this.http.get<SpaceAvailabilityResponse>(`${this.apiUrl}/reservations/spaces/${spaceId}/availability`, { params });
  }
}
```

FILE: frontend/src/app/services/space.service.ts

```typescript
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { Space, CreateSpaceData, UpdateSpaceData, PublicSpaceFilters } from '../models/space.model';
import { PaginationParams, PaginatedResult } from '../models/api.model';

@Injectable({ providedIn: 'root' })
export class SpaceService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = environment.apiUrl;

  createSpace(data: CreateSpaceData): Observable<Space> {
    return this.http.post<Space>(`${this.apiUrl}/spaces/spaces`, data);
  }

  getPublicSpaces(filters?: PublicSpaceFilters): Observable<PaginatedResult<Space>> {
    let httpParams = new HttpParams();
    if (filters) {
      if (filters.page !== undefined) httpParams = httpParams.set('page', filters.page);
      if (filters.limit !== undefined) httpParams = httpParams.set('limit', filters.limit);
      if (filters.sortBy) httpParams = httpParams.set('sortBy', filters.sortBy);
      if (filters.sortOrder) httpParams = httpParams.set('sortOrder', filters.sortOrder);
      if (filters.city) httpParams = httpParams.set('city', filters.city);
      if (filters.minCapacity !== undefined) httpParams = httpParams.set('minCapacity', filters.minCapacity);
      if (filters.maxPricePerHour !== undefined) httpParams = httpParams.set('maxPricePerHour', filters.maxPricePerHour);
      if (filters.amenities?.length) {
        filters.amenities.forEach(amenity => {
          httpParams = httpParams.append('amenities', amenity);
        });
      }
    }
    return this.http.get<PaginatedResult<Space>>(`${this.apiUrl}/spaces/spaces/public`, { params: httpParams });
  }

  getSpace(spaceId: string): Observable<Space> {
    return this.http.get<Space>(`${this.apiUrl}/spaces/spaces/${spaceId}`);
  }

  getCompanySpaces(params?: PaginationParams): Observable<PaginatedResult<Space>> {
    let httpParams = new HttpParams();
    if (params) {
      if (params.page !== undefined) httpParams = httpParams.set('page', params.page);
      if (params.limit !== undefined) httpParams = httpParams.set('limit', params.limit);
      if (params.sortBy) httpParams = httpParams.set('sortBy', params.sortBy);
      if (params.sortOrder) httpParams = httpParams.set('sortOrder', params.sortOrder);
    }
    return this.http.get<PaginatedResult<Space>>(`${this.apiUrl}/spaces/spaces/company`, { params: httpParams });
  }

  updateSpace(spaceId: string, data: UpdateSpaceData): Observable<Space> {
    return this.http.put<Space>(`${this.apiUrl}/spaces/spaces/${spaceId}`, data);
  }

  deleteSpace(spaceId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/spaces/spaces/${spaceId}`);
  }

  toggleSpaceActive(spaceId: string): Observable<Space> {
    return this.http.patch<Space>(`${this.apiUrl}/spaces/spaces/${spaceId}/toggle-active`, {});
  }
}
```

FILE: frontend/src/app/services/user.service.ts

```typescript
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { User, UserProfile, UpdateProfileData, ChangePasswordData, PublicUser } from '../models/user.model';
import { PaginationParams, PaginatedResult } from '../models/api.model';

@Injectable({ providedIn: 'root' })
export class UserService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = environment.apiUrl;

  getProfile(): Observable<UserProfile> {
    return this.http.get<UserProfile>(`${this.apiUrl}/users/profile`);
  }

  updateProfile(data: UpdateProfileData): Observable<UserProfile> {
    return this.http.put<UserProfile>(`${this.apiUrl}/users/profile`, data);
  }

  changePassword(data: ChangePasswordData): Observable<void> {
    return this.http.post<void>(`${this.apiUrl}/users/profile/password`, data);
  }

  deleteProfileImage(): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/users/profile/image`);
  }

  uploadProfileImage(file: File): Observable<{ profileImage: string }> {
    const formData = new FormData();
    formData.append('image', file);
    return this.http.post<{ profileImage: string }>(`${this.apiUrl}/users/profile/image`, formData);
  }

  getAdminUsers(params?: PaginationParams): Observable<PaginatedResult<PublicUser>> {
    let httpParams = new HttpParams();
    if (params) {
      if (params.page !== undefined) httpParams = httpParams.set('page', params.page);
      if (params.limit !== undefined) httpParams = httpParams.set('limit', params.limit);
      if (params.sortBy) httpParams = httpParams.set('sortBy', params.sortBy);
      if (params.sortOrder) httpParams = httpParams.set('sortOrder', params.sortOrder);
    }
    return this.http.get<PaginatedResult<PublicUser>>(`${this.apiUrl}/users/admin/users`, { params: httpParams });
  }

  getAdminUser(userId: string): Observable<PublicUser> {
    return this.http.get<PublicUser>(`${this.apiUrl}/users/admin/users/${userId}`);
  }

  updateAdminUserStatus(userId: string, status: string): Observable<PublicUser> {
    return this.http.put<PublicUser>(`${this.apiUrl}/users/admin/users/${userId}/status`, { status });
  }

  updateAdminUserRole(userId: string, role: string): Observable<PublicUser> {
    return this.http.put<PublicUser>(`${this.apiUrl}/users/admin/users/${userId}/role`, { role });
  }

  deleteAdminUser(userId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/users/admin/users/${userId}`);
  }
}
```

FILE: frontend/src/app/services/index.ts

```typescript
export * from './auth.service';
export * from './admin.service';
export * from './company.service';
export * from './registration.service';
export * from './reservation.service';
export * from './space.service';
export * from './user.service';
```