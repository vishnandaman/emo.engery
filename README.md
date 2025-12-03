# Content Management API

A production-ready RESTful API service built with FastAPI that allows users to upload text content and automatically processes it to generate summaries and sentiment analysis. The application uses MySQL database and implements intelligent fallback mechanisms for reliable text analysis.

## 🚀 Features

- **User Authentication**: Secure JWT-based authentication system with signup and login
- **Content Management**: Full CRUD operations for user content
- **Text Analysis**: Automatic text summarization and sentiment detection
- **Intelligent Fallback System**: Multiple fallback mechanisms ensure reliable results
- **Async Processing**: Non-blocking background processing for better performance
- **MySQL Database**: Production-ready database with phpMyAdmin support
- **Docker Support**: Containerized application for easy deployment
- **Comprehensive Testing**: Unit tests with pytest

## 📋 Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: MySQL with SQLAlchemy ORM
- **Authentication**: JWT (JSON Web Tokens) with bcrypt password hashing
- **Text Analysis**: HuggingFace API (primary) with intelligent fallback system
- **Containerization**: Docker & Docker Compose
- **Testing**: pytest with test coverage

## 🎯 Why HuggingFace Instead of OpenAI?

### Primary Choice: HuggingFace API

**Reason for Selection:**
- **Free Access**: HuggingFace offers free API access without requiring a credit card
- **No Payment Barrier**: OpenAI requires a credit card for free trial, which wasn't available
- **Open Source Models**: Access to a wide range of open-source models
- **Suitable for Learning**: Perfect for academic and learning projects

### Fallback System Implementation

Despite multiple attempts to integrate HuggingFace API, the service sometimes returns 404/410 errors due to:
- API endpoint deprecations
- Model availability issues
- Rate limiting on free tier

**Solution Implemented:**
1. **Primary**: Attempts HuggingFace API for both summarization and sentiment
2. **Fallback Summary Generator**: If API fails, extracts the first meaningful sentence from the text
3. **Keyword-Based Sentiment**: Uses keyword matching to detect positive/negative sentiment when API is unavailable

This ensures the application **always provides results** even when external APIs are unavailable.

## 🏗️ Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── database.py             # MySQL database configuration
│   ├── models.py               # SQLAlchemy database models
│   ├── schemas.py              # Pydantic schemas for validation
│   ├── auth.py                 # JWT authentication utilities
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py             # Authentication endpoints
│   │   └── contents.py         # Content management endpoints
│   └── services/
│       ├── __init__.py
│       └── ai_service.py       # Text analysis service with fallbacks
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── test_auth.py            # Authentication tests
│   └── test_contents.py        # Content management tests
├── Dockerfile                  # Docker image configuration
├── docker-compose.yml          # Docker Compose with MySQL
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── MYSQL_SETUP.md             # MySQL setup guide
├── QUICK_START.md             # Quick setup guide
└── README.md                  # This file
```

## 🛠️ Setup Instructions

### Prerequisites

- Python 3.11 or higher
- MySQL Server (or XAMPP/WAMP with phpMyAdmin)
- MySQL root access (usually no password for XAMPP/WAMP)
- HuggingFace API key (FREE - get at https://huggingface.co/settings/tokens)
- OpenAI API key (optional, only if you want paid fallback)

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd "Emo Energy"
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- FastAPI and Uvicorn
- SQLAlchemy with MySQL driver (pymysql)
- JWT authentication libraries
- HTTP client for API calls
- Testing frameworks

### Step 4: Set Up MySQL Database

#### Option A: Using phpMyAdmin (Recommended)

1. **Create Database**:
   - Open phpMyAdmin (`http://localhost/phpmyadmin`)
   - Click "New" to create database
   - Database name: `emo_energy`
   - Collation: `utf8mb4_unicode_ci`
   - Click "Create"

2. **Note MySQL Credentials**:
   - Username: `root` (default)
   - Password: Usually empty for XAMPP/WAMP
   - Host: `localhost`
   - Port: `3306`

#### Option B: Using Docker Compose

```bash
docker-compose up -d
```

This automatically creates the MySQL database and starts the application.

### Step 5: Configure Environment Variables

1. **Copy environment template**:
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file** with your configuration:

   ```env
   # Database Configuration
   # Format: mysql+pymysql://user:password@host:port/database
   # For XAMPP/WAMP (usually no password):
   DATABASE_URL=mysql+pymysql://root@localhost:3306/emo_energy
   
   # If MySQL has a password:
   # DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/emo_energy

   # JWT Authentication
   SECRET_KEY=your-secret-key-minimum-32-characters-long-change-this
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30

   # API Keys
   HUGGINGFACE_API_KEY=your-huggingface-api-key-here
   OPENAI_API_KEY=your-openai-api-key-here  # Optional
   ```

3. **Get HuggingFace API Key** (FREE):
   - Go to https://huggingface.co/settings/tokens
   - Click "New token"
   - Select "Read" permission
   - Copy the token and paste in `.env`

### Step 6: Test Database Connection

Run the test script to verify MySQL connection:

```bash
python test_mysql_connection.py
```

This will test common MySQL configurations and show you the correct connection string.

### Step 7: Run the Application

```bash
uvicorn app.main:app --reload
```

The application will:
- Connect to MySQL database
- Automatically create tables (`users` and `contents`)
- Start the API server on `http://localhost:8000`

### Step 8: Access the API

- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc (ReDoc)
- **Health Check**: http://localhost:8000/health

## 📖 API Usage

### 1. Register a New User

```bash
POST /api/auth/signup
Content-Type: application/json

{
  "username": "testuser",
  "email": "test@example.com",
  "password": "securepassword123"
}
```

### 2. Login

```bash
POST /api/auth/login
Content-Type: application/json

{
  "username": "testuser",
  "password": "securepassword123"
}
```

Response includes `access_token` - use this for authenticated requests.

### 3. Create Content (with Analysis)

```bash
POST /api/contents
Authorization: Bearer <your_access_token>
Content-Type: application/json

{
  "text": "I absolutely love this new product! It's amazing and works perfectly."
}
```

The API will:
1. Save content immediately
2. Process text in background (summary + sentiment)
3. Update content with results when ready

### 4. Get Content

```bash
GET /api/contents/{content_id}
Authorization: Bearer <your_access_token>
```

Response includes:
- Original text
- Generated summary (or fallback summary)
- Detected sentiment (Positive/Negative/Neutral)

## 🔄 How the Fallback System Works

### Text Analysis Flow

```
1. Attempt HuggingFace API
   ├─ Success → Return AI-generated summary & sentiment
   └─ Failure (404/410/timeout)
       ├─ Fallback Summary: Extract first meaningful sentence
       └─ Keyword Sentiment: Match positive/negative keywords
```

### Fallback Summary Generator

- Extracts the first sentence if substantial (>15 characters)
- Otherwise takes first 30 words
- Ensures users always get a summary

### Keyword-Based Sentiment

- **Positive Keywords**: love, amazing, great, excellent, wonderful, etc.
- **Negative Keywords**: hate, terrible, awful, bad, worst, etc.
- Uses word boundary matching for accuracy
- Returns Neutral if no clear sentiment detected

## 🗄️ Database Schema

### Users Table
- `id`: Primary key
- `username`: Unique username
- `email`: Unique email address
- `hashed_password`: Bcrypt hashed password
- `created_at`: Timestamp

### Contents Table
- `id`: Primary key
- `user_id`: Foreign key to users
- `text`: Original text content
- `summary`: Generated summary (or fallback)
- `sentiment`: Positive/Negative/Neutral
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

## 🐳 Docker Deployment

### Using Docker Compose

```bash
# Start all services (MySQL + API)
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### Manual Docker Build

```bash
# Build image
docker build -t content-api .

# Run container
docker run -p 8000:8000 --env-file .env content-api
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py
```

## 📚 Additional Documentation

- **MYSQL_SETUP.md**: Detailed MySQL setup guide
- **QUICK_START.md**: Quick setup instructions
- **SWAGGER_AUTH_GUIDE.md**: How to use Swagger UI with authentication
- **TESTING_GUIDE.md**: Comprehensive testing guide

## 🔒 Security Features

- **Password Hashing**: Bcrypt with SHA256 pre-hashing for long passwords
- **JWT Tokens**: Secure token-based authentication
- **Environment Variables**: All secrets stored in `.env` (never committed)
- **Input Validation**: Pydantic schemas validate all inputs
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection

## 🚨 Troubleshooting

### Database Connection Issues

**Error**: "Access denied for user 'root'@'localhost'"
- Check MySQL password in `.env`
- Try without password: `mysql+pymysql://root@localhost:3306/emo_energy`

**Error**: "Can't connect to MySQL server"
- Ensure MySQL service is running
- Check if MySQL is on port 3306
- Verify database `emo_energy` exists

### API Issues

**HuggingFace API returns 404/410**
- This is expected - the fallback system handles it
- Summary and sentiment will still be generated using fallbacks

**No summary generated**
- Check HuggingFace API key in `.env`
- Fallback should still work even without API key

## 📝 Notes for Evaluators

### Design Decisions

1. **HuggingFace Over OpenAI**: Chosen for free access without credit card requirement
2. **Fallback System**: Implemented to ensure reliability when APIs are unavailable
3. **MySQL Over SQLite**: Migrated to MySQL for production-ready web application
4. **Background Processing**: Async processing ensures fast API responses

### Known Limitations

- HuggingFace API sometimes unavailable (handled by fallbacks)
- Fallback summary is simpler than AI-generated summaries
- Keyword sentiment is less accurate than ML-based sentiment

### Future Improvements

- Implement caching for API responses
- Add more sophisticated fallback algorithms
- Support multiple sentiment analysis models
- Add content categorization features

## 📄 License

This project is created for educational and evaluation purposes.

## 👤 Author

Created as part of a content management API project demonstrating:
- RESTful API design
- Database integration
- Authentication and authorization
- Text processing and analysis
- Error handling and fallback mechanisms

---

**Status**: ✅ Production Ready
**Database**: MySQL (phpMyAdmin compatible)
**API**: FastAPI with Swagger documentation
**Testing**: Comprehensive test suite included
