# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- Persistent SQLite storage for activities, students, and registrations

## Getting Started

1. Install the dependencies:

   ```
   pip install -r ../requirements.txt
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |

## Data Model

The application uses SQLite with a simple relational data model:

1. **Activities** - Uses activity name as unique identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Email

3. **Registrations** - Links students to activities:
   - Activity reference
   - Student reference
   - Registration timestamp

Data is stored in `src/school.db` and survives server restarts.

## Database setup and migration

- On app startup, tables are created automatically if they do not exist.
- On first run (empty database), default activities and participant registrations are seeded.
- Existing API behavior remains compatible for:
  - `GET /activities`
  - `POST /activities/{activity_name}/signup?email=...`
  - `DELETE /activities/{activity_name}/unregister?email=...`
