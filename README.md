# JanMitra 🇮🇳

**AI-Powered Government Scheme Discovery Assistant**

JanMitra helps citizens discover relevant Indian government schemes, understand eligibility criteria, and access scheme-related information through an AI-powered assistant.

## Features

- AI-powered scheme assistance using natural language.
- Government scheme discovery and recommendations.
- Profile-based eligibility checking.
- Scheme benefits and document information.
- Save schemes, compare schemes, and application checklists.

## Tech Stack

- **Frontend:** Next.js 16, React 19, TypeScript, Tailwind CSS
- **Backend:** Python, FastAPI, SQLAlchemy
- **Database:** SQLite
- **AI:** Google Gemini API

## Project Setup

**1. Clone the repository**
```bash
git clone https://github.com/Saylee12R/JanMitra.git
cd JanMitra
```

**2. Start the backend**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Configure your `backend/.env` with the required environment variables, including `GEMINI_API_KEY` and `DATABASE_URL`.

**3. Start the frontend** (in a new terminal)
```bash
cd frontend
npm install
npm run dev
```

Configure `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

Open **http://localhost:3000** to use the application.

## API Documentation

When the backend is running: http://127.0.0.1:8000/docs

## Testing

```bash
cd backend
source venv/bin/activate
pytest
```

## Project Goal

To make government welfare schemes easier to discover and understand, helping citizens access information about benefits, eligibility, and application requirements.

**Built with ❤️ for accessible public welfare information.**