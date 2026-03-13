# 🎯 Mock Interview Coach

AI-Powered Technical Interview Practice Platform using AWS Bedrock Nova 2 Lite

![AWS](https://img.shields.io/badge/AWS-Bedrock-FF9900?logo=amazon-aws)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi)
![Vercel](https://img.shields.io/badge/Vercel-000000?logo=vercel)

## 📋 Overview

Mock Interview Coach is an intelligent interview practice platform that helps technical professionals prepare for job interviews. Powered by AWS Bedrock Nova 2 Lite, it provides:

- **AI-Generated Questions**: Dynamic, adaptive questions based on role and experience level
- **Intelligent Evaluation**: Automated response analysis with detailed feedback
- **Structured Feedback**: Strengths, areas for improvement, and recommended study topics
- **Professional Reports**: Downloadable PDF reports with performance analysis
- **Performance Dashboard**: Track progress and identify weak areas

## ✨ Features

### 🤖 AI-Powered Interview System
- AWS Bedrock Nova 2 Lite for question generation and evaluation
- Adaptive difficulty based on performance
- Support for multiple roles: Cloud Engineer, DevOps Engineer, ML Engineer
- Multi-language support (English, Spanish)

### 📊 Detailed Feedback
- Score (0-100) with color-coded indicators
- Strengths identification
- Areas for improvement
- Recommended topics for study
- Technical area breakdown

### 📄 Professional Reports
- Modern PDF reports with glassmorphism design
- Detailed feedback per question
- Performance by technical area
- Learning resource recommendations

### 📈 Performance Dashboard
- Global statistics tracking
- Performance by technical area
- Progress monitoring

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- AWS Account with Bedrock access
- AWS credentials configured

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/mock-interview-coach.git
cd mock-interview-coach
```

2. **Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
```

Edit `.env` with your AWS credentials:
```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
ENABLE_DEV_MODE=false
```

5. **Run the application**
```bash
python app.py
```

6. **Open your browser**
```
http://localhost:8000
```

## 🏗️ Architecture

```
┌─────────────────┐
│   Frontend      │
│   (HTML/JS)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   FastAPI       │
│   Backend       │
└────────┬────────┘
         │
         ├──────────────┐
         ▼              ▼
┌─────────────────┐  ┌──────────────┐
│  AWS Bedrock    │  │  Local       │
│  Nova 2 Lite    │  │  Storage     │
└─────────────────┘  └──────────────┘
```

## 📁 Project Structure

```
mock-interview-coach/
├── api/                      # API modules
│   ├── health.py            # Health check endpoint
│   ├── rate_limiter.py      # Rate limiting
│   └── websocket.py         # WebSocket handler
├── mock_interview_coach/    # Core application
│   ├── data/               # Learning resources
│   ├── difficulty_adjuster/ # Adaptive difficulty
│   ├── evaluator/          # Response evaluation
│   ├── metrics/            # Performance tracking
│   ├── models/             # Data models
│   ├── question_generator/ # Question generation
│   ├── report_generator/   # PDF report generation
│   ├── session_manager/    # Session management
│   └── voice_interface/    # Voice features (Nova Sonic)
├── static/                  # Frontend assets
│   ├── css/                # Stylesheets
│   ├── js/                 # JavaScript modules
│   └── index.html          # Main page
├── tests/                   # Test suite
├── app.py                   # FastAPI application
├── requirements.txt         # Python dependencies
└── vercel.json             # Vercel deployment config
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS access key | Required |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | Required |
| `AWS_REGION` | AWS region | `us-east-1` |
| `ENABLE_DEV_MODE` | Enable development mode | `false` |

### Supported Roles

- **Cloud Engineer**: AWS, Azure, GCP infrastructure
- **DevOps Engineer**: CI/CD, automation, monitoring
- **ML Engineer**: Machine learning, data science

### Experience Levels

- **Junior**: Entry-level questions
- **Mid**: Intermediate-level questions

## 🧪 Testing

Run the test suite:

```bash
pytest
```

Run specific tests:

```bash
pytest tests/test_evaluator.py
pytest tests/test_question_generator.py
```

## 🚀 Deployment

### Vercel Deployment

1. **Install Vercel CLI**
```bash
npm install -g vercel
```

2. **Deploy**
```bash
vercel --prod
```

3. **Configure environment variables** in Vercel dashboard

See [VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md) for detailed instructions.

## 📊 API Endpoints

### Session Management
- `POST /api/session/start` - Start new interview session
- `GET /api/session/{session_id}/question` - Get next question
- `POST /api/session/{session_id}/response` - Submit response
- `POST /api/session/{session_id}/end` - End session

### Performance
- `GET /api/session/{session_id}/performance` - Get performance analysis
- `GET /api/metrics/global` - Get global statistics
- `GET /api/metrics/areas` - Get area-specific metrics

### Reports
- `GET /api/report/{session_id}` - Download PDF report

### Health
- `GET /api/health` - Health check endpoint

## 🎨 UI Features

- Modern glassmorphism design
- AWS/Nova color scheme
- Responsive layout
- Dark theme
- Professional navbar
- Interactive dashboard

## 🔐 Security

- Rate limiting on API endpoints
- Input validation
- AWS credentials via environment variables
- CORS configuration for production

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

For questions or support, please open an issue on GitHub.

## 🙏 Acknowledgments

- AWS Bedrock Nova 2 Lite for AI capabilities
- FastAPI for the backend framework
- ReportLab for PDF generation
- Vercel for hosting

---

**Built with ❤️ using AWS Bedrock Nova 2 Lite**
