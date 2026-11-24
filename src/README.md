# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities

## Getting Started

1. Create a virtual environment and install the dependencies:

   ```
   python -m venv .venv
   source .venv/bin/activate
   python -m pip install --pre -r requirements.txt
   ```

2. Set an OpenAI API key in the server terminal. Do not put the key in frontend files or commit it:

   ```
   export OPENAI_API_KEY="your-key"
   ```

3. Run the application from the repository root:

   ```
   uvicorn src.app:app --reload
   ```

4. Open http://localhost:8000 and sign in to use the assistant. The default local account is `admin@mergington.edu` with password `mergington123`.
   API documentation is available at http://localhost:8000/docs.

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |
| POST   | `/chat`                                                            | Send chat messages to the assistant (sign-in required)              |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
