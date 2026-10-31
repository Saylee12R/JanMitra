# JanMitra 🇮🇳

## Your Personal Government Services Assistant

JanMitra is a personalized government services assistant designed to help citizens discover government schemes that may be relevant to their personal circumstances.

Instead of requiring users to search through large numbers of government websites and scheme documents, JanMitra collects basic information such as age, gender, state, occupation, income, and category, and uses a rule-based eligibility engine to identify potentially relevant schemes.

> **Important:** JanMitra provides potentially relevant schemes based on available information. Final eligibility must always be confirmed through the respective official government authority or portal.

---

# 🚀 Current Features

The current version of JanMitra supports:

- Personalized user onboarding
- User profile collection
- Government scheme database
- PostgreSQL database
- Rule-based eligibility matching
- Personalized scheme recommendations
- Scheme categories
- Scheme benefits
- Required documents
- Application process
- Official application links
- FastAPI backend
- Next.js frontend
- REST APIs
- Interactive API documentation

---

# 🏗️ Project Architecture

```text
                         JANMITRA
                            │
                            ↓
                     Next.js Frontend
                            │
                            ↓
                       FastAPI API
                            │
             ┌──────────────┴──────────────┐
             ↓                             ↓
       PostgreSQL                   Eligibility Engine
             │                             │
             ↓                             ↓
      Government Schemes             User Information
             │                             │
             └──────────────┬──────────────┘
                            ↓
                    Recommended Schemes
```

---

# 🛠️ Tech Stack

## Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS

## Backend

- Python
- FastAPI
- SQLAlchemy
- Pydantic

## Database

- PostgreSQL

## Development

- Git
- GitHub
- Uvicorn

## Future AI Layer

The AI layer will be integrated after finalizing the AI services available through the hackathon/Forge environment.

Planned AI capabilities include:

- Natural-language profile understanding
- Scheme explanation
- Government scheme Q&A
- Retrieval-Augmented Generation (RAG)
- AI-powered government services assistant

---

# 📁 Project Structure

```text
janmitra/
│
├── frontend/
│   ├── src/
│   │   └── app/
│   │       ├── onboarding/
│   │       │   └── page.tsx
│   │       │
│   │       ├── recommendations/
│   │       │   └── page.tsx
│   │       │
│   │       ├── page.tsx
│   │       ├── layout.tsx
│   │       └── globals.css
│   │
│   ├── .env.local
│   ├── package.json
│   └── ...
│
├── backend/
│   ├── app/
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── scheme.py
│   │   │   └── user.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── scheme.py
│   │   │   └── recommendation.py
│   │   │
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── health.py
│   │   │   ├── schemes.py
│   │   │   └── recommendation.py
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── eligibility.py
│   │   │
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── main.py
│   │   └── seed.py
│   │
│   ├── .env
│   ├── .env.example
│   └── requirements.txt
│
├── data/
├── docs/
├── .gitignore
├── README.md
└── docker-compose.yml
```

---

# ⚙️ Prerequisites

Make sure the following are installed:

- Node.js 20+
- npm
- Python 3.11+
- PostgreSQL
- Git

Check your installations:

```bash
node --version
npm --version
python3 --version
psql --version
git --version
```

---

# 📥 Installation

## 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

Go inside the project:

```bash
cd janmitra
```

---

# 🐍 Backend Setup

Go to the backend:

```bash
cd backend
```

Create a Python virtual environment:

```bash
python3 -m venv venv
```

Activate it:

### macOS / Linux

```bash
source venv/bin/activate
```

### Windows

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# 🗄️ PostgreSQL Setup

Open PostgreSQL:

```bash
psql postgres
```

Create the database:

```sql
CREATE DATABASE janmitra;
```

Connect to it:

```sql
\c janmitra
```

Exit:

```sql
\q
```

---

# 🔐 Backend Environment Variables

Create:

```text
backend/.env
```

Add:

```env
APP_NAME=JanMitra API
ENVIRONMENT=development
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/janmitra
```

Replace `YOUR_PASSWORD` with your PostgreSQL password.

Example:

```env
APP_NAME=JanMitra API
ENVIRONMENT=development
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/janmitra
```

Never commit `.env` to GitHub.

---

# 🌱 Seed the Database

Start the backend environment:

```bash
source venv/bin/activate
```

Run:

```bash
python -m app.seed
```

This inserts the initial demonstration schemes into PostgreSQL.

---

# ▶️ Start the Backend

From:

```text
janmitra/backend
```

run:

```bash
uvicorn app.main:app --reload
```

Backend:

```text
http://localhost:8000
```

API documentation:

```text
http://localhost:8000/docs
```

---

# 💻 Frontend Setup

Open another terminal.

Go to:

```bash
cd janmitra/frontend
```

Install dependencies:

```bash
npm install
```

Create:

```text
frontend/.env.local
```

Add:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Start the frontend:

```bash
npm run dev
```

Open:

```text
http://localhost:3000
```

---

# 🔄 Application Flow

The current JanMitra flow is:

```text
                    Homepage
                       │
                       ↓
                  Get Started
                       │
                       ↓
                  Onboarding
                       │
                       ↓
             User enters information
                       │
                       ↓
              POST /api/recommend
                       │
                       ↓
                FastAPI Backend
                       │
                       ↓
                 PostgreSQL
                       │
                       ↓
              Eligibility Engine
                       │
                       ↓
              Matching Schemes
                       │
                       ↓
                Recommendations
```

---

# 👤 User Information

The current onboarding collects:

| Field | Description |
|---|---|
| Age | User's age |
| Gender | Male/Female/Other |
| State | User's state |
| Occupation | Student/Farmer/Employee/etc. |
| Income | Annual income |
| Category | General/OBC/SC/ST |

This information is used by the eligibility engine.

---

# 🧠 Eligibility Engine

The current recommendation system is rule-based.

A scheme can define:

```text
Minimum age
Maximum age
Income limit
Gender
Occupation
State
```

The engine checks the user's profile against these conditions.

For example:

```text
User:

Age       = 20
Gender    = Female
State     = Maharashtra
Occupation = Student
Income    = ₹1,00,000
```

A scheme requiring:

```text
Age       = 16–30
Occupation = Student
Income    ≤ ₹2,50,000
```

will be considered potentially relevant.

The eligibility engine is intentionally separate from the AI layer so that AI does not independently decide official eligibility.

---

# 🔌 API Endpoints

## Health Check

```http
GET /api/health
```

Example:

```text
http://localhost:8000/api/health
```

---

## Get All Schemes

```http
GET /api/schemes
```

Returns active government schemes stored in the database.

---

## Get Single Scheme

```http
GET /api/schemes/{scheme_id}
```

Example:

```http
GET /api/schemes/1
```

---

## Get Recommendations

```http
POST /api/recommend
```

Example request:

```json
{
  "age": 20,
  "gender": "Female",
  "state": "Maharashtra",
  "occupation": "Student",
  "income": 100000,
  "category": "General"
}
```

Example response structure:

```json
{
  "count": 2,
  "schemes": [
    {
      "id": 3,
      "name": "Post Matric Scholarship",
      "category": "Education"
    },
    {
      "id": 4,
      "name": "Student Education Support",
      "category": "Education"
    }
  ]
}
```

---

# 🗃️ Database Structure

## `users`

Stores user profile information.

```text
id
age
gender
state
occupation
income
category
```

## `schemes`

Stores government scheme information.

```text
id
name
category
description
min_age
max_age
income_limit
gender
occupation
state
benefits
documents
application_process
application_url
active
```

---

# 🧪 Testing

First start the backend:

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

Then open:

```text
http://localhost:8000/docs
```

Test:

```text
GET /api/schemes
```

and:

```text
POST /api/recommend
```

Then start the frontend:

```bash
cd frontend
npm run dev
```

Open:

```text
http://localhost:3000
```

Test the complete flow:

```text
Homepage
→ Get Started
→ Onboarding
→ Enter profile
→ Find My Schemes
→ Recommendations
```

---

# 🔒 Important Disclaimer

JanMitra is an assistance and discovery platform.

The recommendations generated by JanMitra should not be treated as a legal or official confirmation of eligibility.

Users should verify:

- Eligibility
- Required documents
- Application deadlines
- Benefits
- Application procedure

through the relevant official government authority before applying.

---

# 🛣️ Roadmap

## Phase 1 — Current MVP

- [x] Next.js frontend
- [x] FastAPI backend
- [x] PostgreSQL database
- [x] Scheme database
- [x] User onboarding
- [x] Eligibility engine
- [x] Recommendation API
- [x] Recommendation page

## Phase 2 — Scheme Management

- [ ] Scheme details page
- [ ] Save scheme
- [ ] Saved schemes page
- [ ] Required document checklist
- [ ] Application progress tracking
- [ ] User profile management

## Phase 3 — AI

- [ ] Forge AI integration
- [ ] Natural-language profile extraction
- [ ] AI scheme explanations
- [ ] Government services chatbot
- [ ] RAG pipeline
- [ ] Source-grounded responses

## Phase 4 — Government Data

- [ ] Integrate official scheme datasets
- [ ] myScheme integration where supported
- [ ] data.gov.in integration where applicable
- [ ] API Setu integration where applicable
- [ ] Scheme data validation
- [ ] Source URLs
- [ ] Last verified dates

## Phase 5 — Production

- [ ] Authentication
- [ ] Secure API keys
- [ ] Rate limiting
- [ ] Input validation
- [ ] Production PostgreSQL
- [ ] Backend deployment
- [ ] Frontend deployment
- [ ] HTTPS
- [ ] Monitoring

---

# 🤖 Planned AI Architecture

The planned architecture separates deterministic eligibility logic from AI:

```text
                  User
                    │
                    ↓
             AI Understanding
                    │
                    ↓
            Structured Profile
                    │
                    ↓
          Eligibility Rule Engine
                    │
                    ↓
          Potentially Matching
                Schemes
                    │
                    ↓
             Official Sources
                    │
                    ↓
              AI Explanation
                    │
                    ↓
              User-Friendly
                 Answer
```

AI will be used primarily for understanding and explanation, while structured rules and official data will remain the foundation for scheme matching.

---

# 🌐 Future Production Architecture

```text
                    ┌──────────────┐
                    │    User      │
                    └──────┬───────┘
                           │
                           ↓
                  ┌────────────────┐
                  │   Next.js UI   │
                  └───────┬────────┘
                          │
                          ↓
                  ┌────────────────┐
                  │  FastAPI API   │
                  └───────┬────────┘
                          │
          ┌───────────────┼────────────────┐
          ↓               ↓                ↓
   ┌────────────┐  ┌──────────────┐  ┌─────────────┐
   │ PostgreSQL │  │ Eligibility  │  │   AI/RAG    │
   │            │  │   Engine     │  │   Service   │
   └────────────┘  └──────────────┘  └─────────────┘
          │               │                │
          └───────────────┼────────────────┘
                          ↓
                  ┌────────────────┐
                  │ Government     │
                  │ Scheme Data    │
                  └────────────────┘
```

---

# 👨‍💻 Development

Create a new feature branch:

```bash
git checkout -b feature/your-feature
```

After making changes:

```bash
git add .
git commit -m "describe your changes"
git push origin feature/your-feature
```

Recommended branches:

```text
main
develop
feature/frontend
feature/backend
feature/ai
feature/schemes
```

---

# 📌 Project Status

**Current status: MVP development**

The current implementation focuses on the core personalized scheme discovery pipeline:

```text
PostgreSQL
    ↓
Scheme Data
    ↓
Eligibility Engine
    ↓
FastAPI Recommendation API
    ↓
Next.js Onboarding
    ↓
Personalized Recommendations
```

The next major development stage is:

```text
Scheme Details
      ↓
Save Scheme
      ↓
Application Checklist
      ↓
AI Integration
      ↓
Government Data Integration
      ↓
Deployment
```

---

# 🇮🇳 Vision

JanMitra aims to make government services easier to discover and understand by turning complex scheme information into a simple, personalized experience.

**One profile.  
Relevant schemes.  
Simple explanations.  
Clear next steps.**

---

## License

This project is currently being developed as a hackathon/project prototype.
