# services/workout_service.py
from __future__ import annotations

from datetime import date
from typing import Any

from db.session import get_session
from models.muscle_group import MuscleGroup
from models.session_muscle import SessionMuscle
from models.workout_session import WorkoutSession


class WorkoutService:
    """
    MVP: Workouts = date + notes + selected muscle groups.
    """

    # ---- Muscles ----
    def list_muscles(self) -> list[dict[str, Any]]:
        with get_session() as session:
            muscles = session.query(MuscleGroup).order_by(MuscleGroup.id.asc()).all()
            return [{"id": m.id, "name": m.name, "svg_key": m.svg_key} for m in muscles]

    # ---- Sessions ----
    def create_session(
        self,
        user_id: int,
        workout_date: date,
        notes: str | None,
        muscle_ids: list[int],
    ) -> int:
        if not muscle_ids:
            raise ValueError("Select at least one muscle group.")

        with get_session() as session:
            # --- ADD THIS CHECK ---
            existing_session = session.query(WorkoutSession).filter(
                WorkoutSession.user_id == user_id,
                WorkoutSession.workout_date == workout_date
            ).first()
            
            if existing_session:
                raise ValueError("You already have a tracked training for this day.")
            # ----------------------

            ws = WorkoutSession(user_id=user_id, workout_date=workout_date, notes=notes)
            session.add(ws)
            session.commit()
            session.refresh(ws)

            # Create join rows (session <-> muscle)
            for mid in set(muscle_ids):
                link = SessionMuscle(workout_session_id=ws.id, muscle_group_id=mid)
                session.add(link)

            session.commit()
            return ws.id
        
    def list_sessions(self, user_id: int, limit: int = 20) -> list[dict[str, Any]]:
        """
        Returns list of dicts:
        {id, date, notes, muscle_names[]}
        """
        with get_session() as session:
            sessions = (
                session.query(WorkoutSession)
                .filter(WorkoutSession.user_id == user_id)
                .order_by(WorkoutSession.workout_date.desc(), WorkoutSession.id.desc())
                .limit(limit)
                .all()
            )

            result: list[dict[str, Any]] = []
            for ws in sessions:
                muscle_names = (
                    session.query(MuscleGroup.name)
                    .join(SessionMuscle, SessionMuscle.muscle_group_id == MuscleGroup.id)
                    .filter(SessionMuscle.workout_session_id == ws.id)
                    .order_by(MuscleGroup.id.asc())
                    .all()
                )
                # muscle_names is list of tuples [(name,), ...]
                names = [mn[0] for mn in muscle_names]

                result.append(
                    {
                        "id": ws.id,
                        "date": ws.workout_date,
                        "notes": ws.notes,
                        "muscle_names": names,
                    }
                )

            return result

    def delete_session(self, session_id: int, user_id: int) -> None:
        with get_session() as session:
            ws = (
                session.query(WorkoutSession)
                .filter(WorkoutSession.id == session_id, WorkoutSession.user_id == user_id)
                .first()
            )
            if ws is None:
                raise ValueError("Workout not found (or not yours).")

            session.delete(ws)
            session.commit()

    def list_sessions_in_range(
        self,
        user_id: int,
        start_date: date,
        end_date: date,
    ) -> list[dict[str, Any]]:
        """
        Used by MuscleMapService. Inclusive range: start_date..end_date
        """
        with get_session() as session:
            sessions = (
                session.query(WorkoutSession)
                .filter(
                    WorkoutSession.user_id == user_id,
                    WorkoutSession.workout_date >= start_date,
                    WorkoutSession.workout_date <= end_date,
                )
                .order_by(WorkoutSession.workout_date.asc(), WorkoutSession.id.asc())
                .all()
            )

            result: list[dict[str, Any]] = []
            for ws in sessions:
                muscle_names = (
                    session.query(MuscleGroup.name)
                    .join(SessionMuscle, SessionMuscle.muscle_group_id == MuscleGroup.id)
                    .filter(SessionMuscle.workout_session_id == ws.id)
                    .order_by(MuscleGroup.id.asc())
                    .all()
                )
                names = [mn[0] for mn in muscle_names]

                result.append(
                    {
                        "id": ws.id,
                        "date": ws.workout_date,
                        "notes": ws.notes,
                        "muscle_names": names,
                    }
                )
    def get_session_by_id(self, session_id: int, user_id: int) -> dict:
        with get_session() as session:
            ws = (
                session.query(WorkoutSession)
                .filter(
                    WorkoutSession.id == session_id,
                    WorkoutSession.user_id == user_id,
                )
                .first()
            )

            if ws is None:
                raise ValueError("Workout not found.")

            muscle_links = (
                session.query(SessionMuscle.muscle_group_id)
                .filter(SessionMuscle.workout_session_id == ws.id)
                .all()
            )

            muscle_ids = [m[0] for m in muscle_links]

            return {
                "id": ws.id,
                "date": ws.workout_date,
                "notes": ws.notes,
                "muscle_ids": muscle_ids,
            }


    def update_session(
        self,
        session_id: int,
        user_id: int,
        workout_date: date,
        notes: str | None,
        muscle_ids: list[int],
    ) -> None:
        if not muscle_ids:
            raise ValueError("Select at least one muscle group.")

        with get_session() as session:
            ws = (
                session.query(WorkoutSession)
                .filter(
                    WorkoutSession.id == session_id,
                    WorkoutSession.user_id == user_id,
                )
                .first()
            )

            if ws is None:
                raise ValueError("Workout not found.")

            ws.workout_date = workout_date
            ws.notes = notes

            session.query(SessionMuscle).filter(
                SessionMuscle.workout_session_id == ws.id
            ).delete()

            for mid in set(muscle_ids):
                session.add(SessionMuscle(
                    workout_session_id=ws.id,
                    muscle_group_id=mid,
                ))

            session.commit()

            return result
    