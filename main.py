# main.py
from __future__ import annotations
import os
from datetime import date
from nicegui import ui, app
from db.engine import init_db
from services.auth_service import AuthService
from services.workout_service import WorkoutService
from services.muscle_map_service import MuscleMapService
app.add_static_files('/static', 'static')

# -----------------------------
# Bootstrap
# -----------------------------
def build_services():
    auth = AuthService()
    workout = WorkoutService()
    muscle_map = MuscleMapService(workout_service=workout)
    return auth, workout, muscle_map

init_db()
auth_service, workout_service, muscle_map_service = build_services()

# -----------------------------
# Helpers: session state
# -----------------------------
def get_current_user_id() -> int | None:
    return app.storage.user.get("user_id")

def set_current_user_id(user_id: int | None) -> None:
    if user_id is None:
        app.storage.user.clear()
    else:
        app.storage.user["user_id"] = user_id

def require_login() -> int:
    user_id = get_current_user_id()
    if user_id is None:
        ui.navigate.to("/")
        raise RuntimeError("Not logged in")
    return user_id

# -----------------------------
# Pages (Login/ Register/ Dashboard/ Workout/ Week)
# -----------------------------
@ui.page("/")
def login_page():
    ui.dark_mode().enable()

    ui.add_head_html('''
    <style>
        html, body {
            margin: 0;
            padding: 0;
            height: 100%;
            overflow: hidden;
        }

        .login-page {
            min-height: 100vh;
            width: 100vw;
            background: url("/static/Login_Page1.png") no-repeat center center;
            background-size: cover;
            background-attachment: fixed;
        }
    </style>
    ''')

    if get_current_user_id() is not None:
        ui.navigate.to("/dashboard")
        return

    with ui.column().classes('login-page w-full h-screen items-center justify-center'):

        ui.label("Gym Progress Tracker").classes("text-7xl font-bold")

        with ui.card().classes("w-full max-w-md").style('background: #1e1e1e; border-radius: 16px; padding: 30px;'):
            ui.label("Login or register to start tracking.").classes("text-gray-600")
            username = ui.input("Username").props("clearable")
            password = ui.input("Password", password=True, password_toggle_button=True)

        def do_login():
            try:
                user_id = auth_service.login(username.value or "", password.value or "")
                set_current_user_id(user_id)
                ui.navigate.to("/dashboard")
            except ValueError as e:
                ui.notify(str(e), type="negative")

        def do_register():
            try:
                user_id = auth_service.register(username.value or "", password.value or "")
                set_current_user_id(user_id)
                ui.navigate.to("/dashboard")
            except ValueError as e:
                ui.notify(str(e), type="negative")

        with ui.row().classes("gap-2"):
            ui.button("Login", on_click=do_login).style('background: white !important; color: black !important;')
            ui.button("Register", on_click=lambda: ui.navigate.to("/register")).style('background: white !important; color: black !important;')

        def handle_enter(e): #logs in when you hit enter
            do_login()

        username.on('keydown.enter', lambda e: do_login())
        password.on('keydown.enter', lambda e: do_login())

@ui.page('/register')
def register_page():
    ui.dark_mode().enable()

    ui.add_head_html('''
    <style>
        html, body{
            margin: 0;
            padding: 0;
            height: 100%;
            overflow: hidden;
        }
        .register-page {
            min-height: 110vh;
            width: 100%;
            background: url("/static/Register_Page2.png") no-repeat center center;
            background-size: cover;
            overflow: hidden;
        }
    </style>
    ''')

    with ui.column().classes('register-page w-full items-center justify-center'):

        with ui.card().classes('w-full max-w-lg shadow-2xl')\
            .style('background: #1e1e1e; border-radius: 16px; padding: 30px;'):

            ui.label('Register').classes('text-2xl font-bold text-white')
            ui.label('Create an account to start.').classes('text-gray-400')

            new_username = ui.input('Username').props('clearable')
            new_password = ui.input('Password', password=True, password_toggle_button=True)

        def do_create_account():
            try:
                user_id = auth_service.register(new_username.value or "", new_password.value or "")
                set_current_user_id(user_id)
                ui.notify('Register Successful!', type='positive')
                ui.navigate.to("/dashboard")
            except ValueError as e:
                ui.notify(str(e), type='negative')

        with ui.row().classes('gap-2'):
            ui.button(
                'Create Account',
                on_click=do_create_account
            ).style('background: white !important; color: black !important')
            ui.button('Back to Login', on_click=lambda: ui.navigate.to('/')).style('background: white !important; color: black !important;')

@ui.page("/dashboard")
def dashboard_page():
    ui.dark_mode().enable()
    user_id = require_login()

    with ui.column().classes("w-full items-center"):
        with ui.column().style(
            "max-width: 1100px; "
            "width: 100%; "
            "background: #262626; "
            "border-radius: 20px; "
            "padding: 30px; "
            "margin-top: 30px; "
            "box-shadow: 0 10px 30px rgba(0,0,0,0.4);"
        ):
            
            ui.label("Dashboard").classes("w-full items-center")

            with ui.row().classes("items-center gap-6"):
                ui.button("New Workout", on_click=lambda: ui.navigate.to("/workout/new"))
                ui.button("This Week", on_click=lambda: ui.navigate.to("/week"))
                ui.button(
                    "Logout",
                    on_click=lambda: (set_current_user_id(None), ui.navigate.to("/"))
                ).props("outline")

    ui.separator()
    ui.label("Recent Workouts").classes("text-lg font-semibold")

    sessions = workout_service.list_sessions(user_id=user_id, limit=14)

    if not sessions:
        ui.label("No workouts yet. Click 'New Workout' to add your first one.").classes("text-gray-600")
        return

    rows = []
    for s in sessions:
        rows.append({
            "id": s["id"],
            "date": s["date"].strftime("%d.%m.%Y"),
            "muscles": ", ".join(s["muscle_names"]),
              "notes": s.get("notes") or "",
        })

    columns = [
        {"name": "date", "label": "Date", "field": "date", "sortable": True},
        {"name": "muscles", "label": "Muscles", "field": "muscles"},
        {"name": "notes", "label": "Notes", "field": "notes"},
        {"name": "actions", "label": "Actions", "field": "actions"},
    ]

    table = ui.table(columns=columns, rows=rows, row_key="id").classes("w-full")

    # Add delete buttons in an "actions" slot
    table.add_slot(
        "body-cell-actions",
        r"""
        <q-td :props="props">
          <q-btn dense flat icon="delete" @click="$parent.$emit('delete_row', props.row)" />
        </q-td>
        """,
    )


    def delete_row(ev):
        row_data = ev.args
        
        
        with ui.dialog() as dialog, ui.card().classes('p-4'):
            ui.label(f'Do you want to delete the entry from the {row_data["date"]} ?')
            with ui.row().classes('w-full justify-end'):
                ui.button('Cancel', on_click=dialog.close).props('flat')
                ui.button('Delete', on_click=lambda: execute_deletion(row_data, dialog), color='red',)
        
        dialog.open()

    def execute_deletion(row, dialog):
        try:
        
            workout_service.delete_session(session_id=row["id"], user_id=user_id)
            ui.notify("Workout deleted", type="positive")
            dialog.close()
            ui.navigate.to("/dashboard")
        except Exception as e:
            ui.notify(f"Fehler: {e}", type="negative")

    
    table.on("delete_row", delete_row)

    def edit_row(ev):
        row = ev.args
        ui.navigate.to(f"/workout/edit/{row['id']}")

    table.on("edit_row", edit_row)
    table.on("delete_row", delete_row)

    table.add_slot(
        "body-cell-actions",
        r"""
        <q-td :props="props">
            <q-btn dense flat icon="edit" @click="$parent.$emit('edit_row', props.row)" />
            <q-btn dense flat icon="delete" @click="$parent.$emit('delete_row', props.row)" />
        </q-td>
        """,
    )

@ui.page("/workout/edit/{session_id}")
def edit_workout_page(session_id: int):
    ui.dark_mode().enable()
    user_id = require_login()

    session_data = workout_service.get_session_by_id(session_id=session_id, user_id=user_id)
    all_muscles = workout_service.list_muscles()

    ui.label("Edit Workout").classes("text-2xl font-bold")

    with ui.card().classes("w-full max-w-2xl"):
        workout_date = ui.date(value=session_data["date"].isoformat())
        notes = ui.textarea("Notes (optional)", value=session_data["notes"] or "").props("autogrow")

        ui.label("Muscles trained").classes("font-semibold")

        selected_ids = set(session_data["muscle_ids"])
        checkboxes = []

        with ui.column().classes("gap-1"):
            for m in all_muscles:
                cb = ui.checkbox(m["name"], value=(m["id"] in selected_ids))
                checkboxes.append((m, cb))

        def save():
            new_muscle_ids = [m["id"] for (m, cb) in checkboxes if cb.value]
            if not new_muscle_ids:
                ui.notify("Select at least one muscle group.", type="warning")
                return

            try:
                workout_service.update_session(
                    session_id=session_id,
                    user_id=user_id,
                    workout_date=date.fromisoformat(str(workout_date.value).replace("/", "-")),
                    notes=notes.value,
                    muscle_ids=new_muscle_ids,
                )
                ui.notify("Workout updated!", type="positive")
                ui.timer(0.8, lambda: ui.navigate.to("/dashboard"), once=True)
                ui.navigate.to("/dashboard")
            except ValueError as e:
                ui.notify(str(e), type="negative")

        with ui.row().classes("gap-2"):
            ui.button("Save Changes", on_click=save)
            ui.button("Cancel", on_click=lambda: ui.navigate.to("/dashboard")).props("outline")      

@ui.page("/workout/new")
def new_workout_page():
    ui.dark_mode().enable()
    user_id = require_login()

    ui.label("New Workout").classes("text-2xl font-bold")

    all_muscles = workout_service.list_muscles()  # [{"id":..,"name":..,"svg_key":..}]

    with ui.card().classes("w-full max-w-2xl"):
        workout_date = ui.date(value=date.today().isoformat())
        notes = ui.textarea("Notes (optional)").props("autogrow")

        ui.label("Muscles trained").classes("font-semibold")

        checkboxes: list[tuple[dict, ui.checkbox]] = []
        with ui.column().classes("gap-1"):
            for m in all_muscles:
                cb = ui.checkbox(m["name"])
                checkboxes.append((m, cb))

        def save():
            selected_ids = [m["id"] for (m, cb) in checkboxes if cb.value]
            if not selected_ids:
                ui.notify("Select at least one muscle group.", type="warning")
                return

            try:
                workout_service.create_session(
                    user_id=user_id,
                    workout_date=date.fromisoformat(str(workout_date.value).replace("/", "-")),
                    notes=notes.value,
                    muscle_ids=selected_ids,
                )
                ui.notify("Workout saved!", type="positive")
                ui.timer(0.8, lambda: ui.navigate.to("/dashboard"), once=True)
                ui.navigate.to("/dashboard")
            except ValueError as e:
                ui.notify(str(e), type="negative")

        with ui.row().classes("gap-2"):
            ui.button("Save Workout", on_click=save).props("outline")
            ui.button("Cancel", on_click=lambda: ui.navigate.to("/dashboard")).props("outline")


@ui.page("/week")
def week_view_page():
    ui.dark_mode().enable()
    user_id = require_login()

    ui.label("This Week").classes("text-2xl font-bold")

    result = muscle_map_service.week_summary(user_id=user_id, day_in_week=date.today())

    with ui.card().classes("w-full max-w-2xl"):
        start_str = result["week_start"].strftime("%d.%m.%Y")
        end_str = result["week_end"].strftime("%d.%m.%Y")

        ui.label(f"Week: {start_str} → {end_str}")
        ui.separator()

        if not result["muscles"]:
            ui.label("No workouts this week yet.").classes("text-gray-600")
        else:
            # Simple text bars for MVP (replace with SVG later)
            for item in result["muscles"]:
                bar = "█" * (item["intensity"] + 1)
                ui.label(f"{item['name']}: {item['count']} sessions  {bar}")

    with ui.row().classes("gap-2"):
        ui.button("Back", on_click=lambda: ui.navigate.to("/dashboard"))

# -----------------------------
# Run
# -----------------------------
ui.run(
    title="Gym Progress Tracker",
    reload=False,
    # Needed for app.storage.user (signed cookies/session storage)
    storage_secret=os.environ.get("NICEGUI_STORAGE_SECRET", "dev-secret-change-me"),
)