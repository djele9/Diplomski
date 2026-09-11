FILE: frontend/src/app/models/user-role.enum.ts

```typescript
export enum UserRole {
  MEMBER = 'MEMBER',
  MANAGER = 'MANAGER',
  ADMIN = 'ADMIN',
}
```

FILE: frontend/src/app/models/user-status.enum.ts

```typescript
export enum UserStatus {
  PENDING = 'PENDING',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED',
}
```

FILE: frontend/src/app/models/registration-status.enum.ts

```typescript
export enum RegistrationStatus {
  PENDING = 'PENDING',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED',
}
```

FILE: frontend/src/app/models/reservation-status.enum.ts

```typescript
export enum ReservationStatus {
  PENDING = 'PENDING',
  CONFIRMED = 'CONFIRMED',
  CANCELLED = 'CANCELLED',
  COMPLETED = 'COMPLETED',
}
```

FILE: frontend/src/app/models/user.model.ts

```typescript
import { UserRole } from './user-role.enum';
import { UserStatus } from './user-status.enum';

export interface User {
  id: string;
  username: string;
  firstName: string;
  lastName: string;
  phone: string;
  email: string;
  role: UserRole;
  status: UserStatus;
  profileImage: string;
  companyId?: string;
  createdAt: string;
  updatedAt: string;
}

export interface UserProfile extends User {
  // UserProfile from backend includes all User fields
  // No additional fields based on backend user.service.ts
}

export interface UpdateProfileData {
  firstName?: string;
  lastName?: string;
  phone?: string;
  email?: string;
  profileImage?: string;
}

export interface ChangePasswordData {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

export interface PublicUser {
  id: string;
  username: string;
  firstName: string;
  lastName: string;
  email: string;
  role: UserRole;
  status: UserStatus;
  profileImage: string;
  companyId?: string;
  createdAt: string;
}
```

FILE: frontend/src/app/models/company.model.ts

```typescript
export interface Company {
  id: string;
  name: string;
  headquartersAddress: string;
  companyNumber: string;
  taxId: string;
  createdAt: string;
  updatedAt: string;
}

export interface CompanyData {
  name: string;
  headquartersAddress: string;
  companyNumber: string;
  taxId: string;
}

export interface CompanyManagersCount {
  count: number;
}

export interface CompanyPendingManagersCount {
  count: number;
}
```

FILE: frontend/src/app/models/registration-request.model.ts

```typescript
import { UserRole } from './user-role.enum';
import { RegistrationStatus } from './registration-status.enum';

export interface RegistrationRequest {
  id: string;
  username: string;
  firstName: string;
  lastName: string;
  phone: string;
  email: string;
  role: UserRole;
  companyName?: string;
  headquartersAddress?: string;
  companyNumber?: string;
  taxId?: string;
  status: RegistrationStatus;
  submittedAt: string;
  decidedAt?: string;
  decidedBy?: string;
  profileImage: string;
  createdAt: string;
  updatedAt: string;
}

export interface PendingRegistrationRequest extends RegistrationRequest {
  // Same as RegistrationRequest but status is always PENDING
}

export interface RegisterMemberData {
  username: string;
  password: string;
  firstName: string;
  lastName: string;
  phone: string;
  email: string;
  profileImage?: string;
}

export interface RegisterManagerData extends RegisterMemberData {
  companyName: string;
  headquartersAddress: string;
  companyNumber: string;
  taxId: string;
}

export interface RegistrationResponse {
  message: string;
  request: {
    id: string;
    username: string;
    role: UserRole;
    status: RegistrationStatus;
  };
}

export interface CheckAvailabilityResponse {
  available: boolean;
}
```

FILE: frontend/src/app/models/password-reset.model.ts

```typescript
export interface PasswordResetToken {
  id: string;
  userId: string;
  expiresAt: string;
  usedAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface RequestPasswordResetData {
  identifier: string;
}

export interface RequestPasswordResetResponse {
  message: string;
}

export interface VerifyPasswordResetTokenResponse {
  valid: boolean;
}

export interface ConfirmPasswordResetData {
  newPassword: string;
  confirmPassword: string;
}

export interface ConfirmPasswordResetResponse {
  message: string;
}
```

FILE: frontend/src/app/models/space.model.ts

```typescript
export interface Space {
  id: string;
  name: string;
  description: string;
  address: string;
  city: string;
  capacity: number;
  amenities: string[];
  images: string[];
  companyId: string;
  pricePerHour: number;
  pricePerDay: number;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CreateSpaceData {
  name: string;
  description: string;
  address: string;
  city: string;
  capacity: number;
  amenities?: string[];
  images?: string[];
  companyId: string;
  pricePerHour: number;
  pricePerDay: number;
}

export interface UpdateSpaceData {
  name?: string;
  description?: string;
  address?: string;
  city?: string;
  capacity?: number;
  amenities?: string[];
  images?: string[];
  pricePerHour?: number;
  pricePerDay?: number;
  isActive?: boolean;
}

export interface PublicSpaceFilters {
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  city?: string;
  minCapacity?: number;
  maxPricePerHour?: number;
  amenities?: string[];
}

export interface SpaceAvailabilityResponse {
  available: boolean;
  conflictingReservations?: Array<{
    id: string;
    startTime: string;
    endTime: string;
  }>;
}
```

FILE: frontend/src/app/models/reservation.model.ts

```typescript
import { ReservationStatus } from './reservation-status.enum';

export interface Reservation {
  id: string;
  userId: string;
  spaceId: string;
  startTime: string;
  endTime: string;
  status: ReservationStatus;
  totalPrice: number;
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

export interface ReservationWithDetails extends Reservation {
  user?: {
    id: string;
    username: string;
    firstName: string;
    lastName: string;
    email: string;
    profileImage: string;
  };
  space?: {
    id: string;
    name: string;
    address: string;
    city: string;
    pricePerHour: number;
    pricePerDay: number;
  };
  company?: {
    id: string;
    name: string;
  };
}

export interface CreateReservationData {
  spaceId: string;
  startTime: string;
  endTime: string;
  notes?: string;
}

export interface ReservationFilters {
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  status?: ReservationStatus;
}
```

FILE: frontend/src/app/models/auth.model.ts

```typescript
import { UserRole } from './user-role.enum';

export interface LoginData {
  username: string;
  password: string;
}

export interface LoginResult {
  accessToken: string;
  refreshToken: string;
  user: {
    id: string;
    username: string;
    role: UserRole;
  };
}

export interface RefreshTokenData {
  refreshToken: string;
}

export interface RefreshTokenResult {
  accessToken: string;
  refreshToken: string;
}

export interface JwtPayload {
  sub: string;
  username: string;
  role: UserRole;
  iat?: number;
  exp?: number;
}

export interface TokenPair {
  accessToken: string;
  refreshToken: string;
}

export interface MeResponse {
  id: string;
  username: string;
  role: UserRole;
}

export interface LogoutResponse {
  message: string;
}
```

FILE: frontend/src/app/models/api.model.ts

```typescript
export interface FieldError {
  field: string;
  message: string;
}

export interface ErrorResponse {
  status: number;
  message: string;
  fieldErrors?: FieldError[];
}

export interface PaginationParams {
  page: number;
  limit: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface PaginatedResult<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

export interface AdminStatistics {
  totalUsers: number;
  pendingRegistrations: number;
  totalCompanies: number;
  totalSpaces: number;
  usersByRole: Record<string, number>;
}

export interface ApproveRegistrationResult {
  message: string;
  user: {
    id: string;
    username: string;
    role: string;
    status: string;
  };
}

export interface RejectRegistrationResult {
  message: string;
  user: {
    id: string;
    username: string;
    role: string;
    status: string;
  };
}

export interface DeleteResult {
  message: string;
}
```

FILE: frontend/src/app/models/index.ts

```typescript
export * from './user-role.enum';
export * from './user-status.enum';
export * from './registration-status.enum';
export * from './reservation-status.enum';
export * from './user.model';
export * from './company.model';
export * from './registration-request.model';
export * from './password-reset.model';
export * from './space.model';
export * from './reservation.model';
export * from './auth.model';
export * from './api.model';
```