from __future__ import annotations
from datetime import date, timedelta
from nicegui import ui, app


def register_pages(
    auth_service,
    workout_service,
    muscle_map_service,
    require_login,
    get_current_user_id,
    set_current_user_id,
):

    def build_heatmap_svg(result):
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

        return f"""
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

            <circle cx="250" cy="70" r="40" fill="#555" stroke="#111" stroke-width="3"/>

            <rect class="muscle" x="125" y="125" width="80" height="55" rx="25" fill="{color('shoulders')}"/>
            <rect class="muscle" x="295" y="125" width="80" height="55" rx="25" fill="{color('shoulders')}"/>

            <rect class="muscle" x="175" y="140" width="70" height="90" rx="20" fill="{color('chest')}"/>
            <rect class="muscle" x="255" y="140" width="70" height="90" rx="20" fill="{color('chest')}"/>

            <path class="muscle" d="M175 245 Q250 290 325 245 L315 350 Q250 390 185 350 Z" fill="{color('back')}"/>

            <rect class="muscle" x="205" y="245" width="90" height="125" rx="25" fill="{color('abs')}"/>
            <line x1="250" y1="250" x2="250" y2="360" stroke="#111" stroke-width="3"/>
            <line x1="210" y1="285" x2="290" y2="285" stroke="#111" stroke-width="3"/>
            <line x1="210" y1="325" x2="290" y2="325" stroke="#111" stroke-width="3"/>

            <rect class="muscle" x="95" y="190" width="55" height="120" rx="25" fill="{color('biceps')}"/>
            <rect class="muscle" x="350" y="190" width="55" height="120" rx="25" fill="{color('biceps')}"/>

            <rect class="muscle" x="60" y="210" width="45" height="120" rx="22" fill="{color('triceps')}"/>
            <rect class="muscle" x="395" y="210" width="45" height="120" rx="22" fill="{color('triceps')}"/>

            <rect class="muscle" x="180" y="390" width="60" height="180" rx="28" fill="{color('legs')}"/>
            <rect class="muscle" x="260" y="390" width="60" height="180" rx="28" fill="{color('legs')}"/>

            <text x="250" y="625">Muscle groups trained this week</text>
        </svg>
        """

    # ── shared full-page style ──────────────────────────────────────────────
    FULL_PAGE_STYLE = """
    <style>
        html, body, .q-page { margin: 0; padding: 0; height: 100%; overflow: hidden; }
    </style>
    """

    def show_add_exercise_dialog(user_id: int):
        with ui.dialog() as dialog, ui.card().classes("p-6 w-full max-w-md"):
            ui.label("Exercises").classes("text-xl font-bold")

            exercise_list = ui.column().classes("gap-2 mb-4 border p-3 rounded")

            def refresh_exercise_list():
                exercise_list.clear()
                exercises = workout_service.list_exercises(user_id=user_id)
                with exercise_list:
                    if not exercises:
                        ui.label("No custom exercises yet.").classes("text-gray-500")
                    else:
                        for exercise in exercises:
                            with ui.row().classes("justify-between items-center w-full"):
                                ui.label(exercise["name"])
                                ui.button(
                                    icon="delete",
                                    on_click=lambda ex_id=exercise["id"]: delete_exercise(ex_id),
                                ).props("flat color=negative size=sm")

            def delete_exercise(ex_id):
                try:
                    workout_service.delete_exercise(ex_id, user_id)
                    ui.notify("Exercise deleted!", type="positive")
                    dialog.close()
                    ui.navigate.to("/workout/new")
                except ValueError as e:
                    ui.notify(str(e), type="negative")
            refresh_exercise_list()

            ui.label("Add New Exercise").classes("text-md font-semibold mt-4")
            exercise_name = ui.input("Exercise Name").classes("w-full")

            def add_exercise():
                try:
                    if not exercise_name.value or not exercise_name.value.strip():
                        ui.notify("Exercise name cannot be empty.", type="warning")
                        return
                    workout_service.create_exercise(
                        user_id=user_id,
                        name=exercise_name.value.strip(),
                    )
                    ui.notify("Exercise added!", type="positive")
                    exercise_name.value = ""
                    dialog.close()
                    ui.navigate.to("/workout/new")
                except ValueError as e:
                    ui.notify(str(e), type="negative")

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Close", on_click=dialog.close).props("outline")
                ui.button("Add", on_click=add_exercise)

        dialog.open()

    @ui.page("/")
    def login_page():
        ui.dark_mode().enable()
        ui.add_head_html("""
        <style>
            html, body { margin: 0; padding: 0; height: 100%; overflow: hidden; }
            .login-page {
                min-height: 100vh; width: 100vw;
                background: url("/static/Login_Page1.png") no-repeat center center;
                background-size: cover; background-attachment: fixed;
            }
        </style>
        """)

        if get_current_user_id() is not None:
            ui.navigate.to("/dashboard")
            return

        with ui.column().classes("login-page w-full h-screen items-center justify-center"):
            ui.label("Gym Progress Tracker").classes("text-7xl font-bold")

            with ui.card().classes("w-full max-w-md").style(
                "background: #1e1e1e; border-radius: 16px; padding: 30px;"
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
                        "background: white !important; color: black !important;"
                    )
                    ui.button("Register", on_click=lambda: ui.navigate.to("/register")).style(
                        "background: white !important; color: black !important;"
                    )

                username.on("keydown.enter", lambda e: do_login())
                password.on("keydown.enter", lambda e: do_login())

    @ui.page("/register")
    def register_page():
        ui.dark_mode().enable()
        ui.add_head_html("""
        <style>
            html, body { margin: 0; padding: 0; height: 100%; overflow: hidden; }
            .register-page {
                min-height: 110vh; width: 100%;
                background: url("/static/Register_Page2.png") no-repeat center center;
                background-size: cover; overflow: hidden;
            }
        </style>
        """)

        with ui.column().classes("register-page w-full items-center justify-center"):
            with ui.card().classes("w-full max-w-lg shadow-2xl").style(
                "background: #1e1e1e; border-radius: 16px; padding: 30px;"
            ):
                ui.label("Register").classes("text-2xl font-bold text-white")
                ui.label("Create an account to start.").classes("text-gray-400")

                new_username = ui.input("Username").props("clearable")
                new_password = ui.input("Password", password=True, password_toggle_button=True)

                def do_create_account():
                    try:
                        user_id = auth_service.register(
                            new_username.value or "",
                            new_password.value or "",
                        )
                        set_current_user_id(user_id)
                        ui.notify("Register Successful!", type="positive")
                        ui.navigate.to("/dashboard")
                    except ValueError as e:
                        ui.notify(str(e), type="negative")

                with ui.row().classes("gap-2"):
                    ui.button("Create Account", on_click=do_create_account).style(
                        "background: white !important; color: black !important;"
                    )
                    ui.button("Back to Login", on_click=lambda: ui.navigate.to("/")).style(
                        "background: white !important; color: black !important;"
                    )

    @ui.page("/dashboard")
    def dashboard_page():
        ui.dark_mode().enable()
        ui.add_head_html(FULL_PAGE_STYLE)
        user_id = require_login()

        with ui.column().classes("w-full items-center").style("height: 100vh; overflow: hidden;"):

            with ui.column().style(
                "max-width: 1100px; width: 100%; "
                "background: #262626; border-radius: 20px; "
                "padding: 20px 30px; margin-top: 20px; "
                "box-shadow: 0 10px 30px rgba(0,0,0,0.4); flex-shrink: 0;"
            ):
                user = auth_service.get_user_by_id(user_id)
                username = user["username"]
                ui.label(f"Welcome back {username}").classes("text-3xl font-bold")
                ui.label("Dashboard").classes("text-xl text-gray-400 mt-1")
                with ui.row().classes("items-center gap-6"):
                    ui.button("New Workout", on_click=lambda: ui.navigate.to("/workout/new"))
                    ui.button("Weekly Summary", on_click=lambda: ui.navigate.to("/week"))
                    ui.button("PR Tracker", on_click=lambda: ui.navigate.to("/pr-tracker"))
                    ui.button(
                        "Logout",
                        on_click=lambda: (set_current_user_id(None), ui.navigate.to("/")),
                    ).props("outline")

            with ui.column().style(
                "max-width: 1100px; width: 100%; flex: 1; overflow-y: auto; "
                "padding: 16px 0 16px 0;"
            ):
                ui.label("Recent Workouts").classes("text-lg font-semibold")

                sessions = workout_service.list_sessions(user_id=user_id, limit=14)

                if not sessions:
                    ui.label("No workouts yet. Click 'New Workout' to add your first one.").classes(
                        "text-gray-600"
                    )
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
                    with ui.dialog() as dialog, ui.card().classes("p-4"):
                        ui.label(f'Do you want to delete the entry from {row_data["date"]}?')
                        with ui.row().classes("w-full justify-end"):
                            ui.button("Cancel", on_click=dialog.close).props("flat")
                            ui.button(
                                "Delete",
                                on_click=lambda: execute_deletion(row_data, dialog),
                                color="red",
                            )
                    dialog.open()

                def execute_deletion(row, dialog):
                    try:
                        workout_service.delete_session(session_id=row["id"], user_id=user_id)
                        ui.notify("Workout deleted", type="positive")
                        dialog.close()
                        ui.navigate.to("/dashboard")
                    except Exception as e:
                        ui.notify(f"Error: {e}", type="negative")

                def edit_row(ev):
                    row = ev.args
                    ui.navigate.to(f"/workout/edit/{row['id']}")

                table.on("edit_row", edit_row)
                table.on("delete_row", delete_row)
                table.add_slot(
                    "body-cell-actions",
                    """
                    <q-td :props="props">
                        <q-btn dense flat icon="edit" @click="$parent.$emit('edit_row', props.row)" />
                        <q-btn dense flat icon="delete" @click="$parent.$emit('delete_row', props.row)" />
                    </q-td>
                    """,
                )

    # ── shared helper: builds the muscles + exercises columns ──────────────
    def _build_workout_form(
        user_id: int,
        workout_service,
        notes_value: str = "",
        selected_muscle_ids: set | None = None,
    ):
        """Returns (workout_date_widget, notes_widget, checkboxes, exercise_inputs)."""
        selected_muscle_ids = selected_muscle_ids or set()

        all_muscles = workout_service.list_muscles()
        all_exercises_list = ["Benchpress", "Deadlift", "Squats", "Lat Pulldown"]
        custom_exercises = workout_service.list_exercises(user_id=user_id)
        all_exercises_list.extend([e["name"] for e in custom_exercises])

        workout_date = ui.input("Date", value=date.today().isoformat()).props("type=date")
        notes = ui.textarea("Notes (optional)", value=notes_value).props("autogrow").style(
            "max-height: 80px; overflow-y: auto;"
        )

        checkboxes: list = []
        exercise_inputs: dict = {}

        with ui.row().classes("gap-8 w-full").style("overflow-y: auto; flex: 1;"):
            with ui.column().style("width: 35%; overflow-y: auto; max-height: 55vh;"):
                ui.label("Muscles trained").classes("font-semibold")
                with ui.column().classes("gap-1"):
                    for m in all_muscles:
                        cb = ui.checkbox(m["name"], value=(m["id"] in selected_muscle_ids))
                        checkboxes.append((m, cb))

            with ui.column().style("width: 65%; overflow-y: auto; max-height: 55vh;"):
                ui.label("Exercises and PRs (kg)").classes("font-semibold")
                with ui.column().classes("gap-3"):
                    for exercise in all_exercises_list:
                        with ui.row().classes("gap-2 items-center"):
                            cb = ui.checkbox(exercise)
                            pr_input = ui.input(
                                "PR",
                                placeholder="kg",
                                validation={
                                    "Please enter a number": lambda v: (
                                        v == ""
                                        or v.replace(".", "", 1).replace("-", "", 1).isdigit()
                                    )
                                },
                            ).props("type=number").style("width: 100px")
                            exercise_inputs[exercise] = (cb, pr_input)

        return workout_date, notes, checkboxes, exercise_inputs

    @ui.page("/workout/edit/{session_id}")
    def edit_workout_page(session_id: int):
        ui.dark_mode().enable()
        ui.add_head_html(FULL_PAGE_STYLE)
        user_id = require_login()

        session_data = workout_service.get_session_by_id(
            session_id=session_id,
            user_id=user_id,
        )

        with ui.column().classes("w-full items-center").style(
            "height: 100vh; overflow: hidden; padding: 16px;"
        ):
            with ui.card().classes("w-full max-w-2xl").style(
                "height: 100%; display: flex; flex-direction: column; overflow: hidden;"
            ):
                with ui.row().classes("items-center justify-between w-full").style("flex-shrink: 0;"):
                    ui.label("Edit Workout").classes("text-2xl font-bold")
                    with ui.row().classes("gap-2"):
                        ui.button("Cancel", on_click=lambda: ui.navigate.to("/dashboard")).props("outline")

                ui.separator().style("flex-shrink: 0;")

                with ui.column().style("flex: 1; overflow-y: auto; padding: 8px 0;"):
                    workout_date, notes, checkboxes, exercise_inputs = _build_workout_form(
                        user_id=user_id,
                        workout_service=workout_service,
                        notes_value=session_data["notes"] or "",
                        selected_muscle_ids=set(session_data["muscle_ids"]),
                    )
                    workout_date.value = session_data["date"].isoformat()

                ui.separator().style("flex-shrink: 0;")
                with ui.row().classes("gap-2 justify-end").style("flex-shrink: 0; padding-top: 8px;"):
                    def save():
                        new_muscle_ids = [m["id"] for (m, cb) in checkboxes if cb.value]
                        if not new_muscle_ids:
                            ui.notify("Select at least one muscle group.", type="warning")
                            return
                        try:
                            workout_date_value = date.fromisoformat(
                                str(workout_date.value).replace("/", "-")
                            )
                            workout_service.update_session(
                                session_id=session_id,
                                user_id=user_id,
                                workout_date=workout_date_value,
                                notes=notes.value,
                                muscle_ids=new_muscle_ids,
                            )
                            for exercise_name, (cb, pr_input) in exercise_inputs.items():
                                if cb.value and pr_input.value:
                                    try:
                                        weight = float(pr_input.value)
                                        if weight > 0:
                                            workout_service.save_pr(
                                                user_id=user_id,
                                                exercise_name=exercise_name,
                                                weight_kg=weight,
                                                recorded_date=workout_date_value,
                                            )
                                    except ValueError:
                                        pass
                            ui.notify("Workout updated!", type="positive")
                            ui.navigate.to("/dashboard")
                        except ValueError as e:
                            ui.notify(str(e), type="negative")

                    ui.button("Save Changes", on_click=save)
                    ui.button("Cancel", on_click=lambda: ui.navigate.to("/dashboard")).props("outline")

    @ui.page("/workout/new")
    def new_workout_page():
        ui.dark_mode().enable()
        ui.add_head_html(FULL_PAGE_STYLE)
        user_id = require_login()

        all_muscles = workout_service.list_muscles()
        all_exercises_list = ["Benchpress", "Deadlift", "Squats", "Lat Pulldown"]
        custom_exercises = workout_service.list_exercises(user_id=user_id)
        all_exercises_list.extend([e["name"] for e in custom_exercises])

        recent_sessions = workout_service.list_sessions(user_id=user_id, limit=10)
        template_options = {
            s["id"]: f"{s['date'].strftime('%d.%m.%Y')} - {', '.join(s['muscle_names'])}"
            for s in recent_sessions
        }

        with ui.column().classes("w-full items-center").style(
            "height: 100vh; overflow: hidden; padding: 16px;"
        ):
            with ui.card().classes("w-full max-w-4xl").style(
                "height: 100%; display: flex; flex-direction: column; overflow: hidden;"
            ):
                ui.label("New Workout").classes("text-2xl font-bold").style("flex-shrink: 0;")
                ui.separator().style("flex-shrink: 0;")

                with ui.column().style("flex-shrink: 0; padding-bottom: 8px;"):
                    def load_template(e):
                        if not e.value:
                            return
                        details = workout_service.get_session_by_id(e.value, user_id)
                        notes_widget.value = details["notes"] or ""
                        selected_muscles = set(details["muscle_ids"])
                        for m, cb in muscle_checkboxes:
                            cb.value = m["id"] in selected_muscles
                        ui.notify("Template loaded!", type="positive")

                    ui.label("Load from recent workouts").classes("font-semibold")
                    ui.select(
                        options=template_options,
                        label="Load from past workout...",
                        on_change=load_template,
                        clearable=True,
                    ).classes("w-full")

                workout_date = ui.input("Date", value=date.today().isoformat()).props(
                    "type=date"
                ).style("flex-shrink: 0;")
                notes_widget = ui.textarea("Notes (optional)").props("autogrow").style(
                    "flex-shrink: 0; max-height: 80px; overflow-y: auto;"
                )

                muscle_checkboxes: list = []
                exercise_inputs: dict = {}

                with ui.element("div").style("display: flex; flex-direction: row; gap: 32px; flex: 1; min-height: 0; width: 100%;"):
                    # Left side config
                    with ui.element("div").style("width: 50%; overflow-y: auto;"):
                        ui.label("Muscles trained").classes("font-semibold")
                        with ui.column().classes("gap-1"):
                            for m in all_muscles:
                                cb = ui.checkbox(m["name"])
                                muscle_checkboxes.append((m, cb))

                    # Right side config
                    with ui.element("div").style("width: 50%; overflow-y: auto;"):
                        ui.button("Edit Exercises", on_click=lambda: show_add_exercise_dialog(user_id)).classes("mb-3")
                        ui.label("Exercises & PRs (kg)").classes("font-semibold")
                        with ui.column().classes("gap-1"):
                            for exercise in all_exercises_list:
                                with ui.row().classes("gap-2 items-center"):
                                    cb = ui.checkbox(exercise).style("width: 150px;")
                                    pr_input = ui.input(
                                        "PR",
                                        placeholder="kg",
                                        validation={
                                            "Please enter a number": lambda v: (
                                                v == ""
                                                or v.replace(".", "", 1).replace("-", "", 1).isdigit()
                                            )
                                        },
                                    ).props("type=number").style("width: 100px")
                                    exercise_inputs[exercise] = (cb, pr_input)

                ui.separator().style("flex-shrink: 0;")
                with ui.row().classes("gap-2 justify-end").style("flex-shrink: 0; padding-top: 8px;"):
                    def save():
                        selected_ids = [m["id"] for (m, cb) in muscle_checkboxes if cb.value]
                        if not selected_ids:
                            ui.notify("Select at least one muscle group.", type="warning")
                            return
                        try:
                            workout_date_val = date.fromisoformat(
                                str(workout_date.value).replace("/", "-")
                            )
                            workout_service.create_session(
                                user_id=user_id,
                                workout_date=workout_date_val,
                                notes=notes_widget.value,
                                muscle_ids=selected_ids,
                            )
                            # PRs save
                            for exercise_name, (cb, pr_input) in exercise_inputs.items():
                                if cb.value and pr_input.value:
                                    try:
                                        weight = float(pr_input.value)
                                        if weight > 0:
                                            workout_service.save_pr(
                                                user_id=user_id,
                                                exercise_name=exercise_name,
                                                weight_kg=weight,
                                                recorded_date=workout_date_val,
                                            )
                                    except ValueError:
                                        pass
                            ui.notify("Workout saved!", type="positive")
                            ui.navigate.to("/dashboard")
                        except ValueError as e:
                            ui.notify(str(e), type="negative")

                    ui.button("Save Workout", on_click=save)
                    ui.button("Cancel", on_click=lambda: ui.navigate.to("/dashboard")).props("outline")

    @ui.page("/week")
    def week_view_page():
        ui.dark_mode().enable()
        ui.add_head_html(FULL_PAGE_STYLE)
        user_id = require_login()

        state = {"week_offset": 0}

        def get_week_label():
            offset = state["week_offset"]
            if offset == 0:
                return "This Week"
            if offset == 1:
                return "Last Week"
            return f"{offset} weeks ago"

        @ui.refreshable
        def week_display():
            current_day = date.today() - timedelta(weeks=state["week_offset"])
            result = muscle_map_service.week_summary(
                user_id=user_id,
                day_in_week=current_day,
            )

            start_str = result["week_start"].strftime("%d.%m.%Y")
            end_str = result["week_end"].strftime("%d.%m.%Y")

            ui.label(f"Week: {start_str} \u2192 {end_str}").classes("text-lg font-semibold")
            ui.separator()

            with ui.element("div").style(
                "display: flex; flex-direction: row; gap: 24px;"
                "width: 100%; flex: 1; overflow: hidden;"
            ):
                # LEFT: Summary (top) + Legend (bottom)
                with ui.element("div").style(
                    "width: 25%; min-width: 180px; display: flex; flex-direction: column; "
                    "gap: 16px; overflow-y: auto;"
                ):
                    with ui.column().classes("gap-1"):
                        ui.label("Summary").classes("text-xl font-bold")
                        if not result["muscles"]:
                            ui.label("No workouts this week yet.").classes("text-gray-600")
                        else:
                            for item in result["muscles"]:
                                ui.label(f"{item['name']}: {item['count']} sessions").style(
                                    "font-size: 13px;"
                                )

                    ui.separator()

                    with ui.column().classes("gap-1"):
                        ui.label("Legend").classes("font-semibold")
                        for dot, text in [
                            ("\U0001f532", "Not trained"),
                            ("\U0001f7e1", "1 training"),
                            ("\U0001f7e0", "2 trainings"),
                            ("\U0001f534", "3+ trainings"),
                        ]:
                            ui.label(f"{dot}  {text}").style("font-size: 13px;")

                # RIGHT: Big heatmap
                with ui.element("div").style(
                    "display: flex; align-items: center; justify-content: flex-end; "
                    "overflow: hidden; flex: 1; padding-right: 10px; margin-left: 300px;"
                ):
                    ui.html(build_heatmap_svg(result)).style(
                        "width: 200%; max-width: 1700px; height: 200%; max-height: 95vh; "
                        "display: flex; align-items: center; justify-content: center; "
                        "transform: scale(1.3);"
                    )

        # ── page shell: fixed header + nav + scrollable content ────────────
        with ui.column().classes("w-full items-center").style(
            "height: 100vh; overflow: hidden; padding: 16px; gap: 8px;"
        ):
            # Title + week navigation — always visible at top
            with ui.element("div").style(
                "display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; "
                "gap: 16px; width: 100%; max-width: 1200px; flex-shrink: 0;"
            ):
                with ui.element("div").style("justify-self: start;"):
                    ui.label("Weekly Summary").classes("text-2xl font-bold")

                with ui.row().classes("items-center gap-2").style("justify-self: center;"):
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

                    ui.button(icon="arrow_back", on_click=go_previous).props("round flat")
                    week_label = ui.label(get_week_label())
                    next_button = ui.button(icon="arrow_forward", on_click=go_next).props("round flat")
                    next_button.enabled = False

                with ui.element("div").style("justify-self: end;"):
                    ui.button("Back", on_click=lambda: ui.navigate.to("/dashboard")).props("outline")

            # Content card — fills remaining space, no outer scroll
            with ui.card().classes("w-full").style(
                "max-width: 1200px; flex: 1; overflow: hidden; display: flex; flex-direction: column;"
            ):
                with ui.column().style("flex: 1; overflow: hidden;"):
                    week_display()
        
    @ui.page("/pr-tracker")
    def pr_tracker_page():
        ui.dark_mode().enable()
        ui.add_head_html(FULL_PAGE_STYLE)
        user_id = require_login()

        with ui.column().classes("w-full items-center").style(
            "height: 100vh; overflow: hidden; padding: 16px; gap: 12px;"
        ):
            with ui.row().classes("items-center justify-between w-full").style(
                "max-width: 900px; flex-shrink: 0;"
            ):
                ui.label("PR Tracker").classes("text-3xl font-bold")
                ui.button("Back", on_click=lambda: ui.navigate.to("/dashboard")).props("outline")

            with ui.card().classes("w-full").style(
                "max-width: 900px; flex: 1; overflow-y: auto;"
            ):
                best_prs = workout_service.get_best_prs(user_id=user_id)

                if not best_prs:
                    ui.label(
                        "Noch keine PRs erfasst. Trag beim nächsten Workout ein Gewicht ein!"
                    ).classes("text-gray-500 p-4")
                else:
                    columns = [
                        {"name": "exercise", "label": "Exercise", "field": "exercise", "sortable": True},
                        {"name": "weight_kg", "label": "Best PR (kg)", "field": "weight_kg", "sortable": True},
                        {"name": "date", "label": "Date", "field": "date"},
                        {"name": "actions", "label": "Actions", "field": "actions"},
                    ]
                    rows = [
                        {
                            "id": pr["id"],
                            "exercise": pr["exercise"],
                            "weight_kg": pr["weight_kg"],
                            "date": pr["date"].strftime("%d.%m.%Y"),
                            "date_iso": pr["date"].isoformat(),
                        }
                        for pr in best_prs
                    ]
                    table = ui.table(columns=columns, rows=rows, row_key="id").classes("w-full")

                    def edit_pr(ev):
                        row = ev.args

                        with ui.dialog() as dialog, ui.card().classes("p-6 w-full max-w-sm"):
                            ui.label(f"Edit PR - {row['exercise']}").classes("text-xl font-bold")
                            ui.separator()
                            weight_input = ui.input(
                                "Weight (kg)",
                                value=str(row["weight_kg"]),
                                placeholder="Enter new weight",
                            ).props("type=number")
                            date_input = ui.input(
                                "Recorded Date",
                                value=row["date_iso"],
                            ).props("type=date")

                            def save_pr_edit():
                                try:
                                    workout_service.update_pr(
                                        pr_id=row["id"],
                                        user_id=user_id,
                                        weight_kg=float(weight_input.value),
                                        recorded_date=date.fromisoformat(
                                            str(date_input.value).replace("/", "-")
                                        ),
                                    )
                                    ui.notify("PR updated!", type="positive")
                                    dialog.close()
                                    ui.navigate.to("/pr-tracker")
                                except ValueError as e:
                                    ui.notify(str(e), type="negative")

                            with ui.row().classes("justify-end gap-2"):
                                ui.button("Cancel", on_click=dialog.close).props("outline")
                                ui.button("Save", on_click=save_pr_edit)

                        dialog.open()

                    table.on("edit_pr", edit_pr)
                    def delete_pr(ev):
                        row = ev.args
                        with ui.dialog() as dialog, ui.card().classes("p-4"):
                            ui.label(f"Delete {row['exercise']} PR?").classes("text-lg font-semibold")
                            ui.label("This action cannot be undone.").classes("text-sm text-gray-500")
                            with ui.row().classes("w-full justify-end gap-2"):
                                ui.button("Cancel", on_click=dialog.close).props("flat")
                                ui.button(
                                    "Delete",
                                    color="negative",
                                    on_click=lambda: execute_pr_deletion(row["id"], dialog),
                                )
                        dialog.open()

                    def execute_pr_deletion(pr_id: int, dialog):
                        try:
                            workout_service.delete_pr(pr_id=pr_id, user_id=user_id)
                            ui.notify("PR deleted", type="positive")
                            dialog.close()
                            ui.navigate.to("/pr-tracker")
                        except ValueError as e:
                            ui.notify(str(e), type="negative")

                    table.on("delete_pr", delete_pr)
                    table.add_slot(
                        "body-cell-actions",
                        """
                        <q-td :props="props">
                            <q-btn dense flat icon="edit" @click="$parent.$emit('edit_pr', props.row)" />
                            <q-btn dense flat icon="delete" @click="$parent.$emit('delete_pr', props.row)" />
                        </q-td>
                        """,
                    )