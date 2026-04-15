# VocalSync

AI Speech Coach

A comprehensive web application for real-time speech analysis and feedback, powered by AI. Transform your public speaking skills with instant analysis of speaking rate, filler words, confidence, and more.

## 🚀 Features

### Core Functionality

### Technical Features

## 📋 Prerequisites


## 🛠️ Quick Start

### Option 1: Docker Compose (Recommended)

1. **Clone the repository**
```bash
git clone <repository-url>
cd speech-coach-ai
```

2. **Set up environment variables**
```bash
# Backend
cp backend/.env.example backend/.env
# Edit backend/.env with your Firebase credentials

# Frontend  
cp frontend/.env.example frontend/.env
# Edit frontend/.env with your Firebase config
```

3. **Start all services**
```bash
docker-compose up -d
```

4. **Access the application**

### Option 2: Manual Setup

#### Backend Setup

1. **Navigate to backend directory**
```bash
cd backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Set up MySQL database**
```bash
mysql -u root -p < docs/database_schema.sql
```

6. **Start the backend server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your Firebase configuration
```

4. **Start the development server**
```bash
npm run dev
```

## 🔧 Configuration

### Firebase Setup

1. **Create a Firebase project**
   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Create a new project
   - Enable Authentication with Google provider

2. **Get Firebase credentials**
   - Go to Project Settings > Service accounts
   - Generate a new private key
   - Download the JSON file

3. **Configure backend**
   ```env
   FIREBASE_PROJECT_ID=your-project-id
   FIREBASE_PRIVATE_KEY_ID=your-private-key-id
   FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYour-Key-Here\n-----END PRIVATE KEY-----\n"
   FIREBASE_CLIENT_EMAIL=your-service-account-email
   FIREBASE_CLIENT_ID=your-client-id
   ```

4. **Configure frontend**
   ```env
   NEXT_PUBLIC_FIREBASE_API_KEY=your-api-key
   NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
   NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
   NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
   NEXT_PUBLIC_FIREBASE_APP_ID=your-app-id
   ```

### Database Setup

1. **Install MySQL 8.0+**
2. **Create database**
```sql
CREATE DATABASE speech_coach CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

3. **Run the schema**
```bash
mysql -u username -p speech_coach < docs/database_schema.sql
```

## 📊 API Documentation

### Authentication Endpoints

### Session Endpoints

### Dashboard Endpoints

### WebSocket

## 🏗️ Architecture

### Backend Structure
```
backend/
├── app/
│   └── main.py              # FastAPI application entry point
├── core/
│   ├── config.py           # Configuration settings
│   └── security.py         # Authentication & security
├── api/routes/
│   ├── auth.py             # Authentication endpoints
│   ├── session.py          # Session management
│   └── dashboard.py        # Analytics endpoints
├── services/
│   ├── speech/             # Speech processing (Whisper, fillers)
│   ├── audio/              # Audio analysis (Librosa)
│   ├── emotion/            # Emotion detection
│   ├── scoring/            # Goal-based scoring
│   └── analytics/          # Trend analysis
├── models/                 # SQLAlchemy models
├── schemas/                # Pydantic schemas
├── db/                     # Database configuration
└── workers/                # Background processing
```

### Frontend Structure
```
frontend/
├── app/
│   ├── login/              # Authentication pages
│   ├── practice/           # Practice session interface
│   ├── dashboard/          # Analytics dashboard
│   └── session/            # Session details
├── components/
│   ├── ui/                 # Reusable UI components
│   ├── audio/              # Audio recording components
│   ├── video/              # Video capture components
│   └── charts/             # Data visualization
├── hooks/                  # Custom React hooks
├── services/               # API & WebSocket services
└── styles/                 # Tailwind CSS configuration
```

## 🧠 AI Pipeline

### Real-time Processing
1. **Audio Capture**: Web Audio API captures microphone input
2. **Chunk Streaming**: Audio chunks sent via WebSocket
3. **Live Analysis**: 
   - Volume level detection
   - Silence detection
   - Speaking rate calculation
   - Filler word counting

### Post-session Analysis
1. **Full Transcription**: Whisper converts audio to text
2. **Feature Extraction**: Librosa analyzes audio characteristics
3. **Emotion Detection**: Rule-based analysis of speech patterns
4. **Goal Scoring**: Weighted scoring based on practice objectives
5. **Trend Analysis**: Performance tracking over time

## 📈 Metrics & Analytics

### Speech Metrics

### Analytics Features

## 🚀 Deployment

### Production Deployment

1. **Environment Setup**
```bash
# Set production environment variables
export NODE_ENV=production
export DATABASE_URL=mysql+mysqlconnector://user:pass@host:3306/db
```

2. **Build and Deploy**
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm run build
npm start
```

3. **Docker Deployment**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables

#### Backend (.env)
```env
DATABASE_URL=mysql+mysqlconnector://user:password@localhost:3306/speech_coach
SECRET_KEY=your-production-secret-key
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----..."
FIREBASE_CLIENT_EMAIL=service-account@project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id
```

#### Frontend (.env)
```env
NEXT_PUBLIC_API_URL=https://your-api-domain.com
NEXT_PUBLIC_FIREBASE_API_KEY=your-api-key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Integration Tests
```bash
# Test WebSocket connection
# Test audio processing pipeline
# Test database operations
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

### Common Issues

1. **Firebase Authentication Errors**
   - Verify Firebase project configuration
   - Check service account permissions
   - Ensure OAuth domains are configured

2. **Database Connection Issues**
   - Verify MySQL is running
   - Check connection string format
   - Ensure database exists and schema is loaded

3. **Audio Recording Issues**
   - Check browser permissions
   - Verify HTTPS is used in production
   - Test microphone hardware

4. **WebSocket Connection Issues**
   - Check CORS configuration
   - Verify firewall settings
   - Test network connectivity

### Performance Optimization

1. **Backend Optimization**
   - Use connection pooling for database
   - Implement Redis for caching
   - Optimize audio processing pipeline

2. **Frontend Optimization**
   - Use React.memo for component optimization
   - Implement lazy loading for charts
   - Optimize bundle size with code splitting

## 📞 Support

For support and questions:


**Built with ❤️ for improving public speaking skills**
