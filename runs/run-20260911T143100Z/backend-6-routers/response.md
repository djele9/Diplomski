FILE: backend/src/routers/auth.routes.ts

```typescript
/**
 * Routes declared in this file:
 * POST   /api/auth/login
 * POST   /api/auth/admin/login
 * POST   /api/auth/forgot-password
 * GET    /api/auth/reset-password/:token
 * POST   /api/auth/reset-password/:token
 * POST   /api/auth/refresh
 * POST   /api/auth/logout
 * GET    /api/auth/me
 */

import { Router } from 'express';
import { authController } from '../controllers/auth.controller';
import { authenticate } from '../middlewares/auth.middleware';
import { authorize } from '../middlewares/authorize.middleware';
import { validate } from '../middlewares/validate.middleware';
import { body, param } from 'express-validator';
import { UserRole } from '../types';

const router = Router();

/**
 * Public sign-in for Members and Space Managers
 */
router.post(
  '/login',
  validate([
    body('username').isString().notEmpty().withMessage('Username is required.'),
    body('password').isString().notEmpty().withMessage('Password is required.'),
  ]),
  authController.login
);

/**
 * Administrator sign-in through dedicated route
 */
router.post(
  '/admin/login',
  validate([
    body('username').isString().notEmpty().withMessage('Username is required.'),
    body('password').isString().notEmpty().withMessage('Password is required.'),
  ]),
  authController.adminLogin
);

/**
 * Request password reset link
 */
router.post(
  '/forgot-password',
  validate([
    body('identifier').isString().notEmpty().withMessage('Username or email is required.'),
  ]),
  authController.requestPasswordReset
);

/**
 * Verify password reset token (shows new-password form)
 */
router.get(
  '/reset-password/:token',
  validate([
    param('token').isString().notEmpty().withMessage('Reset token is required.'),
  ]),
  authController.verifyPasswordResetToken
);

/**
 * Confirm password reset with new password
 */
router.post(
  '/reset-password/:token',
  validate([
    param('token').isString().notEmpty().withMessage('Reset token is required.'),
    body('newPassword').isString().notEmpty().withMessage('New password is required.'),
    body('confirmPassword').isString().notEmpty().withMessage('Confirm password is required.'),
  ]),
  authController.confirmPasswordReset
);

/**
 * Refresh access token using refresh token
 */
router.post(
  '/refresh',
  validate([
    body('refreshToken').isString().notEmpty().withMessage('Refresh token is required.'),
  ]),
  authController.refreshAccessToken
);

/**
 * Sign out (client discards tokens)
 */
router.post('/logout', authController.logout);

/**
 * Get current authenticated user profile
 */
router.get('/me', authenticate, authorize(UserRole.MEMBER, UserRole.MANAGER, UserRole.ADMIN), authController.getMe);

export default router;
```

FILE: backend/src/routers/registration.routes.ts

```typescript
/**
 * Routes declared in this file:
 * POST   /api/auth/register/member
 * POST   /api/auth/register/manager
 * GET    /api/admin/registration-requests
 * POST   /api/admin/registration-requests/:requestId/approve
 * POST   /api/admin/registration-requests/:requestId/reject
 * GET    /api/auth/check-username
 * GET    /api/auth/check-email
 */

import { Router } from 'express';
import { registrationController } from '../controllers/registration.controller';
import { authenticate } from '../middlewares/auth.middleware';
import { authorize } from '../middlewares/authorize.middleware';
import { validate } from '../middlewares/validate.middleware';
import { validateQuery } from '../middlewares/validate.middleware';
import { upload, validateImageDimensions, handleMulterError } from '../middlewares/upload.middleware';
import { body, param, query } from 'express-validator';
import { UserRole } from '../types';

const router = Router();

/**
 * Register a new Member (public)
 */
router.post(
  '/register/member',
  upload.single('profileImage'),
  handleMulterError,
  validateImageDimensions,
  validate([
    body('username').isString().notEmpty().withMessage('Username is required.'),
    body('password').isString().notEmpty().withMessage('Password is required.'),
    body('firstName').isString().notEmpty().withMessage('First name is required.'),
    body('lastName').isString().notEmpty().withMessage('Last name is required.'),
    body('phone').isString().notEmpty().withMessage('Contact phone is required.'),
    body('email').isEmail().withMessage('Enter a valid email address.'),
  ]),
  registrationController.registerMember
);

/**
 * Register a new Space Manager (public)
 */
router.post(
  '/register/manager',
  upload.single('profileImage'),
  handleMulterError,
  validateImageDimensions,
  validate([
    body('username').isString().notEmpty().withMessage('Username is required.'),
    body('password').isString().notEmpty().withMessage('Password is required.'),
    body('firstName').isString().notEmpty().withMessage('First name is required.'),
    body('lastName').isString().notEmpty().withMessage('Last name is required.'),
    body('phone').isString().notEmpty().withMessage('Contact phone is required.'),
    body('email').isEmail().withMessage('Enter a valid email address.'),
    body('companyName').isString().notEmpty().withMessage('Company name is required.'),
    body('headquartersAddress').isString().notEmpty().withMessage('Headquarters address is required.'),
    body('companyNumber').isString().matches(/^\d{8}$/).withMessage('Company number must be exactly 8 digits.'),
    body('taxId').isString().matches(/^[1-9]\d{8}$/).withMessage('Tax ID must be exactly 9 digits and must not begin with zero.'),
  ]),
  registrationController.registerManager
);

/**
 * List pending registration requests (admin only)
 */
router.get(
  '/admin/registration-requests',
  authenticate,
  authorize(UserRole.ADMIN),
  registrationController.getPendingRequests
);

/**
 * Approve a registration request (admin only)
 */
router.post(
  '/admin/registration-requests/:requestId/approve',
  authenticate,
  authorize(UserRole.ADMIN),
  validate([
    param('requestId').isMongoId().withMessage('Invalid request ID.'),
  ]),
  registrationController.approveRequest
);

/**
 * Reject a registration request (admin only)
 */
router.post(
  '/admin/registration-requests/:requestId/reject',
  authenticate,
  authorize(UserRole.ADMIN),
  validate([
    param('requestId').isMongoId().withMessage('Invalid request ID.'),
  ]),
  registrationController.rejectRequest
);

/**
 * Check username availability (public)
 */
router.get(
  '/check-username',
  validateQuery([
    query('username').isString().notEmpty().withMessage('Username query parameter is required.'),
  ]),
  registrationController.checkUsernameAvailability
);

/**
 * Check email availability (public)
 */
router.get(
  '/check-email',
  validateQuery([
    query('email').isEmail().withMessage('Enter a valid email address.'),
  ]),
  registrationController.checkEmailAvailability
);

export default router;
```

FILE: backend/src/routers/user.routes.ts

```typescript
/**
 * Routes declared in this file:
 * GET    /api/users/profile
 * PUT    /api/users/profile
 * POST   /api/users/profile/password
 * DELETE /api/users/profile/image
 * POST   /api/users/profile/image
 * GET    /api/admin/users
 * GET    /api/admin/users/:userId
 * PUT    /api/admin/users/:userId/status
 * PUT    /api/admin/users/:userId/role
 * DELETE /api/admin/users/:userId
 */

import { Router } from 'express';
import { userController } from '../controllers/user.controller';
import { authenticate } from '../middlewares/auth.middleware';
import { authorize } from '../middlewares/authorize.middleware';
import { validate } from '../middlewares/validate.middleware';
import { upload, validateImageDimensions, handleMulterError } from '../middlewares/upload.middleware';
import { body, param, query } from 'express-validator';
import { UserRole, UserStatus } from '../types';

const router = Router();

/**
 * Get own profile (authenticated user)
 */
router.get(
  '/profile',
  authenticate,
  authorize(UserRole.MEMBER, UserRole.MANAGER, UserRole.ADMIN),
  userController.getProfile
);

/**
 * Update own profile (authenticated user)
 */
router.put(
  '/profile',
  authenticate,
  authorize(UserRole.MEMBER, UserRole.MANAGER, UserRole.ADMIN),
  upload.single('profileImage'),
  handleMulterError,
  validateImageDimensions,
  validate([
    body('firstName').optional().isString().notEmpty().withMessage('First name cannot be empty.'),
    body('lastName').optional().isString().notEmpty().withMessage('Last name cannot be empty.'),
    body('phone').optional().isString().notEmpty().withMessage('Contact phone cannot be empty.'),
    body('email').optional().isEmail().withMessage('Enter a valid email address.'),
  ]),
  userController.updateProfile
);

/**
 * Change own password (authenticated user)
 */
router.post(
  '/profile/password',
  authenticate,
  authorize(UserRole.MEMBER, UserRole.MANAGER, UserRole.ADMIN),
  validate([
    body('currentPassword').isString().notEmpty().withMessage('Current password is required.'),
    body('newPassword').isString().notEmpty().withMessage('New password is required.'),
    body('confirmPassword').isString().notEmpty().withMessage('Confirm password is required.'),
  ]),
  userController.changePassword
);

/**
 * Delete own profile image (authenticated user)
 */
router.delete(
  '/profile/image',
  authenticate,
  authorize(UserRole.MEMBER, UserRole.MANAGER, UserRole.ADMIN),
  userController.deleteProfileImage
);

/**
 * Upload/replace own profile image (authenticated user)
 */
router.post(
  '/profile/image',
  authenticate,
  authorize(UserRole.MEMBER, UserRole.MANAGER, UserRole.ADMIN),
  upload.single('profileImage'),
  handleMulterError,
  validateImageDimensions,
  userController.uploadProfileImage
);

/**
 * List all users (admin only)
 */
router.get(
  '/admin/users',
  authenticate,
  authorize(UserRole.ADMIN),
  validateQuery([
    query('page').optional().isInt({ min: 1 }).withMessage('Page must be a positive integer.'),
    query('limit').optional().isInt({ min: 1, max: 100 }).withMessage('Limit must be between 1 and 100.'),
    query('sortBy').optional().isString(),
    query('sortOrder').optional().isIn(['asc', 'desc']).withMessage('Sort order must be asc or desc.'),
    query('role').optional().isIn(Object.values(UserRole)).withMessage('Invalid role.'),
    query('status').optional().isIn(Object.values(UserStatus)).withMessage('Invalid status.'),
  ]),
  userController.getUsers
);

/**
 * Get user by ID (admin only)
 */
router.get(
  '/admin/users/:userId',
  authenticate,
  authorize(UserRole.ADMIN),
  validate([
    param('userId').isMongoId().withMessage('Invalid user ID.'),
  ]),
  userController.getUserById
);

/**
 * Update user status (admin only)
 */
router.put(
  '/admin/users/:userId/status',
  authenticate,
  authorize(UserRole.ADMIN),
  validate([
    param('userId').isMongoId().withMessage('Invalid user ID.'),
    body('status').isIn(Object.values(UserStatus)).withMessage('Invalid status.'),
  ]),
  userController.updateUserStatus
);

/**
 * Update user role (admin only)
 */
router.put(
  '/admin/users/:userId/role',
  authenticate,
  authorize(UserRole.ADMIN),
  validate([
    param('userId').isMongoId().withMessage('Invalid user ID.'),
    body('role').isIn(Object.values(UserRole)).withMessage('Invalid role.'),
  ]),
  userController.updateUserRole
);

/**
 * Delete user (admin only)
 */
router.delete(
  '/admin/users/:userId',
  authenticate,
  authorize(UserRole.ADMIN),
  validate([
    param('userId').isMongoId().withMessage('Invalid user ID.'),
  ]),
  userController.deleteUser
);

export default router;
```

FILE: backend/src/routers/company.routes.ts

```typescript
/**
 * Routes declared in this file:
 * POST   /api/companies
 * GET    /api/companies/:companyId
 * GET    /api/admin/companies
 * PUT    /api/admin/companies/:companyId
 * DELETE /api/admin/companies/:companyId
 * GET    /api/companies/:companyId/managers/count
 * GET    /api/admin/companies/:companyNumber/pending-managers/count
 */

import { Router } from 'express';
import { companyController } from '../controllers/company.controller';
import { authenticate } from '../middlewares/auth.middleware';
import { authorize } from '../middlewares/authorize.middleware';
import { validate } from '../middlewares/validate.middleware';
import { validateQuery } from '../middlewares/validate.middleware';
import { body, param, query } from 'express-validator';
import { UserRole } from '../types';

const router = Router();

/**
 * Create a new company (admin or manager)
 */
router.post(
  '/companies',
  authenticate,
  authorize(UserRole.ADMIN, UserRole.MANAGER),
  validate([
    body('name').isString().notEmpty().withMessage('Company name is required.'),
    body('headquartersAddress').isString().notEmpty().withMessage('Headquarters address is required.'),
    body('companyNumber').isString().matches(/^\d{8}$/).withMessage('Company number must be exactly 8 digits.'),
    body('taxId').isString().matches(/^[1-9]\d{8}$/).withMessage('Tax ID must be exactly 9 digits and must not begin with zero.'),
  ]),
  companyController.createCompany
);

/**
 * Get company by ID (authenticated user)
 */
router.get(
  '/companies/:companyId',
  authenticate,
  authorize(UserRole.MEMBER, UserRole.MANAGER, UserRole.ADMIN),
  validate([
    param('companyId').isMongoId().withMessage('Invalid company ID.'),
  ]),
  companyController.getCompanyById
);

/**
 * List all companies (admin only)
 */
router.get(
  '/admin/companies',
  authenticate,
  authorize(UserRole.ADMIN),
  validateQuery([
    query('page').optional().isInt({ min: 1 }).withMessage('Page must be a positive integer.'),
    query('limit').optional().isInt({ min: 1, max: 100 }).withMessage('Limit must be between 1 and 100.'),
    query('sortBy').optional().isString(),
    query('sortOrder').optional().isIn(['asc', 'desc']).withMessage('Sort order must be asc or desc.'),
  ]),
  companyController.getCompanies
);

/**
 * Update company (admin only)
 */
router.put(
  '/admin/companies/:companyId',
  authenticate,
  authorize(UserRole.ADMIN),
  validate([
    param('companyId').isMongoId().withMessage('Invalid company ID.'),
    body('name').optional().isString().notEmpty().withMessage('Company name cannot be empty.'),
    body('headquartersAddress').optional().isString().notEmpty().withMessage('Headquarters address cannot be empty.'),
    body('companyNumber').optional().isString().matches(/^\d{8}$/).withMessage('Company number must be exactly 8 digits.'),
    body('taxId').optional().isString().matches(/^[1-9]\d{8}$/).withMessage('Tax ID must be exactly 9 digits and must not begin with zero.'),
  ]),
  companyController.updateCompany
);

/**
 * Delete company (admin only)
 */
router.delete(
  '/admin/companies/:companyId',
  authenticate,
  authorize(UserRole.ADMIN),
  validate([
    param('companyId').isMongoId().withMessage('Invalid company ID.'),
  ]),
  companyController.deleteCompany
);

/**
 * Get approved managers count for a company (admin or manager)
 */
router.get(
  '/companies/:companyId/managers/count',
  authenticate,
  authorize(UserRole.ADMIN, UserRole.MANAGER),
  validate([
    param('companyId').isMongoId().withMessage('Invalid company ID.'),
  ]),
  companyController.getCompanyManagersCount
);

/**
 * Get pending managers count for a company by company number (admin only)
 */
router.get(
  '/admin/companies/:companyNumber/pending-managers/count',
  authenticate,
  authorize(UserRole.ADMIN),
  validate([
    param('companyNumber').isString().matches(/^\d{8}$/).withMessage('Company number must be exactly 8 digits.'),
  ]),
  companyController.getCompanyPendingManagersCount
);

export default router;
```

FILE: backend/src/routers/admin.routes.ts

```typescript
/**
 * Routes declared in this file:
 * GET    /api/admin/statistics
 * GET    /api/admin/registration-requests
 * POST   /api/admin/registration-requests/:requestId/approve
 * POST   /api/admin/registration-requests/:requestId/reject
 * GET    /api/admin/users
 * GET    /api/admin/users/:userId
 * PUT    /api/admin/users/:userId/status
 * PUT    /api/admin/users/:userId/role
 * DELETE /api/admin/users/:userId
 * GET    /api/admin/companies
 * GET    /api/admin/spaces
 * GET    /api/admin/reservations
 */

import { Router } from 'express';
import { adminController } from '../controllers/admin.controller';
import { authenticate } from '../middlewares/auth.middleware';
import { authorize } from '../middlewares/authorize.middleware';
import { validate } from '../middlewares/validate.middleware';
import { validateQuery } from '../middlewares/validate.middleware';
import { param, query } from 'express-validator';
import { UserRole, UserStatus } from '../types';

const router = Router();

/**
 * Get system statistics (admin only)
 */
router.get(
  '/statistics',
  authenticate,
  authorize(UserRole.ADMIN),
  adminController.getStatistics
);

/**
 * List pending registration requests (admin only)
 */
router.get(
  '/registration-requests',
  authenticate,
  authorize(UserRole.ADMIN),
  adminController.getPendingRegistrations
);

/**
 * Approve a registration request (admin only)
 */
router.post(
  '/registration-requests/:requestId/approve',
  authenticate,
  authorize(UserRole.ADMIN),
  validate([
    param('requestId').isMongoId().withMessage('Invalid request ID.'),
  ]),
  adminController.approveRegistration
);

/**
 * Reject a registration request (admin only)
 */
router.post(
  '/registration-requests/:requestId/reject',
  authenticate,
  authorize(UserRole.ADMIN),
  validate([
    param('requestId').isMongoId().withMessage('Invalid request ID.'),
  ]),
  adminController.rejectRegistration
);

/**
 * List all users (admin only)
 */
router.get(
  '/users',
  authenticate,
  authorize(UserRole.ADMIN),
  validateQuery([
    query('page').optional().isInt({ min: 1 }).withMessage('Page must be a positive integer.'),
    query('limit').optional().isInt({ min: 1, max: 100 }).withMessage('Limit must be between 1 and 100.'),
    query('sortBy').optional().isString(),
    query('sortOrder').optional().isIn(['asc', 'desc']).withMessage('Sort order must be asc or desc.'),
    query('role').optional().isIn(Object.values(UserRole)).withMessage('Invalid role.'),
    query('status').optional().isIn(Object.values(UserStatus)).withMessage('Invalid status.'),
  ]),
  adminController.getUsers
);

/**
 * Get user by ID (admin only)
 */
router.get(
  '/users/:userId',
  authenticate,
  authorize(UserRole.ADMIN),
  validate([
    param('userId').isMongoId().withMessage('Invalid user ID.'),
  ]),
  adminController.getUserById
);

/**
 * Update user status (admin only)
 */
router.put(
  '/users/:userId/status',
  authenticate,
  authorize(UserRole.ADMIN),
  validate([
    param('userId').isMongoId().withMessage('Invalid user ID.'),
    body('status').isIn(Object.values(UserStatus)).withMessage('Invalid status.'),
  ]),
  adminController.updateUserStatus
);

/**
 * Update user role (admin only)
 */
router.put(
  '/users/:userId/role',
  authenticate,
  authorize(UserRole.ADMIN),
  validate([
    param('userId').isMongoId().withMessage('Invalid user ID.'),
    body('role').isIn(Object.values(UserRole)).withMessage('Invalid role.'),
  ]),
  adminController.updateUserRole
);

/**
 * Delete user (admin only)
 */
router.delete(
  '/users/:userId',
  authenticate,
  authorize(UserRole.ADMIN),
  validate([
    param('userId').isMongoId().withMessage('Invalid user ID.'),
  ]),
  adminController.deleteUser
);

/**
 * List all companies (admin only)
 */
router.get(
  '/companies',
  authenticate,
  authorize(UserRole.ADMIN),
  validateQuery([
    query('page').optional().isInt({ min: 1 }).withMessage('Page must be a positive integer.'),
    query('limit').optional().isInt({ min: 1, max: 100 }).withMessage('Limit must be between 1 and 100.'),
    query('sortBy').optional().isString(),
    query('sortOrder').optional().isIn(['asc', 'desc']).withMessage('Sort order must be asc or desc.'),
  ]),
  adminController.getCompanies
);

/**
 * List all spaces (admin only)
 */
router.get(
  '/spaces',
  authenticate,
  authorize(UserRole.ADMIN),
  validateQuery([
    query('page').optional().isInt({ min: 1 }).withMessage('Page must be a positive integer.'),
    query('limit').optional().isInt({ min: 1, max: 100 }).withMessage('Limit must be between 1 and 100.'),
    query('sortBy').optional().isString(),
    query('sortOrder').optional().isIn(['asc', 'desc']).withMessage('Sort order must be asc or desc.'),
    query('isActive').optional().isBoolean().withMessage('isActive must be a boolean.'),
  ]),
  adminController.getSpaces
);

/**
 * List all reservations (admin only)
 */
router.get(
  '/reservations',
  authenticate,
  authorize(UserRole.ADMIN),
  validateQuery([
    query('page').optional().isInt({ min: 1 }).withMessage('Page must be a positive integer.'),
    query('limit').optional().isInt({ min: 1, max: 100 }).withMessage('Limit must be between 1 and 100.'),
    query('sortBy').optional().isString(),
    query('sortOrder').optional().isIn(['asc', 'desc']).withMessage('Sort order must be asc or desc.'),
    query('status').optional().isString(),
  ]),
  adminController.getReservations
);

export default router;
```

FILE: backend/src/routers/space.routes.ts

```typescript
/**
 * Routes declared in this file:
 * POST   /api/spaces
 * GET    /api/spaces/public
 * GET    /api/spaces/:spaceId
 * GET    /api/spaces/company
 * PUT    /api/spaces/:spaceId
 * DELETE /api/spaces/:spaceId
 * PATCH  /api/spaces/:spaceId/toggle-active
 */

import { Router } from 'express';
import { spaceController } from '../controllers/space.controller';
import { authenticate } from '../middlewares/auth.middleware';
import { authorize } from '../middlewares/authorize.middleware';
import { validate } from '../middlewares/validate.middleware';
import { validateQuery } from '../middlewares/validate.middleware';
import { body, param, query } from 'express-validator';
import { UserRole } from '../types';

const router = Router();

/**
 * Create a new space (manager or admin)
 */
router.post(
  '/spaces',
  authenticate,
  authorize(UserRole.MANAGER, UserRole.ADMIN),
  validate([
    body('name').isString().notEmpty().withMessage('Space name is required.'),
    body('description').isString().notEmpty().withMessage('Description is required.'),
    body('address').isString().notEmpty().withMessage('Address is required.'),
    body('city').isString().notEmpty().withMessage('City is required.'),
    body('capacity').isInt({ min: 1 }).withMessage('Capacity must be at least 1.'),
    body('pricePerHour').isFloat({ min: 0 }).withMessage('Price per hour must be a positive number.'),
    body('amenities').optional().isArray().withMessage('Amenities must be an array.'),
    body('images').optional().isArray().withMessage('Images must be an array.'),
    body('companyId').optional().isMongoId().withMessage('Invalid company ID.'),
  ]),
  spaceController.createSpace
);

/**
 * List public spaces (public)
 */
router.get(
  '/spaces/public',
  validateQuery([
    query('page').optional().isInt({ min: 1 }).withMessage('Page must be a positive integer.'),
    query('limit').optional().isInt({ min: 1, max: 100 }).withMessage('Limit must be between 1 and 100.'),
    query('sortBy').optional().isString(),
    query('sortOrder').optional().isIn(['asc', 'desc']).withMessage('Sort order must be asc or desc.'),
    query('city').optional().isString(),
    query('minCapacity').optional().isInt({ min: 1 }).withMessage('Minimum capacity must be a positive integer.'),
    query('maxPricePerHour').optional().isFloat({ min: 0 }).withMessage('Maximum price per hour must be a positive number.'),
    query('amenities').optional().isString(),
  ]),
  spaceController.getPublicSpaces
);

/**
 * Get space by ID (public)
 */
router.get(
  '/spaces/:spaceId',
  validate([
    param('spaceId').isMongoId().withMessage('Invalid space ID.'),
  ]),
  spaceController.getSpaceById
);

/**
 * List spaces for authenticated user's company (manager or admin)
 */
router.get(
  '/spaces/company',
  authenticate,
  authorize(UserRole.MANAGER, UserRole.ADMIN),
  validateQuery([
    query('page').optional().isInt({ min: 1 }).withMessage('Page must be a positive integer.'),
    query('limit').optional().isInt({ min: 1, max: 100 }).withMessage('Limit must be between 1 and 100.'),
    query('sortBy').optional().isString(),
    query('sortOrder').optional().isIn(['asc', 'desc']).withMessage('Sort order must be asc or desc.'),
    query('isActive').optional().isBoolean().withMessage('isActive must be a boolean.'),
    query('companyId').optional().isMongoId().withMessage('Invalid company ID.'),
  ]),
  spaceController.getSpacesByCompany
);

/**
 * Update space (manager or admin)
 */
router.put(
  '/spaces/:spaceId',
  authenticate,
  authorize(UserRole.MANAGER, UserRole.ADMIN),
  validate([
    param('spaceId').isMongoId().withMessage('Invalid space ID.'),
    body('name').optional().isString().notEmpty().withMessage('Space name cannot be empty.'),
    body('description').optional().isString().notEmpty().withMessage('Description cannot be empty.'),
    body('address').optional().isString().notEmpty().withMessage('Address cannot be empty.'),
    body('city').optional().isString().notEmpty().withMessage('City cannot be empty.'),
    body('capacity').optional().isInt({ min: 1 }).withMessage('Capacity must be at least 1.'),
    body('pricePerHour').optional().isFloat({ min: 0 }).withMessage('Price per hour must be a positive number.'),
    body('amenities').optional().isArray().withMessage('Amenities must be an array.'),
    body('images').optional().isArray().withMessage('Images must be an array.'),
    body('isActive').optional().isBoolean().withMessage('isActive must be a boolean.'),
  ]),
  spaceController.updateSpace
);

/**
 * Delete space (manager or admin)
 */
router.delete(
  '/spaces/:spaceId',
  authenticate,
  authorize(UserRole.MANAGER, UserRole.ADMIN),
  validate([
    param('spaceId').isMongoId().withMessage('Invalid space ID.'),
  ]),
  spaceController.deleteSpace
);

/**
 * Toggle space active status (manager or admin)
 */
router.patch(
  '/spaces/:spaceId/toggle-active',
  authenticate,
  authorize(UserRole.MANAGER, UserRole.ADMIN),
  validate([
    param('spaceId').isMongoId().withMessage('Invalid space ID.'),
  ]),
  spaceController.toggleSpaceActive
);

export default router;
```

FILE: backend/src/routers/reservation.routes.ts

```typescript
/**
 * Routes declared in this file:
 * POST   /api/reservations
 * GET    /api/reservations
 * GET    /api/reservations/:reservationId
 * GET    /api/reservations/company
 * POST   /api/reservations/:reservationId/cancel
 * POST   /api/reservations/:reservationId/confirm
 * POST   /api/reservations/:reservationId/complete
 * GET    /api/spaces/:spaceId/availability
 */

import { Router } from 'express';
import { reservationController } from '../controllers/reservation.controller';
import { authenticate } from '../middlewares/auth.middleware';
import { authorize } from '../middlewares/authorize.middleware';
import { validate } from '../middlewares/validate.middleware';
import { validateQuery } from '../middlewares/validate.middleware';
import { body, param, query } from 'express-validator';
import { UserRole, ReservationStatus } from '../types';

const router = Router();

/**
 * Create a new reservation (authenticated user)
 */
router.post(
  '/reservations',
  authenticate,
  authorize(UserRole.MEMBER, UserRole.MANAGER, UserRole.ADMIN),
  validate([
    body('spaceId').isMongoId().withMessage('Invalid space ID.'),
    body('startTime').isISO8601().withMessage('Start time must be a valid ISO 8601 date.'),
    body('endTime').isISO8601().withMessage('End time must be a valid ISO 8601 date.'),
  ]),
  reservationController.createReservation
);

/**
 * List own reservations (authenticated user)
 */
router.get(
  '/reservations',
  authenticate,
  authorize(UserRole.MEMBER, UserRole.MANAGER, UserRole.ADMIN),
  validateQuery([
    query('page').optional().isInt({ min: 1 }).withMessage('Page must be a positive integer.'),
    query('limit').optional().isInt({ min: 1, max: 100 }).withMessage('Limit must be between 1 and 100.'),
    query('sortBy').optional().isString(),
    query('sortOrder').optional().isIn(['asc', 'desc']).withMessage('Sort order must be asc or desc.'),
    query('status').optional().isIn(Object.values(ReservationStatus)).withMessage('Invalid status.'),
  ]),
  reservationController.getUserReservations
);

/**
 * Get reservation by ID (authenticated user)
 */
router.get(
  '/reservations/:reservationId',
  authenticate,
  authorize(UserRole.MEMBER, UserRole.MANAGER, UserRole.ADMIN),
  validate([
    param('reservationId').isMongoId().withMessage('Invalid reservation ID.'),
  ]),
  reservationController.getReservationById
);

/**
 * List company reservations (manager or admin)
 */
router.get(
  '/reservations/company',
  authenticate,
  authorize(UserRole.MANAGER, UserRole.ADMIN),
  validateQuery([
    query('page').optional().isInt({ min: 1 }).withMessage('Page must be a positive integer.'),
    query('limit').optional().isInt({ min: 1, max: 100 }).withMessage('Limit must be between 1 and 100.'),
    query('sortBy').optional().isString(),
    query('sortOrder').optional().isIn(['asc', 'desc']).withMessage('Sort order must be asc or desc.'),
    query('status').optional().isIn(Object.values(ReservationStatus)).withMessage('Invalid status.'),
    query('companyId').optional().isMongoId().withMessage('Invalid company ID.'),
  ]),
  reservationController.getCompanyReservations
);

/**
 * Cancel reservation (authenticated user)
 */
router.post(
  '/reservations/:reservationId/cancel',
  authenticate,
  authorize(UserRole.MEMBER, UserRole.MANAGER, UserRole.ADMIN),
  validate([
    param('reservationId').isMongoId().withMessage('Invalid reservation ID.'),
  ]),
  reservationController.cancelReservation
);

/**
 * Confirm reservation (manager or admin)
 */
router.post(
  '/reservations/:reservationId/confirm',
  authenticate,
  authorize(UserRole.MANAGER, UserRole.ADMIN),
  validate([
    param('reservationId').isMongoId().withMessage('Invalid reservation ID.'),
  ]),
  reservationController.confirmReservation
);

/**
 * Complete reservation (manager or admin)
 */
router.post(
  '/reservations/:reservationId/complete',
  authenticate,
  authorize(UserRole.MANAGER, UserRole.ADMIN),
  validate([
    param('reservationId').isMongoId().withMessage('Invalid reservation ID.'),
  ]),
  reservationController.completeReservation
);

/**
 * Check space availability (public)
 */
router.get(
  '/spaces/:spaceId/availability',
  validate([
    param('spaceId').isMongoId().withMessage('Invalid space ID.'),
    query('startTime').isISO8601().withMessage('Start time must be a valid ISO 8601 date.'),
    query('endTime').isISO8601().withMessage('End time must be a valid ISO 8601 date.'),
  ]),
  reservationController.checkAvailability
);

export default router;
```