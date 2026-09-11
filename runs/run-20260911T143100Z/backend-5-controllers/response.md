FILE: backend/src/utils/asyncHandler.ts

```typescript
import { Request, Response, NextFunction } from 'express';

export function asyncHandler(
  fn: (req: Request, res: Response, next: NextFunction) => Promise<void>
): (req: Request, res: Response, next: NextFunction) => void {
  return (req: Request, res: Response, next: NextFunction): void => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}
```

FILE: backend/src/controllers/auth.controller.ts

```typescript
import { Request, Response, NextFunction } from 'express';
import { asyncHandler } from '../utils/asyncHandler';
import { authService, LoginResult } from '../services/auth.service';
import { AppError } from '../utils/AppError';
import { AuthenticatedRequest } from '../types';

export class AuthController {
  login = asyncHandler(async (req: Request, res: Response, _next: NextFunction): Promise<void> => {
    const { username, password } = req.body as { username: string; password: string };
    const result: LoginResult = await authService.login(username, password, false);
    res.status(200).json(result);
  });

  adminLogin = asyncHandler(async (req: Request, res: Response, _next: NextFunction): Promise<void> => {
    const { username, password } = req.body as { username: string; password: string };
    const result: LoginResult = await authService.login(username, password, true);
    res.status(200).json(result);
  });

  requestPasswordReset = asyncHandler(async (req: Request, res: Response, _next: NextFunction): Promise<void> => {
    const { identifier } = req.body as { identifier: string };
    const result = await authService.requestPasswordReset(identifier);
    res.status(200).json(result);
  });

  verifyPasswordResetToken = asyncHandler(async (req: Request, res: Response, _next: NextFunction): Promise<void> => {
    const { token } = req.params as { token: string };
    const result = await authService.verifyPasswordResetToken(token);
    res.status(200).json({ valid: result.valid });
  });

  confirmPasswordReset = asyncHandler(async (req: Request, res: Response, _next: NextFunction): Promise<void> => {
    const { token } = req.params as { token: string };
    const { newPassword, confirmPassword } = req.body as { newPassword: string; confirmPassword: string };
    const result = await authService.confirmPasswordReset(token, newPassword, confirmPassword);
    res.status(200).json(result);
  });

  refreshAccessToken = asyncHandler(async (req: Request, res: Response, _next: NextFunction): Promise<void> => {
    const { refreshToken } = req.body as { refreshToken: string };
    if (!refreshToken) {
      throw AppError.badRequest('Refresh token is required.');
    }
    const result = await authService.refreshAccessToken(refreshToken);
    res.status(200).json(result);
  });

  logout = asyncHandler(async (_req: Request, res: Response, _next: NextFunction): Promise<void> => {
    res.status(200).json({ message: 'Signed out successfully.' });
  });

  getMe = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user) {
      throw AppError.unauthorized('Authentication required');
    }
    res.status(200).json({
      id: req.user.sub,
      username: req.user.username,
      role: req.user.role,
    });
  });
}

export const authController = new AuthController();
```

FILE: backend/src/controllers/registration.controller.ts

```typescript
import { Request, Response, NextFunction } from 'express';
import { asyncHandler } from '../utils/asyncHandler';
import { authService, RegisterMemberData, RegisterManagerData } from '../services/auth.service';
import { registrationService, PendingRegistrationRequest } from '../services/registration.service';
import { AppError } from '../utils/AppError';
import { AuthenticatedRequest } from '../types';
import { UserRole } from '../types';

export class RegistrationController {
  registerMember = asyncHandler(async (req: Request, res: Response, _next: NextFunction): Promise<void> => {
    const data = req.body as RegisterMemberData;
    data.profileImage = req.file ? req.file.filename : undefined;
    const request = await authService.registerMember(data);
    res.status(201).json({
      message: 'Your registration request has been submitted and is awaiting approval.',
      request: {
        id: request._id.toString(),
        username: request.username,
        role: request.role,
        status: request.status,
      },
    });
  });

  registerManager = asyncHandler(async (req: Request, res: Response, _next: NextFunction): Promise<void> => {
    const data = req.body as RegisterManagerData;
    data.profileImage = req.file ? req.file.filename : undefined;
    const request = await authService.registerManager(data);
    res.status(201).json({
      message: 'Your registration request has been submitted and is awaiting approval.',
      request: {
        id: request._id.toString(),
        username: request.username,
        role: request.role,
        status: request.status,
      },
    });
  });

  getPendingRequests = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can view pending registrations.');
    }
    const requests: PendingRegistrationRequest[] = await registrationService.getPendingRequests();
    res.status(200).json({ data: requests });
  });

  approveRequest = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can approve registrations.');
    }
    const { requestId } = req.params as { requestId: string };
    const result = await registrationService.approveRequest(requestId, req.user.sub);
    res.status(200).json(result);
  });

  rejectRequest = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can reject registrations.');
    }
    const { requestId } = req.params as { requestId: string };
    const result = await registrationService.rejectRequest(requestId, req.user.sub);
    res.status(200).json(result);
  });

  checkUsernameAvailability = asyncHandler(async (req: Request, res: Response, _next: NextFunction): Promise<void> => {
    const { username } = req.query as { username: string };
    if (!username) {
      throw AppError.badRequest('Username query parameter is required.');
    }
    const available = await registrationService.isUsernameAvailable(username);
    res.status(200).json({ available });
  });

  checkEmailAvailability = asyncHandler(async (req: Request, res: Response, _next: NextFunction): Promise<void> => {
    const { email } = req.query as { email: string };
    if (!email) {
      throw AppError.badRequest('Email query parameter is required.');
    }
    const available = await registrationService.isEmailAvailable(email);
    res.status(200).json({ available });
  });
}

export const registrationController = new RegistrationController();
```

FILE: backend/src/controllers/user.controller.ts

```typescript
import { Request, Response, NextFunction } from 'express';
import { asyncHandler } from '../utils/asyncHandler';
import { userService, UpdateProfileData, ChangePasswordData, UserProfile } from '../services/user.service';
import { AppError } from '../utils/AppError';
import { AuthenticatedRequest } from '../types';
import { UserRole } from '../types';

export class UserController {
  getProfile = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user) {
      throw AppError.unauthorized('Authentication required');
    }
    const profile: UserProfile = await userService.getProfile(req.user.sub);
    res.status(200).json(profile);
  });

  updateProfile = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user) {
      throw AppError.unauthorized('Authentication required');
    }
    const data = req.body as UpdateProfileData;
    if (req.file) {
      data.profileImage = req.file.filename;
    }
    const profile: UserProfile = await userService.updateProfile(req.user.sub, data);
    res.status(200).json(profile);
  });

  changePassword = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user) {
      throw AppError.unauthorized('Authentication required');
    }
    const data = req.body as ChangePasswordData;
    const result = await userService.changePassword(req.user.sub, data);
    res.status(200).json(result);
  });

  deleteProfileImage = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user) {
      throw AppError.unauthorized('Authentication required');
    }
    const result = await userService.deleteProfileImage(req.user.sub);
    res.status(200).json(result);
  });

  uploadProfileImage = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user) {
      throw AppError.unauthorized('Authentication required');
    }
    if (!req.file) {
      throw AppError.badRequest('No image file provided.');
    }
    const profile: UserProfile = await userService.updateProfile(req.user.sub, { profileImage: req.file.filename });
    res.status(200).json({ profileImage: profile.profileImage });
  });

  getUsers = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can list users.');
    }
    const page = parseInt(req.query.page as string) || 1;
    const limit = parseInt(req.query.limit as string) || 20;
    const sortBy = (req.query.sortBy as string) || 'createdAt';
    const sortOrder = (req.query.sortOrder as 'asc' | 'desc') || 'desc';
    const role = req.query.role as UserRole | undefined;
    const status = req.query.status as string | undefined;

    const result = await userService.getUsers(page, limit, sortBy, sortOrder, role, status as any);
    res.status(200).json(result);
  });

  getUserById = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can view user details.');
    }
    const { userId } = req.params as { userId: string };
    const profile: UserProfile = await userService.getUserById(userId);
    res.status(200).json(profile);
  });

  updateUserStatus = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can update user status.');
    }
    const { userId } = req.params as { userId: string };
    const { status } = req.body as { status: string };
    const profile: UserProfile = await userService.updateUserStatus(userId, status as any, req.user.sub);
    res.status(200).json(profile);
  });

  updateUserRole = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can update user role.');
    }
    const { userId } = req.params as { userId: string };
    const { role } = req.body as { role: UserRole };
    const profile: UserProfile = await userService.updateUserRole(userId, role, req.user.sub);
    res.status(200).json(profile);
  });

  deleteUser = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can delete users.');
    }
    const { userId } = req.params as { userId: string };
    const result = await userService.deleteUser(userId, req.user.sub);
    res.status(200).json(result);
  });
}

export const userController = new UserController();
```

FILE: backend/src/controllers/company.controller.ts

```typescript
import { Request, Response, NextFunction } from 'express';
import { asyncHandler } from '../utils/asyncHandler';
import { companyService, CompanyData } from '../services/company.service';
import { AppError } from '../utils/AppError';
import { AuthenticatedRequest } from '../types';
import { UserRole } from '../types';

export class CompanyController {
  createCompany = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || (req.user.role !== 'ADMIN' && req.user.role !== 'MANAGER')) {
      throw AppError.forbidden('Only administrators and space managers can create companies.');
    }
    const data = req.body as CompanyData;
    const company = await companyService.createCompany(data);
    res.status(201).json(company);
  });

  getCompanyById = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user) {
      throw AppError.unauthorized('Authentication required');
    }
    const { companyId } = req.params as { companyId: string };
    const company = await companyService.getCompanyById(companyId);
    res.status(200).json(company);
  });

  getCompanies = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can list all companies.');
    }
    const page = parseInt(req.query.page as string) || 1;
    const limit = parseInt(req.query.limit as string) || 20;
    const sortBy = (req.query.sortBy as string) || 'createdAt';
    const sortOrder = (req.query.sortOrder as 'asc' | 'desc') || 'desc';

    const result = await companyService.getCompanies(page, limit, sortBy, sortOrder);
    res.status(200).json(result);
  });

  updateCompany = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can update companies.');
    }
    const { companyId } = req.params as { companyId: string };
    const data = req.body as Partial<CompanyData>;
    const company = await companyService.updateCompany(companyId, data);
    res.status(200).json(company);
  });

  deleteCompany = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can delete companies.');
    }
    const { companyId } = req.params as { companyId: string };
    const result = await companyService.deleteCompany(companyId);
    res.status(200).json(result);
  });

  getCompanyManagersCount = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || (req.user.role !== 'ADMIN' && req.user.role !== 'MANAGER')) {
      throw AppError.forbidden('Insufficient permissions.');
    }
    const { companyId } = req.params as { companyId: string };
    const count = await companyService.getCompanyManagersCount(companyId);
    res.status(200).json({ count });
  });

  getCompanyPendingManagersCount = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can view pending manager counts.');
    }
    const { companyNumber } = req.params as { companyNumber: string };
    const count = await companyService.getCompanyPendingManagersCount(companyNumber);
    res.status(200).json({ count });
  });
}

export const companyController = new CompanyController();
```

FILE: backend/src/controllers/admin.controller.ts

```typescript
import { Request, Response, NextFunction } from 'express';
import { asyncHandler } from '../utils/asyncHandler';
import { adminService, AdminStatistics } from '../services/admin.service';
import { registrationService, PendingRegistrationRequest } from '../services/registration.service';
import { userService, UserProfile } from '../services/user.service';
import { AppError } from '../utils/AppError';
import { AuthenticatedRequest } from '../types';
import { UserRole, UserStatus, RegistrationStatus } from '../types';

export class AdminController {
  getStatistics = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can view statistics.');
    }
    const statistics: AdminStatistics = await adminService.getStatistics();
    res.status(200).json(statistics);
  });

  getPendingRegistrations = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can view pending registrations.');
    }
    const requests: PendingRegistrationRequest[] = await registrationService.getPendingRequests();
    res.status(200).json({ data: requests });
  });

  approveRegistration = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can approve registrations.');
    }
    const { requestId } = req.params as { requestId: string };
    const result = await registrationService.approveRequest(requestId, req.user.sub);
    res.status(200).json(result);
  });

  rejectRegistration = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can reject registrations.');
    }
    const { requestId } = req.params as { requestId: string };
    const result = await registrationService.rejectRequest(requestId, req.user.sub);
    res.status(200).json(result);
  });

  getUsers = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can list users.');
    }
    const page = parseInt(req.query.page as string) || 1;
    const limit = parseInt(req.query.limit as string) || 20;
    const sortBy = (req.query.sortBy as string) || 'createdAt';
    const sortOrder = (req.query.sortOrder as 'asc' | 'desc') || 'desc';
    const role = req.query.role as UserRole | undefined;
    const status = req.query.status as UserStatus | undefined;

    const result = await adminService.getAllUsers(page, limit, sortBy, sortOrder, role, status);
    res.status(200).json(result);
  });

  getUserById = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can view user details.');
    }
    const { userId } = req.params as { userId: string };
    const profile: UserProfile = await userService.getUserById(userId);
    res.status(200).json(profile);
  });

  updateUserStatus = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can update user status.');
    }
    const { userId } = req.params as { userId: string };
    const { status } = req.body as { status: UserStatus };
    const result = await adminService.updateUserStatus(userId, status, req.user.sub);
    res.status(200).json(result);
  });

  updateUserRole = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can update user role.');
    }
    const { userId } = req.params as { userId: string };
    const { role } = req.body as { role: UserRole };
    const result = await adminService.updateUserRole(userId, role, req.user.sub);
    res.status(200).json(result);
  });

  deleteUser = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can delete users.');
    }
    const { userId } = req.params as { userId: string };
    const result = await adminService.deleteUser(userId, req.user.sub);
    res.status(200).json(result);
  });

  getCompanies = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can list companies.');
    }
    const page = parseInt(req.query.page as string) || 1;
    const limit = parseInt(req.query.limit as string) || 20;
    const sortBy = (req.query.sortBy as string) || 'createdAt';
    const sortOrder = (req.query.sortOrder as 'asc' | 'desc') || 'desc';

    const result = await adminService.getAllCompanies(page, limit, sortBy, sortOrder);
    res.status(200).json(result);
  });

  getSpaces = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can list all spaces.');
    }
    const page = parseInt(req.query.page as string) || 1;
    const limit = parseInt(req.query.limit as string) || 20;
    const sortBy = (req.query.sortBy as string) || 'createdAt';
    const sortOrder = (req.query.sortOrder as 'asc' | 'desc') || 'desc';
    const isActive = req.query.isActive !== undefined ? req.query.isActive === 'true' : undefined;

    const result = await adminService.getAllSpaces(page, limit, sortBy, sortOrder, isActive);
    res.status(200).json(result);
  });

  getReservations = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || req.user.role !== 'ADMIN') {
      throw AppError.forbidden('Only administrators can list all reservations.');
    }
    const page = parseInt(req.query.page as string) || 1;
    const limit = parseInt(req.query.limit as string) || 20;
    const sortBy = (req.query.sortBy as string) || 'createdAt';
    const sortOrder = (req.query.sortOrder as 'asc' | 'desc') || 'desc';
    const status = req.query.status as string | undefined;

    const result = await adminService.getAllReservations(page, limit, sortBy, sortOrder, status as any);
    res.status(200).json(result);
  });
}

export const adminController = new AdminController();
```

FILE: backend/src/controllers/space.controller.ts

```typescript
import { Request, Response, NextFunction } from 'express';
import { asyncHandler } from '../utils/asyncHandler';
import { spaceService, CreateSpaceData, UpdateSpaceData } from '../services/space.service';
import { AppError } from '../utils/AppError';
import { AuthenticatedRequest } from '../types';
import { UserRole } from '../types';

export class SpaceController {
  createSpace = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || (req.user.role !== 'MANAGER' && req.user.role !== 'ADMIN')) {
      throw AppError.forbidden('Only space managers and administrators can create spaces.');
    }
    const data = req.body as CreateSpaceData;
    data.companyId = req.user.role === 'ADMIN' ? data.companyId : req.user.sub;
    const space = await spaceService.createSpace(data, req.user.sub);
    res.status(201).json(space);
  });

  getSpaceById = asyncHandler(async (req: Request, res: Response, _next: NextFunction): Promise<void> => {
    const { spaceId } = req.params as { spaceId: string };
    const space = await spaceService.getSpaceById(spaceId);
    res.status(200).json(space);
  });

  getSpacesByCompany = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || (req.user.role !== 'MANAGER' && req.user.role !== 'ADMIN')) {
      throw AppError.forbidden('Only space managers and administrators can list company spaces.');
    }
    const companyId = req.user.role === 'ADMIN' 
      ? (req.query.companyId as string) 
      : req.user.sub;
    
    if (!companyId) {
      throw AppError.badRequest('Company ID is required.');
    }

    const page = parseInt(req.query.page as string) || 1;
    const limit = parseInt(req.query.limit as string) || 20;
    const sortBy = (req.query.sortBy as string) || 'createdAt';
    const sortOrder = (req.query.sortOrder as 'asc' | 'desc') || 'desc';
    const isActive = req.query.isActive !== undefined ? req.query.isActive === 'true' : undefined;

    const result = await spaceService.getSpacesByCompany(companyId, page, limit, sortBy, sortOrder, isActive);
    res.status(200).json(result);
  });

  getPublicSpaces = asyncHandler(async (req: Request, res: Response, _next: NextFunction): Promise<void> => {
    const page = parseInt(req.query.page as string) || 1;
    const limit = parseInt(req.query.limit as string) || 20;
    const sortBy = (req.query.sortBy as string) || 'createdAt';
    const sortOrder = (req.query.sortOrder as 'asc' | 'desc') || 'desc';
    const city = req.query.city as string | undefined;
    const minCapacity = req.query.minCapacity ? parseInt(req.query.minCapacity as string) : undefined;
    const maxPricePerHour = req.query.maxPricePerHour ? parseFloat(req.query.maxPricePerHour as string) : undefined;
    const amenities = req.query.amenities ? (req.query.amenities as string).split(',') : undefined;

    const result = await spaceService.getPublicSpaces(page, limit, sortBy, sortOrder, city, minCapacity, maxPricePerHour, amenities);
    res.status(200).json(result);
  });

  updateSpace = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || (req.user.role !== 'MANAGER' && req.user.role !== 'ADMIN')) {
      throw AppError.forbidden('Only space managers and administrators can update spaces.');
    }
    const { spaceId } = req.params as { spaceId: string };
    const data = req.body as UpdateSpaceData;
    const space = await spaceService.updateSpace(spaceId, data, req.user.sub);
    res.status(200).json(space);
  });

  deleteSpace = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || (req.user.role !== 'MANAGER' && req.user.role !== 'ADMIN')) {
      throw AppError.forbidden('Only space managers and administrators can delete spaces.');
    }
    const { spaceId } = req.params as { spaceId: string };
    const result = await spaceService.deleteSpace(spaceId, req.user.sub);
    res.status(200).json(result);
  });

  toggleSpaceActive = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || (req.user.role !== 'MANAGER' && req.user.role !== 'ADMIN')) {
      throw AppError.forbidden('Only space managers and administrators can toggle space status.');
    }
    const { spaceId } = req.params as { spaceId: string };
    const space = await spaceService.toggleSpaceActive(spaceId, req.user.sub);
    res.status(200).json(space);
  });
}

export const spaceController = new SpaceController();
```

FILE: backend/src/controllers/reservation.controller.ts

```typescript
import { Request, Response, NextFunction } from 'express';
import { asyncHandler } from '../utils/asyncHandler';
import { reservationService, CreateReservationData, ReservationWithDetails } from '../services/reservation.service';
import { AppError } from '../utils/AppError';
import { AuthenticatedRequest } from '../types';
import { UserRole, ReservationStatus } from '../types';

export class ReservationController {
  createReservation = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user) {
      throw AppError.unauthorized('Authentication required');
    }
    const data = req.body as CreateReservationData;
    const reservation: ReservationWithDetails = await reservationService.createReservation(req.user.sub, data);
    res.status(201).json(reservation);
  });

  getReservationById = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user) {
      throw AppError.unauthorized('Authentication required');
    }
    const { reservationId } = req.params as { reservationId: string };
    const reservation: ReservationWithDetails = await reservationService.getReservationById(reservationId, req.user.sub, req.user.role);
    res.status(200).json(reservation);
  });

  getUserReservations = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user) {
      throw AppError.unauthorized('Authentication required');
    }
    const page = parseInt(req.query.page as string) || 1;
    const limit = parseInt(req.query.limit as string) || 20;
    const sortBy = (req.query.sortBy as string) || 'startTime';
    const sortOrder = (req.query.sortOrder as 'asc' | 'desc') || 'desc';
    const status = req.query.status as ReservationStatus | undefined;

    const result = await reservationService.getUserReservations(req.user.sub, page, limit, sortBy, sortOrder, status);
    res.status(200).json(result);
  });

  getCompanyReservations = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || (req.user.role !== 'MANAGER' && req.user.role !== 'ADMIN')) {
      throw AppError.forbidden('Only space managers and administrators can view company reservations.');
    }
    const companyId = req.user.role === 'ADMIN' 
      ? (req.query.companyId as string) 
      : req.user.sub;
    
    if (!companyId) {
      throw AppError.badRequest('Company ID is required.');
    }

    const page = parseInt(req.query.page as string) || 1;
    const limit = parseInt(req.query.limit as string) || 20;
    const sortBy = (req.query.sortBy as string) || 'startTime';
    const sortOrder = (req.query.sortOrder as 'asc' | 'desc') || 'desc';
    const status = req.query.status as ReservationStatus | undefined;

    const result = await reservationService.getCompanyReservations(companyId, page, limit, sortBy, sortOrder, status);
    res.status(200).json(result);
  });

  cancelReservation = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user) {
      throw AppError.unauthorized('Authentication required');
    }
    const { reservationId } = req.params as { reservationId: string };
    const result = await reservationService.cancelReservation(reservationId, req.user.sub, req.user.role);
    res.status(200).json(result);
  });

  confirmReservation = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || (req.user.role !== 'MANAGER' && req.user.role !== 'ADMIN')) {
      throw AppError.forbidden('Only space managers and administrators can confirm reservations.');
    }
    const { reservationId } = req.params as { reservationId: string };
    const result = await reservationService.confirmReservation(reservationId, req.user.sub);
    res.status(200).json(result);
  });

  completeReservation = asyncHandler(async (req: AuthenticatedRequest, res: Response, _next: NextFunction): Promise<void> => {
    if (!req.user || (req.user.role !== 'MANAGER' && req.user.role !== 'ADMIN')) {
      throw AppError.forbidden('Only space managers and administrators can complete reservations.');
    }
    const { reservationId } = req.params as { reservationId: string };
    const result = await reservationService.completeReservation(reservationId, req.user.sub);
    res.status(200).json(result);
  });

  checkAvailability = asyncHandler(async (req: Request, res: Response, _next: NextFunction): Promise<void> => {
    const { spaceId } = req.params as { spaceId: string };
    const { startTime, endTime } = req.query as { startTime: string; endTime: string };
    
    if (!startTime || !endTime) {
      throw AppError.badRequest('startTime and endTime query parameters are required.');
    }

    const result = await reservationService.checkAvailability(spaceId, new Date(startTime), new Date(endTime));
    res.status(200).json(result);
  });
}

export const reservationController = new ReservationController();
```

FILE: backend/src/controllers/index.ts

```typescript
export { authController, AuthController } from './auth.controller';
export { registrationController, RegistrationController } from './registration.controller';
export { userController, UserController } from './user.controller';
export { companyController, CompanyController } from './company.controller';
export { adminController, AdminController } from './admin.controller';
export { spaceController, SpaceController } from './space.controller';
export { reservationController, ReservationController } from './reservation.controller';
```