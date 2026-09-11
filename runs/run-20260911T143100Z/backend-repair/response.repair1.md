FILE: backend/package.json

```json
{
  "name": "coworking-backend",
  "version": "1.0.0",
  "description": "Coworking space management backend",
  "main": "dist/index.js",
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "build": "tsc",
    "start": "node dist/index.js",
    "prisma:generate": "prisma generate",
    "prisma:migrate": "prisma migrate dev",
    "prisma:studio": "prisma studio",
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "dependencies": {
    "@prisma/client": "^5.10.0",
    "bcryptjs": "^2.4.3",
    "cookie-parser": "^1.4.6",
    "cors": "^2.8.5",
    "express": "^4.18.2",
    "express-rate-limit": "^7.1.5",
    "express-validator": "^7.0.1",
    "jsonwebtoken": "^9.0.2",
    "multer": "^1.4.5-lts.1",
    "sharp": "^0.33.2",
    "uuid": "^9.0.1",
    "zod": "^3.22.4"
  },
  "devDependencies": {
    "@types/bcryptjs": "^2.4.6",
    "@types/cookie-parser": "^1.4.7",
    "@types/cors": "^2.8.17",
    "@types/express": "^4.17.21",
    "@types/jsonwebtoken": "^9.0.5",
    "@types/multer": "^1.4.11",
    "@types/node": "^20.11.0",
    "@types/uuid": "^9.0.8",
    "prisma": "^5.10.0",
    "tsx": "^4.7.0",
    "typescript": "^5.3.3",
    "vitest": "^1.3.0"
  }
}
```

FILE: backend/tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "lib": ["ES2022"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    },
    "typeRoots": ["./node_modules/@types", "./src/types"]
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

FILE: backend/prisma/schema.prisma

```prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "sqlite"
  url      = env("DATABASE_URL")
}

enum Role {
  ADMIN
  MANAGER
  MEMBER
}

enum RegistrationStatus {
  PENDING
  APPROVED
  REJECTED
}

model User {
  id            String   @id @default(uuid())
  username      String   @unique
  email         String   @unique
  passwordHash  String
  firstName     String
  lastName      String
  phone         String
  role          Role     @default(MEMBER)
  status        RegistrationStatus @default(PENDING)
  profileImage  String?  @default("default-avatar.png")
  companyId     String?
  company       Company? @relation(fields: [companyId], references: [id])
  createdAt     DateTime @default(now())
  updatedAt     DateTime @updatedAt
  resetTokens   PasswordResetToken[]
  registrationRequest RegistrationRequest?
  
  @@index([email])
  @@index([username])
}

model Company {
  id                 String   @id @default(uuid())
  name               String
  headquartersAddress String
  companyNumber      String   @unique
  taxId              String   @unique
  managers           User[]
  spaces             Space[]
  createdAt          DateTime @default(now())
  updatedAt          DateTime @updatedAt
  
  @@index([companyNumber])
  @@index([taxId])
}

model Space {
  id          String   @id @default(uuid())
  name        String
  description String?
  address     String
  capacity    Int
  pricePerHour Float
  companyId   String
  company     Company  @relation(fields: [companyId], references: [id])
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
  
  @@index([companyId])
}

model PasswordResetToken {
  id        String   @id @default(uuid())
  token     String   @unique
  userId    String
  user      User     @relation(fields: [userId], references: [id], onDelete: Cascade)
  expiresAt DateTime
  usedAt    DateTime?
  createdAt DateTime @default(now())
  
  @@index([token])
  @@index([userId])
}

model RegistrationRequest {
  id          String   @id @default(uuid())
  username    String   @unique
  email       String   @unique
  passwordHash String
  firstName   String
  lastName    String
  phone       String
  role        Role
  companyName String?
  headquartersAddress String?
  companyNumber String?
  taxId       String?
  profileImage String?
  status      RegistrationStatus @default(PENDING)
  submittedAt DateTime @default(now())
  decidedAt   DateTime?
  decidedBy   String?
  
  @@index([status])
  @@index([submittedAt])
}
```

FILE: backend/src/types/express.d.ts

```typescript
import { Role } from '@prisma/client';

declare global {
  namespace Express {
    interface Request {
      user?: {
        id: string;
        username: string;
        email: string;
        role: Role;
        companyId?: string;
      };
    }
  }
}
```

FILE: backend/src/config/env.ts

```typescript
import { z } from 'zod';

const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  PORT: z.coerce.number().default(3000),
  DATABASE_URL: z.string().default('file:./dev.db'),
  JWT_SECRET: z.string().min(32),
  JWT_EXPIRES_IN: z.string().default('7d'),
  UPLOAD_DIR: z.string().default('./uploads'),
  MAX_FILE_SIZE: z.coerce.number().default(5 * 1024 * 1024), // 5MB
  FRONTEND_URL: z.string().url().default('http://localhost:5173'),
});

export const env = envSchema.parse(process.env);
```

FILE: backend/src/utils/errors.ts

```typescript
export class AppError extends Error {
  constructor(
    public readonly statusCode: number,
    public readonly message: string,
    public readonly code?: string,
    public readonly details?: Record<string, string>
  ) {
    super(message);
    this.name = 'AppError';
    Error.captureStackTrace(this, this.constructor);
  }
}

export class ValidationError extends AppError {
  constructor(message: string, details?: Record<string, string>) {
    super(400, message, 'VALIDATION_ERROR', details);
    this.name = 'ValidationError';
  }
}

export class AuthenticationError extends AppError {
  constructor(message = 'Authentication required') {
    super(401, message, 'AUTHENTICATION_ERROR');
    this.name = 'AuthenticationError';
  }
}

export class AuthorizationError extends AppError {
  constructor(message = 'Insufficient permissions') {
    super(403, message, 'AUTHORIZATION_ERROR');
    this.name = 'AuthorizationError';
  }
}

export class NotFoundError extends AppError {
  constructor(message = 'Resource not found') {
    super(404, message, 'NOT_FOUND');
    this.name = 'NotFoundError';
  }
}

export class ConflictError extends AppError {
  constructor(message: string) {
    super(409, message, 'CONFLICT');
    this.name = 'ConflictError';
  }
}

export class GoneError extends AppError {
  constructor(message: string) {
    super(410, message, 'GONE');
    this.name = 'GoneError';
  }
}

export class PayloadTooLargeError extends AppError {
  constructor(message = 'The uploaded file is too large') {
    super(413, message, 'PAYLOAD_TOO_LARGE');
    this.name = 'PayloadTooLargeError';
  }
}

export class UnsupportedMediaTypeError extends AppError {
  constructor(message = 'Unsupported media type') {
    super(415, message, 'UNSUPPORTED_MEDIA_TYPE');
    this.name = 'UnsupportedMediaTypeError';
  }
}
```

FILE: backend/src/utils/password.ts

```typescript
import bcrypt from 'bcryptjs';

const SALT_ROUNDS = 12;

export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, SALT_ROUNDS);
}

export async function verifyPassword(password: string, hash: string): Promise<boolean> {
  return bcrypt.compare(password, hash);
}

export function validatePasswordPolicy(password: string): { valid: boolean; message?: string } {
  if (password.length < 8 || password.length > 12) {
    return { valid: false, message: 'Password must be between 8 and 12 characters.' };
  }
  if (!/[A-Z]/.test(password)) {
    return { valid: false, message: 'Password must contain at least one uppercase letter.' };
  }
  if (!/[0-9]/.test(password)) {
    return { valid: false, message: 'Password must contain at least one digit.' };
  }
  if (!/[^A-Za-z0-9]/.test(password)) {
    return { valid: false, message: 'Password must contain at least one special character.' };
  }
  if (!/^[A-Za-z]/.test(password)) {
    return { valid: false, message: 'Password must begin with a letter.' };
  }
  return { valid: true };
}
```

FILE: backend/src/utils/jwt.ts

```typescript
import jwt from 'jsonwebtoken';
import { env } from '@/config/env';
import { Role } from '@prisma/client';

export interface TokenPayload {
  id: string;
  username: string;
  email: string;
  role: Role;
  companyId?: string;
}

export function generateToken(payload: TokenPayload): string {
  return jwt.sign(payload, env.JWT_SECRET, { expiresIn: env.JWT_EXPIRES_IN });
}

export function verifyToken(token: string): TokenPayload {
  return jwt.verify(token, env.JWT_SECRET) as TokenPayload;
}

export function extractTokenFromHeader(authHeader?: string): string | null {
  if (!authHeader) return null;
  const [type, token] = authHeader.split(' ');
  if (type !== 'Bearer' || !token) return null;
  return token;
}
```

FILE: backend/src/utils/validation.ts

```typescript
import { z } from 'zod';

export const usernameSchema = z.string().min(3).max(50).regex(/^[a-zA-Z0-9._-]+$/);
export const emailSchema = z.string().email();
export const phoneSchema = z.string().regex(/^[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,3}[)]?[-\s\.]?[0-9]{4,6}$/);
export const nameSchema = z.string().min(1).max(100);
export const companyNumberSchema = z.string().regex(/^\d{8}$/);
export const taxIdSchema = z.string().regex(/^[1-9]\d{8}$/);

export const loginSchema = z.object({
  username: usernameSchema,
  password: z.string().min(1),
});

export const registerMemberSchema = z.object({
  username: usernameSchema,
  password: z.string().min(8).max(12),
  firstName: nameSchema,
  lastName: nameSchema,
  phone: phoneSchema,
  email: emailSchema,
});

export const registerManagerSchema = registerMemberSchema.extend({
  companyName: nameSchema,
  headquartersAddress: z.string().min(5).max(200),
  companyNumber: companyNumberSchema,
  taxId: taxIdSchema,
});

export const forgotPasswordSchema = z.object({
  identifier: z.string().min(1),
});

export const resetPasswordSchema = z.object({
  token: z.string().uuid(),
  password: z.string().min(8).max(12),
  confirmPassword: z.string().min(8).max(12),
}).refine(data => data.password === data.confirmPassword, {
  message: 'The two passwords do not match.',
  path: ['confirmPassword'],
});

export const approveRejectSchema = z.object({
  username: usernameSchema,
});
```

FILE: backend/src/middleware/auth.ts

```typescript
import { Request, Response, NextFunction } from 'express';
import { extractTokenFromHeader, verifyToken, TokenPayload } from '@/utils/jwt';
import { AuthenticationError, AuthorizationError } from '@/utils/errors';

export function authenticate(req: Request, _res: Response, next: NextFunction) {
  const token = extractTokenFromHeader(req.headers.authorization);
  if (!token) {
    throw new AuthenticationError();
  }
  try {
    const payload = verifyToken(token);
    req.user = payload;
    next();
  } catch {
    throw new AuthenticationError('Invalid or expired token');
  }
}

export function requireRole(...roles: TokenPayload['role'][]) {
  return (req: Request, _res: Response, next: NextFunction) => {
    if (!req.user) {
      throw new AuthenticationError();
    }
    if (!roles.includes(req.user.role)) {
      throw new AuthorizationError();
    }
    next();
  };
}

export function requireAdmin(req: Request, _res: Response, next: NextFunction) {
  return requireRole('ADMIN')(req, _res, next);
}

export function requireManagerOrAdmin(req: Request, _res: Response, next: NextFunction) {
  return requireRole('MANAGER', 'ADMIN')(req, _res, next);
}

export function optionalAuth(req: Request, _res: Response, next: NextFunction) {
  const token = extractTokenFromHeader(req.headers.authorization);
  if (token) {
    try {
      req.user = verifyToken(token);
    } catch {
      // Ignore invalid token for optional auth
    }
  }
  next();
}
```

FILE: backend/src/middleware/validation.ts

```typescript
import { Request, Response, NextFunction } from 'express';
import { validationResult, ValidationChain } from 'express-validator';
import { ValidationError } from '@/utils/errors';

export function validate(validations: ValidationChain[]) {
  return async (req: Request, _res: Response, next: NextFunction) => {
    await Promise.all(validations.map(validation => validation.run(req)));
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      const details: Record<string, string> = {};
      errors.array().forEach(err => {
        if ('path' in err) {
          details[err.path] = err.msg;
        }
      });
      throw new ValidationError('Validation failed', details);
    }
    next();
  };
}
```

FILE: backend/src/middleware/errorHandler.ts

```typescript
import { Request, Response, NextFunction } from 'express';
import { AppError } from '@/utils/errors';
import { ZodError } from 'zod';
import { Prisma } from '@prisma/client';

export function errorHandler(err: Error, _req: Request, res: Response, _next: NextFunction) {
  console.error('Error:', err);

  if (err instanceof AppError) {
    return res.status(err.statusCode).json({
      error: err.code || 'ERROR',
      message: err.message,
      details: err.details,
    });
  }

  if (err instanceof ZodError) {
    const details: Record<string, string> = {};
    err.errors.forEach(e => {
      const path = e.path.join('.');
      details[path] = e.message;
    });
    return res.status(400).json({
      error: 'VALIDATION_ERROR',
      message: 'Validation failed',
      details,
    });
  }

  if (err instanceof Prisma.PrismaClientKnownRequestError) {
    if (err.code === 'P2002') {
      const target = (err.meta?.target as string[])?.join(', ') || 'field';
      return res.status(409).json({
        error: 'CONFLICT',
        message: `A record with this ${target} already exists`,
      });
    }
  }

  if (err instanceof SyntaxError && 'status' in err && err.status === 400 && 'body' in err) {
    return res.status(400).json({
      error: 'INVALID_JSON',
      message: 'Invalid JSON payload',
    });
  }

  return res.status(500).json({
    error: 'INTERNAL_ERROR',
    message: 'An unexpected error occurred',
  });
}
```

FILE: backend/src/middleware/rateLimiter.ts

```typescript
import rateLimit from 'express-rate-limit';

export const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 20, // limit each IP to 20 requests per windowMs
  message: { error: 'RATE_LIMITED', message: 'Too many attempts, please try again later' },
  standardHeaders: true,
  legacyHeaders: false,
});

export const apiLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 100,
  standardHeaders: true,
  legacyHeaders: false,
});
```

FILE: backend/src/services/userService.ts

```typescript
import { PrismaClient, Role, RegistrationStatus, User } from '@prisma/client';
import { hashPassword, verifyPassword, validatePasswordPolicy } from '@/utils/password';
import { generateToken, TokenPayload } from '@/utils/jwt';
import { AppError, ConflictError, NotFoundError, ValidationError } from '@/utils/errors';
import { v4 as uuidv4 } from 'uuid';

const prisma = new PrismaClient();

export async function createRegistrationRequest(data: {
  username: string;
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  phone: string;
  role: Role;
  companyName?: string;
  headquartersAddress?: string;
  companyNumber?: string;
  taxId?: string;
  profileImage?: string;
}): Promise<{ requestId: string; message: string }> {
  // Check username uniqueness
  const existingUser = await prisma.user.findUnique({ where: { username: data.username } });
  if (existingUser) {
    throw new ConflictError('That username is already taken.');
  }

  const existingRequest = await prisma.registrationRequest.findUnique({ where: { username: data.username } });
  if (existingRequest) {
    throw new ConflictError('That username is already taken.');
  }

  // Check email uniqueness
  const existingEmailUser = await prisma.user.findUnique({ where: { email: data.email } });
  if (existingEmailUser) {
    throw new ConflictError('An account with that email address already exists.');
  }

  const existingEmailRequest = await prisma.registrationRequest.findUnique({ where: { email: data.email } });
  if (existingEmailRequest) {
    throw new ConflictError('An account with that email address already exists.');
  }

  // Validate password policy
  const passwordValidation = validatePasswordPolicy(data.password);
  if (!passwordValidation.valid) {
    throw new ValidationError(passwordValidation.message!, { password: passwordValidation.message! });
  }

  // Hash password
  const passwordHash = await hashPassword(data.password);

  // Handle company for managers
  let companyId: string | undefined;
  if (data.role === 'MANAGER') {
    if (!data.companyName || !data.headquartersAddress || !data.companyNumber || !data.taxId) {
      throw new ValidationError('Company fields are required for Space Manager registration');
    }

    // Check company number uniqueness
    const existingCompanyNumber = await prisma.company.findUnique({ where: { companyNumber: data.companyNumber } });
    if (existingCompanyNumber) {
      throw new ConflictError('A different company is already registered with that company number.');
    }

    // Check tax ID uniqueness
    const existingTaxId = await prisma.company.findUnique({ where: { taxId: data.taxId } });
    if (existingTaxId) {
      throw new ConflictError('A different company is already registered with that tax ID.');
    }

    // Count existing managers for this company (approved + pending)
    const managerCount = await prisma.user.count({
      where: {
        role: 'MANAGER',
        status: { in: ['APPROVED', 'PENDING'] },
        company: { companyNumber: data.companyNumber },
      },
    });

    const pendingManagerCount = await prisma.registrationRequest.count({
      where: {
        role: 'MANAGER',
        status: 'PENDING',
        companyNumber: data.companyNumber,
      },
    });

    if (managerCount + pendingManagerCount >= 2) {
      throw new ConflictError('This company already has the maximum of two space managers.');
    }

    // Create company
    const company = await prisma.company.create({
      data: {
        name: data.companyName,
        headquartersAddress: data.headquartersAddress,
        companyNumber: data.companyNumber,
        taxId: data.taxId,
      },
    });
    companyId = company.id;
  }

  // Create registration request
  const request = await prisma.registrationRequest.create({
    data: {
      username: data.username,
      email: data.email,
      passwordHash,
      firstName: data.firstName,
      lastName: data.lastName,
      phone: data.phone,
      role: data.role,
      companyName: data.companyName,
      headquartersAddress: data.headquartersAddress,
      companyNumber: data.companyNumber,
      taxId: data.taxId,
      profileImage: data.profileImage,
      status: 'PENDING',
    },
  });

  return { requestId: request.id, message: 'Your registration request has been submitted and is awaiting approval.' };
}

export async function approveRegistrationRequest(username: string, adminId: string): Promise<void> {
  const request = await prisma.registrationRequest.findUnique({ where: { username } });
  if (!request) {
    throw new NotFoundError('Registration request not found');
  }
  if (request.status !== 'PENDING') {
    throw new ConflictError('This registration request has already been decided.');
  }

  // For managers, check company limit again
  if (request.role === 'MANAGER' && request.companyNumber) {
    const managerCount = await prisma.user.count({
      where: {
        role: 'MANAGER',
        status: 'APPROVED',
        company: { companyNumber: request.companyNumber },
      },
    });
    if (managerCount >= 2) {
      throw new ConflictError('This company already has the maximum of two space managers.');
    }
  }

  // Create user from request
  let companyId: string | undefined;
  if (request.role === 'MANAGER' && request.companyNumber) {
    let company = await prisma.company.findUnique({ where: { companyNumber: request.companyNumber } });
    if (!company) {
      company = await prisma.company.create({
        data: {
          name: request.companyName!,
          headquartersAddress: request.headquartersAddress!,
          companyNumber: request.companyNumber!,
          taxId: request.taxId!,
        },
      });
    }
    companyId = company.id;
  }

  await prisma.$transaction(async (tx) => {
    await tx.user.create({
      data: {
        username: request.username,
        email: request.email,
        passwordHash: request.passwordHash,
        firstName: request.firstName,
        lastName: request.lastName,
        phone: request.phone,
        role: request.role,
        status: 'APPROVED',
        profileImage: request.profileImage || 'default-avatar.png',
        companyId,
      },
    });

    await tx.registrationRequest.update({
      where: { username },
      data: { status: 'APPROVED', decidedAt: new Date(), decidedBy: adminId },
    });
  });
}

export async function rejectRegistrationRequest(username: string, adminId: string): Promise<void> {
  const request = await prisma.registrationRequest.findUnique({ where: { username } });
  if (!request) {
    throw new NotFoundError('Registration request not found');
  }
  if (request.status !== 'PENDING') {
    throw new ConflictError('This registration request has already been decided.');
  }

  await prisma.registrationRequest.update({
    where: { username },
    data: { status: 'REJECTED', decidedAt: new Date(), decidedBy: adminId },
  });
}

export async function getPendingRegistrations(): Promise<Array<{
  username: string;
  firstName: string;
  lastName: string;
  email: string;
  role: Role;
  submittedAt: Date;
  companyName?: string;
  headquartersAddress?: string;
  companyNumber?: string;
  taxId?: string;
}>> {
  const requests = await prisma.registrationRequest.findMany({
    where: { status: 'PENDING' },
    orderBy: { submittedAt: 'asc' },
  });

  return requests.map(r => ({
    username: r.username,
    firstName: r.firstName,
    lastName: r.lastName,
    email: r.email,
    role: r.role,
    submittedAt: r.submittedAt,
    companyName: r.companyName ?? undefined,
    headquartersAddress: r.headquartersAddress ?? undefined,
    companyNumber: r.companyNumber ?? undefined,
    taxId: r.taxId ?? undefined,
  }));
}

export async function login(username: string, password: string, isAdminRoute: boolean): Promise<{ token: string; user: TokenPayload }> {
  const user = await prisma.user.findUnique({ where: { username } });
  if (!user) {
    throw new AppError(401, 'Invalid username or password.', 'INVALID_CREDENTIALS');
  }

  // Admin route only allows ADMIN role
  if (isAdminRoute && user.role !== 'ADMIN') {
    throw new AppError(401, 'Invalid username or password.', 'INVALID_CREDENTIALS');
  }

  // Public route does not allow ADMIN role
  if (!isAdminRoute && user.role === 'ADMIN') {
    throw new AppError(401, 'Invalid username or password.', 'INVALID_CREDENTIALS');
  }

  // Check if user is approved
  if (user.status !== 'APPROVED') {
    if (user.status === 'PENDING') {
      throw new AppError(403, 'Your registration is still awaiting administrator approval.', 'PENDING_APPROVAL');
    }
    if (user.status === 'REJECTED') {
      throw new AppError(403, 'Your registration request was rejected.', 'REJECTED');
    }
  }

  const valid = await verifyPassword(password, user.passwordHash);
  if (!valid) {
    throw new AppError(401, 'Invalid username or password.', 'INVALID_CREDENTIALS');
  }

  const payload: TokenPayload = {
    id: user.id,
    username: user.username,
    email: user.email,
    role: user.role,
    companyId: user.companyId ?? undefined,
  };

  const token = generateToken(payload);
  return { token, user: payload };
}

export async function getUserById(id: string): Promise<User | null> {
  return prisma.user.findUnique({ where: { id } });
}

export async function updateProfileImage(userId: string, imagePath: string): Promise<void> {
  const user = await prisma.user.findUnique({ where: { id: userId } });
  if (!user) throw new NotFoundError('User not found');

  // Delete old image if not default
  if (user.profileImage && user.profileImage !== 'default-avatar.png') {
    // In a real app, you'd delete the file here
    // For now, we just update the reference
  }

  await prisma.user.update({
    where: { id: userId },
    data: { profileImage: imagePath },
  });
}

export async function getAllUsers(): Promise<User[]> {
  return prisma.user.findMany({
    orderBy: { createdAt: 'desc' },
    select: {
      id: true,
      username: true,
      email: true,
      firstName: true,
      lastName: true,
      phone: true,
      role: true,
      status: true,
      profileImage: true,
      companyId: true,
      createdAt: true,
      updatedAt: true,
    },
  });
}

export async function deleteUser(userId: string): Promise<void> {
  await prisma.user.delete({ where: { id: userId } });
}
```

FILE: backend/src/services/passwordResetService.ts

```typescript
import { PrismaClient } from '@prisma/client';
import { hashPassword } from '@/utils/password';
import { AppError, GoneError, NotFoundError, ValidationError } from '@/utils/errors';
import { v4 as uuidv4 } from 'uuid';

const prisma = new PrismaClient();
const TOKEN_EXPIRY_MINUTES = 30;

export async function requestPasswordReset(identifier: string): Promise<{ message: string }> {
  // Find user by username or email
  const user = await prisma.user.findFirst({
    where: {
      OR: [
        { username: identifier },
        { email: identifier },
      ],
    },
  });

  // Always return success message to prevent account enumeration
  const message = 'If an account exists, a password reset link has been sent to your email.';

  if (!user) {
    return { message };
  }

  // Invalidate any existing unused tokens for this user
  await prisma.passwordResetToken.updateMany({
    where: { userId: user.id, usedAt: null },
    data: { usedAt: new Date() },
  });

  // Create new token
  const token = uuidv4();
  const expiresAt = new Date(Date.now() + TOKEN_EXPIRY_MINUTES * 60 * 1000);

  await prisma.passwordResetToken.create({
    data: {
      token,
      userId: user.id,
      expiresAt,
    },
  });

  // In a real app, send email here with the reset link
  // For now, we just log it (in development)
  console.log(`Password reset token for ${user.email}: ${token}`);
  console.log(`Reset link: ${process.env.FRONTEND_URL}/reset-password?token=${token}`);

  return { message };
}

export async function validateResetToken(token: string): Promise<{ userId: string; email: string }> {
  const resetToken = await prisma.passwordResetToken.findUnique({ where: { token } });
  if (!resetToken) {
    throw new GoneError('This reset link has expired. Please request a new one.');
  }

  if (resetToken.usedAt) {
    throw new GoneError('This reset link has already been used.');
  }

  if (new Date() > resetToken.expiresAt) {
    throw new GoneError('This reset link has expired. Please request a new one.');
  }

  const user = await prisma.user.findUnique({ where: { id: resetToken.userId } });
  if (!user) {
    throw new GoneError('This reset link is no longer valid.');
  }

  return { userId: user.id, email: user.email };
}

export async function resetPassword(token: string, password: string): Promise<{ message: string }> {
  const { userId } = await validateResetToken(token);

  const passwordValidation = validatePasswordPolicy(password);
  if (!passwordValidation.valid) {
    throw new ValidationError(passwordValidation.message!, { password: passwordValidation.message! });
  }

  const passwordHash = await hashPassword(password);

  await prisma.$transaction(async (tx) => {
    await tx.user.update({
      where: { id: userId },
      data: { passwordHash },
    });

    await tx.passwordResetToken.update({
      where: { token },
      data: { usedAt: new Date() },
    });

    // Invalidate all other tokens for this user
    await tx.passwordResetToken.updateMany({
      where: { userId, usedAt: null, token: { not: token } },
      data: { usedAt: new Date() },
    });
  });

  return { message: 'Password has been reset successfully.' };
}

function validatePasswordPolicy(password: string): { valid: boolean; message?: string } {
  if (password.length < 8 || password.length > 12) {
    return { valid: false, message: 'Password must be between 8 and 12 characters.' };
  }
  if (!/[A-Z]/.test(password)) {
    return { valid: false, message: 'Password must contain at least one uppercase letter.' };
  }
  if (!/[0-9]/.test(password)) {
    return { valid: false, message: 'Password must contain at least one digit.' };
  }
  if (!/[^A-Za-z0-9]/.test(password)) {
    return { valid: false, message: 'Password must contain at least one special character.' };
  }
  if (!/^[A-Za-z]/.test(password)) {
    return { valid: false, message: 'Password must begin with a letter.' };
  }
  return { valid: true };
}
```

FILE: backend/src/services/imageService.ts

```typescript
import { PrismaClient } from '@prisma/client';
import sharp from 'sharp';
import { v4 as uuidv4 } from 'uuid';
import path from 'path';
import fs from 'fs/promises';
import { AppError, ValidationError, PayloadTooLargeError, UnsupportedMediaTypeError } from '@/utils/errors';
import { env } from '@/config/env';

const prisma = new PrismaClient();
const ALLOWED_MIME_TYPES = ['image/jpeg', 'image/png'];
const MAX_DIMENSION = 300;
const MIN_DIMENSION = 100;
const MAX_FILE_SIZE = env.MAX_FILE_SIZE;

export async function validateAndProcessImage(
  file: Express.Multer.File,
  userId: string
): Promise<string> {
  // Check file size
  if (file.size > MAX_FILE_SIZE) {
    throw new PayloadTooLargeError();
  }

  // Validate MIME type by content (not extension)
  const image = sharp(file.buffer);
  const metadata = await image.metadata();
  
  if (!metadata.format || !ALLOWED_MIME_TYPES.includes(`image/${metadata.format}`)) {
    throw new UnsupportedMediaTypeError('Only JPG and PNG images are accepted.');
  }

  // Validate dimensions
  const width = metadata.width ?? 0;
  const height = metadata.height ?? 0;

  if (width < MIN_DIMENSION || width > MAX_DIMENSION || height < MIN_DIMENSION || height > MAX_DIMENSION) {
    throw new ValidationError(`The image must be between ${MIN_DIMENSION}x${MIN_DIMENSION} and ${MAX_DIMENSION}x${MAX_DIMENSION} pixels.`);
  }

  // Generate safe filename
  const ext = metadata.format === 'jpeg' ? 'jpg' : 'png';
  const filename = `${uuidv4()}.${ext}`;
  const uploadDir = env.UPLOAD_DIR;
  const filepath = path.join(uploadDir, filename);

  // Ensure upload directory exists
  await fs.mkdir(uploadDir, { recursive: true });

  // Process and save image (resize to max 300x300 maintaining aspect ratio)
  await image
    .resize(MAX_DIMENSION, MAX_DIMENSION, { fit: 'inside', withoutEnlargement: true })
    .toFile(filepath);

  // Update user profile image
  const user = await prisma.user.findUnique({ where: { id: userId } });
  if (!user) throw new AppError(404, 'User not found');

  // Delete old image if not default
  if (user.profileImage && user.profileImage !== 'default-avatar.png') {
    const oldPath = path.join(uploadDir, user.profileImage);
    try {
      await fs.unlink(oldPath);
    } catch {
      // Ignore if file doesn't exist
    }
  }

  await prisma.user.update({
    where: { id: userId },
    data: { profileImage: filename },
  });

  return filename;
}

export async function getImagePath(filename: string): Promise<string> {
  // Prevent path traversal
  const safeFilename = path.basename(filename);
  if (safeFilename !== filename || safeFilename.includes('..') || safeFilename.includes('\\')) {
    throw new AppError(400, 'Invalid filename');
  }
  return path.join(env.UPLOAD_DIR, safeFilename);
}

export function getDefaultImagePath(): string {
  return path.join(process.cwd(), 'public', 'default-avatar.png');
}
```

FILE: backend/src/controllers/authController.ts

```typescript
import { Request, Response, NextFunction } from 'express';
import { body } from 'express-validator';
import { login, createRegistrationRequest, getPendingRegistrations, approveRegistrationRequest, rejectRegistrationRequest } from '@/services/userService';
import { requestPasswordReset, validateResetToken, resetPassword } from '@/services/passwordResetService';
import { validate } from '@/middleware/validation';
import { authenticate, requireAdmin } from '@/middleware/auth';
import { AppError } from '@/utils/errors';

export const loginValidation = validate([
  body('username').isString().notEmpty(),
  body('password').isString().notEmpty(),
]);

export async function publicLogin(req: Request, res: Response, next: NextFunction) {
  try {
    const { username, password } = req.body;
    const { token, user } = await login(username, password, false);
    res.json({ token, user: { username: user.username, role: user.role } });
  } catch (err) {
    next(err);
  }
}

export async function adminLogin(req: Request, res: Response, next: NextFunction) {
  try {
    const { username, password } = req.body;
    const { token, user } = await login(username, password, true);
    res.json({ token, user: { username: user.username, role: user.role } });
  } catch (err) {
    next(err);
  }
}

export const registerMemberValidation = validate([
  body('username').isString().isLength({ min: 3, max: 50 }),
  body('password').isString().isLength({ min: 8, max: 12 }),
  body('firstName').isString().notEmpty(),
  body('lastName').isString().notEmpty(),
  body('phone').isString().notEmpty(),
  body('email').isEmail(),
]);

export async function registerMember(req: Request, res: Response, next: NextFunction) {
  try {
    const { username, password, firstName, lastName, phone, email } = req.body;
    const profileImage = req.file ? req.file.filename : undefined;
    const result = await createRegistrationRequest({
      username,
      email,
      password,
      firstName,
      lastName,
      phone,
      role: 'MEMBER',
      profileImage,
    });
    res.status(201).json(result);
  } catch (err) {
    next(err);
  }
}

export const registerManagerValidation = validate([
  body('username').isString().isLength({ min: 3, max: 50 }),
  body('password').isString().isLength({ min: 8, max: 12 }),
  body('firstName').isString().notEmpty(),
  body('lastName').isString().notEmpty(),
  body('phone').isString().notEmpty(),
  body('email').isEmail(),
  body('companyName').isString().notEmpty(),
  body('headquartersAddress').isString().notEmpty(),
  body('companyNumber').matches(/^\d{8}$/),
  body('taxId').matches(/^[1-9]\d{8}$/),
]);

export async function registerManager(req: Request, res: Response, next: NextFunction) {
  try {
    const { username, password, firstName, lastName, phone, email, companyName, headquartersAddress, companyNumber, taxId } = req.body;
    const profileImage = req.file ? req.file.filename : undefined;
    const result = await createRegistrationRequest({
      username,
      email,
      password,
      firstName,
      lastName,
      phone,
      role: 'MANAGER',
      companyName,
      headquartersAddress,
      companyNumber,
      taxId,
      profileImage,
    });
    res.status(201).json(result);
  } catch (err) {
    next(err);
  }
}

export const forgotPasswordValidation = validate([
  body('identifier').isString().notEmpty(),
]);

export async function forgotPassword(req: Request, res: Response, next: NextFunction) {
  try {
    const { identifier } = req.body;
    const result = await requestPasswordReset(identifier);
    res.json(result);
  } catch (err) {
    next(err);
  }
}

export async function getResetTokenStatus(req: Request, res: Response, next: NextFunction) {
  try {
    const { token } = req.params;
    await validateResetToken(token);
    res.json({ valid: true });
  } catch (err) {
    next(err);
  }
}

export const resetPasswordValidation = validate([
  body('token').isUUID(),
  body('password').isString().isLength({ min: 8, max: 12 }),
  body('confirmPassword').isString().isLength({ min: 8, max: 12 }),
]);

export async function resetPasswordHandler(req: Request, res: Response, next: NextFunction) {
  try {
    const { token, password } = req.body;
    const result = await resetPassword(token, password);
    res.json(result);
  } catch (err) {
    next(err);
  }
}

export async function getPendingRegistrationsHandler(req: Request, res: Response, next: NextFunction) {
  try {
    const requests = await getPendingRegistrations();
    res.json(requests);
  } catch (err) {
    next(err);
  }
}

export const approveValidation = validate([
  body('username').isString().notEmpty(),
]);

export async function approveRegistration(req: Request, res: Response, next: NextFunction) {
  try {
    const { username } = req.body;
    await approveRegistrationRequest(username, req.user!.id);
    res.json({ message: 'Registration approved' });
  } catch (err) {
    next(err);
  }
}

export async function rejectRegistration(req: Request, res: Response, next: NextFunction) {
  try {
    const { username } = req.body;
    await rejectRegistrationRequest(username, req.user!.id);
    res.json({ message: 'Registration rejected' });
  } catch (err) {
    next(err);
  }
}

export async function getCurrentUser(req: Request, res: Response, next: NextFunction) {
  try {
    res.json({ user: req.user });
  } catch (err) {
    next(err);
  }
}

export async function logout(req: Response) {
  // Client-side token removal, but we can also blacklist tokens here if needed
  res.json({ message: 'Logged out successfully' });
}
```

FILE: backend/src/controllers/imageController.ts

```typescript
import { Request, Response, NextFunction } from 'express';
import multer from 'multer';
import { validateAndProcessImage, getImagePath, getDefaultImagePath } from '@/services/imageService';
import { authenticate } from '@/middleware/auth';
import { AppError } from '@/utils/errors';
import fs from 'fs/promises';
import path from 'path';

// Configure multer for memory storage (we process with sharp)
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 5 * 1024 * 1024 }, // 5MB
  fileFilter: (_req, file, cb) => {
    if (file.mimetype === 'image/jpeg' || file.mimetype === 'image/png') {
      cb(null, true);
    } else {
      cb(new AppError(415, 'Only JPG and PNG images are accepted.', 'UNSUPPORTED_MEDIA_TYPE'));
    }
  },
});

export const uploadProfileImage = upload.single('profileImage');

export async function handleProfileImageUpload(req: Request, res: Response, next: NextFunction) {
  try {
    if (!req.file) {
      throw new AppError(400, 'No file uploaded');
    }
    if (!req.user) {
      throw new AppError(401, 'Authentication required');
    }
    const filename = await validateAndProcessImage(req.file, req.user.id);
    res.json({ filename, message: 'Profile image uploaded successfully' });
  } catch (err) {
    next(err);
  }
}

export async function serveProfileImage(req: Request, res: Response, next: NextFunction) {
  try {
    const { filename } = req.params;
    const filepath = await getImagePath(filename);
    
    // Check if file exists
    try {
      await fs.access(filepath);
    } catch {
      // Serve default image
      const defaultPath = getDefaultImagePath();
      return res.sendFile(defaultPath);
    }
    
    res.sendFile(filepath);
  } catch (err) {
    next(err);
  }
}

export async function serveDefaultImage(_req: Request, res: Response, next: NextFunction) {
  try {
    const defaultPath = getDefaultImagePath();
    res.sendFile(defaultPath);
  } catch (err) {
    next(err);
  }
}
```

FILE: backend/src/controllers/adminController.ts

```typescript
import { Request, Response, NextFunction } from 'express';
import { PrismaClient } from '@prisma/client';
import { authenticate, requireAdmin } from '@/middleware/auth';
import { AppError } from '@/utils/errors';

const prisma = new PrismaClient();

export async function getAllUsers(req: Request, res: Response, next: NextFunction) {
  try {
    const users = await prisma.user.findMany({
      orderBy: { createdAt: 'desc' },
      select: {
        id: true,
        username: true,
        email: true,
        firstName: true,
        lastName: true,
        phone: true,
        role: true,
        status: true,
        profileImage: true,
        companyId: true,
        createdAt: true,
        updatedAt: true,
      },
    });
    res.json(users);
  } catch (err) {
    next(err);
  }
}

export async function getAdminStats(req: Request, res: Response, next: NextFunction) {
  try {
    const [totalUsers, pendingRegistrations, totalCompanies, totalSpaces] = await Promise.all([
      prisma.user.count({ where: { status: 'APPROVED' } }),
      prisma.registrationRequest.count({ where: { status: 'PENDING' } }),
      prisma.company.count(),
      prisma.space.count(),
    ]);

    const usersByRole = await prisma.user.groupBy({
      by: ['role'],
      where: { status: 'APPROVED' },
      _count: true,
    });

    res.json({
      totalUsers,
      pendingRegistrations,
      totalCompanies,
      totalSpaces,
      usersByRole: usersByRole.reduce((acc, curr) => {
        acc[curr.role] = curr._count;
        return acc;
      }, {} as Record<string, number>),
    });
  } catch (err) {
    next(err);
  }
}

export async function getPendingSpaces(req: Request, res: Response, next: NextFunction) {
  try {
    // This would be for space approval if we had that feature
    res.json([]);
  } catch (err) {
    next(err);
  }
}
```

FILE: backend/src/routes/auth.ts

```typescript
import { Router } from 'express';
import { authLimiter } from '@/middleware/rateLimiter';
import {
  publicLogin,
  adminLogin,
  registerMember,
  registerManager,
  forgotPassword,
  getResetTokenStatus,
  resetPasswordHandler,
  getPendingRegistrationsHandler,
  approveRegistration,
  rejectRegistration,
  getCurrentUser,
  logout,
  loginValidation,
  registerMemberValidation,
  registerManagerValidation,
  forgotPasswordValidation,
  resetPasswordValidation,
  approveValidation,
} from '@/controllers/authController';
import { authenticate, requireAdmin } from '@/middleware/auth';
import { uploadProfileImage } from '@/controllers/imageController';

const router = Router();

// Public auth routes
router.post('/login', authLimiter, loginValidation, publicLogin);
router.post('/admin/login', authLimiter, loginValidation, adminLogin);
router.post('/register/member', authLimiter, uploadProfileImage, registerMemberValidation, registerMember);
router.post('/register/manager', authLimiter, uploadProfileImage, registerManagerValidation, registerManager);
router.post('/forgot-password', authLimiter, forgotPasswordValidation, forgotPassword);
router.get('/reset-password/:token', getResetTokenStatus);
router.post('/reset-password', authLimiter, resetPasswordValidation, resetPasswordHandler);

// Protected routes
router.get('/me', authenticate, getCurrentUser);
router.post('/logout', authenticate, logout);

// Admin routes
router.get('/admin/registration-requests', authenticate, requireAdmin, getPendingRegistrationsHandler);
router.post('/admin/registration-requests/approve', authenticate, requireAdmin, approveValidation, approveRegistration);
router.post('/admin/registration-requests/reject', authenticate, requireAdmin, approveValidation, rejectRegistration);

export default router;
```

FILE: backend/src/routes/images.ts

```typescript
import { Router } from 'express';
import { authenticate } from '@/middleware/auth';
import { uploadProfileImage, handleProfileImageUpload, serveProfileImage, serveDefaultImage } from '@/controllers/imageController';

const router = Router();

// Upload profile image (authenticated users)
router.post('/profile-image', authenticate, uploadProfileImage, handleProfileImageUpload);

// Serve uploaded images
router.get('/uploads/:filename', serveProfileImage);
router.get('/default-avatar.png', serveDefaultImage);

export default router;
```

FILE: backend/src/routes/admin.ts

```typescript
import { Router } from 'express';
import { authenticate, requireAdmin } from '@/middleware/auth';
import { getAllUsers, getAdminStats, getPendingSpaces } from '@/controllers/adminController';

const router = Router();

router.get('/users', authenticate, requireAdmin, getAllUsers);
router.get('/statistics', authenticate, requireAdmin, getAdminStats);
router.get('/spaces/pending', authenticate, requireAdmin, getPendingSpaces);

export default router;
```

FILE: backend/src/index.ts

```typescript
import express from 'express';
import cors from 'cors';
import cookieParser from 'cookie-parser';
import { env } from '@/config/env';
import { errorHandler } from '@/middleware/errorHandler';
import { apiLimiter } from '@/middleware/rateLimiter';
import authRoutes from '@/routes/auth';
import imageRoutes from '@/routes/images';
import adminRoutes from '@/routes/admin';
import { PrismaClient } from '@prisma/client';

const app = express();
const prisma = new PrismaClient();

// Middleware
app.use(cors({
  origin: env.FRONTEND_URL,
  credentials: true,
}));
app.use(express.json());
app.use(cookieParser());
app.use(apiLimiter);

// Request logging in development
if (env.NODE_ENV === 'development') {
  app.use((req, _res, next) => {
    console.log(`${req.method} ${req.path}`);
    next();
  });
}

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/users', imageRoutes);
app.use('/api/admin', adminRoutes);

// Health check
app.get('/health', (_req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// 404 handler
app.use((_req, res) => {
  res.status(404).json({ error: 'NOT_FOUND', message: 'Route not found' });
});

// Error handler
app.use(errorHandler);

// Graceful shutdown
process.on('SIGINT', async () => {
  await prisma.$disconnect();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  await prisma.$disconnect();
  process.exit(0);
});

app.listen(env.PORT, () => {
  console.log(`Server running on port ${env.PORT} in ${env.NODE_ENV} mode`);
});

export default app;
```

FILE: backend/.env.example

```env
NODE_ENV=development
PORT=3000
DATABASE_URL="file:./dev.db"
JWT_SECRET="your-super-secret-jwt-key-min-32-chars-long"
JWT_EXPIRES_IN="7d"
UPLOAD_DIR="./uploads"
MAX_FILE_SIZE=5242880
FRONTEND_URL="http://localhost:5173"
```

FILE: backend/.gitignore

```
node_modules/
dist/
.env
*.log
uploads/
prisma/dev.db
prisma/dev.db-journal
coverage/
.vercel
```

FILE: backend/README.md

```markdown
# Coworking Backend API

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Copy `.env.example` to `.env` and configure:
   ```bash
   cp .env.example .env
   ```

3. Generate Prisma client and run migrations:
   ```bash
   npm run prisma:generate
   npm run prisma:migrate
   ```

4. Start development server:
   ```bash
   npm run dev
   ```

## API Endpoints

### Authentication
- `POST /api/auth/login` - Public login (MEMBER, MANAGER)
- `POST /api/auth/admin/login` - Admin login (ADMIN only)
- `POST /api/auth/register/member` - Member registration
- `POST /api/auth/register/manager` - Space Manager registration
- `POST /api/auth/forgot-password` - Request password reset
- `GET /api/auth/reset-password/:token` - Validate reset token
- `POST /api/auth/reset-password` - Reset password with token
- `GET /api/auth/me` - Get current user (requires auth)
- `POST /api/auth/logout` - Logout (requires auth)

### Admin (requires ADMIN role)
- `GET /api/admin/registration-requests` - List pending registrations
- `POST /api/admin/registration-requests/approve` - Approve registration
- `POST /api/admin/registration-requests/reject` - Reject registration
- `GET /api/admin/users` - List all users
- `GET /api/admin/statistics` - Get admin statistics
- `GET /api/admin/spaces/pending` - List pending spaces

### User Profile
- `POST /api/users/profile-image` - Upload profile image (requires auth)
- `GET /api/users/uploads/:filename` - Serve uploaded image
- `GET /api/users/default-avatar.png` - Serve default avatar

## Features Implemented

- JWT-based authentication with role-based access control
- Separate login routes for public users and administrators
- Password reset with 30-minute expiry tokens
- Member and Space Manager registration with admin approval
- Company constraints (max 2 managers per company)
- Profile image upload with validation (JPG/PNG, 100x100 to 300x300)
- Rate limiting on auth endpoints
- Comprehensive input validation
- Secure password hashing with bcrypt
- Protection against account enumeration
- Path traversal prevention for file uploads
```
```