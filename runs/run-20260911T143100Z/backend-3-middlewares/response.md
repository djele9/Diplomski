FILE: backend/src/middlewares/auth.middleware.ts

```typescript
import { Request, Response, NextFunction } from 'express';
import { verifyAccessToken, decodeToken } from '../utils/token';
import { AppError, isAppError } from '../utils/AppError';
import { User } from '../models/user.model';
import { JwtPayload, AuthenticatedRequest } from '../types';

export async function authenticate(
  req: Request,
  _res: Response,
  next: NextFunction
): Promise<void> {
  try {
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      throw AppError.unauthorized('Missing or invalid Authorization header');
    }

    const token = authHeader.slice(7).trim();

    if (!token) {
      throw AppError.unauthorized('Missing token');
    }

    let payload: JwtPayload;

    try {
      payload = verifyAccessToken(token);
    } catch (err) {
      if (err instanceof jwt.TokenExpiredError) {
        throw AppError.unauthorized('Token has expired');
      }
      if (err instanceof jwt.JsonWebTokenError) {
        throw AppError.unauthorized('Invalid token');
      }
      throw AppError.unauthorized('Invalid token');
    }

    const user = await User.findById(payload.sub).select('+passwordHash').lean();

    if (!user) {
      throw AppError.unauthorized('User no longer exists');
    }

    if (user.status !== 'APPROVED') {
      throw AppError.unauthorized('Account is not active');
    }

    const authenticatedReq = req as AuthenticatedRequest;
    authenticatedReq.user = {
      sub: user._id.toString(),
      username: user.username,
      role: user.role,
      iat: payload.iat,
      exp: payload.exp,
    };

    next();
  } catch (error) {
    if (isAppError(error)) {
      next(error);
    } else {
      next(AppError.unauthorized('Authentication failed'));
    }
  }
}

import jwt from 'jsonwebtoken';
```

FILE: backend/src/middlewares/authorize.middleware.ts

```typescript
import { Request, Response, NextFunction } from 'express';
import { AppError, isAppError } from '../utils/AppError';
import { UserRole } from '../types';
import { AuthenticatedRequest } from '../types';

export function authorize(...allowedRoles: UserRole[]) {
  return (req: Request, _res: Response, next: NextFunction): void => {
    try {
      const authReq = req as AuthenticatedRequest;

      if (!authReq.user) {
        throw AppError.unauthorized('Authentication required');
      }

      if (!allowedRoles.includes(authReq.user.role)) {
        throw AppError.forbidden('Insufficient permissions');
      }

      next();
    } catch (error) {
      if (isAppError(error)) {
        next(error);
      } else {
        next(AppError.forbidden('Authorization failed'));
      }
    }
  };
}

export function authorizeOwner(
  getResourceUserId: (req: Request) => Promise<string | null> | string | null
) {
  return async (req: Request, _res: Response, next: NextFunction): Promise<void> => {
    try {
      const authReq = req as AuthenticatedRequest;

      if (!authReq.user) {
        throw AppError.unauthorized('Authentication required');
      }

      const resourceUserId = await getResourceUserId(req);

      if (!resourceUserId) {
        throw AppError.notFound('Resource not found');
      }

      if (authReq.user.sub !== resourceUserId && authReq.user.role !== UserRole.ADMIN) {
        throw AppError.forbidden('You can only access your own resources');
      }

      next();
    } catch (error) {
      if (isAppError(error)) {
        next(error);
      } else {
        next(AppError.forbidden('Ownership verification failed'));
      }
    }
  };
}

export function authorizeCompany(
  getResourceCompanyId: (req: Request) => Promise<string | null> | string | null
) {
  return async (req: Request, _res: Response, next: NextFunction): Promise<void> => {
    try {
      const authReq = req as AuthenticatedRequest;

      if (!authReq.user) {
        throw AppError.unauthorized('Authentication required');
      }

      const resourceCompanyId = await getResourceCompanyId(req);

      if (!resourceCompanyId) {
        throw AppError.notFound('Resource not found');
      }

      const user = await import('../models/user.model').then(m => m.User.findById(authReq.user!.sub).lean());

      if (!user) {
        throw AppError.unauthorized('User not found');
      }

      const userCompanyId = user.company?.toString();

      if (authReq.user.role !== UserRole.ADMIN && userCompanyId !== resourceCompanyId) {
        throw AppError.forbidden('You can only access resources from your own company');
      }

      next();
    } catch (error) {
      if (isAppError(error)) {
        next(error);
      } else {
        next(AppError.forbidden('Company authorization failed'));
      }
    }
  };
}
```

FILE: backend/src/middlewares/validate.middleware.ts

```typescript
import { Request, Response, NextFunction } from 'express';
import { validationResult, ValidationChain, ValidationError } from 'express-validator';
import { AppError } from '../utils/AppError';
import { FieldError } from '../types';

export function validate(validations: ValidationChain[]) {
  return async (req: Request, _res: Response, next: NextFunction): Promise<void> => {
    await Promise.all(validations.map(validation => validation.run(req)));

    const errors = validationResult(req);

    if (!errors.isEmpty()) {
      const fieldErrors: FieldError[] = errors.array().map((error: ValidationError) => {
        if ('path' in error) {
          return { field: error.path, message: error.msg };
        }
        return { field: 'unknown', message: error.msg };
      });

      const uniqueFieldErrors = fieldErrors.reduce((acc: FieldError[], current) => {
        if (!acc.some(e => e.field === current.field && e.message === current.message)) {
          acc.push(current);
        }
        return acc;
      }, []);

      throw AppError.badRequest('Validation failed', uniqueFieldErrors);
    }

    next();
  };
}

export function validateQuery(validations: ValidationChain[]) {
  return async (req: Request, _res: Response, next: NextFunction): Promise<void> => {
    const originalQuery = req.query;
    req.query = { ...req.query };

    await Promise.all(validations.map(validation => validation.run(req)));

    const errors = validationResult(req);

    req.query = originalQuery;

    if (!errors.isEmpty()) {
      const fieldErrors: FieldError[] = errors.array().map((error: ValidationError) => {
        if ('path' in error) {
          return { field: error.path, message: error.msg };
        }
        return { field: 'unknown', message: error.msg };
      });

      const uniqueFieldErrors = fieldErrors.reduce((acc: FieldError[], current) => {
        if (!acc.some(e => e.field === current.field && e.message === current.message)) {
          acc.push(current);
        }
        return acc;
      }, []);

      throw AppError.badRequest('Validation failed', uniqueFieldErrors);
    }

    next();
  };
}
```

FILE: backend/src/middlewares/error.middleware.ts

```typescript
import { Request, Response, NextFunction } from 'express';
import mongoose from 'mongoose';
import { AppError, isAppError } from '../utils/AppError';
import { ErrorResponse } from '../types';

export function errorHandler(
  err: Error,
  _req: Request,
  res: Response,
  _next: NextFunction
): void {
  console.error('Error:', {
    message: err.message,
    stack: err.stack,
    name: err.name,
  });

  if (isAppError(err)) {
    const response: ErrorResponse = err.toResponse();
    res.status(err.status).json(response);
    return;
  }

  if (err instanceof mongoose.Error.ValidationError) {
    const fieldErrors = Object.values(err.errors).map(e => ({
      field: e.path,
      message: e.message,
    }));
    const response: ErrorResponse = {
      status: 400,
      message: 'Validation failed',
      fieldErrors,
    };
    res.status(400).json(response);
    return;
  }

  if (err instanceof mongoose.mongo.MongoServerError && err.code === 11000) {
    const field = Object.keys(err.keyPattern || {})[0] || 'field';
    const response: ErrorResponse = {
      status: 409,
      message: `A record with this ${field} already exists`,
      fieldErrors: [{ field, message: `${field} must be unique` }],
    };
    res.status(409).json(response);
    return;
  }

  if (err instanceof SyntaxError && 'status' in err && err.status === 400 && 'body' in err) {
    const response: ErrorResponse = {
      status: 400,
      message: 'Invalid JSON payload',
    };
    res.status(400).json(response);
    return;
  }

  const response: ErrorResponse = {
    status: 500,
    message: 'An unexpected error occurred',
  };
  res.status(500).json(response);
}

export function notFoundHandler(_req: Request, res: Response): void {
  const response: ErrorResponse = {
    status: 404,
    message: 'Route not found',
  };
  res.status(404).json(response);
}
```

FILE: backend/src/middlewares/upload.middleware.ts

```typescript
import multer, { FileFilterCallback, Multer } from 'multer';
import { Request } from 'express';
import { AppError } from '../utils/AppError';
import { env } from '../config/env';
import * as path from 'path';
import * as fs from 'fs';
import { fileTypeFromBuffer } from 'file-type';

const ALLOWED_MIME_TYPES = ['image/jpeg', 'image/png'];
const ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png'];
const MIN_DIMENSION = 100;
const MAX_DIMENSION = 300;

function ensureUploadDir(): void {
  if (!fs.existsSync(env.uploadDir)) {
    fs.mkdirSync(env.uploadDir, { recursive: true });
  }
}

function sanitizeFileName(originalName: string): string {
  const ext = path.extname(originalName).toLowerCase();
  const baseName = path.basename(originalName, ext)
    .replace(/[^a-zA-Z0-9._-]/g, '_')
    .substring(0, 100);
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 8);
  return `${baseName}_${timestamp}_${random}${ext}`;
}

const storage = multer.diskStorage({
  destination: (_req: Request, _file: Express.Multer.File, cb: (error: Error | null, destination: string) => void): void => {
    ensureUploadDir();
    cb(null, env.uploadDir);
  },
  filename: (_req: Request, file: Express.Multer.File, cb: (error: Error | null, filename: string) => void): void => {
    cb(null, sanitizeFileName(file.originalname));
  },
});

function fileFilter(
  _req: Request,
  file: Express.Multer.File,
  cb: FileFilterCallback
): void {
  if (!ALLOWED_MIME_TYPES.includes(file.mimetype)) {
    cb(new AppError(415, 'Only JPG and PNG images are accepted'));
    return;
  }

  const ext = path.extname(file.originalname).toLowerCase();
  if (!ALLOWED_EXTENSIONS.includes(ext)) {
    cb(new AppError(415, 'Only JPG and PNG images are accepted'));
    return;
  }

  cb(null, true);
}

export const upload: Multer = multer({
  storage,
  fileFilter,
  limits: {
    fileSize: env.maxFileSize,
    files: 1,
  },
});

export async function validateImageDimensions(
  req: Request,
  _res: Response,
  next: NextFunction
): Promise<void> {
  try {
    if (!req.file) {
      return next();
    }

    const fileBuffer = req.file.buffer || fs.readFileSync(req.file.path);
    const type = await fileTypeFromBuffer(fileBuffer);

    if (!type || !ALLOWED_MIME_TYPES.includes(type.mime)) {
      if (req.file.path && fs.existsSync(req.file.path)) {
        fs.unlinkSync(req.file.path);
      }
      throw AppError.unsupportedMediaType('Only JPG and PNG images are accepted');
    }

    const sharp = (await import('sharp')).default;
    const metadata = await sharp(fileBuffer).metadata();

    if (!metadata.width || !metadata.height) {
      if (req.file.path && fs.existsSync(req.file.path)) {
        fs.unlinkSync(req.file.path);
      }
      throw AppError.badRequest('Unable to determine image dimensions');
    }

    if (
      metadata.width < MIN_DIMENSION ||
      metadata.height < MIN_DIMENSION ||
      metadata.width > MAX_DIMENSION ||
      metadata.height > MAX_DIMENSION
    ) {
      if (req.file.path && fs.existsSync(req.file.path)) {
        fs.unlinkSync(req.file.path);
      }
      throw AppError.badRequest('The image must be between 100x100 and 300x300 pixels.');
    }

    next();
  } catch (error) {
    if (error instanceof AppError) {
      next(error);
    } else {
      next(AppError.badRequest('Image validation failed'));
    }
  }
}

export function handleMulterError(
  err: Error,
  _req: Request,
  _res: Response,
  next: NextFunction
): void {
  if (err instanceof multer.MulterError) {
    if (err.code === 'LIMIT_FILE_SIZE') {
      next(AppError.payloadTooLarge('The uploaded file is too large'));
      return;
    }
    if (err.code === 'LIMIT_FILE_COUNT') {
      next(AppError.badRequest('Too many files'));
      return;
    }
    if (err.code === 'LIMIT_UNEXPECTED_FILE') {
      next(AppError.badRequest('Unexpected file field'));
      return;
    }
    next(AppError.badRequest(err.message));
    return;
  }
  next(err);
}
```