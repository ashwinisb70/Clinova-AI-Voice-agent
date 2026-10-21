# CLINOVA — Hospital Management Platform

A modern, professional SaaS application for hospital management built with React, FastAPI, and MongoDB.

## Overview

CLINOVA is a comprehensive hospital management platform that enables healthcare institutions to:

- **Manage Patients** - Centralized patient records and profiles
- **Schedule Appointments** - Efficient appointment booking and tracking
- **Manage Doctors** - Doctor profiles, specializations, and availability
- **Organize Departments** - Department management and coordination
- **Billing & Payments** - Secure invoicing and online payment processing
- **Notifications** - Automated patient and staff communications
- **Email Management** - Email logs and retry functionality
- **Activity History** - Complete audit trail of all operations

## Tech Stack

### Frontend
- **React 18** - UI library
- **TypeScript** - Type-safe development
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Axios** - HTTP client
- **React Router** - Routing
- **Recharts** - Data visualization
- **Lucide React** - Icons

### Backend
- **FastAPI** - Python web framework
- **MongoDB** - NoSQL database
- **Motor** - Async MongoDB driver
- **JWT** - Authentication
- **Razorpay** - Payment processing
- **Bolna** - AI receptionist
- **Deepgram** - Speech-to-text
- **Sendgrid/SMTP** - Email delivery

## Project Structure

```
CLINOVA/
│
├── frontend/                 # React + TypeScript frontend
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/           # Application pages
│   │   ├── services/        # API service layer
│   │   ├── context/         # React Context for state
│   │   ├── App.tsx          # Main App component
│   │   └── main.tsx         # Entry point
│   ├── .env.example         # Frontend environment variables
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── backend/                  # FastAPI backend
│   ├── main.py              # Application entry point
│   ├── auth.py              # Authentication logic
│   ├── database.py          # Database configuration
│   ├── models.py            # Pydantic models
│   ├── routers/             # API route handlers
│   │   ├── patients.py
│   │   ├── appointments.py
│   │   ├── billing.py
│   │   ├── notifications.py
│   │   ├── hospital.py
│   │   ├── admin.py
│   │   ├── conversations.py
│   │   └── voice.py
│   ├── services/            # Business logic
│   │   ├── booking.py
│   │   ├── email_service.py
│   │   ├── payments_gateway.py
│   │   ├── notify.py
│   │   └── common.py
│   ├── .env.example         # Backend environment variables
│   └── requirements.txt      # Python dependencies
│
└── README.md                # This file
```

## Installation & Setup

### Prerequisites

- **Node.js** 16+ and npm/yarn
- **Python** 3.9+
- **MongoDB** 4.0+
- Git

### Backend Setup (Windows)

1. **Navigate to backend directory**
   ```cmd
   cd backend
   ```

2. **Create Python virtual environment**
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```cmd
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```cmd
   copy .env.example .env
   ```
   Edit `.env` and set your configuration:
   - MongoDB connection string
   - JWT secret key
   - Hospital details
   - API keys (optional integrations)

5. **Run the server**
   ```cmd
   uvicorn main:app --reload
   ```
   Backend will be available at `http://localhost:8000`
   - Swagger documentation: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

### Frontend Setup (Windows)

1. **Navigate to frontend directory**
   ```cmd
   cd frontend
   ```

2. **Install dependencies**
   ```cmd
   npm install
   ```

3. **Configure environment variables**
   ```cmd
   copy .env.example .env
   ```
   Configure:
   ```
   VITE_API_URL=http://localhost:8000
   VITE_APP_NAME=CLINOVA
   ```

4. **Start development server**
   ```cmd
   npm run dev
   ```
   Frontend will be available at `http://localhost:5173`

5. **Build for production**
   ```cmd
   npm run build
   ```

## Environment Variables

### Backend - Required for Basic Application

| Variable | Description | Example |
|----------|-------------|---------|
| `MONGODB_URI` | MongoDB connection string | `mongodb://localhost:27017` |
| `MONGODB_DB_NAME` | Database name | `clinova_hospital` |
| `JWT_SECRET` | Secret key for JWT tokens | `your_secret_key` |
| `DEFAULT_HOSPITAL_ID` | Default hospital identifier | `DEFAULT` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `http://localhost:5173` |
| `HOSPITAL_NAME` | Hospital name | `Default Hospital` |
| `EMAIL_HOST` | SMTP server host | `smtp.gmail.com` |
| `EMAIL_USERNAME` | SMTP username | `your_email@gmail.com` |
| `EMAIL_PASSWORD` | SMTP password/app password | `your_app_password` |

### Backend - Optional Features

| Feature | Variables | Impact if Missing |
|---------|-----------|-------------------|
| **Online Payments** | `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET` | Online payment checkout unavailable, but billing records still display |
| **AI Receptionist** | `BOLNA_API_KEY`, `BOLNA_AGENT_ID`, `BOLNA_API_BASE`, `AGENT_API_KEY` | AI receptionist callback unavailable, regular booking still works |
| **Speech-to-Text** | `STT_API_KEY` (Deepgram) | Speech-to-text feature unavailable |
| **Email Delivery** | `EMAIL_*` variables | Email records display but delivery fails, use console output for testing |

**CRITICAL SECURITY RULE:** Never expose these keys to the frontend:
- `RAZORPAY_KEY_SECRET`
- `RAZORPAY_WEBHOOK_SECRET`
- `MONGODB_URI` (if credentials included)
- `JWT_SECRET`
- `BOLNA_API_KEY`
- Email credentials

### Frontend

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `http://localhost:8000` |
| `VITE_APP_NAME` | Application name | `CLINOVA` |

## Features

### Public Pages
- **Landing Page** - Marketing homepage with feature showcase
- **Login** - Staff/Admin authentication
- **Signup** - New user registration

### Protected Pages (Requires Authentication)

#### Dashboard
- Hospital statistics and KPIs
- Appointment overview chart
- Recent activity feed
- Quick actions

#### Patients
- Patient directory with search
- Patient profiles with medical history
- Patient registration
- Contact information management

#### Doctors
- Doctor directory and profiles
- Specialization and department tracking
- Availability scheduling
- Consultation fees

#### Departments
- Department management
- Staff allocation
- Specialization tracking

#### Appointments
- Appointment scheduling
- Calendar view
- Status tracking (Pending, Confirmed, Completed, Cancelled)
- Reschedule functionality
- Walk-in appointments
- Recurring appointments

#### Billing
- Invoice generation and tracking
- Invoice line items management
- Status monitoring (Pending, Paid, Overdue)
- Invoice history

#### Payments
- Payment records and history
- Payment method tracking
- Online payment integration (Razorpay)
- Payment status monitoring

#### Notifications
- Patient and staff notifications
- Notification history
- Mark as read functionality

#### Email
- Email delivery logs
- Email status tracking
- Failed email retry functionality

#### History
- Complete activity audit trail
- Appointment history
- System event logs

#### My Profile
- User profile information
- Personal details editing
- Security settings
- Password management

## API Documentation

### Authentication Endpoints

```
POST /auth/register          # Staff registration
POST /auth/login             # Staff login
GET /auth/me                 # Get current user info
```

### Patient Endpoints

```
POST /patients/register      # Patient registration
POST /patients/login         # Patient login
GET /patients/me             # Get patient profile
PUT /patients/me             # Update patient profile
```

### Hospital Data

```
GET /hospital                # Get hospital details
GET /doctors                 # List doctors
GET /departments             # List departments
POST /admin/doctors          # Create doctor (admin)
POST /admin/departments      # Create department (admin)
```

### Appointments

```
POST /book-appointment       # Book appointment
GET /appointments            # List appointments
GET /appointments/{id}       # Get appointment details
POST /appointments/{id}/cancel
POST /appointments/{id}/reschedule
```

### Billing & Payments

```
GET /invoices                # List invoices
GET /invoices/{id}           # Get invoice details
GET /payments                # List payments
POST /payments               # Record payment
```

### Notifications

```
GET /notifications           # List notifications
POST /notifications/{id}/read
```

## Running the Application

### Development

**Terminal 1 - Backend:**
```cmd
cd backend
venv\Scripts\activate
uvicorn main:app --reload
# Backend at http://localhost:8000
```

**Terminal 2 - Frontend:**
```cmd
cd frontend
npm run dev
# Frontend at http://localhost:5173
```

### Testing

1. **Login** with credentials created during setup
2. **Dashboard** shows overview statistics
3. **Create test data** in Dashboard page
4. **Test appointment booking** in Appointments page
5. **Test billing** in Billing page
6. **Test notifications** in Notifications page

### Production Build

**Frontend:**
```cmd
cd frontend
npm run build
npm run preview
```

**Backend:**
```cmd
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Security Considerations

### Backend Security
✅ JWT-based authentication
✅ Password hashing with bcrypt
✅ CORS configuration
✅ Environment variable separation
✅ Database scoping by hospital_id

### Frontend Security
✅ Protected routes with AuthContext
✅ Token stored in localStorage (consider moving to secure HttpOnly cookies)
✅ No API keys in frontend
✅ Input validation on forms

### Important Rules
⚠️ Never commit `.env` files
⚠️ Never expose `RAZORPAY_KEY_SECRET` to frontend
⚠️ Always use HTTPS in production
⚠️ Rotate JWT secrets regularly
⚠️ Keep dependencies updated

## Troubleshooting

### Backend won't start
```bash
# Check MongoDB is running
# Check port 8000 is available
# Verify .env file exists
# Check Python version (3.9+)
```

### Frontend build fails
```bash
# Clear node_modules and reinstall
rm -r node_modules
npm install
npm run build
```

### API connection errors
```bash
# Verify backend is running on correct port
# Check VITE_API_URL in frontend .env
# Verify CORS configuration in backend
```

### Database errors
```bash
# Ensure MongoDB is running
# Check MONGODB_URI in .env
# Verify database permissions
```

## Development Workflow

1. **Create a new branch** for each feature
   ```bash
   git checkout -b feature/patient-import
   ```

2. **Frontend changes:**
   - Create components in `src/components/`
   - Create pages in `src/pages/`
   - Update API service in `src/services/api.ts`

3. **Backend changes:**
   - Update models in `models.py`
   - Create routes in `routers/`
   - Add business logic in `services/`

4. **Test locally** before committing
5. **Commit with clear messages**
   ```bash
   git commit -m "feat: add patient import functionality"
   ```

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## License

Proprietary - CLINOVA Hospital Management Platform

## Support

For issues or questions:
- Create an issue on GitHub
- Contact support@clinova.com

## Changelog

### v1.0.0 (Oct 2024)
- Initial release
- Core hospital management features
- Patient appointment system
- Billing and payment integration
- Email and notification system
- AI receptionist integration

---

**CLINOVA — Smarter Hospital Management for a Healthier Tomorrow**

© 2024 CLINOVA. All rights reserved.
