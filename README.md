<div align="center">

# NovA AI

### AI-powered technical interview coach built on AWS Generative AI

[![AWS Bedrock](https://img.shields.io/badge/AWS%20Bedrock-Nova%202%20Lite-FF9900?style=for-the-badge&logo=amazon-aws&logoColor=white)](https://aws.amazon.com/bedrock/)
[![Amazon Nova Sonic](https://img.shields.io/badge/Nova%20Sonic-Voice%20AI-FF9900?style=for-the-badge&logo=amazon-aws&logoColor=white)](https://aws.amazon.com/bedrock/)
[![AWS App Runner](https://img.shields.io/badge/AWS%20App%20Runner-Container-FF9900?style=for-the-badge&logo=amazon-aws&logoColor=white)](https://aws.amazon.com/apprunner/)
[![Amazon DynamoDB](https://img.shields.io/badge/DynamoDB-NoSQL-4053D6?style=for-the-badge&logo=amazon-dynamodb&logoColor=white)](https://aws.amazon.com/dynamodb/)
[![Amazon Cognito](https://img.shields.io/badge/Cognito-Google%20OAuth-DD344C?style=for-the-badge&logo=amazon-aws&logoColor=white)](https://aws.amazon.com/cognito/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Python%203.12-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

**NovA AI** is a generative AI interview coach that helps Latin American tech professionals prepare for Cloud Engineering, DevOps, and ML interviews — in English or Spanish, with real-time feedback and personal progress tracking.

[Live Demo](https://9dkx2gnjif.us-east-1.awsapprunner.com) · [Architecture](#architecture) · [Quickstart](#quickstart)

</div>

---

## The Problem

Tech professionals in LATAM face a real gap when preparing for technical interviews at global companies:

- **No contextualized practice** — most resources are in English and oriented toward US/EU markets.
- **No immediate feedback** — practicing alone doesn't tell you which concepts you missed or what to study next.
- **No progress tracking** — there's no way to know if you're actually improving session over session.

NovA AI solves all three using AWS generative AI, fully accessible from the browser with no setup required.

---

## What NovA AI Does

| Feature | Description |
|---------|-------------|
| **Conversational AI interviewer** | Nova greets you by time of day and conducts the interview like a real conversation, not a form |
| **Adaptive questions** | Bedrock Nova 2 Lite generates questions and adjusts difficulty in real time based on your performance |
| **Instant evaluation** | Every answer gets a 0–100 score, strengths, improvement areas, and recommended topics to study |
| **3 technical roles** | Cloud Engineer · DevOps Engineer · ML Engineer at Junior and Mid-level |
| **Fully bilingual** | English and Spanish with fully localized prompts, feedback, and UI |
| **Bidirectional voice** | Amazon Nova Sonic processes audio in real time over WebSocket — speak and listen without typing |
| **Personal dashboard** | Session history, average score, score progression chart, and per-area breakdown — persisted per user via DynamoDB |
| **PDF report** | A downloadable PDF with the full interview breakdown is generated at the end of each session |
| **Google Sign-In** | Auth via Cognito PKCE + Google OAuth — entirely optional, demo mode works without an account |

---

## Architecture

```
Browser (index.html · vanilla JS)
  ├── Landing      →  Google Sign-In (Cognito PKCE)  /  Try Demo
  ├── Setup        →  Role · Level · Language
  ├── Interview    →  Chat + Voice (WebSocket)
  ├── Results      →  Score ring · Area bars · PDF download
  └── Dashboard    →  History table · Sparkline · Area breakdown
        │
        │  HTTP + WebSocket  (persistent process — App Runner)
        ▼
FastAPI  (app.py)
  ├── /auth/*              →  Cognito JWT validation · PKCE exchange · logout
  ├── /api/session/*       →  Start · Next question · Submit response · End
  ├── /api/user/*/sessions →  Per-user DynamoDB session history
  ├── /api/report/{id}     →  PDF download
  └── /ws/{id}             →  Nova Sonic bidirectional audio stream
        │
        ▼
mock_interview_coach/
  ├── question_generator/   Bedrock Nova 2 Lite — adaptive question generation
  ├── evaluator/            0–100 scoring · structured feedback
  ├── difficulty_adjuster/  Dynamic difficulty per session
  ├── report_generator/     PDF export via ReportLab
  ├── voice_interface/      Nova Sonic client · WebSocket handler · audio utils
  └── auth/                 Cognito JWT · PKCE · DynamoDB helpers
        │
        ▼
AWS
  ├── Bedrock Nova 2 Lite  →  Question generation + answer evaluation
  ├── Bedrock Nova Sonic   →  Real-time bidirectional voice streaming
  ├── Cognito Hosted UI    →  Google OAuth (optional)
  ├── DynamoDB             →  nova_users + nova_sessions (silent no-ops when unconfigured)
  └── App Runner           →  HTTPS · auto-scaling · persistent WebSocket
```

> **Why App Runner and not Lambda:** WebSockets require a persistent process. Lambda has a 29-second max invocation and no support for long-lived bidirectional connections. App Runner scales to zero when idle and serves WebSocket natively — zero ops overhead.

---

## Quickstart

```bash
# 1. Clone and install
git clone https://github.com/AndresRJ18/nova-ai-interview.git
cd nova-ai-interview
python -m venv .venv && source .venv/Scripts/activate   # Windows
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env: set AWS_REGION + AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY

# 3. Run (demo mode — no AWS credentials required)
ENABLE_DEV_MODE=true python app.py
# Open http://localhost:8000
```

To run with real AWS (Bedrock-generated questions):

```bash
# Without ENABLE_DEV_MODE — uses your AWS credentials
python app.py
```

---

## AWS Services & Why Each One

| Service | Role in the project | Why this and not something else |
|---------|--------------------|---------------------------------|
| **Bedrock Nova 2 Lite** | Question generation + answer scoring | Low latency, competitive token cost, native support in us-east-1 |
| **Bedrock Nova Sonic** | Real-time bidirectional voice | The only AWS multimodal model with bidirectional audio streaming over WebSocket |
| **App Runner** | FastAPI container hosting | Native WebSocket support, scales to zero, automatic HTTPS, no infra to manage |
| **Cognito Hosted UI** | Google OAuth + PKCE | Removes secret handling from the frontend; the hosted UI handles the OAuth redirect directly |
| **DynamoDB** | User profiles + session history | PAY_PER_REQUEST, serverless, no capacity planning — perfect for variable hackathon traffic |
| **ECR** | Container registry | Native integration with App Runner for auto-deploy on every image push |

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AWS_REGION` | Yes | e.g. `us-east-1` |
| `NOVA_SONIC_MODEL_ID` | Yes | `amazon.nova-sonic-v1:0` |
| `COGNITO_USER_POOL_ID` | No | Enables Google login |
| `COGNITO_CLIENT_ID` | No | Cognito app client |
| `COGNITO_DOMAIN` | No | Hosted UI domain |
| `COGNITO_REDIRECT_URI` | No | OAuth callback URL |
| `DYNAMO_USERS_TABLE` | No | Default: `nova_users` |
| `DYNAMO_SESSIONS_TABLE` | No | Default: `nova_sessions` |
| `ENABLE_DEV_MODE` | No | `true` for local dev without AWS credentials |

On App Runner, credentials are injected via IAM Role — no `AWS_ACCESS_KEY_ID` needed in production.

---

## Deployment on App Runner

```bash
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
REGION=us-east-1

# Create registry and push image
aws ecr create-repository --repository-name nova-interview --region $REGION
aws ecr get-login-password --region $REGION | \
  docker login --username AWS --password-stdin $ACCOUNT.dkr.ecr.$REGION.amazonaws.com

docker build -t nova-interview .
docker tag nova-interview:latest $ACCOUNT.dkr.ecr.$REGION.amazonaws.com/nova-interview:latest
docker push $ACCOUNT.dkr.ecr.$REGION.amazonaws.com/nova-interview:latest
```

Required IAM Role (`nova-apprunner-role`):
- `bedrock:InvokeModel`, `bedrock:InvokeModelWithResponseStream` on `*`
- `dynamodb:PutItem`, `dynamodb:GetItem`, `dynamodb:UpdateItem`, `dynamodb:Query` on both tables

---

## Auth Flow

```
1. Frontend calls GET /auth/config     →  receives client_id, domain, redirect_uri
2. PKCE: browser generates code_verifier + code_challenge (stored in sessionStorage)
3. Redirect to Cognito Hosted UI       →  Google login  →  back to app with ?code=
4. Frontend POST /auth/callback        →  {code, redirect_uri, code_verifier}
5. Backend exchanges code for tokens, validates RS256 JWT (JWKS cached), upserts user in DynamoDB
6. Token stored in localStorage        →  sent as Authorization: Bearer <token> on each request
```

When Cognito env vars are absent: the Google button stays disabled and demo mode works normally. No errors, no broken screens.

---

## Author

**Andrés Rodas** — Computer Engineering, UPCH · Cloud Computing & AI

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Andrés_Rodas-0A66C2?style=flat-square&logo=linkedin)](https://www.linkedin.com/in/andres-rodas-802309272)
[![GitHub](https://img.shields.io/badge/GitHub-@AndresRJ18-181717?style=flat-square&logo=github)](https://github.com/AndresRJ18)
[![Email](https://img.shields.io/badge/Email-andrescloud18sj@gmail.com-D14836?style=flat-square&logo=gmail)](mailto:andrescloud18sj@gmail.com)

---

<div align="center">
Made with love by Andres  · Lima, Peru · 2026
</div>
