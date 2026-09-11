FILE: backend/src/services/auth.service.ts

```typescript
import { User, IUser } from '../models/user.model';
import { RegistrationRequest, IRegistrationRequest } from '../models/registration-request.model';
import { PasswordResetToken, IPasswordResetToken } from '../models/password-reset-token.model';
import { Company, ICompany } from '../models/company.model';
import { AppError } from '../utils/AppError';
import { UserRole, UserStatus, RegistrationStatus } from '../types';
import { hashPassword, verifyPassword, validatePasswordPolicy } from '../utils/password';
import { signTokenPair, signPasswordResetToken, verifyPasswordResetToken } from '../utils/token';
import mongoose, { ClientSession } from 'mongoose';

export interface LoginResult {
  user: {
    id: string;
    username: string;
    firstName: string;
    lastName: string;
    role: UserRole;
    profileImage: string;
  };
  tokens: {
    accessToken: string;
    refreshToken: string;
  };
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

export interface PasswordResetRequestResult {
  message: string;
}

export interface PasswordResetVerifyResult {
  valid: boolean;
  userId?: string;
  token?: string;
}

export interface PasswordResetConfirmResult {
  message: string;
}

export class AuthService {
  async login(
    username: string,
    password: string,
    isAdminRoute: boolean = false,
    now: Date = new Date()
  ): Promise<LoginResult> {
    const user = await User.findOne({ username }).select('+passwordHash').lean();

    if (!user) {
      throw AppError.unauthorized('Invalid username or password.');
    }

    if (isAdminRoute) {
      if (user.role !== UserRole.ADMIN) {
        throw AppError.unauthorized('Invalid username or password.');
      }
    } else {
      if (user.role === UserRole.ADMIN) {
        throw AppError.unauthorized('Invalid username or password.');
      }
    }

    const isValid = await verifyPassword(password, user.passwordHash);
    if (!isValid) {
      throw AppError.unauthorized('Invalid username or password.');
    }

    if (user.status !== UserStatus.APPROVED) {
      if (user.status === UserStatus.PENDING) {
        throw AppError.forbidden('Your registration is still awaiting administrator approval.');
      }
      if (user.status === UserStatus.REJECTED) {
        throw AppError.forbidden('Your registration request was rejected.');
      }
      throw AppError.forbidden('Account is not active');
    }

    const tokens = signTokenPair({
      sub: user._id.toString(),
      username: user.username,
      role: user.role,
    });

    return {
      user: {
        id: user._id.toString(),
        username: user.username,
        firstName: user.firstName,
        lastName: user.lastName,
        role: user.role,
        profileImage: user.profileImage,
      },
      tokens,
    };
  }

  async registerMember(data: RegisterMemberData, session?: ClientSession): Promise<IRegistrationRequest> {
    const passwordValidation = validatePasswordPolicy(data.password);
    if (!passwordValidation.valid) {
      throw AppError.badRequest(passwordValidation.message!, [{ field: 'password', message: passwordValidation.message! }]);
    }

    const existingUser = await User.findOne({
      $or: [{ username: data.username }, { email: data.email }],
    }).session(session || null);

    if (existingUser) {
      if (existingUser.username === data.username) {
        throw AppError.conflict('That username is already taken.');
      }
      throw AppError.conflict('An account with that email address already exists.');
    }

    const existingRequest = await RegistrationRequest.findOne({
      $or: [{ username: data.username }, { email: data.email }],
    }).session(session || null);

    if (existingRequest) {
      if (existingRequest.username === data.username) {
        throw AppError.conflict('That username is already taken.');
      }
      throw AppError.conflict('An account with that email address already exists.');
    }

    const passwordHash = await hashPassword(data.password);

    const registrationRequest = new RegistrationRequest({
      username: data.username,
      passwordHash,
      firstName: data.firstName,
      lastName: data.lastName,
      phone: data.phone,
      email: data.email.toLowerCase(),
      role: UserRole.MEMBER,
      profileImage: data.profileImage || 'default-avatar.png',
      status: RegistrationStatus.PENDING,
      submittedAt: new Date(),
    });

    await registrationRequest.save({ session: session || null });
    return registrationRequest;
  }

  async registerManager(data: RegisterManagerData, session?: ClientSession): Promise<IRegistrationRequest> {
    const passwordValidation = validatePasswordPolicy(data.password);
    if (!passwordValidation.valid) {
      throw AppError.badRequest(passwordValidation.message!, [{ field: 'password', message: passwordValidation.message! }]);
    }

    if (!/^\d{8}$/.test(data.companyNumber)) {
      throw AppError.badRequest('Company number must be exactly 8 digits.', [{ field: 'companyNumber', message: 'Company number must be exactly 8 digits.' }]);
    }

    if (!/^[1-9]\d{8}$/.test(data.taxId)) {
      throw AppError.badRequest('Tax ID must be exactly 9 digits and must not begin with zero.', [{ field: 'taxId', message: 'Tax ID must be exactly 9 digits and must not begin with zero.' }]);
    }

    const existingUser = await User.findOne({
      $or: [{ username: data.username }, { email: data.email }],
    }).session(session || null);

    if (existingUser) {
      if (existingUser.username === data.username) {
        throw AppError.conflict('That username is already taken.');
      }
      throw AppError.conflict('An account with that email address already exists.');
    }

    const existingRequest = await RegistrationRequest.findOne({
      $or: [{ username: data.username }, { email: data.email }],
    }).session(session || null);

    if (existingRequest) {
      if (existingRequest.username === data.username) {
        throw AppError.conflict('That username is already taken.');
      }
      throw AppError.conflict('An account with that email address already exists.');
    }

    let company: ICompany | null = null;
    const existingCompany = await Company.findOne({
      $or: [{ companyNumber: data.companyNumber }, { taxId: data.taxId }],
    }).session(session || null);

    if (existingCompany) {
      if (existingCompany.companyNumber === data.companyNumber && existingCompany.taxId !== data.taxId) {
        throw AppError.conflict('A different company is already registered with that company number.');
      }
      if (existingCompany.taxId === data.taxId && existingCompany.companyNumber !== data.companyNumber) {
        throw AppError.conflict('A different company is already registered with that tax ID.');
      }
      company = existingCompany;
    }

    const managerCount = await this.countCompanyManagers(company?._id || new mongoose.Types.ObjectId(), session);

    if (managerCount >= 2) {
      throw AppError.conflict('This company already has the maximum of two space managers.');
    }

    const passwordHash = await hashPassword(data.password);

    const registrationRequest = new RegistrationRequest({
      username: data.username,
      passwordHash,
      firstName: data.firstName,
      lastName: data.lastName,
      phone: data.phone,
      email: data.email.toLowerCase(),
      role: UserRole.MANAGER,
      companyName: data.companyName,
      headquartersAddress: data.headquartersAddress,
      companyNumber: data.companyNumber,
      taxId: data.taxId,
      profileImage: data.profileImage || 'default-avatar.png',
      status: RegistrationStatus.PENDING,
      submittedAt: new Date(),
    });

    await registrationRequest.save({ session: session || null });
    return registrationRequest;
  }

  private async countCompanyManagers(companyId: mongoose.Types.ObjectId, session?: ClientSession): Promise<number> {
    const approvedManagers = await User.countDocuments({
      company: companyId,
      role: UserRole.MANAGER,
      status: UserStatus.APPROVED,
    }).session(session || null);

    const pendingManagers = await RegistrationRequest.countDocuments({
      companyNumber: (await Company.findById(companyId).session(session || null))?.companyNumber,
      role: UserRole.MANAGER,
      status: RegistrationStatus.PENDING,
    }).session(session || null);

    return approvedManagers + pendingManagers;
  }

  async requestPasswordReset(identifier: string, now: Date = new Date()): Promise<PasswordResetRequestResult> {
    const user = await User.findOne({
      $or: [{ username: identifier }, { email: identifier.toLowerCase() }],
      status: UserStatus.APPROVED,
    }).lean();

    if (!user) {
      return { message: 'If an account exists, a reset link has been sent to your email.' };
    }

    await PasswordResetToken.deleteMany({ user: user._id, usedAt: { $exists: false } });

    const expiresAt = new Date(now.getTime() + 30 * 60 * 1000);
    const tokenPayload = {
      sub: user._id.toString(),
      username: user.username,
      role: user.role,
      type: 'password-reset' as const,
    };
    const token = signPasswordResetToken(tokenPayload);

    await PasswordResetToken.create({
      user: user._id,
      token,
      expiresAt,
    });

    return { message: 'If an account exists, a reset link has been sent to your email.' };
  }

  async verifyPasswordResetToken(token: string, now: Date = new Date()): Promise<PasswordResetVerifyResult> {
    let payload: { sub: string; type: string };
    try {
      payload = verifyPasswordResetToken(token) as { sub: string; type: string };
    } catch {
      throw AppError.gone('This reset link has expired. Please request a new one.');
    }

    if (payload.type !== 'password-reset') {
      throw AppError.gone('This reset link has expired. Please request a new one.');
    }

    const resetToken = await PasswordResetToken.findOne({ token }).lean();

    if (!resetToken) {
      throw AppError.gone('This reset link has expired. Please request a new one.');
    }

    if (resetToken.usedAt) {
      throw AppError.gone('This reset link has already been used.');
    }

    if (resetToken.expiresAt < now) {
      throw AppError.gone('This reset link has expired. Please request a new one.');
    }

    return { valid: true, userId: resetToken.user.toString(), token };
  }

  async confirmPasswordReset(token: string, newPassword: string, confirmPassword: string, now: Date = new Date()): Promise<PasswordResetConfirmResult> {
    if (newPassword !== confirmPassword) {
      throw AppError.badRequest('The two passwords do not match.', [{ field: 'confirmPassword', message: 'The two passwords do not match.' }]);
    }

    const passwordValidation = validatePasswordPolicy(newPassword);
    if (!passwordValidation.valid) {
      throw AppError.badRequest(passwordValidation.message!, [{ field: 'password', message: passwordValidation.message! }]);
    }

    const verification = await this.verifyPasswordResetToken(token, now);
    if (!verification.valid || !verification.userId || !verification.token) {
      throw AppError.gone('This reset link has expired. Please request a new one.');
    }

    const session = await mongoose.startSession();
    session.startTransaction();

    try {
      const passwordHash = await hashPassword(newPassword);

      await User.findByIdAndUpdate(
        verification.userId,
        { passwordHash },
        { session }
      );

      await PasswordResetToken.findOneAndUpdate(
        { token: verification.token },
        { usedAt: now },
        { session }
      );

      await PasswordResetToken.updateMany(
        { user: verification.userId, usedAt: { $exists: false }, _id: { $ne: (await PasswordResetToken.findOne({ token: verification.token }).lean())?._id } },
        { usedAt: now },
        { session }
      );

      await session.commitTransaction();
      return { message: 'Your password has been changed successfully.' };
    } catch (error) {
      await session.abortTransaction();
      throw error;
    } finally {
      await session.endSession();
    }
  }

  async refreshAccessToken(refreshToken: string): Promise<{ accessToken: string }> {
    let payload: { sub: string; username: string; role: UserRole };
    try {
      payload = verifyPasswordResetToken(refreshToken) as { sub: string; username: string; role: UserRole };
    } catch {
      throw AppError.unauthorized('Invalid or expired refresh token');
    }

    const user = await User.findById(payload.sub).lean();
    if (!user || user.status !== UserStatus.APPROVED) {
      throw AppError.unauthorized('User no longer exists or is not active');
    }

    const accessToken = signTokenPair({
      sub: user._id.toString(),
      username: user.username,
      role: user.role,
    }).accessToken;

    return { accessToken };
  }
}

export const authService = new AuthService();
```

FILE: backend/src/services/registration.service.ts

```typescript
import { RegistrationRequest, IRegistrationRequest } from '../models/registration-request.model';
import { User, IUser } from '../models/user.model';
import { Company, ICompany } from '../models/company.model';
import { AppError } from '../utils/AppError';
import { UserRole, UserStatus, RegistrationStatus } from '../types';
import mongoose, { ClientSession } from 'mongoose';

export interface PendingRegistrationRequest {
  id: string;
  username: string;
  firstName: string;
  lastName: string;
  email: string;
  role: UserRole;
  submittedAt: Date;
  companyName?: string;
  headquartersAddress?: string;
  companyNumber?: string;
  taxId?: string;
  profileImage: string;
}

export interface RegistrationDecisionResult {
  message: string;
  user?: {
    id: string;
    username: string;
    role: UserRole;
  };
}

export class RegistrationService {
  async getPendingRequests(): Promise<PendingRegistrationRequest[]> {
    const requests = await RegistrationRequest.find({ status: RegistrationStatus.PENDING })
      .sort({ submittedAt: 1 })
      .lean();

    return requests.map(req => ({
      id: req._id.toString(),
      username: req.username,
      firstName: req.firstName,
      lastName: req.lastName,
      email: req.email,
      role: req.role,
      submittedAt: req.submittedAt,
      companyName: req.companyName,
      headquartersAddress: req.headquartersAddress,
      companyNumber: req.companyNumber,
      taxId: req.taxId,
      profileImage: req.profileImage,
    }));
  }

  async approveRequest(requestId: string, adminId: string, now: Date = new Date()): Promise<RegistrationDecisionResult> {
    const session = await mongoose.startSession();
    session.startTransaction();

    try {
      const request = await RegistrationRequest.findById(requestId).session(session);
      if (!request) {
        throw AppError.notFound('Registration request not found');
      }

      if (request.status !== RegistrationStatus.PENDING) {
        throw AppError.conflict('This registration request has already been decided.');
      }

      if (request.role === UserRole.MANAGER) {
        await this.validateCompanyManagerLimit(request, session);
      }

      let companyId: mongoose.Types.ObjectId | undefined;

      if (request.role === UserRole.MANAGER && request.companyNumber && request.taxId) {
        let company = await Company.findOne({
          $or: [{ companyNumber: request.companyNumber }, { taxId: request.taxId }],
        }).session(session);

        if (!company) {
          company = new Company({
            name: request.companyName!,
            headquartersAddress: request.headquartersAddress!,
            companyNumber: request.companyNumber,
            taxId: request.taxId,
          });
          await company.save({ session });
        }
        companyId = company._id;
      }

      const user = new User({
        username: request.username,
        passwordHash: request.passwordHash,
        firstName: request.firstName,
        lastName: request.lastName,
        phone: request.phone,
        email: request.email,
        role: request.role,
        status: UserStatus.APPROVED,
        profileImage: request.profileImage,
        company: companyId,
      });

      await user.save({ session });

      request.status = RegistrationStatus.APPROVED;
      request.decidedAt = now;
      request.decidedBy = new mongoose.Types.ObjectId(adminId);
      await request.save({ session });

      await session.commitTransaction();

      return {
        message: 'Registration request approved successfully.',
        user: {
          id: user._id.toString(),
          username: user.username,
          role: user.role,
        },
      };
    } catch (error) {
      await session.abortTransaction();
      throw error;
    } finally {
      await session.endSession();
    }
  }

  async rejectRequest(requestId: string, adminId: string, now: Date = new Date()): Promise<RegistrationDecisionResult> {
    const request = await RegistrationRequest.findById(requestId);
    if (!request) {
      throw AppError.notFound('Registration request not found');
    }

    if (request.status !== RegistrationStatus.PENDING) {
      throw AppError.conflict('This registration request has already been decided.');
    }

    request.status = RegistrationStatus.REJECTED;
    request.decidedAt = now;
    request.decidedBy = new mongoose.Types.ObjectId(adminId);
    await request.save();

    return { message: 'Registration request rejected.' };
  }

  private async validateCompanyManagerLimit(request: IRegistrationRequest, session: ClientSession): Promise<void> {
    if (!request.companyNumber || !request.taxId) {
      return;
    }

    const company = await Company.findOne({
      $or: [{ companyNumber: request.companyNumber }, { taxId: request.taxId }],
    }).session(session);

    const companyId = company?._id;

    const approvedManagers = await User.countDocuments({
      company: companyId,
      role: UserRole.MANAGER,
      status: UserStatus.APPROVED,
    }).session(session);

    const pendingManagers = await RegistrationRequest.countDocuments({
      companyNumber: request.companyNumber,
      role: UserRole.MANAGER,
      status: RegistrationStatus.PENDING,
      _id: { $ne: request._id },
    }).session(session);

    if (approvedManagers + pendingManagers >= 2) {
      throw AppError.conflict('This company already has the maximum of two space managers.');
    }
  }

  async isUsernameAvailable(username: string, excludeRequestId?: string): Promise<boolean> {
    const user = await User.findOne({ username }).lean();
    if (user) return false;

    const query: Record<string, unknown> = { username };
    if (excludeRequestId) {
      query._id = { $ne: excludeRequestId };
    }
    const request = await RegistrationRequest.findOne(query).lean();
    return !request;
  }

  async isEmailAvailable(email: string, excludeRequestId?: string): Promise<boolean> {
    const user = await User.findOne({ email: email.toLowerCase() }).lean();
    if (user) return false;

    const query: Record<string, unknown> = { email: email.toLowerCase() };
    if (excludeRequestId) {
      query._id = { $ne: excludeRequestId };
    }
    const request = await RegistrationRequest.findOne(query).lean();
    return !request;
  }

  async releaseUsername(username: string): Promise<void> {
    await RegistrationRequest.deleteOne({ username, status: RegistrationStatus.REJECTED });
  }
}

export const registrationService = new RegistrationService();
```

FILE: backend/src/services/user.service.ts

```typescript
import { User, IUser } from '../models/user.model';
import { AppError } from '../utils/AppError';
import { UserRole, UserStatus } from '../types';
import { hashPassword, validatePasswordPolicy } from '../utils/password';
import mongoose, { ClientSession } from 'mongoose';

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

export interface UserProfile {
  id: string;
  username: string;
  firstName: string;
  lastName: string;
  phone: string;
  email: string;
  role: UserRole;
  status: UserStatus;
  profileImage: string;
  company?: string;
  createdAt: Date;
  updatedAt: Date;
}

export class UserService {
  async getProfile(userId: string): Promise<UserProfile> {
    const user = await User.findById(userId).lean();
    if (!user) {
      throw AppError.notFound('User not found');
    }

    return this.mapToProfile(user);
  }

  async updateProfile(userId: string, data: UpdateProfileData): Promise<UserProfile> {
    const user = await User.findById(userId);
    if (!user) {
      throw AppError.notFound('User not found');
    }

    if (data.email) {
      const existingUser = await User.findOne({
        email: data.email.toLowerCase(),
        _id: { $ne: userId },
      }).lean();

      if (existingUser) {
        throw AppError.conflict('An account with that email address already exists.');
      }
      user.email = data.email.toLowerCase();
    }

    if (data.firstName) user.firstName = data.firstName;
    if (data.lastName) user.lastName = data.lastName;
    if (data.phone) user.phone = data.phone;
    if (data.profileImage) user.profileImage = data.profileImage;

    await user.save();
    return this.mapToProfile(user);
  }

  async changePassword(userId: string, data: ChangePasswordData): Promise<{ message: string }> {
    if (data.newPassword !== data.confirmPassword) {
      throw AppError.badRequest('The two passwords do not match.', [{ field: 'confirmPassword', message: 'The two passwords do not match.' }]);
    }

    const passwordValidation = validatePasswordPolicy(data.newPassword);
    if (!passwordValidation.valid) {
      throw AppError.badRequest(passwordValidation.message!, [{ field: 'password', message: passwordValidation.message! }]);
    }

    const user = await User.findById(userId).select('+passwordHash');
    if (!user) {
      throw AppError.notFound('User not found');
    }

    const isValid = await require('../utils/password').verifyPassword(data.currentPassword, user.passwordHash);
    if (!isValid) {
      throw AppError.badRequest('Current password is incorrect.', [{ field: 'currentPassword', message: 'Current password is incorrect.' }]);
    }

    user.passwordHash = await hashPassword(data.newPassword);
    await user.save();

    return { message: 'Password changed successfully.' };
  }

  async deleteProfileImage(userId: string): Promise<{ message: string; profileImage: string }> {
    const user = await User.findById(userId);
    if (!user) {
      throw AppError.notFound('User not found');
    }

    const oldImage = user.profileImage;
    user.profileImage = 'default-avatar.png';
    await user.save();

    return { message: 'Profile image reset to default.', profileImage: user.profileImage };
  }

  async getUsers(
    page: number = 1,
    limit: number = 20,
    sortBy: string = 'createdAt',
    sortOrder: 'asc' | 'desc' = 'desc',
    role?: UserRole,
    status?: UserStatus
  ): Promise<{ data: UserProfile[]; total: number; page: number; limit: number; totalPages: number }> {
    const query: Record<string, unknown> = {};
    if (role) query.role = role;
    if (status) query.status = status;

    const sort: Record<string, 1 | -1> = { [sortBy]: sortOrder === 'asc' ? 1 : -1 };

    const [users, total] = await Promise.all([
      User.find(query)
        .sort(sort)
        .skip((page - 1) * limit)
        .limit(limit)
        .lean(),
      User.countDocuments(query),
    ]);

    return {
      data: users.map(u => this.mapToProfile(u)),
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async getUserById(userId: string): Promise<UserProfile> {
    const user = await User.findById(userId).lean();
    if (!user) {
      throw AppError.notFound('User not found');
    }
    return this.mapToProfile(user);
  }

  async updateUserStatus(userId: string, status: UserStatus, adminId: string): Promise<UserProfile> {
    const user = await User.findById(userId);
    if (!user) {
      throw AppError.notFound('User not found');
    }

    if (user._id.toString() === adminId) {
      throw AppError.badRequest('You cannot change your own status.');
    }

    user.status = status;
    await user.save();

    return this.mapToProfile(user);
  }

  async updateUserRole(userId: string, role: UserRole, adminId: string): Promise<UserProfile> {
    const user = await User.findById(userId);
    if (!user) {
      throw AppError.notFound('User not found');
    }

    if (user._id.toString() === adminId) {
      throw AppError.badRequest('You cannot change your own role.');
    }

    user.role = role;
    await user.save();

    return this.mapToProfile(user);
  }

  async deleteUser(userId: string, adminId: string): Promise<{ message: string }> {
    const user = await User.findById(userId);
    if (!user) {
      throw AppError.notFound('User not found');
    }

    if (user._id.toString() === adminId) {
      throw AppError.badRequest('You cannot delete your own account.');
    }

    await User.findByIdAndDelete(userId);
    return { message: 'User deleted successfully.' };
  }

  private mapToProfile(user: IUser & { _id: mongoose.Types.ObjectId }): UserProfile {
    return {
      id: user._id.toString(),
      username: user.username,
      firstName: user.firstName,
      lastName: user.lastName,
      phone: user.phone,
      email: user.email,
      role: user.role,
      status: user.status,
      profileImage: user.profileImage,
      company: user.company?.toString(),
      createdAt: user.createdAt,
      updatedAt: user.updatedAt,
    };
  }
}

export const userService = new UserService();
```

FILE: backend/src/services/company.service.ts

```typescript
import { Company, ICompany } from '../models/company.model';
import { User, IUser } from '../models/user.model';
import { AppError } from '../utils/AppError';
import { UserRole, UserStatus } from '../types';
import mongoose, { ClientSession } from 'mongoose';

export interface CompanyData {
  name: string;
  headquartersAddress: string;
  companyNumber: string;
  taxId: string;
}

export interface CompanyWithManagers extends ICompany {
  managers: Array<{
    id: string;
    username: string;
    firstName: string;
    lastName: string;
    email: string;
    status: UserStatus;
  }>;
}

export class CompanyService {
  async createCompany(data: CompanyData, session?: ClientSession): Promise<ICompany> {
    if (!/^\d{8}$/.test(data.companyNumber)) {
      throw AppError.badRequest('Company number must be exactly 8 digits.', [{ field: 'companyNumber', message: 'Company number must be exactly 8 digits.' }]);
    }

    if (!/^[1-9]\d{8}$/.test(data.taxId)) {
      throw AppError.badRequest('Tax ID must be exactly 9 digits and must not begin with zero.', [{ field: 'taxId', message: 'Tax ID must be exactly 9 digits and must not begin with zero.' }]);
    }

    const existingCompany = await Company.findOne({
      $or: [{ companyNumber: data.companyNumber }, { taxId: data.taxId }],
    }).session(session || null);

    if (existingCompany) {
      if (existingCompany.companyNumber === data.companyNumber) {
        throw AppError.conflict('A different company is already registered with that company number.');
      }
      throw AppError.conflict('A different company is already registered with that tax ID.');
    }

    const company = new Company(data);
    await company.save({ session: session || null });
    return company;
  }

  async getCompanyById(companyId: string): Promise<CompanyWithManagers> {
    const company = await Company.findById(companyId).lean();
    if (!company) {
      throw AppError.notFound('Company not found');
    }

    const managers = await User.find({ company: company._id, role: UserRole.MANAGER })
      .select('username firstName lastName email status')
      .lean();

    return {
      ...company,
      managers: managers.map(m => ({
        id: m._id.toString(),
        username: m.username,
        firstName: m.firstName,
        lastName: m.lastName,
        email: m.email,
        status: m.status,
      })),
    } as CompanyWithManagers;
  }

  async getCompanies(
    page: number = 1,
    limit: number = 20,
    sortBy: string = 'createdAt',
    sortOrder: 'asc' | 'desc' = 'desc'
  ): Promise<{ data: ICompany[]; total: number; page: number; limit: number; totalPages: number }> {
    const sort: Record<string, 1 | -1> = { [sortBy]: sortOrder === 'asc' ? 1 : -1 };

    const [companies, total] = await Promise.all([
      Company.find()
        .sort(sort)
        .skip((page - 1) * limit)
        .limit(limit)
        .lean(),
      Company.countDocuments(),
    ]);

    return {
      data: companies,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async updateCompany(companyId: string, data: Partial<CompanyData>): Promise<ICompany> {
    if (data.companyNumber && !/^\d{8}$/.test(data.companyNumber)) {
      throw AppError.badRequest('Company number must be exactly 8 digits.', [{ field: 'companyNumber', message: 'Company number must be exactly 8 digits.' }]);
    }

    if (data.taxId && !/^[1-9]\d{8}$/.test(data.taxId)) {
      throw AppError.badRequest('Tax ID must be exactly 9 digits and must not begin with zero.', [{ field: 'taxId', message: 'Tax ID must be exactly 9 digits and must not begin with zero.' }]);
    }

    const company = await Company.findById(companyId);
    if (!company) {
      throw AppError.notFound('Company not found');
    }

    if (data.companyNumber && data.companyNumber !== company.companyNumber) {
      const existing = await Company.findOne({ companyNumber: data.companyNumber }).lean();
      if (existing) {
        throw AppError.conflict('A different company is already registered with that company number.');
      }
      company.companyNumber = data.companyNumber;
    }

    if (data.taxId && data.taxId !== company.taxId) {
      const existing = await Company.findOne({ taxId: data.taxId }).lean();
      if (existing) {
        throw AppError.conflict('A different company is already registered with that tax ID.');
      }
      company.taxId = data.taxId;
    }

    if (data.name) company.name = data.name;
    if (data.headquartersAddress) company.headquartersAddress = data.headquartersAddress;

    await company.save();
    return company;
  }

  async deleteCompany(companyId: string): Promise<{ message: string }> {
    const company = await Company.findById(companyId);
    if (!company) {
      throw AppError.notFound('Company not found');
    }

    const managersCount = await User.countDocuments({ company: company._id, role: UserRole.MANAGER });
    if (managersCount > 0) {
      throw AppError.conflict('Cannot delete company with associated space managers.');
    }

    await Company.findByIdAndDelete(companyId);
    return { message: 'Company deleted successfully.' };
  }

  async getCompanyManagersCount(companyId: string): Promise<number> {
    return User.countDocuments({ company: companyId, role: UserRole.MANAGER, status: UserStatus.APPROVED });
  }

  async getCompanyPendingManagersCount(companyNumber: string): Promise<number> {
    const { RegistrationRequest } = await import('../models/registration-request.model');
    const { RegistrationStatus } = await import('../types');
    return RegistrationRequest.countDocuments({
      companyNumber,
      role: UserRole.MANAGER,
      status: RegistrationStatus.PENDING,
    });
  }
}

export const companyService = new CompanyService();
```

FILE: backend/src/services/admin.service.ts

```typescript
import { User, IUser } from '../models/user.model';
import { RegistrationRequest, IRegistrationRequest } from '../models/registration-request.model';
import { Company, ICompany } from '../models/company.model';
import { Space, ISpace } from '../models/space.model';
import { Reservation, IReservation, ReservationStatus } from '../models/reservation.model';
import { AppError } from '../utils/AppError';
import { UserRole, UserStatus, RegistrationStatus } from '../types';
import mongoose from 'mongoose';

export interface AdminStatistics {
  users: {
    total: number;
    members: number;
    managers: number;
    admins: number;
    pending: number;
    approved: number;
    rejected: number;
  };
  companies: {
    total: number;
  };
  spaces: {
    total: number;
    active: number;
    inactive: number;
  };
  reservations: {
    total: number;
    pending: number;
    confirmed: number;
    cancelled: number;
    completed: number;
  };
}

export interface PendingRegistrationRequest {
  id: string;
  username: string;
  firstName: string;
  lastName: string;
  email: string;
  role: UserRole;
  submittedAt: Date;
  companyName?: string;
  headquartersAddress?: string;
  companyNumber?: string;
  taxId?: string;
  profileImage: string;
}

export class AdminService {
  async getStatistics(): Promise<AdminStatistics> {
    const [
      totalUsers,
      members,
      managers,
      admins,
      pendingUsers,
      approvedUsers,
      rejectedUsers,
      totalCompanies,
      totalSpaces,
      activeSpaces,
      inactiveSpaces,
      totalReservations,
      pendingReservations,
      confirmedReservations,
      cancelledReservations,
      completedReservations,
    ] = await Promise.all([
      User.countDocuments(),
      User.countDocuments({ role: UserRole.MEMBER }),
      User.countDocuments({ role: UserRole.MANAGER }),
      User.countDocuments({ role: UserRole.ADMIN }),
      User.countDocuments({ status: UserStatus.PENDING }),
      User.countDocuments({ status: UserStatus.APPROVED }),
      User.countDocuments({ status: UserStatus.REJECTED }),
      Company.countDocuments(),
      Space.countDocuments(),
      Space.countDocuments({ isActive: true }),
      Space.countDocuments({ isActive: false }),
      Reservation.countDocuments(),
      Reservation.countDocuments({ status: ReservationStatus.PENDING }),
      Reservation.countDocuments({ status: ReservationStatus.CONFIRMED }),
      Reservation.countDocuments({ status: ReservationStatus.CANCELLED }),
      Reservation.countDocuments({ status: ReservationStatus.COMPLETED }),
    ]);

    return {
      users: {
        total: totalUsers,
        members,
        managers,
        admins,
        pending: pendingUsers,
        approved: approvedUsers,
        rejected: rejectedUsers,
      },
      companies: {
        total: totalCompanies,
      },
      spaces: {
        total: totalSpaces,
        active: activeSpaces,
        inactive: inactiveSpaces,
      },
      reservations: {
        total: totalReservations,
        pending: pendingReservations,
        confirmed: confirmedReservations,
        cancelled: cancelledReservations,
        completed: completedReservations,
      },
    };
  }

  async getPendingRegistrations(): Promise<PendingRegistrationRequest[]> {
    const requests = await RegistrationRequest.find({ status: RegistrationStatus.PENDING })
      .sort({ submittedAt: 1 })
      .lean();

    return requests.map(req => ({
      id: req._id.toString(),
      username: req.username,
      firstName: req.firstName,
      lastName: req.lastName,
      email: req.email,
      role: req.role,
      submittedAt: req.submittedAt,
      companyName: req.companyName,
      headquartersAddress: req.headquartersAddress,
      companyNumber: req.companyNumber,
      taxId: req.taxId,
      profileImage: req.profileImage,
    }));
  }

  async getAllUsers(
    page: number = 1,
    limit: number = 20,
    sortBy: string = 'createdAt',
    sortOrder: 'asc' | 'desc' = 'desc',
    role?: UserRole,
    status?: UserStatus
  ): Promise<{ data: Array<IUser & { id: string }>; total: number; page: number; limit: number; totalPages: number }> {
    const query: Record<string, unknown> = {};
    if (role) query.role = role;
    if (status) query.status = status;

    const sort: Record<string, 1 | -1> = { [sortBy]: sortOrder === 'asc' ? 1 : -1 };

    const [users, total] = await Promise.all([
      User.find(query)
        .sort(sort)
        .skip((page - 1) * limit)
        .limit(limit)
        .lean(),
      User.countDocuments(query),
    ]);

    return {
      data: users.map(u => ({ ...u, id: u._id.toString() })),
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async getAllCompanies(
    page: number = 1,
    limit: number = 20,
    sortBy: string = 'createdAt',
    sortOrder: 'asc' | 'desc' = 'desc'
  ): Promise<{ data: ICompany[]; total: number; page: number; limit: number; totalPages: number }> {
    const sort: Record<string, 1 | -1> = { [sortBy]: sortOrder === 'asc' ? 1 : -1 };

    const [companies, total] = await Promise.all([
      Company.find()
        .sort(sort)
        .skip((page - 1) * limit)
        .limit(limit)
        .lean(),
      Company.countDocuments(),
    ]);

    return {
      data: companies,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async getAllSpaces(
    page: number = 1,
    limit: number = 20,
    sortBy: string = 'createdAt',
    sortOrder: 'asc' | 'desc' = 'desc',
    isActive?: boolean
  ): Promise<{ data: ISpace[]; total: number; page: number; limit: number; totalPages: number }> {
    const query: Record<string, unknown> = {};
    if (isActive !== undefined) query.isActive = isActive;

    const sort: Record<string, 1 | -1> = { [sortBy]: sortOrder === 'asc' ? 1 : -1 };

    const [spaces, total] = await Promise.all([
      Space.find(query)
        .sort(sort)
        .skip((page - 1) * limit)
        .limit(limit)
        .lean(),
      Space.countDocuments(query),
    ]);

    return {
      data: spaces,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async getAllReservations(
    page: number = 1,
    limit: number = 20,
    sortBy: string = 'createdAt',
    sortOrder: 'asc' | 'desc' = 'desc',
    status?: ReservationStatus
  ): Promise<{ data: IReservation[]; total: number; page: number; limit: number; totalPages: number }> {
    const query: Record<string, unknown> = {};
    if (status) query.status = status;

    const sort: Record<string, 1 | -1> = { [sortBy]: sortOrder === 'asc' ? 1 : -1 };

    const [reservations, total] = await Promise.all([
      Reservation.find(query)
        .sort(sort)
        .skip((page - 1) * limit)
        .limit(limit)
        .lean(),
      Reservation.countDocuments(query),
    ]);

    return {
      data: reservations,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async deleteUser(userId: string, adminId: string): Promise<{ message: string }> {
    if (userId === adminId) {
      throw AppError.badRequest('You cannot delete your own account.');
    }

    const user = await User.findById(userId);
    if (!user) {
      throw AppError.notFound('User not found');
    }

    await User.findByIdAndDelete(userId);
    return { message: 'User deleted successfully.' };
  }

  async updateUserStatus(userId: string, status: UserStatus, adminId: string): Promise<{ message: string }> {
    if (userId === adminId) {
      throw AppError.badRequest('You cannot change your own status.');
    }

    const user = await User.findById(userId);
    if (!user) {
      throw AppError.notFound('User not found');
    }

    user.status = status;
    await user.save();

    return { message: `User status updated to ${status}.` };
  }

  async updateUserRole(userId: string, role: UserRole, adminId: string): Promise<{ message: string }> {
    if (userId === adminId) {
      throw AppError.badRequest('You cannot change your own role.');
    }

    const user = await User.findById(userId);
    if (!user) {
      throw AppError.notFound('User not found');
    }

    user.role = role;
    await user.save();

    return { message: `User role updated to ${role}.` };
  }
}

export const adminService = new AdminService();
```

FILE: backend/src/services/space.service.ts

```typescript
import { Space, ISpace } from '../models/space.model';
import { Company, ICompany } from '../models/company.model';
import { AppError } from '../utils/AppError';
import { UserRole } from '../types';
import mongoose, { ClientSession } from 'mongoose';

export interface CreateSpaceData {
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

export class SpaceService {
  async createSpace(data: CreateSpaceData, managerId: string, session?: ClientSession): Promise<ISpace> {
    const company = await Company.findById(data.companyId).session(session || null);
    if (!company) {
      throw AppError.notFound('Company not found');
    }

    const user = await require('../models/user.model').User.findById(managerId).session(session || null);
    if (!user) {
      throw AppError.notFound('User not found');
    }

    if (user.role !== UserRole.MANAGER && user.role !== UserRole.ADMIN) {
      throw AppError.forbidden('Only space managers can create spaces.');
    }

    if (user.role === UserRole.MANAGER && user.company?.toString() !== data.companyId) {
      throw AppError.forbidden('You can only create spaces for your own company.');
    }

    const space = new Space({
      ...data,
      company: data.companyId,
    });

    await space.save({ session: session || null });
    return space;
  }

  async getSpaceById(spaceId: string): Promise<ISpace> {
    const space = await Space.findById(spaceId).populate('company').lean();
    if (!space) {
      throw AppError.notFound('Space not found');
    }
    return space;
  }

  async getSpacesByCompany(
    companyId: string,
    page: number = 1,
    limit: number = 20,
    sortBy: string = 'createdAt',
    sortOrder: 'asc' | 'desc' = 'desc',
    isActive?: boolean
  ): Promise<{ data: ISpace[]; total: number; page: number; limit: number; totalPages: number }> {
    const query: Record<string, unknown> = { company: companyId };
    if (isActive !== undefined) query.isActive = isActive;

    const sort: Record<string, 1 | -1> = { [sortBy]: sortOrder === 'asc' ? 1 : -1 };

    const [spaces, total] = await Promise.all([
      Space.find(query)
        .sort(sort)
        .skip((page - 1) * limit)
        .limit(limit)
        .lean(),
      Space.countDocuments(query),
    ]);

    return {
      data: spaces,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async getPublicSpaces(
    page: number = 1,
    limit: number = 20,
    sortBy: string = 'createdAt',
    sortOrder: 'asc' | 'desc' = 'desc',
    city?: string,
    minCapacity?: number,
    maxPricePerHour?: number,
    amenities?: string[]
  ): Promise<{ data: ISpace[]; total: number; page: number; limit: number; totalPages: number }> {
    const query: Record<string, unknown> = { isActive: true };

    if (city) query.city = new RegExp(city, 'i');
    if (minCapacity) query.capacity = { $gte: minCapacity };
    if (maxPricePerHour) query.pricePerHour = { $lte: maxPricePerHour };
    if (amenities && amenities.length > 0) query.amenities = { $all: amenities };

    const sort: Record<string, 1 | -1> = { [sortBy]: sortOrder === 'asc' ? 1 : -1 };

    const [spaces, total] = await Promise.all([
      Space.find(query)
        .sort(sort)
        .skip((page - 1) * limit)
        .limit(limit)
        .lean(),
      Space.countDocuments(query),
    ]);

    return {
      data: spaces,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async updateSpace(spaceId: string, data: UpdateSpaceData, managerId: string): Promise<ISpace> {
    const space = await Space.findById(spaceId);
    if (!space) {
      throw AppError.notFound('Space not found');
    }

    const user = await require('../models/user.model').User.findById(managerId);
    if (!user) {
      throw AppError.notFound('User not found');
    }

    if (user.role !== UserRole.MANAGER && user.role !== UserRole.ADMIN) {
      throw AppError.forbidden('Only space managers can update spaces.');
    }

    if (user.role === UserRole.MANAGER && user.company?.toString() !== space.company.toString()) {
      throw AppError.forbidden('You can only update spaces for your own company.');
    }

    if (data.name) space.name = data.name;
    if (data.description) space.description = data.description;
    if (data.address) space.address = data.address;
    if (data.city) space.city = data.city;
    if (data.capacity !== undefined) space.capacity = data.capacity;
    if (data.amenities) space.amenities = data.amenities;
    if (data.images) space.images = data.images;
    if (data.pricePerHour !== undefined) space.pricePerHour = data.pricePerHour;
    if (data.pricePerDay !== undefined) space.pricePerDay = data.pricePerDay;
    if (data.isActive !== undefined) space.isActive = data.isActive;

    await space.save();
    return space;
  }

  async deleteSpace(spaceId: string, managerId: string): Promise<{ message: string }> {
    const space = await Space.findById(spaceId);
    if (!space) {
      throw AppError.notFound('Space not found');
    }

    const user = await require('../models/user.model').User.findById(managerId);
    if (!user) {
      throw AppError.notFound('User not found');
    }

    if (user.role !== UserRole.MANAGER && user.role !== UserRole.ADMIN) {
      throw AppError.forbidden('Only space managers can delete spaces.');
    }

    if (user.role === UserRole.MANAGER && user.company?.toString() !== space.company.toString()) {
      throw AppError.forbidden('You can only delete spaces for your own company.');
    }

    await Space.findByIdAndDelete(spaceId);
    return { message: 'Space deleted successfully.' };
  }

  async toggleSpaceActive(spaceId: string, managerId: string): Promise<ISpace> {
    const space = await Space.findById(spaceId);
    if (!space) {
      throw AppError.notFound('Space not found');
    }

    const user = await require('../models/user.model').User.findById(managerId);
    if (!user) {
      throw AppError.notFound('User not found');
    }

    if (user.role !== UserRole.MANAGER && user.role !== UserRole.ADMIN) {
      throw AppError.forbidden('Only space managers can toggle space status.');
    }

    if (user.role === UserRole.MANAGER && user.company?.toString() !== space.company.toString()) {
      throw AppError.forbidden('You can only toggle spaces for your own company.');
    }

    space.isActive = !space.isActive;
    await space.save();
    return space;
  }
}

export const spaceService = new SpaceService();
```

FILE: backend/src/services/reservation.service.ts

```typescript
import { Reservation, IReservation, ReservationStatus } from '../models/reservation.model';
import { Space, ISpace } from '../models/space.model';
import { User, IUser } from '../models/user.model';
import { AppError } from '../utils/AppError';
import { UserRole, UserStatus } from '../types';
import mongoose, { ClientSession } from 'mongoose';

export interface CreateReservationData {
  spaceId: string;
  startTime: Date;
  endTime: Date;
  notes?: string;
}

export interface ReservationWithDetails extends IReservation {
  space: ISpace;
  user: {
    id: string;
    username: string;
    firstName: string;
    lastName: string;
    email: string;
  };
}

export class ReservationService {
  async createReservation(userId: string, data: CreateReservationData, now: Date = new Date()): Promise<ReservationWithDetails> {
    if (data.startTime < now) {
      throw AppError.badRequest('Start time cannot be in the past.');
    }

    if (data.startTime >= data.endTime) {
      throw AppError.badRequest('End time must be after start time.');
    }

    const space = await Space.findById(data.spaceId);
    if (!space) {
      throw AppError.notFound('Space not found');
    }

    if (!space.isActive) {
      throw AppError.badRequest('This space is not available for reservations.');
    }

    const user = await User.findById(userId);
    if (!user) {
      throw AppError.notFound('User not found');
    }

    if (user.status !== UserStatus.APPROVED) {
      throw AppError.forbidden('Your account is not approved.');
    }

    const session = await mongoose.startSession();
    session.startTransaction();

    try {
      const overlappingReservation = await Reservation.findOne({
        space: data.spaceId,
        status: { $in: [ReservationStatus.PENDING, ReservationStatus.CONFIRMED] },
        startTime: { $lt: data.endTime },
        endTime: { $gt: data.startTime },
      }).session(session);

      if (overlappingReservation) {
        throw AppError.conflict('The space is already reserved for the selected time period.');
      }

      const durationHours = (data.endTime.getTime() - data.startTime.getTime()) / (1000 * 60 * 60);
      const totalPrice = Math.ceil(durationHours) * space.pricePerHour;

      const reservation = new Reservation({
        user: userId,
        space: data.spaceId,
        startTime: data.startTime,
        endTime: data.endTime,
        status: ReservationStatus.PENDING,
        totalPrice,
        notes: data.notes,
      });

      await reservation.save({ session });

      await session.commitTransaction();

      const populatedReservation = await Reservation.findById(reservation._id)
        .populate('space')
        .populate('user', 'username firstName lastName email')
        .lean();

      return this.mapToReservationWithDetails(populatedReservation!);
    } catch (error) {
      await session.abortTransaction();
      throw error;
    } finally {
      await session.endSession();
    }
  }

  async getReservationById(reservationId: string, userId: string, userRole: UserRole): Promise<ReservationWithDetails> {
    const reservation = await Reservation.findById(reservationId)
      .populate('space')
      .populate('user', 'username firstName lastName email')
      .lean();

    if (!reservation) {
      throw AppError.notFound('Reservation not found');
    }

    if (userRole !== UserRole.ADMIN && reservation.user._id.toString() !== userId) {
      const space = await Space.findById(reservation.space._id).lean();
      if (!space || space.company.toString() !== (await User.findById(userId).lean())?.company?.toString()) {
        throw AppError.forbidden('You can only access your own reservations.');
      }
    }

    return this.mapToReservationWithDetails(reservation);
  }

  async getUserReservations(
    userId: string,
    page: number = 1,
    limit: number = 20,
    sortBy: string = 'startTime',
    sortOrder: 'asc' | 'desc' = 'desc',
    status?: ReservationStatus
  ): Promise<{ data: ReservationWithDetails[]; total: number; page: number; limit: number; totalPages: number }> {
    const query: Record<string, unknown> = { user: userId };
    if (status) query.status = status;

    const sort: Record<string, 1 | -1> = { [sortBy]: sortOrder === 'asc' ? 1 : -1 };

    const [reservations, total] = await Promise.all([
      Reservation.find(query)
        .sort(sort)
        .skip((page - 1) * limit)
        .limit(limit)
        .populate('space')
        .populate('user', 'username firstName lastName email')
        .lean(),
      Reservation.countDocuments(query),
    ]);

    return {
      data: reservations.map(r => this.mapToReservationWithDetails(r)),
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async getCompanyReservations(
    companyId: string,
    page: number = 1,
    limit: number = 20,
    sortBy: string = 'startTime',
    sortOrder: 'asc' | 'desc' = 'desc',
    status?: ReservationStatus
  ): Promise<{ data: ReservationWithDetails[]; total: number; page: number; limit: number; totalPages: number }> {
    const spaces = await Space.find({ company: companyId }).select('_id').lean();
    const spaceIds = spaces.map(s => s._id);

    const query: Record<string, unknown> = { space: { $in: spaceIds } };
    if (status) query.status = status;

    const sort: Record<string, 1 | -1> = { [sortBy]: sortOrder === 'asc' ? 1 : -1 };

    const [reservations, total] = await Promise.all([
      Reservation.find(query)
        .sort(sort)
        .skip((page - 1) * limit)
        .limit(limit)
        .populate('space')
        .populate('user', 'username firstName lastName email')
        .lean(),
      Reservation.countDocuments(query),
    ]);

    return {
      data: reservations.map(r => this.mapToReservationWithDetails(r)),
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async cancelReservation(reservationId: string, userId: string, userRole: UserRole): Promise<{ message: string }> {
    const reservation = await Reservation.findById(reservationId);
    if (!reservation) {
      throw AppError.notFound('Reservation not found');
    }

    if (userRole !== UserRole.ADMIN && reservation.user.toString() !== userId) {
      const space = await Space.findById(reservation.space).lean();
      if (!space || space.company.toString() !== (await User.findById(userId).lean())?.company?.toString()) {
        throw AppError.forbidden('You can only cancel your own reservations.');
      }
    }

    if (reservation.status === ReservationStatus.CANCELLED) {
      throw AppError.badRequest('Reservation is already cancelled.');
    }

    if (reservation.status === ReservationStatus.COMPLETED) {
      throw AppError.badRequest('Cannot cancel a completed reservation.');
    }

    reservation.status = ReservationStatus.CANCELLED;
    await reservation.save();

    return { message: 'Reservation cancelled successfully.' };
  }

  async confirmReservation(reservationId: string, managerId: string): Promise<{ message: string }> {
    const reservation = await Reservation.findById(reservationId).populate('space');
    if (!reservation) {
      throw AppError.notFound('Reservation not found');
    }

    const space = reservation.space as ISpace;
    const user = await User.findById(managerId);
    if (!user) {
      throw AppError.notFound('User not found');
    }

    if (user.role !== UserRole.MANAGER && user.role !== UserRole.ADMIN) {
      throw AppError.forbidden('Only space managers can confirm reservations.');
    }

    if (user.role === UserRole.MANAGER && user.company?.toString() !== space.company.toString()) {
      throw AppError.forbidden('You can only confirm reservations for your own company spaces.');
    }

    if (reservation.status !== ReservationStatus.PENDING) {
      throw AppError.badRequest('Only pending reservations can be confirmed.');
    }

    reservation.status = ReservationStatus.CONFIRMED;
    await reservation.save();

    return { message: 'Reservation confirmed successfully.' };
  }

  async completeReservation(reservationId: string, managerId: string): Promise<{ message: string }> {
    const reservation = await Reservation.findById(reservationId).populate('space');
    if (!reservation) {
      throw AppError.notFound('Reservation not found');
    }

    const space = reservation.space as ISpace;
    const user = await User.findById(managerId);
    if (!user) {
      throw AppError.notFound('User not found');
    }

    if (user.role !== UserRole.MANAGER && user.role !== UserRole.ADMIN) {
      throw AppError.forbidden('Only space managers can complete reservations.');
    }

    if (user.role === UserRole.MANAGER && user.company?.toString() !== space.company.toString()) {
      throw AppError.forbidden('You can only complete reservations for your own company spaces.');
    }

    if (reservation.status !== ReservationStatus.CONFIRMED) {
      throw AppError.badRequest('Only confirmed reservations can be completed.');
    }

    reservation.status = ReservationStatus.COMPLETED;
    await reservation.save();

    return { message: 'Reservation marked as completed.' };
  }

  async checkAvailability(spaceId: string, startTime: Date, endTime: Date): Promise<{ available: boolean; conflictingReservations: IReservation[] }> {
    const space = await Space.findById(spaceId);
    if (!space) {
      throw AppError.notFound('Space not found');
    }

    const conflictingReservations = await Reservation.find({
      space: spaceId,
      status: { $in: [ReservationStatus.PENDING, ReservationStatus.CONFIRMED] },
      startTime: { $lt: endTime },
      endTime: { $gt: startTime },
    }).lean();

    return {
      available: conflictingReservations.length === 0,
      conflictingReservations,
    };
  }

  private mapToReservationWithDetails(reservation: IReservation & {
    space: ISpace;
    user: { _id: mongoose.Types.ObjectId; username: string; firstName: string; lastName: string; email: string };
  }): ReservationWithDetails {
    return {
      ...reservation,
      space: reservation.space,
      user: {
        id: reservation.user._id.toString(),
        username: reservation.user.username,
        firstName: reservation.user.firstName,
        lastName: reservation.user.lastName,
        email: reservation.user.email,
      },
    };
  }
}

export const reservationService = new ReservationService();
```

FILE: backend/src/services/index.ts

```typescript
export { authService, AuthService } from './auth.service';
export { registrationService, RegistrationService } from './registration.service';
export { userService, UserService } from './user.service';
export { companyService, CompanyService } from './company.service';
export { adminService, AdminService } from './admin.service';
export { spaceService, SpaceService } from './space.service';
export { reservationService, ReservationService } from './reservation.service';
```