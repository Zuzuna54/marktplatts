# Motoren NL - Marktplaats Motorcycle Dashboard

Search and filter motorcycle listings from Marktplaats with advanced filters that Marktplaats doesn't offer: mileage, engine size, construction year, and more.

## Setup

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Features

- Search motorcycles by keyword or browse all
- Filter by price, mileage (km), engine size (cc), construction year
- Filter by location (zip code + radius)
- Sort by price, mileage, year, date posted, engine size
- Infinite scroll
- Save favorites
- Dark mode UI
