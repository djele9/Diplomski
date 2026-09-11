FILE: backend/src/app.ts

```typescript
import express, { Request, Response, NextFunction } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import rateLimit from 'express-rate-limit';
import * as path from 'path';
import { env } from '../config/env';
import { errorHandler, notFoundHandler } from '../middlewares/error.middleware';
import authRouter from '../routers/auth.routes';
import registrationRouter from '../routers/registration.routes';
import userRouter from '../routers/user.routes';
import spaceRouter from '../routers/space.routes';
import reservationRouter from '../routers/reservation.routes';
import companyRouter from '../routers/company.routes';
import adminRouter from '../routers/admin.routes';

const app = express();

app.use(helmet());

app.use(cors({
  origin: env.corsOrigin,
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
}));

app.use(express.json({ limit: '1mb' }));
app.use(express.urlencoded({ extended: true, limit: '1mb' }));

app.use(morgan('combined'));

const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 20,
  message: { status: 429, message: 'Too many authentication attempts, please try again later.' },
  standardHeaders: true,
  legacyHeaders: false,
});

app.use('/api/auth/login', authLimiter);
app.use('/api/auth/admin/login', authLimiter);
app.use('/api/auth/forgot-password', authLimiter);
app.use('/api/auth/reset-password', authLimiter);
app.use('/api/auth/register', authLimiter);

app.use('/uploads', express.static(path.join(process.cwd(), env.uploadDir)));

app.use('/api/auth', authRouter);
app.use('/api/auth', registrationRouter);
app.use('/api/users', userRouter);
app.use('/api/spaces', spaceRouter);
app.use('/api/reservations', reservationRouter);
app.use('/api/companies', companyRouter);
app.use('/api/admin', adminRouter);

app.get('/api/health', (_req: Request, res: Response): void => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.use(notFoundHandler);
app.use(errorHandler);

export default app;
```

FILE: backend/src/server.ts

```typescript
import { createServer } from 'http';
import { connectDatabase } from '../config/database';
import { env } from '../config/env';
import { runBootstrap } from '../seed/bootstrap';
import app from './app';

let server: ReturnType<typeof createServer>;

async function start(): Promise<void> {
  try {
    await connectDatabase();
    await runBootstrap();

    server = createServer(app);

    server.listen(env.port, (): void => {
      console.log(`Server running in ${env.nodeEnv} mode on port ${env.port}`);
    });
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

function shutdown(signal: string): void {
  console.log(`${signal} received, shutting down gracefully...`);

  if (server) {
    server.close(async (): Promise<void> => {
      console.log('HTTP server closed');

      try {
        const mongoose = await import('mongoose');
        await mongoose.connection.close();
        console.log('MongoDB connection closed');
        process.exit(0);
      } catch (error) {
        console.error('Error during shutdown:', error);
        process.exit(1);
      }
    });

    setTimeout((): void => {
      console.error('Forced shutdown after timeout');
      process.exit(1);
    }, 10000);
  } else {
    process.exit(0);
  }
}

process.on('SIGINT', () => shutdown('SIGINT'));
process.on('SIGTERM', () => shutdown('SIGTERM'));

process.on('uncaughtException', (error: Error): void => {
  console.error('Uncaught exception:', error);
  shutdown('uncaughtException');
});

process.on('unhandledRejection', (reason: unknown): void => {
  console.error('Unhandled rejection:', reason);
  shutdown('unhandledRejection');
});

start();
```

FILE: backend/src/seed/bootstrap.ts

```typescript
import { User } from '../models/user.model';
import { hashPassword } from '../utils/password';
import { env } from '../config/env';
import { UserRole, UserStatus } from '../types';

export async function runBootstrap(): Promise<void> {
  const adminUsername = process.env.ADMIN_USERNAME;
  const adminPassword = process.env.ADMIN_PASSWORD;

  if (!adminUsername || !adminPassword) {
    throw new Error('ADMIN_USERNAME and ADMIN_PASSWORD environment variables are required for administrator bootstrap');
  }

  const existingAdmin = await User.findOne({ role: UserRole.ADMIN }).lean();

  if (existingAdmin) {
    console.log('Administrator account already exists, skipping bootstrap');
    return;
  }

  const passwordHash = await hashPassword(adminPassword);

  await User.create({
    username: adminUsername,
    passwordHash,
    firstName: 'System',
    lastName: 'Administrator',
    phone: '+381000000000',
    email: 'admin@localhost',
    role: UserRole.ADMIN,
    status: UserStatus.APPROVED,
    profileImage: 'default-avatar.png',
  });

  console.log(`Administrator account "${adminUsername}" created successfully`);
}
```

FILE: backend/.env

```
PORT=3000
NODE_ENV=development
MONGODB_URI=mongodb://localhost:27017/coworking
JWT_SECRET=dev-secret-change-in-production-min-32-chars
JWT_ACCESS_TOKEN_TTL=15m
JWT_REFRESH_TOKEN_TTL=7d
PASSWORD_RESET_TOKEN_TTL=30m
UPLOAD_DIR=uploads
MAX_FILE_SIZE=5242880
CORS_ORIGIN=http://localhost:5173
ADMIN_USERNAME=admin
ADMIN_PASSWORD=Admin123!
```