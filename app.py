import tkinter as tk
from tkinter import ttk

try:
    import sv_ttk
    HAS_THEME = True
except:
    HAS_THEME = False


class WebmailApp:

    def __init__(self):

        self.root = tk.Tk()

        self.root.title("Webmail Alt")
        self.root.geometry("1500x900")

        self.dark_mode = True

        if HAS_THEME:
            sv_ttk.set_theme("dark")

        self.build_toolbar()
        self.build_main_area()
        self.build_statusbar()

    # ==================================================
    # TOOLBAR
    # ==================================================

    def build_toolbar(self):

        self.toolbar = ttk.Frame(
            self.root,
            padding=8
        )

        self.toolbar.pack(
            fill="x"
        )

        self.refresh_btn = ttk.Button(
            self.toolbar,
            text="Refresh"
        )

        self.refresh_btn.pack(
            side="left",
            padx=2
        )

        self.compose_btn = ttk.Button(
            self.toolbar,
            text="Compose"
        )

        self.compose_btn.pack(
            side="left",
            padx=2
        )

        self.delete_btn = ttk.Button(
            self.toolbar,
            text="Delete"
        )

        self.delete_btn.pack(
            side="left",
            padx=2
        )

        self.move_btn = ttk.Button(
            self.toolbar,
            text="Move"
        )

        self.move_btn.pack(
            side="left",
            padx=2
        )

        self.search_entry = ttk.Entry(
            self.toolbar,
            width=40
        )

        self.search_entry.pack(
            side="right",
            padx=10
        )

        self.theme_btn = ttk.Button(
            self.toolbar,
            text="🌙",
            command=self.toggle_theme
        )

        self.theme_btn.pack(
            side="right"
        )

        ttk.Separator(
            self.root
        ).pack(fill="x")

    # ==================================================
    # MAIN AREA
    # ==================================================

    def build_main_area(self):

        self.main = ttk.PanedWindow(
            self.root,
            orient="horizontal"
        )

        self.main.pack(
            fill="both",
            expand=True
        )

        self.build_sidebar()
        self.build_content_area()

    # ==================================================
    # SIDEBAR
    # ==================================================

    def build_sidebar(self):

        self.sidebar = ttk.Frame(
            self.main
        )

        ttk.Label(
            self.sidebar,
            text="MAILBOXES"
        ).pack(
            anchor="w",
            padx=10,
            pady=10
        )

        self.mailbox_list = tk.Listbox(
            self.sidebar,
            activestyle="none"
        )

        self.mailbox_list.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )

        for mailbox in [
            "INBOX",
            "Sent",
            "Drafts",
            "Trash",
            "Spam",
            "Archive"
        ]:
            self.mailbox_list.insert(
                "end",
                mailbox
            )

        self.main.add(
            self.sidebar,
            weight=1
        )

    # ==================================================
    # CONTENT AREA
    # ==================================================

    def build_content_area(self):

        self.content = ttk.PanedWindow(
            self.main,
            orient="vertical"
        )

        self.main.add(
            self.content,
            weight=5
        )

        self.build_email_list()
        self.build_email_viewer()

    # ==================================================
    # EMAIL LIST
    # ==================================================

    def build_email_list(self):

        self.email_frame = ttk.Frame(
            self.content
        )

        columns = (
            "from",
            "subject",
            "date"
        )

        self.email_tree = ttk.Treeview(
            self.email_frame,
            columns=columns,
            show="headings"
        )

        self.email_tree.heading(
            "from",
            text="From"
        )

        self.email_tree.heading(
            "subject",
            text="Subject"
        )

        self.email_tree.heading(
            "date",
            text="Date"
        )

        self.email_tree.column(
            "from",
            width=200
        )

        self.email_tree.column(
            "subject",
            width=800
        )

        self.email_tree.column(
            "date",
            width=150
        )

        for i in range(20):

            self.email_tree.insert(
                "",
                "end",
                values=(
                    f"Professor {i}",
                    f"Assignment Reminder {i}",
                    "Today"
                )
            )

        self.email_tree.pack(
            fill="both",
            expand=True
        )

        self.content.add(
            self.email_frame,
            weight=2
        )

    # ==================================================
    # EMAIL VIEWER
    # ==================================================

    def build_email_viewer(self):

        self.viewer_frame = ttk.Frame(
            self.content
        )

        self.subject_label = ttk.Label(
            self.viewer_frame,
            text="CS101 Assignment Reminder",
            font=(
                "Segoe UI",
                16,
                "bold"
            )
        )

        self.subject_label.pack(
            anchor="w",
            padx=15,
            pady=(15, 0)
        )

        self.from_label = ttk.Label(
            self.viewer_frame,
            text="professor@iitb.ac.in"
        )

        self.from_label.pack(
            anchor="w",
            padx=15
        )

        self.date_label = ttk.Label(
            self.viewer_frame,
            text="Today"
        )

        self.date_label.pack(
            anchor="w",
            padx=15,
            pady=(0, 10)
        )

        ttk.Separator(
            self.viewer_frame
        ).pack(
            fill="x",
            padx=15
        )

        self.body = tk.Text(
            self.viewer_frame,
            wrap="word"
        )

        self.body.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=15
        )

        self.body.insert(
            "1.0",
            "Email contents appear here..."
        )

        self.content.add(
            self.viewer_frame,
            weight=4
        )

    # ==================================================
    # STATUS BAR
    # ==================================================

    def build_statusbar(self):

        self.status = ttk.Label(
            self.root,
            text="Connected | INBOX | 20 emails",
            anchor="w"
        )

        self.status.pack(
            fill="x"
        )

    # ==================================================
    # THEME
    # ==================================================

    def toggle_theme(self):

        if not HAS_THEME:
            return

        self.dark_mode = not self.dark_mode

        if self.dark_mode:
            sv_ttk.set_theme("dark")
            self.theme_btn.config(text="🌙")
        else:
            sv_ttk.set_theme("light")
            self.theme_btn.config(text="☀")

    # ==================================================
    # RUN
    # ==================================================

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":

    app = WebmailApp()
    app.run()