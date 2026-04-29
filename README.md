# 🌾 FarmerRoute - Agricultural AI Platform

**FarmerRoute** is a comprehensive digital agriculture platform designed to connect farmers with agricultural experts, provide AI-powered disease detection, real-time weather insights, and market intelligence. Built with Django and powered by machine learning, it empowers farmers with actionable insights for better crop management and market decisions.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation Guide](#installation-guide)
- [Environment Setup](#environment-setup)
- [Database Migration](#database-migration)
- [Running the Application](#running-the-application)
- [API Endpoints](#api-endpoints)
- [Features in Detail](#features-in-detail)
- [Multilingual Support](#multilingual-support)
- [Contributing](#contributing)
- [Support & Contact](#support--contact)
- [License](#license)

---

## 🎯 Overview

FarmerRoute is an end-to-end agricultural solution that bridges the gap between farmers and agricultural experts through:

- **AI-Powered Disease Detection** - Real-time plant disease identification using deep learning models
- **Expert Query System** - Connect with agricultural experts for personalized advice
- **Smart Chatbot** - Voice and text-based AI assistant for farming guidance
- **Weather Intelligence** - Location-based weather forecasts with farming recommendations
- **Market Information** - Real-time crop market prices across different regions
- **Crop Planning Tool** - Detailed crop planning and management resources
- **Multi-language Support** - Support for 9 Indian languages for wider accessibility

---

## ✨ Key Features

### 1. **User Management**
- Three user roles: Farmer, Expert, Administrator
- User authentication with email verification
- Profile management and user dashboard
- Session management for security
- Badge and achievement system

### 2. **AI Disease Detection**
- Real-time plant disease identification
- Upload crop images for instant diagnosis
- disease history and tracking
- Deep learning model with high accuracy (TensorFlow/Keras)
- Support for multiple crop diseases

### 3. **Expert Consultation**
- Farmers can submit crop-related queries with images
- Expert dashboard for query management
- Real-time advice and recommendations
- Query status tracking (Pending, Answered, Closed)
- Email notifications for new queries

### 4. **Smart Farming Chatbot**
- AI-powered conversational assistant
- **Voice Input** - Speak naturally, auto-submits on pause
- **Text Input** - Type your questions
- Multi-language support (Hindi, Telugu, Tamil, Marathi, Bengali, Gujarati, Kannada, Punjabi, English)
- Text-to-speech for responses
- Real-time response generation
- Market region selection for localized advice

### 5. **Weather Integration**
- Real-time weather data using geolocation
- Location-based GPS detection
- Farming advice based on weather conditions
- Wind speed, humidity, temperature monitoring
- Weather-based crop recommendations

### 6. **Market Intelligence**
- Real-time crop market prices
- Region-specific pricing data
- Market trends and analysis
- Help farmers make informed selling decisions

### 7. **Crop Library**
- Detailed crop information database
- Crop-specific guidance and best practices
- Planning resources for each crop type
- Seasonal recommendations

### 8. **Inventory Management**
- Track agricultural inventory
- Item quantity management
- Bulk import/export capabilities
- History tracking

---

## 🛠 Technology Stack

### Backend
- **Framework**: Django 4.2+
- **Database**: SQLite (Development) / PostgreSQL (Production)
- **Python**: 3.8+
- **Task Queue**: (Future - Celery)

### AI/ML
- **TensorFlow/Keras** - Deep learning models for disease detection
- **OpenCV** - Image processing
- **scikit-learn** - Machine learning utilities
- **NumPy/Pandas** - Data processing

### Frontend
- **Template Engine**: Django Templates
- **CSS Framework**: Tailwind CSS
- **JavaScript**: Vanilla JS with async/await
- **Font Awesome**: Icon library

### APIs & Services
- **Web Speech API** - Voice recognition and TTS
- **Geolocation API** - User location detection
- **OpenStreetMap API** - Reverse geocoding
- **Weather API** - Real-time weather data

### Authentication & Security
- Django built-in authentication
- CSRF protection
- Password reset via email
- Email verification for signup
- Session management

### Multilingual
- Django i18n/l10n
- Support for 9 Indian languages

---

## 📁 Project Structure

```
FarmerRoute/
├── agri_connect/              # Django project settings
│   ├── settings.py            # Project configuration
│   ├── urls.py                # Main URL routing
│   ├── wsgi.py                # WSGI application
│   └── asgi.py                # ASGI application
│
├── core/                       # Main application
│   ├── models.py              # Database models (User, Query, Advice, etc.)
│   ├── views.py               # View controllers
│   ├── urls.py                # App URL routing
│   ├── forms.py               # Django forms
│   ├── admin.py               # Django admin config
│   ├── auth_backends.py       # Custom authentication
│   ├── chatbot_service.py     # AI chatbot logic
│   ├── weather_service.py     # Weather API integration
│   ├── market_service.py      # Market data service
│   ├── email_utils.py         # Email notification system
│   ├── middleware.py          # Custom middleware
│   ├── signals.py             # Django signal handlers
│   ├── utils.py               # Utility functions
│   └── management/
│       └── commands/          # Custom management commands
│
├── templates/                  # HTML templates
│   ├── base.html              # Base template
│   ├── landing.html           # Landing page
│   ├── auth/                  # Authentication templates
│   │   ├── login.html
│   │   └── signup.html
│   ├── dashboard/             # Dashboard templates
│   │   ├── farmer_dashboard.html
│   │   ├── expert_dashboard.html
│   │   └── admin_dashboard.html
│   ├── chatbot/               # Chatbot interface
│   │   └── chatbot.html       # ChatGPT-like interface
│   ├── ai/                    # Disease detection
│   │   ├── diagnose.html
│   │   └── history.html
│   ├── query/                 # Query management
│   └── library/               # Crop library
│
├── static/                     # Static files (CSS, JS, images)
│
├── models/                     # Pre-trained ML models
│   ├── plant_disease_model.h5
│   ├── disease_detection_model.keras
│   └── class_names.json
│
├── data/                       # Data files
│   └── agri_corpus/            # Chatbot knowledge base
│
├── Planning/                   # Crop planning resources
│   ├── Bajra.txt
│   ├── Maize_Corn.txt
│   ├── Rice_Paddy.txt
│   └── ... (other crops)
│
├── locale/                     # Translation files
│   ├── bn/
│   ├── hi/
│   ├── gu/
│   ├── kn/
│   ├── mr/
│   ├── pa/
│   ├── ta/
│   └── te/
│
├── media/                      # User-uploaded files
│
├── logs/                       # Application logs
│
├── db.sqlite3                  # SQLite database (dev)
├── manage.py                   # Django management script
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

---

## 📦 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8** or higher
- **pip** (Python package manager)
- **git** (for version control)
- **Virtual Environment** (recommended)
- **PostgreSQL** (for production, optional)

---

## 🚀 Installation Guide

### 1. Clone the Repository

```bash
git clone https://github.com/your-organization/FarmerRoute.git
cd FarmerRoute
```

### 2. Create Virtual Environment

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Create Environment Variables

Create a `.env` file in the project root:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Database
DATABASE_URL=sqlite:///db.sqlite3
# For PostgreSQL: postgresql://user:password@localhost:5432/farmerroute

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

# Weather API
WEATHER_API_KEY=your-weather-api-key

# Language
LANGUAGE_CODE=en-us
TIME_ZONE=UTC
```

---

## 🗄️ Database Migration

### Initial Setup

```bash
# Apply migrations
python manage.py migrate

# Create superuser (admin account)
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

### Run Migrations After Model Changes

```bash
# Create migration files
python manage.py makemigrations

# Apply those migrations
python manage.py migrate
```

---

## ▶️ Running the Application

### Development Server

```bash
python manage.py runserver
```

Access the application at: **http://127.0.0.1:8000/**

### Access Admin Panel

Navigate to: **http://127.0.0.1:8000/admin/**
- Use your superuser credentials created during migration

### Load Initial Data (Optional)

```bash
# Load crop planning data
python manage.py loaddata crop_plans
```

---

## 🔗 API Endpoints

### Authentication
- `POST /auth/login/` - User login
- `POST /auth/signup/` - User registration
- `GET /auth/logout/` - User logout
- `POST /auth/password-reset/` - Password reset request

### Dashboard
- `GET /dashboard/` - User dashboard
- `GET /dashboard/farmer/` - Farmer dashboard
- `GET /dashboard/expert/` - Expert dashboard
- `GET /dashboard/admin/` - Admin dashboard

### Disease Detection
- `GET /ai/diagnose/` - Disease detection page
- `POST /ai/diagnose/` - Submit image for diagnosis
- `GET /ai/history/` - View diagnosis history
- `AJAX /ajax/ai/predict/` - Get AI prediction (AJAX)

### Chatbot
- `GET /chatbot/` - Chatbot interface
- `AJAX /ajax/chatbot/message/` - Send chatbot message (AJAX)
- `AJAX /ajax/chatbot/speak/` - Get TTS audio (AJAX)

### Queries & Advice
- `GET /query/` - View all queries
- `POST /query/create/` - Create new query
- `GET /query/<id>/` - View query details
- `POST /query/<id>/answer/` - Submit expert answer

### Weather
- `AJAX /ajax/weather/gps/` - Get weather by GPS coordinates

### Market
- `GET /market/prices/` - View market prices

### Library
- `GET /crop-library/` - Crop library listing
- `GET /crop-library/<crop>/` - Crop details

---

## 🎯 Features in Detail

### 1. Disease Detection System

**How it works:**
1. Farmer uploads a crop/plant image
2. AI model analyzes the image
3. System identifies diseases with confidence score
4. Recommendations provided for treatment
5. History saved for tracking

**Models Used:**
- PlantDoc Object Detection Model
- Pre-trained Keras/TensorFlow model
- ~90%+ accuracy on training dataset

**How to use:**
- Navigate to: `http://127.0.0.1:8000/ai/diagnose/`
- Upload a clear image of the affected crop
- View results and recommendations

---

### 2. Smart Farming Chatbot

**Features:**
- 🎤 **Voice Input** - Click mic button or press `Ctrl+M`
  - Speak naturally
  - Auto-submits after 1.5 seconds of silence
  - Press Enter to submit immediately
  
- 💬 **Text Input** - Type your question
  - Press Enter to send
  
- 🌍 **Multi-language** - Select input language
  - English, Hindi, Telugu, Tamil, Marathi, Bengali, Gujarati, Kannada, Punjabi
  
- 📍 **Location-Aware** - Provides region-specific advice
  
- 🔊 **Text-to-Speech** - Listen to responses

**Access:**
- Navigate to: `http://127.0.0.1:8000/chatbot/`

**Keyboard Shortcuts:**
- `Ctrl+M` - Toggle microphone
- `Enter` - Send message
- `Shift+Enter` - New line in text box

---

### 3. Expert Query System

**Farmer Side:**
1. Navigate to `/query/`
2. Click "Submit Query"
3. Add title, description, and image
4. Submit for expert review
5. Track status: Pending → Answered → Closed

**Expert Side:**
1. Dashboard shows pending queries
2. Review query and crop image
3. Provide detailed advice
4. Farmer receives email notification

---

### 4. Weather Integration

**Features:**
- GPS-based location detection
- Real-time weather data
- Farming recommendations based on weather
- Wind, humidity, temperature monitoring

**How it works:**
- Chatbot requests location permission
- Gets weather data automatically
- Provides weather-based farming advice

---

### 5. Multilingual Support

**Supported Languages:**
- English (en-US)
- हिंदी - Hindi (hi-IN)
- తెలుగు - Telugu (te-IN)
- தமிழ் - Tamil (ta-IN)
- मराठी - Marathi (mr-IN)
- বাংলা - Bengali (bn-IN)
- ગુજરાતી - Gujarati (gu-IN)
- ಕನ್ನಡ - Kannada (kn-IN)
- ਪੰਜਾਬੀ - Punjabi (pa-IN)

**How to add translations:**
1. Mark strings with `_()` function
2. Run: `python manage.py makemessages -l hi`
3. Edit translation files in `locale/`
4. Compile: `python manage.py compilemessages`

---

## 🌍 Multilingual Support

The platform is built with internationalization (i18n) support:

```python
from django.utils.translation import gettext_lazy as _

# In templates
{% trans "Hello" %}

# In Python files
message = _("Welcome to FarmerRoute")
```

---

## 📝 User Roles & Permissions

### Farmer
- View personal dashboard
- Submit queries to experts
- Use disease detection tool
- Access market prices
- Use AI chatbot
- View crop library

### Expert
- View expert dashboard
- Answer farmer queries
- View query statistics
- Provide recommendations

### Administrator
- Full system access
- User management
- Content management
- System configuration
- Analytics and reports

---

## 🐛 Troubleshooting

### Common Issues

**1. Microphone not working**
- Check browser permissions
- Ensure HTTPS (required for Web Speech API in production)
- Check console for errors (F12 → Console)
- Browser must support Web Speech API

**2. Disease detection model not found**
```bash
# Download pre-trained models
python manage.py download_models
```

**3. Email not sending**
- Check `.env` EMAIL_* settings
- For Gmail: Use App Password, not regular password
- Enable "Less secure app access" (if needed)

**4. Database errors**
```bash
# Reset database (development only!)
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

**5. Static files not loading**
```bash
python manage.py collectstatic
```

---

## 🧪 Testing

### Run Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test core

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

### Manual Testing Checklist

- [ ] User registration works
- [ ] Email verification works
- [ ] Disease detection accurate
- [ ] Chatbot responds correctly
- [ ] Weather data displays
- [ ] Query submission works
- [ ] Expert can reply
- [ ] Multilingual display correct
- [ ] Voice input works
- [ ] Mobile responsive

---

## 📱 Mobile Responsiveness

The application is fully responsive:
- Desktop: Full-width layout
- Tablet: Adjusted layout
- Mobile: Optimized single-column layout
- Touch-friendly buttons and inputs

---

## 🔒 Security Features

- Django CSRF protection
- SQL injection prevention
- XSS protection
- Secure password hashing (PBKDF2)
- Email verification for signup
- Session timeout
- CORS configuration
- Rate limiting (can be added)

---

## 🚀 Deployment

### Production Checklist

- [ ] Set `DEBUG = False`
- [ ] Set secure `SECRET_KEY`
- [ ] Configure allowed hosts
- [ ] Use PostgreSQL database
- [ ] Set up email backend (SendGrid, AWS SES, etc.)
- [ ] Enable HTTPS
- [ ] Configure static/media file serving
- [ ] Set up monitoring/logging
- [ ] Use Gunicorn as application server
- [ ] Use Nginx as reverse proxy

### Deployment Steps

```bash
# Collect static files
python manage.py collectstatic

# Install production dependencies
pip install gunicorn whitenoise

# Run with Gunicorn
gunicorn agri_connect.wsgi:application --bind 0.0.0.0:8000
```

---

## 📊 Database Models

### Core Models

1. **User** - Custom user model with farmer/expert/admin roles
2. **Query** - Farmer queries with status tracking
3. **Advice** - Expert responses to queries
4. **AIDisease** - Disease detection results
5. **InventoryItem** - Inventory management
6. **Notification** - User notifications
7. **Rating** - Query/Advice ratings

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/your-feature`
5. Submit pull request

**Guidelines:**
- Follow PEP 8 style guide
- Add docstrings to functions
- Write unit tests
- Update README for new features

---

## 💬 Support & Contact

### Getting Help

- **Email**: support@kisanmitra.co.in
- **Support Phone**: +91-XXXX-XXXX-XXXX (24/7)
- **Documentation**: [Wiki](https://github.com/your-org/FarmerRoute/wiki)
- **Issues**: [GitHub Issues](https://github.com/your-org/FarmerRoute/issues)

### Report Issues

Found a bug? Please report it with:
- Detailed description
- Steps to reproduce
- Expected vs actual behavior
- Browser/device information
- Screenshots if applicable

---

## 📄 License

This project is licensed under the **MIT License** - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Django community for the excellent framework
- TensorFlow/Keras for powerful ML models
- Our agricultural experts for domain knowledge
- All farmers using this platform for their valuable feedback

---

## 📈 Roadmap

### Q2 2024
- [ ] Mobile app (iOS/Android)
- [ ] SMS notifications
- [ ] Offline functionality

### Q3 2024
- [ ] Advanced analytics dashboard
- [ ] Video tutorials
- [ ] Crop yield prediction

### Q4 2024
- [ ] IoT sensor integration
- [ ] Drone image analysis
- [ ] Blockchain for supply chain

---

## 🎓 Training Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [TensorFlow Tutorials](https://www.tensorflow.org/tutorials)
- [Web Speech API Guide](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)

---

## 📞 Quick Start Command Reference

```bash
# Setup
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Database
python manage.py migrate
python manage.py createsuperuser

# Run Development Server
python manage.py runserver

# Access
# - Website: http://127.0.0.1:8000/
# - Admin: http://127.0.0.1:8000/admin/
# - Chatbot: http://127.0.0.1:8000/chatbot/

# Common Commands
python manage.py shell           # Django shell
python manage.py makemigrations  # Create migrations
python manage.py migrate         # Apply migrations
python manage.py test            # Run tests
python manage.py collectstatic   # Collect static files
```

---

## 📝 Changelog

### Version 1.0.0 (Current)
- ✅ AI Disease Detection
- ✅ Smart Farming Chatbot with Voice I/O
- ✅ Expert Query System
- ✅ Weather Integration
- ✅ Market Information
- ✅ Multilingual Support (9 languages)
- ✅ ChatGPT-like UI

### Planned Features
- Mobile app
- Advanced analytics
- IoT integration
- Video tutorials

---

**Made with ❤️ for Indian Farmers**

For updates and news, follow us on social media:
- 🐦 Twitter: [@FarmerRoute](https://twitter.com/farmerroute)
- 📘 Facebook: [FarmerRoute](https://facebook.com/farmerroute)
- 📸 Instagram: [@FarmerRoute](https://instagram.com/farmerroute)

---

*Last Updated: April 9, 2026*
