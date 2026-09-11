FILE: backend/src/models/user.model.ts

```typescript
import mongoose, { Document, Schema, Model } from 'mongoose';
import { UserRole, UserStatus } from '../types';

export interface IUser extends Document {
  username: string;
  passwordHash: string;
  firstName: string;
  lastName: string;
  phone: string;
  email: string;
  role: UserRole;
  status: UserStatus;
  profileImage: string;
  company?: mongoose.Types.ObjectId;
  createdAt: Date;
  updatedAt: Date;
}

const userSchema = new Schema<IUser>(
  {
    username: {
      type: String,
      required: [true, 'Username is required.'],
      unique: true,
      trim: true,
      minlength: [1, 'Username is required.'],
      maxlength: [50, 'Username cannot exceed 50 characters.'],
    },
    passwordHash: {
      type: String,
      required: [true, 'Password is required.'],
      select: false,
    },
    firstName: {
      type: String,
      required: [true, 'First name is required.'],
      trim: true,
      minlength: [1, 'First name is required.'],
      maxlength: [50, 'First name cannot exceed 50 characters.'],
    },
    lastName: {
      type: String,
      required: [true, 'Last name is required.'],
      trim: true,
      minlength: [1, 'Last name is required.'],
      maxlength: [50, 'Last name cannot exceed 50 characters.'],
    },
    phone: {
      type: String,
      required: [true, 'Contact phone is required.'],
      trim: true,
      validate: {
        validator: function (v: string): boolean {
          return /^\+?[0-9\s\-()]{7,20}$/.test(v);
        },
        message: 'Enter a valid contact phone number.',
      },
    },
    email: {
      type: String,
      required: [true, 'Email address is required.'],
      unique: true,
      trim: true,
      lowercase: true,
      validate: {
        validator: function (v: string): boolean {
          return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
        },
        message: 'Enter a valid email address.',
      },
    },
    role: {
      type: String,
      enum: {
        values: Object.values(UserRole),
        message: 'Invalid role.',
      },
      required: [true, 'Role is required.'],
      default: UserRole.MEMBER,
    },
    status: {
      type: String,
      enum: {
        values: Object.values(UserStatus),
        message: 'Invalid status.',
      },
      required: [true, 'Status is required.'],
      default: UserStatus.PENDING,
    },
    profileImage: {
      type: String,
      required: true,
      default: 'default-avatar.png',
    },
    company: {
      type: Schema.Types.ObjectId,
      ref: 'Company',
      default: null,
    },
  },
  {
    timestamps: true,
    toJSON: {
      transform: function (_doc, ret: Record<string, unknown>): Record<string, unknown> {
        delete ret.__v;
        delete ret.passwordHash;
        return ret;
      },
    },
    toObject: {
      transform: function (_doc, ret: Record<string, unknown>): Record<string, unknown> {
        delete ret.__v;
        delete ret.passwordHash;
        return ret;
      },
    },
  }
);

userSchema.index({ username: 1 }, { unique: true });
userSchema.index({ email: 1 }, { unique: true });
userSchema.index({ role: 1, status: 1 });
userSchema.index({ company: 1 });

export const User: Model<IUser> = mongoose.model<IUser>('User', userSchema);
```

FILE: backend/src/models/company.model.ts

```typescript
import mongoose, { Document, Schema, Model } from 'mongoose';

export interface ICompany extends Document {
  name: string;
  headquartersAddress: string;
  companyNumber: string;
  taxId: string;
  createdAt: Date;
  updatedAt: Date;
}

const companySchema = new Schema<ICompany>(
  {
    name: {
      type: String,
      required: [true, 'Company name is required.'],
      trim: true,
      minlength: [1, 'Company name is required.'],
      maxlength: [100, 'Company name cannot exceed 100 characters.'],
    },
    headquartersAddress: {
      type: String,
      required: [true, 'Headquarters address is required.'],
      trim: true,
      minlength: [1, 'Headquarters address is required.'],
      maxlength: [200, 'Headquarters address cannot exceed 200 characters.'],
    },
    companyNumber: {
      type: String,
      required: [true, 'Company number is required.'],
      unique: true,
      trim: true,
      validate: {
        validator: function (v: string): boolean {
          return /^\d{8}$/.test(v);
        },
        message: 'Company number must be exactly 8 digits.',
      },
    },
    taxId: {
      type: String,
      required: [true, 'Tax ID is required.'],
      unique: true,
      trim: true,
      validate: {
        validator: function (v: string): boolean {
          return /^[1-9]\d{8}$/.test(v);
        },
        message: 'Tax ID must be exactly 9 digits and must not begin with zero.',
      },
    },
  },
  {
    timestamps: true,
    toJSON: {
      transform: function (_doc, ret: Record<string, unknown>): Record<string, unknown> {
        delete ret.__v;
        return ret;
      },
    },
    toObject: {
      transform: function (_doc, ret: Record<string, unknown>): Record<string, unknown> {
        delete ret.__v;
        return ret;
      },
    },
  }
);

companySchema.index({ companyNumber: 1 }, { unique: true });
companySchema.index({ taxId: 1 }, { unique: true });
companySchema.index({ name: 1 });

export const Company: Model<ICompany> = mongoose.model<ICompany>('Company', companySchema);
```

FILE: backend/src/models/registration-request.model.ts

```typescript
import mongoose, { Document, Schema, Model } from 'mongoose';
import { UserRole, RegistrationStatus } from '../types';

export interface IRegistrationRequest extends Document {
  username: string;
  passwordHash: string;
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
  submittedAt: Date;
  decidedAt?: Date;
  decidedBy?: mongoose.Types.ObjectId;
  profileImage: string;
  createdAt: Date;
  updatedAt: Date;
}

const registrationRequestSchema = new Schema<IRegistrationRequest>(
  {
    username: {
      type: String,
      required: [true, 'Username is required.'],
      unique: true,
      trim: true,
      minlength: [1, 'Username is required.'],
      maxlength: [50, 'Username cannot exceed 50 characters.'],
    },
    passwordHash: {
      type: String,
      required: [true, 'Password is required.'],
      select: false,
    },
    firstName: {
      type: String,
      required: [true, 'First name is required.'],
      trim: true,
      minlength: [1, 'First name is required.'],
      maxlength: [50, 'First name cannot exceed 50 characters.'],
    },
    lastName: {
      type: String,
      required: [true, 'Last name is required.'],
      trim: true,
      minlength: [1, 'Last name is required.'],
      maxlength: [50, 'Last name cannot exceed 50 characters.'],
    },
    phone: {
      type: String,
      required: [true, 'Contact phone is required.'],
      trim: true,
      validate: {
        validator: function (v: string): boolean {
          return /^\+?[0-9\s\-()]{7,20}$/.test(v);
        },
        message: 'Enter a valid contact phone number.',
      },
    },
    email: {
      type: String,
      required: [true, 'Email address is required.'],
      unique: true,
      trim: true,
      lowercase: true,
      validate: {
        validator: function (v: string): boolean {
          return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
        },
        message: 'Enter a valid email address.',
      },
    },
    role: {
      type: String,
      enum: {
        values: Object.values(UserRole),
        message: 'Invalid role.',
      },
      required: [true, 'Role is required.'],
      default: UserRole.MEMBER,
    },
    companyName: {
      type: String,
      trim: true,
      maxlength: [100, 'Company name cannot exceed 100 characters.'],
    },
    headquartersAddress: {
      type: String,
      trim: true,
      maxlength: [200, 'Headquarters address cannot exceed 200 characters.'],
    },
    companyNumber: {
      type: String,
      trim: true,
      validate: {
        validator: function (v: string): boolean {
          return !v || /^\d{8}$/.test(v);
        },
        message: 'Company number must be exactly 8 digits.',
      },
    },
    taxId: {
      type: String,
      trim: true,
      validate: {
        validator: function (v: string): boolean {
          return !v || /^[1-9]\d{8}$/.test(v);
        },
        message: 'Tax ID must be exactly 9 digits and must not begin with zero.',
      },
    },
    status: {
      type: String,
      enum: {
        values: Object.values(RegistrationStatus),
        message: 'Invalid registration status.',
      },
      required: [true, 'Status is required.'],
      default: RegistrationStatus.PENDING,
    },
    submittedAt: {
      type: Date,
      required: true,
      default: Date.now,
    },
    decidedAt: {
      type: Date,
    },
    decidedBy: {
      type: Schema.Types.ObjectId,
      ref: 'User',
    },
    profileImage: {
      type: String,
      required: true,
      default: 'default-avatar.png',
    },
  },
  {
    timestamps: true,
    toJSON: {
      transform: function (_doc, ret: Record<string, unknown>): Record<string, unknown> {
        delete ret.__v;
        delete ret.passwordHash;
        return ret;
      },
    },
    toObject: {
      transform: function (_doc, ret: Record<string, unknown>): Record<string, unknown> {
        delete ret.__v;
        delete ret.passwordHash;
        return ret;
      },
    },
  }
);

registrationRequestSchema.index({ username: 1 }, { unique: true });
registrationRequestSchema.index({ email: 1 }, { unique: true });
registrationRequestSchema.index({ status: 1, submittedAt: 1 });
registrationRequestSchema.index({ role: 1, status: 1 });

export const RegistrationRequest: Model<IRegistrationRequest> = mongoose.model<IRegistrationRequest>(
  'RegistrationRequest',
  registrationRequestSchema
);
```

FILE: backend/src/models/password-reset-token.model.ts

```typescript
import mongoose, { Document, Schema, Model } from 'mongoose';

export interface IPasswordResetToken extends Document {
  user: mongoose.Types.ObjectId;
  token: string;
  expiresAt: Date;
  usedAt?: Date;
  createdAt: Date;
  updatedAt: Date;
}

const passwordResetTokenSchema = new Schema<IPasswordResetToken>(
  {
    user: {
      type: Schema.Types.ObjectId,
      ref: 'User',
      required: [true, 'User is required.'],
    },
    token: {
      type: String,
      required: [true, 'Token is required.'],
      unique: true,
      select: false,
    },
    expiresAt: {
      type: Date,
      required: [true, 'Expiration date is required.'],
    },
    usedAt: {
      type: Date,
    },
  },
  {
    timestamps: true,
    toJSON: {
      transform: function (_doc, ret: Record<string, unknown>): Record<string, unknown> {
        delete ret.__v;
        delete ret.token;
        return ret;
      },
    },
    toObject: {
      transform: function (_doc, ret: Record<string, unknown>): Record<string, unknown> {
        delete ret.__v;
        delete ret.token;
        return ret;
      },
    },
  }
);

passwordResetTokenSchema.index({ token: 1 }, { unique: true });
passwordResetTokenSchema.index({ user: 1, expiresAt: 1 });
passwordResetTokenSchema.index({ expiresAt: 1 }, { expireAfterSeconds: 0 });

export const PasswordResetToken: Model<IPasswordResetToken> = mongoose.model<IPasswordResetToken>(
  'PasswordResetToken',
  passwordResetTokenSchema
);
```

FILE: backend/src/models/space.model.ts

```typescript
import mongoose, { Document, Schema, Model } from 'mongoose';

export interface ISpace extends Document {
  name: string;
  description: string;
  address: string;
  city: string;
  capacity: number;
  amenities: string[];
  images: string[];
  company: mongoose.Types.ObjectId;
  pricePerHour: number;
  pricePerDay: number;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

const spaceSchema = new Schema<ISpace>(
  {
    name: {
      type: String,
      required: [true, 'Space name is required.'],
      trim: true,
      minlength: [1, 'Space name is required.'],
      maxlength: [100, 'Space name cannot exceed 100 characters.'],
    },
    description: {
      type: String,
      required: [true, 'Description is required.'],
      trim: true,
      minlength: [1, 'Description is required.'],
      maxlength: [2000, 'Description cannot exceed 2000 characters.'],
    },
    address: {
      type: String,
      required: [true, 'Address is required.'],
      trim: true,
      minlength: [1, 'Address is required.'],
      maxlength: [200, 'Address cannot exceed 200 characters.'],
    },
    city: {
      type: String,
      required: [true, 'City is required.'],
      trim: true,
      minlength: [1, 'City is required.'],
      maxlength: [100, 'City cannot exceed 100 characters.'],
    },
    capacity: {
      type: Number,
      required: [true, 'Capacity is required.'],
      min: [1, 'Capacity must be at least 1.'],
      max: [1000, 'Capacity cannot exceed 1000.'],
    },
    amenities: {
      type: [String],
      default: [],
      validate: {
        validator: function (v: string[]): boolean {
          return v.length <= 50;
        },
        message: 'Cannot have more than 50 amenities.',
      },
    },
    images: {
      type: [String],
      default: [],
      validate: {
        validator: function (v: string[]): boolean {
          return v.length <= 20;
        },
        message: 'Cannot have more than 20 images.',
      },
    },
    company: {
      type: Schema.Types.ObjectId,
      ref: 'Company',
      required: [true, 'Company is required.'],
    },
    pricePerHour: {
      type: Number,
      required: [true, 'Hourly price is required.'],
      min: [0, 'Price cannot be negative.'],
      max: [100000, 'Price cannot exceed 100000.'],
    },
    pricePerDay: {
      type: Number,
      required: [true, 'Daily price is required.'],
      min: [0, 'Price cannot be negative.'],
      max: [1000000, 'Price cannot exceed 1000000.'],
    },
    isActive: {
      type: Boolean,
      default: true,
    },
  },
  {
    timestamps: true,
    toJSON: {
      transform: function (_doc, ret: Record<string, unknown>): Record<string, unknown> {
        delete ret.__v;
        return ret;
      },
    },
    toObject: {
      transform: function (_doc, ret: Record<string, unknown>): Record<string, unknown> {
        delete ret.__v;
        return ret;
      },
    },
  }
);

spaceSchema.index({ company: 1, isActive: 1 });
spaceSchema.index({ city: 1, isActive: 1 });
spaceSchema.index({ name: 'text', description: 'text', address: 'text' });
spaceSchema.index({ pricePerHour: 1 });
spaceSchema.index({ capacity: 1 });

export const Space: Model<ISpace> = mongoose.model<ISpace>('Space', spaceSchema);
```

FILE: backend/src/models/reservation.model.ts

```typescript
import mongoose, { Document, Schema, Model } from 'mongoose';

export enum ReservationStatus {
  PENDING = 'PENDING',
  CONFIRMED = 'CONFIRMED',
  CANCELLED = 'CANCELLED',
  COMPLETED = 'COMPLETED',
}

export interface IReservation extends Document {
  user: mongoose.Types.ObjectId;
  space: mongoose.Types.ObjectId;
  startTime: Date;
  endTime: Date;
  status: ReservationStatus;
  totalPrice: number;
  notes?: string;
  createdAt: Date;
  updatedAt: Date;
}

const reservationSchema = new Schema<IReservation>(
  {
    user: {
      type: Schema.Types.ObjectId,
      ref: 'User',
      required: [true, 'User is required.'],
    },
    space: {
      type: Schema.Types.ObjectId,
      ref: 'Space',
      required: [true, 'Space is required.'],
    },
    startTime: {
      type: Date,
      required: [true, 'Start time is required.'],
    },
    endTime: {
      type: Date,
      required: [true, 'End time is required.'],
    },
    status: {
      type: String,
      enum: {
        values: Object.values(ReservationStatus),
        message: 'Invalid reservation status.',
      },
      required: [true, 'Status is required.'],
      default: ReservationStatus.PENDING,
    },
    totalPrice: {
      type: Number,
      required: [true, 'Total price is required.'],
      min: [0, 'Total price cannot be negative.'],
    },
    notes: {
      type: String,
      trim: true,
      maxlength: [1000, 'Notes cannot exceed 1000 characters.'],
    },
  },
  {
    timestamps: true,
    toJSON: {
      transform: function (_doc, ret: Record<string, unknown>): Record<string, unknown> {
        delete ret.__v;
        return ret;
      },
    },
    toObject: {
      transform: function (_doc, ret: Record<string, unknown>): Record<string, unknown> {
        delete ret.__v;
        return ret;
      },
    },
  }
);

reservationSchema.index({ user: 1, startTime: -1 });
reservationSchema.index({ space: 1, startTime: 1, endTime: 1 });
reservationSchema.index({ status: 1 });
reservationSchema.index({ startTime: 1, endTime: 1 });

reservationSchema.pre('validate', function (next): void {
  if (this.startTime && this.endTime && this.startTime >= this.endTime) {
    this.invalidate('endTime', 'End time must be after start time.');
  }
  next();
});

export const Reservation: Model<IReservation> = mongoose.model<IReservation>('Reservation', reservationSchema);
```

FILE: backend/src/models/index.ts

```typescript
export { User, IUser } from './user.model';
export { Company, ICompany } from './company.model';
export { RegistrationRequest, IRegistrationRequest } from './registration-request.model';
export { PasswordResetToken, IPasswordResetToken } from './password-reset-token.model';
export { Space, ISpace } from './space.model';
export { Reservation, IReservation, ReservationStatus } from './reservation.model';
```