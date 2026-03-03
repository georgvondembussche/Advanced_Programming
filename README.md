# Advanced_Programming

# Gym Progress Tracker 

A browser-based gym tracking app built with **Python + NiceGUI**.  
Users can log workouts (sets, reps and weight), track progress over time and visualize which muscle groups they trained in the current week using a **muscle heatmap**.

---

## Problem
Many gymrats have problems with tracking their progress in numbers and muscles. Everyone has taken progress pictures before but only a few actually write down how much they lift in numbers (sets, reps and weight). With these methods many people dont use their full potential and lose time and resources during the process.

---

## Goal
Build a simple but powerful web app that enables users to:
- log workouts quickly,
- track progress with statistics and charts,
- understand training balance (which muscles are trained / neglected),
- make better decisions about increasing or decreasing weight and volume.

---

## Key Features (Minimum Viable Product)
- **User accounts** (register/login)
- **Workout logging**: date, exercises, sets (weight, reps)
- **Exercise library**: create/edit exercises
- **Progress tracking**:
  - per exercise: best set, max weight 1RM, volume trend
  - per week: total sessions (also rest and cheat days)
- **Muscle heatmap** (weekly):
  - body figure highlights muscle groups trained this week

---

## Optional / Stretch Goals
- Personal records page (PRs)
- Admin role for managing global exercise library

---

## Target Users
- beginners who want structure without spreadsheets
- intermediate lifters focused on progressive overload
- anyone who wants objective tracking beyond photos

---

## Tech Stack
- **Frontend (Presentation Layer):** NiceGUI (browser UI components rendered via Vue/Quasar engine)
- **Backend (Application Logic):** Python (OOP-based services/controllers)
- **Persistence Layer:** SQLite + ORM (SQLAlchemy)
- **Auth:** session-based authentication (implementation TBD)
- **Charts:** NiceGUI built-in / Chart.js integration (optional)

---

## Architecture Overview
The app follows a 3-layer architecture:

1. **Presentation Layer (Client View)**
   - NiceGUI components: pages, forms, tables, dialogs, charts

2. **Application Logic (Server-side Frontend)**

3. **Persistence Layer**

---

## Data Model (Initial)
Entities (tables):
- **User**
- **WorkoutSession** (date, user_id)
- **Exercise**
- **SetEntry** (session_id, exercise_id, reps, weight)
- **MuscleGroup**

---

## User Stories
### Authentication
- As a user, I want to register and log in so that my workouts are private.
- As a user, I want to log out securely.

### Workout Logging
- As a user, I want to create a workout session with a date.
- As a user, I want to add exercises and multiple sets (weight + reps).
- As a user, I want to edit or delete sets if I made a mistake.

### Progress & Insights
- As a user, I want to see my progress for an exercise over time (best set / max weight 1RM / volume).
- As a user, I want to see weekly training volume and frequency.
- As a user, I want a muscle heatmap that shows which muscles I trained this week.
