# JanMitra 🇮🇳
### AI-Powered Government Scheme Discovery Assistant

JanMitra is an AI-powered platform that helps citizens discover relevant Indian government schemes, understand eligibility criteria, and access scheme-related information through a conversational assistant.

## 🌐 Live Demo

- **Live Website:** [JanMitra – Visit Website](https://jan-mitra-umber.vercel.app/)
- **Project Demo Video:** [Watch JanMitra Demo](https://drive.google.com/file/d/1mo3AzGFegzeiCP4sg3B7I-OWJK11naoJ/view?usp=sharing)

## ✨ Features

- **AI-Powered Assistant:** Ask questions about government schemes in natural language.
- **Scheme Discovery:** Explore government schemes in one place.
- **Eligibility Checking:** Check potential eligibility based on user profile information.
- **Personalized Recommendations:** Discover schemes relevant to your profile.
- **Scheme Details:** View benefits, eligibility criteria, required documents, and official links.
- **Save Schemes:** Keep track of schemes you are interested in.
- **Scheme Comparison:** Compare different schemes.
- **Application Checklist:** Organize documents and application-related tasks.
- **User Dashboard:** Access scheme-related information in one place.

## 🛠️ Tech Stack

**Frontend**
- Next.js 16
- React 19
- TypeScript
- Tailwind CSS v4

**Backend**
- Python
- FastAPI
- SQLAlchemy

**Database**
- SQLite

**AI**
- Google Gemini API

## 📁 Project Structure

```text
janmitra/
├── backend/
│   ├── app/
│   │   ├── ai/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── main.py
│   │   ├── config.py
│   │   └── database.py
│   └── tests/
│
├── frontend/
│   └── src/
│       ├── app/
│       └── components/
│
├── data/
│   ├── schemes/
│   └── seed/
│
└── README.md
```

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Saylee12R/JanMitra.git
cd JanMitra
```

### 2. Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file inside the `backend` directory:

```env
GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=sqlite:///./janmitra.db
```

Start the backend:

```bash
uvicorn app.main:app --reload
```

Backend runs at `http://127.0.0.1:8000`.

API documentation: `http://127.0.0.1:8000/docs`

### 3. Frontend Setup

Open a new terminal:

```bash
cd frontend
npm install
```

Create a `.env.local` file inside the `frontend` directory:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

Start the frontend:

```bash
npm run dev
```

Open `http://localhost:3000` in your browser.

## 🧪 Running Tests

```bash
cd backend
source venv/bin/activate
pytest
```

## ☁️ Deployment

- **Frontend:** Deployed on Vercel.
- **Backend:** Deployed on Render.

The deployed frontend communicates with the backend through the configured API URL.


## 🎯 Project Goal

JanMitra aims to bridge the information gap between citizens and government welfare schemes by making scheme discovery, eligibility understanding, and application preparation more accessible.

**Making government schemes easier to discover, understand, and access.**

---

*Built with ❤️ for accessible public welfare information.*
