import json
from datetime import date
from pathlib import Path
from uuid import uuid4

import flet as ft


DATA_FILE = Path.home() / ".daily_homework_tracker.json"
GREEN = "#2E6654"
GREEN_LIGHT = "#E2EDE5"
PAPER = "#F6F5EF"
INK = "#202C2A"
MUTED = "#77807B"
CORAL = "#CF6048"
AMBER = "#B6782A"
RED = "#C85B4A"
CREATOR_PHOTO_URL = "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=900&q=80"
MUSIC_TRACKS = {
    "1": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
    "2": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
    "3": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
    "4": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3",
}


def _parse_due_date(value):
    if not isinstance(value, str):
        return None
    normalized = value.strip().replace("/", "-").replace("年", "-").replace("月", "-").replace("日", "")
    try:
        return date.fromisoformat(normalized)
    except ValueError:
        return None


def create_assignment(class_name, title, due_date):
    class_name = class_name.strip()
    title = title.strip()
    parsed_due_date = _parse_due_date(due_date)
    if not class_name or not title or parsed_due_date is None:
        raise ValueError("クラス名・宿題・期限を正しく入力してください。")
    return {
        "id": str(uuid4()),
        "class_name": class_name,
        "title": title,
        "due_date": parsed_due_date.isoformat(),
        "done": False,
    }


def load_assignments():
    try:
        raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []

    if not isinstance(raw, list):
        raise ValueError(f"{DATA_FILE} must contain a JSON list")

    assignments = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        class_name = item.get("class_name")
        title = item.get("title")
        due_date = item.get("due_date")
        done = item.get("done")
        if not isinstance(class_name, str) or not isinstance(title, str) or not isinstance(done, bool):
            continue
        if _parse_due_date(due_date) is None:
            continue
        assignments.append(
            {
                "id": str(item.get("id") or uuid4()),
                "class_name": class_name.strip(),
                "title": title.strip(),
                "due_date": due_date,
                "done": done,
            }
        )
    return assignments


def save_assignments(assignments):
    DATA_FILE.write_text(json.dumps(assignments, ensure_ascii=False, indent=2), encoding="utf-8")


def load_tasks():
    return load_assignments()


def save_tasks(tasks):
    save_assignments(tasks)


def is_all_assignments_done(assignments):
    return bool(assignments) and all(assignment["done"] for assignment in assignments)


def get_assignment_summary(today=None, assignments=None):
    if today is None:
        today = date.today()

    if assignments is None:
        assignments = load_assignments()
    remaining = sum(1 for assignment in assignments if not assignment["done"])
    completed = len(assignments) - remaining
    overdue = sum(
        1
        for assignment in assignments
        if not assignment["done"] and _parse_due_date(assignment["due_date"]) is not None and _parse_due_date(assignment["due_date"]) < today
    )
    due_today = sum(
        1
        for assignment in assignments
        if not assignment["done"] and _parse_due_date(assignment["due_date"]) == today
    )
    return {
        "total": len(assignments),
        "remaining": remaining,
        "completed": completed,
        "due_today": due_today,
        "overdue": overdue,
    }


def main(page: ft.Page):
    page.title = "宿題管理 | しおりノート"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = PAPER
    page.padding = 24
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO

    try:
        assignments = load_assignments()
    except (OSError, ValueError) as error:
        page.add(
            ft.Text(
                f"宿題データを読み込めませんでした: {error}",
                color=RED,
                selectable=True,
            )
        )
        return
    current_filter = "all"
    current_class_filter = "all"

    def pretty_due_date(due_date_value):
        due_date_obj = _parse_due_date(due_date_value)
        if due_date_obj is None:
            return "期限未設定"
        return due_date_obj.strftime("%Y/%m/%d")

    def due_badge_color(due_date_value, done):
        if done:
            return "#8AA69D"
        due_date_obj = _parse_due_date(due_date_value)
        if due_date_obj is None:
            return MUTED
        today = date.today()
        delta = (due_date_obj - today).days
        if delta < 0:
            return RED
        if delta <= 2:
            return AMBER
        return GREEN

    def persist():
        try:
            save_assignments(assignments)
        except OSError as error:
            status_text.value = f"保存できませんでした: {error}"
            status_text.visible = True
            return False
        status_text.value = ""
        status_text.visible = False
        return True

    def get_visible_assignments():
        nonlocal current_class_filter
        class_name_list = sorted({assignment["class_name"] for assignment in assignments})
        class_options = ["all"] + class_name_list
        if current_class_filter not in class_options:
            current_class_filter = "all"

        visible = []
        for assignment in assignments:
            ok_class = current_class_filter == "all" or assignment["class_name"] == current_class_filter
            due_date = _parse_due_date(assignment["due_date"])
            is_due_soon = (
                not assignment["done"]
                and due_date is not None
                and 0 <= (due_date - date.today()).days <= 2
            )
            ok_state = (
                current_filter == "all"
                or (current_filter == "active" and not assignment["done"])
                or (current_filter == "done" and assignment["done"])
                or (current_filter == "due_soon" and is_due_soon)
            )
            if ok_class and ok_state:
                visible.append(assignment)
        return visible

    def set_filter(value):
        nonlocal current_filter
        current_filter = value
        render()

    def set_class_filter(value):
        nonlocal current_class_filter
        current_class_filter = value
        render()

    def add_assignment(event=None):
        try:
            assignment = create_assignment(
                class_input.value or "",
                title_input.value or "",
                due_date_input.value or "",
            )
        except ValueError as error:
            status_text.value = f"{error} 期限は 2026-10-29、2026/10/29 の形式で入力できます。"
            status_text.visible = True
            page.update()
            return
        assignments.insert(0, assignment)
        if not persist():
            assignments.remove(assignment)
            render()
            return
        class_input.value = ""
        title_input.value = ""
        due_date_input.value = ""
        render()

    def toggle_assignment(task_id):
        for assignment in assignments:
            if assignment["id"] == task_id:
                assignment["done"] = not assignment["done"]
                break
        persist()
        render()

    def delete_assignment(task_id):
        assignments[:] = [assignment for assignment in assignments if assignment["id"] != task_id]
        persist()
        render()

    def clear_done(event=None):
        assignments[:] = [assignment for assignment in assignments if not assignment["done"]]
        persist()
        render()

    def all_assignments_done():
        return is_all_assignments_done(assignments)

    def play_music(track_id):
        url = MUSIC_TRACKS.get(track_id, MUSIC_TRACKS["1"])
        page.launch_url(url)

    def render():
        summary = get_assignment_summary(date.today(), assignments)
        visible = get_visible_assignments()

        total_label.value = f"{summary['remaining']} 件未完了"
        info_label.value = (
            f"期限超過 {summary['overdue']}件 / 本日 {summary['due_today']}件"
            if summary['total']
            else "まだ宿題はありません"
        )
        clear_done_button.visible = summary['completed'] > 0
        is_done = all_assignments_done()
        celebration_panel.visible = is_done
        creator_message.visible = is_done
        creator_photo.visible = is_done

        class_names = sorted({assignment["class_name"] for assignment in assignments})
        class_dropdown.options = [ft.dropdown.Option("all", "すべてのクラス")] + [ft.dropdown.Option(name, name) for name in class_names]
        class_dropdown.value = current_class_filter
        class_dropdown.disabled = not class_names

        for key, button in filter_buttons.items():
            selected = key == current_filter
            button.style = ft.ButtonStyle(
                color=GREEN if selected else MUTED,
                bgcolor=GREEN_LIGHT if selected else "transparent",
                shape=ft.RoundedRectangleBorder(radius=4),
            )

        rows = []
        for assignment in visible:
            due_date_obj = _parse_due_date(assignment["due_date"])
            if due_date_obj is not None:
                due_delta = (due_date_obj - date.today()).days
                if due_delta < 0:
                    due_status = "期限超過"
                elif due_delta == 0:
                    due_status = "本日締切"
                elif due_delta <= 2:
                    due_status = f"あと {due_delta} 日"
                else:
                    due_status = f"あと {due_delta} 日"
            else:
                due_status = "期限未設定"

            badge = ft.Container(
                content=ft.Text(due_status, size=10, color="white", weight=ft.FontWeight.BOLD),
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                bgcolor=due_badge_color(assignment["due_date"], assignment["done"]),
                border_radius=6,
            )
            checkbox = ft.Checkbox(
                value=assignment["done"],
                label=assignment["title"],
                expand=True,
                active_color=GREEN,
                label_style=ft.TextStyle(
                    color="#929992" if assignment["done"] else INK,
                    decoration=ft.TextDecoration.LINE_THROUGH if assignment["done"] else None,
                    size=14,
                ),
                on_change=lambda event, assignment_id=assignment["id"]: toggle_assignment(assignment_id),
            )
            class_mark = ft.Container(
                content=ft.Text(assignment["class_name"], size=11, color=GREEN, weight=ft.FontWeight.BOLD),
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                bgcolor=GREEN_LIGHT,
                border_radius=6,
            )
            delete_button = ft.IconButton(
                icon=ft.Icons.DELETE_OUTLINE,
                icon_color=MUTED,
                tooltip=f"「{assignment['title']}」を削除",
                on_click=lambda event, assignment_id=assignment["id"]: delete_assignment(assignment_id),
            )
            rows.extend(
                [
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Row([class_mark, badge], spacing=8),
                                ft.Row([checkbox, delete_button], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                                ft.Text(f"期限: {pretty_due_date(assignment['due_date'])}", size=11, color=MUTED),
                            ],
                            spacing=6,
                        ),
                        padding=ft.Padding(10, 12, 10, 12),
                        border=ft.Border.all(1, "#E6E6DF"),
                        border_radius=8,
                        bgcolor="#FFFDF8" if not assignment["done"] else "#F5F7F4",
                    ),
                    ft.Divider(height=1, thickness=1, color="#DEDFD5"),
                ]
            )

        if not visible:
            empty_text = (
                "未完了の宿題はありません。よくできました。"
                if current_filter == "active" and assignments
                else "完了済みの宿題はまだありません。"
                if current_filter == "done" and assignments
                else "期限が近い宿題はまだありません。"
                if current_filter == "due_soon" and assignments
                else "まずは、クラスと期限を入力して宿題を登録しましょう。"
            )
            rows = [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("✓", size=24, color="#9A7629", text_align=ft.TextAlign.CENTER),
                            ft.Text(empty_text, size=13, color=MUTED, text_align=ft.TextAlign.CENTER),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    padding=24,
                    alignment=ft.Alignment.CENTER,
                )
            ]

        list_area.controls = rows
        page.update()

    filter_buttons = {}
    for key, label in (("all", "すべて"), ("active", "未完了"), ("due_soon", "期限が近い"), ("done", "完了")):
        filter_buttons[key] = ft.TextButton(label, on_click=lambda event, value=key: set_filter(value))

    class_input = ft.TextField(label="クラス名", hint_text="例: 数学", expand=True)
    title_input = ft.TextField(label="宿題", hint_text="例: 予習ノート3ページ", expand=True)
    due_date_input = ft.TextField(label="期限", hint_text="YYYY-MM-DD", expand=True)
    status_text = ft.Text(color=RED, size=12)
    status_text.visible = False

    total_label = ft.Text(color=MUTED, size=12)
    info_label = ft.Text(color=MUTED, size=11)
    list_area = ft.Column(spacing=10)
    clear_done_button = ft.TextButton(
        "完了済みを削除",
        icon=ft.Icons.DELETE_OUTLINE,
        style=ft.ButtonStyle(color=CORAL),
        on_click=clear_done,
    )
    class_dropdown = ft.Dropdown(
        label="クラスで絞り込み",
        options=[ft.dropdown.Option("all", "すべてのクラス")],
        value="all",
        on_select=lambda event: set_class_filter(event.control.value or "all"),
    )
    filter_buttons_row = ft.Row(list(filter_buttons.values()), spacing=0)
    filters_panel = ft.Container(
        content=ft.Row(
            [filter_buttons_row, class_dropdown],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.Padding(left=18, right=18, top=8, bottom=8),
        border=ft.Border.only(bottom=ft.BorderSide(1, "#DEDFD5")),
    )
    music_buttons = {
        key: ft.Button(
            f"{key}",
            on_click=lambda event, track_id=key: play_music(track_id),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)),
        )
        for key in ("1", "2", "3", "4")
    }
    creator_message = ft.Text("宿題完了！お疲れさまです。", size=12, color=GREEN, weight=ft.FontWeight.BOLD)
    creator_message.visible = False
    creator_photo = ft.Image(
        src=CREATOR_PHOTO_URL,
        width=180,
        height=180,
        fit=ft.BoxFit.COVER,
        border_radius=90,
        visible=False,
    )
    celebration_panel = ft.Container(
        content=ft.Column(
            [creator_message, creator_photo],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        ),
        visible=all_assignments_done(),
        padding=ft.Padding(top=12),
    )

    composer_fields = ft.Row([class_input, title_input, due_date_input], spacing=10)
    composer = ft.Column(
        [
            composer_fields,
            ft.Row(
                [
                    status_text,
                    ft.Button(
                        "追加する",
                        on_click=add_assignment,
                        bgcolor=GREEN,
                        color="white",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5)),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
        ],
        spacing=8,
    )

    content = ft.Column(
        [
            ft.Row(
                [
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Text("宿", color="white", size=15, weight=ft.FontWeight.BOLD),
                                width=30,
                                height=30,
                                bgcolor=GREEN,
                                border_radius=15,
                                alignment=ft.Alignment.CENTER,
                            ),
                            ft.Text("HOMEWORK TRACKER", size=12, color=GREEN, weight=ft.FontWeight.BOLD),
                        ],
                        spacing=10,
                    ),
                    ft.Text(date.today().strftime("%Y年%m月%d日"), size=12, color=MUTED),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Column(
                [
                    ft.Text("宿題を見逃さない", size=36, color=INK, weight=ft.FontWeight.W_600),
                    ft.Text("クラスごとに期限を管理して、提出漏れを防ぎましょう。", size=13, color=MUTED),
                ],
                spacing=4,
            ),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Container(content=composer, padding=18, bgcolor=GREEN_LIGHT),
                        filters_panel,
                        ft.Container(
                            content=ft.Row([total_label, info_label], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            padding=ft.Padding(left=18, right=18, top=10, bottom=10),
                            border=ft.Border.only(bottom=ft.BorderSide(1, "#DEDFD5")),
                        ),
                        ft.Container(content=list_area, padding=ft.Padding.symmetric(horizontal=18, vertical=12)),
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text("音楽を流す", size=12, color=MUTED, weight=ft.FontWeight.BOLD),
                                    ft.Row(list(music_buttons.values()), spacing=8),
                                    celebration_panel,
                                ],
                                spacing=10,
                            ),
                            padding=ft.Padding(left=18, right=18, top=8, bottom=8),
                            border=ft.Border.only(top=ft.BorderSide(1, "#DEDFD5")),
                        ),
                        ft.Container(
                            content=ft.Row(
                                [ft.Text("期限とクラスで整理", size=12, color=MUTED), clear_done_button],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            padding=ft.Padding(left=18, right=18, top=8, bottom=8),
                            border=ft.Border.only(top=ft.BorderSide(1, "#DEDFD5")),
                        ),
                    ],
                    spacing=0,
                ),
                width=760,
                bgcolor="#FFFEFA",
                border=ft.Border.all(1, "#E3E3D9"),
                border_radius=10,
                shadow=ft.BoxShadow(blur_radius=24, color="#182D2314", offset=ft.Offset(0, 10)),
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            ),
        ],
        width=760,
        spacing=28,
    )

    app_container = ft.Container(content=content, width=760, padding=ft.Padding.only(top=18, bottom=32))
    app_card = content.controls[2]

    def resize_page(event):
        viewport_width = page.width or 820
        page.padding = 12 if viewport_width < 560 else 24
        content_width = min(760, max(300, viewport_width - page.padding * 2))
        app_container.width = content_width
        content.width = content_width
        app_card.width = content_width
        if viewport_width < 640:
            composer.controls[0] = ft.Column(
                [class_input, title_input, due_date_input],
                spacing=8,
            )
            filters_panel.content = ft.Column(
                [filter_buttons_row, class_dropdown],
                spacing=8,
            )
        else:
            composer.controls[0] = composer_fields
            filters_panel.content = ft.Row(
                [filter_buttons_row, class_dropdown],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        page.update()

    page.on_resize = resize_page
    page.add(app_container)
    resize_page(None)
    render()


if __name__ == "__main__":
    ft.run(main, view=ft.AppView.WEB_BROWSER)