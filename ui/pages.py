from __future__ import annotations
from datetime import date
from nicegui import ui, app


def register_pages(
    auth_service,
    workout_service,
    muscle_map_service,
    require_login,
    get_current_user_id,
    set_current_user_id,
):

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

            with ui.card().classes("w-full max-w-md").style(
                'background: #1e1e1e; border-radius: 16px; padding: 30px;'
            ):
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

            with ui.row().classes("gap-2"):
                ui.button("Login", on_click=do_login).style(
                    'background: white !important; color: black !important;'
                )
                ui.button(
                    "Register",
                    on_click=lambda: ui.navigate.to("/register")
                ).style('background: white !important; color: black !important;')

            username.on('keydown.enter', lambda e: do_login())
            password.on('keydown.enter', lambda e: do_login())

    @ui.page('/register')
    def register_page():
        ui.dark_mode().enable()

        ui.add_head_html('''
        <style>
            html, body {
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
            with ui.card().classes('w-full max-w-lg shadow-2xl').style(
                'background: #1e1e1e; border-radius: 16px; padding: 30px;'
            ):
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
                ui.button(
                    'Back to Login',
                    on_click=lambda: ui.navigate.to('/')
                ).style('background: white !important; color: black !important;')

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
                    ui.button("Weekly Summary", on_click=lambda: ui.navigate.to("/week"))
                    ui.button("Heatmap", on_click=lambda: ui.navigate.to("/heatmap"))
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

        def delete_row(ev):
            row_data = ev.args

            with ui.dialog() as dialog, ui.card().classes('p-4'):
                ui.label(f'Do you want to delete the entry from the {row_data["date"]} ?')
                with ui.row().classes('w-full justify-end'):
                    ui.button('Cancel', on_click=lambda: dialog.close()).props('flat')
                    ui.button(
                        'Delete',
                        on_click=lambda: execute_deletion(row_data, dialog),
                        color='red',
                    )

            dialog.open()

        def execute_deletion(row, dialog):
            try:
                workout_service.delete_session(session_id=row["id"], user_id=user_id)
                ui.notify("Workout deleted", type="positive")
                dialog.close()
                ui.navigate.to("/dashboard")
            except Exception as e:
                ui.notify(f"Fehler: {e}", type="negative")

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

        all_muscles = workout_service.list_muscles()

        with ui.card().classes("w-full max-w-2xl"):
            recent_sessions = workout_service.list_sessions(user_id=user_id, limit=10)
            template_options = {
                s['id']: f"{s['date'].strftime('%d.%m.%Y')} - {', '.join(s['muscle_names'])}"
                for s in recent_sessions
            }

            checkboxes = []
            notes = ui.textarea("Notes (optional)").props("autogrow")

            def load_template(e):
                if not e.value:
                    return
                details = workout_service.get_session_by_id(e.value, user_id)
                notes.value = details['notes']
                selected_muscles = set(details['muscle_ids'])
                for m, cb in checkboxes:
                    cb.value = m['id'] in selected_muscles
                ui.notify("Template loaded!", type='positive')

            ui.select(
                options=template_options,
                label="Load from past workout...",
                on_change=load_template,
                clearable=True
            ).classes('w-full mb-4')

            workout_date = ui.date(value=date.today().isoformat())

            ui.label("Muscles trained").classes("font-semibold")

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

        from datetime import timedelta
        
        # Track week offset using a container
        state = {"week_offset": 0}

        def get_week_label():
            offset = state["week_offset"]
            if offset == 0:
                return "This Week"
            elif offset == 1:
                return "Last Week"
            else:
                return f"{offset} weeks ago"

        @ui.refreshable
        def week_display():
            current_day = date.today() - timedelta(weeks=state["week_offset"])
            result = muscle_map_service.week_summary(user_id=user_id, day_in_week=current_day)

            start_str = result["week_start"].strftime("%d.%m.%Y")
            end_str = result["week_end"].strftime("%d.%m.%Y")

            ui.label(f"Week: {start_str} → {end_str}")
            ui.separator()

            if not result["muscles"]:
                ui.label("No workouts this week yet.").classes("text-gray-600")
            else:
                for item in result["muscles"]:
                    bar = "█" * (item["intensity"] + 1)
                    ui.label(f"{item['name']}: {item['count']} sessions  {bar}")

        ui.label("Weekly Summary").classes("text-2xl font-bold")

        # Navigation controls
        with ui.row().classes("items-center gap-4 justify-center"):
            def go_previous():
                state["week_offset"] += 1
                next_button.enabled = True
                week_label.text = get_week_label()
                week_display.refresh()

            def go_next():
                if state["week_offset"] > 0:
                    state["week_offset"] -= 1
                    if state["week_offset"] == 0:
                        next_button.enabled = False
                    week_label.text = get_week_label()
                    week_display.refresh()

            prev_button = ui.button(icon="arrow_back", on_click=go_previous).props("round flat")
            week_label = ui.label(get_week_label())
            next_button = ui.button(icon="arrow_forward", on_click=go_next).props("round flat")
            
            # Disable next button if we're at current week
            if state["week_offset"] == 0:
                next_button.enabled = False

        with ui.card().classes("w-full max-w-2xl"):
            week_display()

        with ui.row().classes("gap-2"):
            ui.button("Back", on_click=lambda: ui.navigate.to("/dashboard"))
    @ui.page("/heatmap")
    def heatmap_page():
        ui.dark_mode().enable()
        user_id = require_login()

        ui.label("Muscle Heatmap").classes("text-2xl font-bold")

        result = muscle_map_service.week_summary(
            user_id=user_id,
            day_in_week=date.today(),
        )

        trained = {
            item["name"].lower().replace(" ", ""): item["count"]
            for item in result["muscles"]
        }

        def color(muscle: str) -> str:
            count = trained.get(muscle.lower().replace(" ", ""), 0)

            if count <= 0:
                return "#3a3a3a"
            if count == 1:
                return "#facc15"
            if count == 2:
                return "#fb923c"
            return "#ef4444"

        svg = f"""
        <svg viewBox="0 0 500 650" width="100%" style="max-width:520px">
            <style>
                .muscle {{
                    stroke: #111;
                    stroke-width: 3;
                    transition: 0.2s;
                }}
                .muscle:hover {{
                    opacity: 0.8;
                    cursor: pointer;
                }}
                text {{
                    fill: white;
                    font-size: 18px;
                    font-family: Arial, sans-serif;
                    text-anchor: middle;
                }}
            </style>

            <!-- Head -->
            <circle cx="250" cy="70" r="40" fill="#555" stroke="#111" stroke-width="3"/>

            <!-- Shoulders -->
            <rect class="muscle" x="125" y="125" width="80" height="55" rx="25"
                  fill="{color('shoulders')}">
                <title>Shoulders</title>
            </rect>
            <rect class="muscle" x="295" y="125" width="80" height="55" rx="25"
                  fill="{color('shoulders')}">
                <title>Shoulders</title>
            </rect>

            <!-- Chest -->
            <rect class="muscle" x="175" y="140" width="70" height="90" rx="20"
                  fill="{color('chest')}">
                <title>Chest</title>
            </rect>
            <rect class="muscle" x="255" y="140" width="70" height="90" rx="20"
                  fill="{color('chest')}">
                <title>Chest</title>
            </rect>

            <!-- Back -->
            <path class="muscle" d="M175 245 Q250 290 325 245 L315 350 Q250 390 185 350 Z"
                  fill="{color('back')}">
                <title>Back</title>
            </path>

            <!-- Abs -->
            <rect class="muscle" x="205" y="245" width="90" height="125" rx="25"
                  fill="{color('abs')}">
                <title>Abs</title>
            </rect>
            <line x1="250" y1="250" x2="250" y2="360" stroke="#111" stroke-width="3"/>
            <line x1="210" y1="285" x2="290" y2="285" stroke="#111" stroke-width="3"/>
            <line x1="210" y1="325" x2="290" y2="325" stroke="#111" stroke-width="3"/>

            <!-- Biceps -->
            <rect class="muscle" x="95" y="190" width="55" height="120" rx="25"
                  fill="{color('biceps')}">
                <title>Biceps</title>
            </rect>
            <rect class="muscle" x="350" y="190" width="55" height="120" rx="25"
                  fill="{color('biceps')}">
                <title>Biceps</title>
            </rect>

            <!-- Triceps -->
            <rect class="muscle" x="60" y="210" width="45" height="120" rx="22"
                  fill="{color('triceps')}">
                <title>Triceps</title>
            </rect>
            <rect class="muscle" x="395" y="210" width="45" height="120" rx="22"
                  fill="{color('triceps')}">
                <title>Triceps</title>
            </rect>

            <!-- Legs -->
            <rect class="muscle" x="180" y="390" width="60" height="180" rx="28"
                  fill="{color('legs')}">
                <title>Legs</title>
            </rect>
            <rect class="muscle" x="260" y="390" width="60" height="180" rx="28"
                  fill="{color('legs')}">
                <title>Legs</title>
            </rect>

            <!-- Labels -->
            <text x="250" y="625">Muscelgroups trained this week</text>
        </svg>
        """

        with ui.card().classes("w-full max-w-2xl items-center"):
            ui.html(svg)

            ui.separator()

            ui.label("Legende").classes("font-semibold")
            ui.label("Gray = Not Trained")
            ui.label("Yellow = 1 Training")
            ui.label("Orange = 2 Trainings")
            ui.label("Red = 3+ Trainings")

        with ui.row().classes("gap-2 mt-4"):
            ui.button("Back", on_click=lambda: ui.navigate.to("/dashboard")).props("outline")