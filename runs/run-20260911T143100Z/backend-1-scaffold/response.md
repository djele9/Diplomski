FILE: backend/package.json

```json
{
  "name": "coworking-backend",
  "version": "1.0.0",
  "description": "Coworking space management backend",
  "main": "dist/server.js",
  "scripts": {
    "build": "tsc",
    "start": "node dist/server.js",
    "dev": "ts-node-dev --respawn --transpile-only src/server.ts"
  },
  "dependencies": {
    "express": "^4.19.2",
    "mongoose": "^8.4.1",
    "jsonwebtoken": "^9.0.2",
    "bcryptjs": "^2.4.3",
    "multer": "^1.4.5-lts.1",
    "dotenv": "^16.4.5",
    "cors": "^2.8.5",
    "helmet": "^7.1.0",
    "express-rate-limit": "^7.4.0"
  },
  "devDependencies": {
    "typescript": "^5.4.5",
    "@types/node": "^20.14.2",
    "@types/express": "^4.17.21",
    "@types/jsonwebtoken": "^9.0.6",
    "@types/bcryptjs": "^2.4.6",
    "@types/multer": "^1.4.11",
    "@types/cors": "^2.8.17",
    "ts-node-dev": "^2.0.0"
  },
  "engines": {
    "node": "22.21.0"
  }
}
```

FILE: backend/tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "moduleResolution": "node",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "outDir": "./dist",
    "rootDir": "./src",
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

FILE: backend/.env.example

```env
# Server
PORT=3000
NODE_ENV=development

# MongoDB
MONGODB_URI=mongodb://localhost:27017/coworking

# JWT
JWT_SECRET=replace-with-a-secure-random-string-at-least-32-chars
JWT_ACCESS_TOKEN_TTL=15m
JWT_REFRESH_TOKEN_TTL=7d

# Password reset
PASSWORD_RESET_TOKEN_TTL=30m

# File upload
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=5242880

# CORS
CORS_ORIGIN=http://localhost:5173
```

FILE: backend/.gitignore

```
node_modules/
dist/
.env
.env.local
*.log
npm-debug.log*
.DS_Store
coverage/
.nyc_output/
uploads/
```

FILE: backend/src/config/env.ts

```typescript
import dotenv from 'dotenv';

dotenv.config();

interface EnvConfig {
  port: number;
  nodeEnv: string;
  mongodbUri: string;
  jwtSecret: string;
  jwtAccessTokenTtl: string;
  jwtRefreshTokenTtl: string;
  passwordResetTokenTtl: string;
  uploadDir: string;
  maxFileSize: number;
  corsOrigin: string;
}

function getEnv(key: string): string {
  const value = process.env[key];
  if (!value) {
    throw new Error(`Missing required environment variable: ${key}`);
  }
  return value;
}

function getEnvNumber(key: string): number {
  const value = getEnv(key);
  const parsed = Number(value);
  if (Number.isNaN(parsed)) {
    throw new Error(`Environment variable ${key} must be a number, got: ${value}`);
  }
  return parsed;
}

export const env: EnvConfig = {
  port: getEnvNumber('PORT'),
  nodeEnv: getEnv('NODE_ENV'),
  mongodbUri: getEnv('MONGODB_URI'),
  jwtSecret: getEnv('JWT_SECRET'),
  jwtAccessTokenTtl: getEnv('JWT_ACCESS_TOKEN_TTL'),
  jwtRefreshTokenTtl: getEnv('JWT_REFRESH_TOKEN_TTL'),
  passwordResetTokenTtl: getEnv('PASSWORD_RESET_TOKEN_TTL'),
  uploadDir: getEnv('UPLOAD_DIR'),
  maxFileSize: getEnvNumber('MAX_FILE_SIZE'),
  corsOrigin: getEnv('CORS_ORIGIN'),
};
```

FILE: backend/src/config/database.ts

```typescript
import mongoose from 'mongoose';
import { env } from './env';

let isConnected = false;

export async function connectDatabase(): Promise<void> {
  if (isConnected) {
    return;
  }

  try {
    await mongoose.connect(env.mongodbUri, {
      maxPoolSize: 10,
      serverSelectionTimeoutMS: 5000,
      socketTimeoutMS: 45000,
    });

    isConnected = true;
    console.log('MongoDB connected successfully');

    mongoose.connection.on('error', (err) => {
      console.error('MongoDB connection error:', err);
      isConnected = false;
    });

    mongoose.connection.on('disconnected', () => {
      console.warn('MongoDB disconnected');
      isConnected = false;
    });

    process.on('SIGINT', async () => {
      await mongoose.connection.close();
      console.log('MongoDB connection closed due to app termination');
      process.exit(0);
    });
  } catch (error) {
    console.error('Failed to connect to MongoDB:', error);
    throw error;
  }
}

export function getConnectionStatus(): boolean {
  return isConnected && mongoose.connection.readyState === 1;
}
```

FILE: backend/src/types/index.ts

```typescript
export enum UserRole {
  MEMBER = 'MEMBER',
  MANAGER = 'MANAGER',
  ADMIN = 'ADMIN',
}

export enum UserStatus {
  PENDING = 'PENDING',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED',
}

export enum RegistrationStatus {
  PENDING = 'PENDING',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED',
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

export interface AuthenticatedRequest extends Express.Request {
  user?: JwtPayload;
}

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
```

FILE: backend/src/utils/AppError.ts

```typescript
import { FieldError, ErrorResponse } from '../types';

export class AppError extends Error {
  public readonly status: number;
  public readonly fieldErrors?: FieldError[];
  public readonly isOperational: boolean;

  constructor(status: number, message: string, fieldErrors?: FieldError[]) {
    super(message);
    this.status = status;
    this.fieldErrors = fieldErrors;
    this.isOperational = true;

    Object.setPrototypeOf(this, AppError.prototype);
    Error.captureStackTrace(this, this.constructor);
  }

  static badRequest(message: string, fieldErrors?: FieldError[]): AppError {
    return new AppError(400, message, fieldErrors);
  }

  static unauthorized(message = 'Invalid or missing credentials'): AppError {
    return new AppError(401, message);
  }

  static forbidden(message = 'You do not have permission to perform this action'): AppError {
    return new AppError(403, message);
  }

  static notFound(message = 'Resource not found'): AppError {
    return new AppError(404, message);
  }

  static conflict(message: string): AppError {
    return new AppError(409, message);
  }

  static payloadTooLarge(message = 'The uploaded file is too large'): AppError {
    return new AppError(413, message);
  }

  static unsupportedMediaType(message = 'Unsupported file type'): AppError {
    return new AppError(415, message);
  }

  static gone(message: string): AppError {
    return new AppError(410, message);
  }

  static internal(message = 'An unexpected error occurred'): AppError {
    const error = new AppError(500, message);
    error.isOperational = false;
    return error;
  }

  toResponse(): ErrorResponse {
    const response: ErrorResponse = {
      status: this.status,
      message: this.message,
    };
    if (this.fieldErrors && this.fieldErrors.length > 0) {
      response.fieldErrors = this.fieldErrors;
    }
    return response;
  }
}

export function isAppError(error: unknown): error is AppError {
  return error instanceof AppError;
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

  if (!/^[A-Za-z]/.test(password)) {
    return { valid: false, message: 'Password must begin with a letter.' };
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

  return { valid: true };
}
```

FILE: backend/src/utils/token.ts

```typescript
import jwt, { SignOptions, VerifyOptions } from 'jsonwebtoken';
import { env } from '../config/env';
import { JwtPayload, TokenPair } from '../types';

const ACCESS_TOKEN_OPTIONS: SignOptions = {
  expiresIn: env.jwtAccessTokenTtl as SignOptions['expiresIn'],
};

const REFRESH_TOKEN_OPTIONS: SignOptions = {
  expiresIn: env.jwtRefreshTokenTtl as SignOptions['expiresIn'],
};

const RESET_TOKEN_OPTIONS: SignOptions = {
  expiresIn: env.passwordResetTokenTtl as SignOptions['expiresIn'],
};

const VERIFY_OPTIONS: VerifyOptions = {
  algorithms: ['HS256'],
};

export function signAccessToken(payload: Omit<JwtPayload, 'iat' | 'exp'>): string {
  return jwt.sign(payload, env.jwtSecret, ACCESS_TOKEN_OPTIONS);
}

export function signRefreshToken(payload: Omit<JwtPayload, 'iat' | 'exp'>): string {
  return jwt.sign(payload, env.jwtSecret, REFRESH_TOKEN_OPTIONS);
}

export function signTokenPair(payload: Omit<JwtPayload, 'iat' | 'exp'>): TokenPair {
  return {
    accessToken: signAccessToken(payload),
    refreshToken: signRefreshToken(payload),
  };
}

export function signPasswordResetToken(payload: Omit<JwtPayload, 'iat' | 'exp'>): string {
  return jwt.sign(payload, env.jwtSecret, RESET_TOKEN_OPTIONS);
}

export function verifyAccessToken(token: string): JwtPayload {
  return jwt.verify(token, env.jwtSecret, VERIFY_OPTIONS) as JwtPayload;
}

export function verifyRefreshToken(token: string): JwtPayload {
  return jwt.verify(token, env.jwtSecret, VERIFY_OPTIONS) as JwtPayload;
}

export function verifyPasswordResetToken(token: string): JwtPayload {
  return jwt.verify(token, env.jwtSecret, VERIFY_OPTIONS) as JwtPayload;
}

export function decodeToken(token: string): JwtPayload | null {
  try {
    return jwt.decode(token) as JwtPayload | null;
  } catch {
    return null;
  }
}
```