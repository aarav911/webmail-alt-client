import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from email import policy
from email.parser import BytesParser, HeaderParser
from concurrent.futures import ThreadPoolExecutor
from backend import MailBackend
from tkinterweb import HtmlFrame
import html

try:
    import sv_ttk
    HAS_THEME = True
except ImportError:
    HAS_THEME = False

CONFIG_FILE = "webmail_config.json"

# Helper
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# ==============================================================================
# FRONTEND WINDOWS & CONFIG INTERACTIVE DESIGN
# ==============================================================================

class SettingsDialog(simpledialog.Dialog):
    """Clean Tkinter form window layout matching native desktop frameworks."""
    def __init__(self, parent, title, current_email, current_token):
        self.current_email = current_email
        self.current_token = current_token
        self.result = None
        super().__init__(parent, title)

    def body(self, master):
        ttk.Label(master, text="IITB Email Address:").grid(row=0, column=0, sticky="w", pady=5, padx=5)
        self.email_entry = ttk.Entry(master, width=35)
        self.email_entry.insert(0, self.current_email)
        self.email_entry.grid(row=0, column=1, pady=5, padx=5)

        ttk.Label(master, text="SSO Access Token:").grid(row=1, column=0, sticky="w", pady=5, padx=5)
        self.token_entry = ttk.Entry(master, width=35, show="*")
        self.token_entry.insert(0, self.current_token)
        self.token_entry.grid(row=1, column=1, pady=5, padx=5)
        return self.email_entry

    def apply(self):
        self.result = (self.email_entry.get().strip(), self.token_entry.get().strip())


class WebmailApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Webmail Alt")
        self.root.geometry("1500x900")
        self.dark_mode = True

        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):        
            icon = tk.PhotoImage(icon_path)
            self.root.iconphoto(True, icon)
        else: 
            print(f"Error: Icon not found at {icon_path}")

        self.backend = MailBackend()
        self.current_emails = []
        self.selected_mailbox = ""
        self.current_email = None

        # Thread scheduler execution pooling engine
        self.executor = ThreadPoolExecutor(max_workers=2)

        if HAS_THEME:
            sv_ttk.set_theme("dark")

        self.build_toolbar()
        self.build_main_area()
        self.build_statusbar()

        # Start asynchronous non-blocking boot sequence
        self.start_async_task(self.initialize_mail_session)

    # --------------------------------------------------------------------------
    # THREADING MANAGEMENT HOOKS
    # --------------------------------------------------------------------------
    def start_async_task(self, target_func, *args):
        """Dispatches tasks to the background thread pool so the UI never freezes."""
        self.executor.submit(target_func, *args)

    def safe_ui_update(self, update_func, *args):
        """Schedules safe graphical updates back to the main GUI thread loop."""
        self.root.after(0, update_func, *args)

    # --------------------------------------------------------------------------
    # CORE INTERACTIVE LOGIC PIPELINES
    # --------------------------------------------------------------------------
    def initialize_mail_session(self):
        if not self.backend.token:
            self.safe_ui_update(self.set_status, "Awaiting credentials initialization. Open Settings.")
            self.safe_ui_update(self.prompt_credentials_setup)
            return

        self.safe_ui_update(self.set_status, "Asynchronously linking connection paths...")
        success, info = self.backend.connect()
        
        if success:
            self.safe_ui_update(self.set_status, "Synchronizing folder system...")
            boxes = self.backend.get_mailboxes()
            self.safe_ui_update(self.update_sidebar_list, boxes)
        else:
            self.safe_ui_update(self.set_status, f"Authentication Refused: {info}")

    def prompt_credentials_setup(self):
        dialog = SettingsDialog(self.root, "Authentication Settings", self.backend.email_address, self.backend.token)
        if dialog.result:
            email, token = dialog.result
            if email and token:
                self.backend.save_credentials(email, token)
                self.start_async_task(self.initialize_mail_session)

    def update_sidebar_list(self, folders):
        self.mailbox_list.delete(0, "end")
        for box in folders:
            self.mailbox_list.insert("end", box)
        self.set_status("Ready.")

    def on_mailbox_selected(self, event):
        selection = self.mailbox_list.curselection()
        if not selection: return
        
        self.selected_mailbox = self.mailbox_list.get(selection[0])
        self.set_status(f"Fetching updates from '{self.selected_mailbox}' headers table...")
        
        # Dispatch fetch to background thread
        self.start_async_task(self._bg_load_mailbox, self.selected_mailbox)

    def _bg_load_mailbox(self, mailbox_name):
        # High speed fetch: handles headers only!
        self.current_emails = self.backend.fetch_latest_headers(mailbox_name, limit=30)
        self.safe_ui_update(self._ui_render_email_tree, mailbox_name)

    def _ui_render_email_tree(self, mailbox_name):
        for item in self.email_tree.get_children():
            self.email_tree.delete(item)
            
        for idx, email in enumerate(self.current_emails):
            self.email_tree.insert("", "end", iid=str(idx), values=(email.sender, email.subject, email.date))
            
        self.set_status(f"Loaded summary index fields for {len(self.current_emails)} records inside '{mailbox_name}'.")

    def on_email_selected(self, event):
        selection = self.email_tree.selection()
        if not selection: return
        
        index = int(selection[0])
        email = self.current_emails[index]
        
        if not email.loaded:
            self.set_status("Streaming email body segments from IMAP host source...")
            self.start_async_task(self._bg_load_full_body, index)
        else:
            self._ui_display_email_body(email)

    def _bg_load_full_body(self, index):
        email = self.current_emails[index]
        updated_email = self.backend.load_full_body(self.selected_mailbox, email)
        self.current_emails[index] = updated_email
        self.safe_ui_update(self._ui_display_email_body, updated_email)

    def _ui_display_email_body(self, email):
        self.subject_label.config(text=email.subject)
        self.from_label.config(text=f"From: {email.sender}")
        self.date_label.config(text=f"Date: {email.date}")

        self.current_email = email

        
        # Determine the best rendering payload
        if hasattr(email, 'html_body') and email.html_body:
            render_content = email.html_body
        elif hasattr(email, 'text_body') and email.text_body:
            # Clean text format and render inside plain text styles within the HTML frame
            # sanitized = email.text_body.replace("\r\n", "\n").replace("\r", "\n")
            render_content = f"<html><body><pre style='font-family: sans-serif; white-space: pre-wrap;'>{html.escape(email.text_body)}</pre></body></html>"
        else:
            render_content = "<html><body><p style='color: gray; font-style: italic;'>No displayable payload variants found.</p></body></html>"
        
        # Load content into the TkinterWeb structural HTML pane

        themed_content = self.parse_and_thematize_html(render_content, self.dark_mode)

        try:
            self.body.load_html(themed_content)
        except AttributeError:
            self.body.set_html(themed_content)
            
        self.set_status("Done.")


    def parse_and_thematize_html(self, html_content, is_dark_mode):
        """
        Sanitizes and wraps an HTML body with programmatic theme-overriding 
        CSS directives without destroying explicit tabular structures.
        """
        if not html_content:
            return ""
            
        # Standard CSS Variables mapping for UI parity
        bg_color = "#1e1e1e" if is_dark_mode else "#ffffff"
        text_color = "#f5f5f5" if is_dark_mode else "#1a1a1a"
        accent_link = "#4a9eff" if is_dark_mode else "#0066cc"
        
        # CSS Injected Reset Rule Block
        theme_css = f"""
        <style>
            /* Force structural base colors */
            html, body, table, td, div, span, p {{
                background-color: {bg_color} !important;
                color: {text_color} !important;
            }}
            
            /* Ensure links remain visible and high-contrast */
            a {{
                color: {accent_link} !important;
                text-decoration: underline !important;
            }}
            
            /* Prevent nested images from acting like flashbangs */
            img, video {{
                opacity: { '0.85' if is_dark_mode else '1.0' } !important;
                filter: { 'brightness(0.8) contrast(1.1)' if is_dark_mode else 'none' } !important;
            }}
            
            /* Keep formatted plain text structures aligned */
            pre {{
                background-color: { '#2d2d2d' if is_dark_mode else '#f4f4f4' } !important;
                color: {text_color} !important;
                padding: 10px;
                border-radius: 4px;
                white-space: pre-wrap;
            }}
        </style>
        """
        
        # If the email lacks structural wrapper tags, supply a baseline layout
        if "<body" not in html_content.lower():
            html_content = f"<html><body>{html_content}</body></html>"
            
        # Dynamically inject our style payload directly behind the body open tag
        # to override inline presentation declarations down the DOM tree tree structure.
        body_idx = html_content.lower().find("<body")
        if body_idx != -1:
            # Find the end of the opening body tag (handling arbitrary element attributes)
            closing_bracket_idx = html_content.find(">", body_idx)
            if closing_bracket_idx != -1:
                return html_content[:closing_bracket_idx+1] + theme_css + html_content[closing_bracket_idx+1:]
                
        return theme_css + html_content
    def get_blank_themed_page(self, is_dark_mode):
        bg_color = "#1e1e1e" if is_dark_mode else "#ffffff"
        text_color = "#f5f5f5" if is_dark_mode else "#1a1a1a"

        return f"""
        <html>
        <head>
            <style>
                html, body {{
                    margin: 0;
                    padding: 0;
                    width: 100%;
                    height: 100%;
                    background-color: {bg_color};
                    color: {text_color};
                    overflow: hidden;
                }}
            </style>
        </head>
        <body>
        </body>
        </html>
        """
    # --------------------------------------------------------------------------
    # WINDOW ASSEMBLY METHOD WRAPPERS
    # --------------------------------------------------------------------------
    def build_toolbar(self):
        self.toolbar = ttk.Frame(self.root, padding=8)
        self.toolbar.pack(fill="x")

        ttk.Button(self.toolbar, text="Refresh", command=lambda: self.start_async_task(self._bg_load_mailbox, self.selected_mailbox) if self.selected_mailbox else None).pack(side="left", padx=2)
        ttk.Button(self.toolbar, text="Settings ⚙", command=self.prompt_credentials_setup).pack(side="left", padx=2)

        self.search_entry = ttk.Entry(self.toolbar, width=40)
        self.search_entry.pack(side="right", padx=10)

        self.theme_btn = ttk.Button(self.toolbar, text="🌙", command=self.toggle_theme)
        self.theme_btn.pack(side="right")
        ttk.Separator(self.root).pack(fill="x")

    def build_main_area(self):
        self.main = ttk.PanedWindow(self.root, orient="horizontal")
        self.main.pack(fill="both", expand=True)
        self.build_sidebar()
        self.build_content_area()

    def build_sidebar(self):
        self.sidebar = ttk.Frame(self.main)
        ttk.Label(self.sidebar, text="MAILBOXES", font=("Noto Sans", 10, "bold")).pack(anchor="w", padx=10, pady=10)

        self.mailbox_list = tk.Listbox(self.sidebar, activestyle="none", selectmode="single")
        self.mailbox_list.pack(fill="both", expand=True, padx=5, pady=5)
        self.mailbox_list.bind("<<ListboxSelect>>", self.on_mailbox_selected)

        self.main.add(self.sidebar, weight=1)

    def build_content_area(self):
        self.content = ttk.PanedWindow(self.main, orient="vertical")
        self.main.add(self.content, weight=5)
        self.build_email_list()
        self.build_email_viewer()

    def build_email_list(self):
        self.email_frame = ttk.Frame(self.content)
        columns = ("from", "subject", "date")
        
        self.email_tree = ttk.Treeview(self.email_frame, columns=columns, show="headings")
        self.email_tree.heading("from", text="From")
        self.email_tree.heading("subject", text="Subject")
        self.email_tree.heading("date", text="Date")
        
        self.email_tree.column("from", width=220)
        self.email_tree.column("subject", width=600)
        self.email_tree.column("date", width=180)
        
        self.email_tree.bind("<<TreeviewSelect>>", self.on_email_selected)
        self.email_tree.pack(fill="both", expand=True)
        self.content.add(self.email_frame, weight=2)

    def build_email_viewer(self):
        self.viewer_frame = ttk.Frame(self.content)
        self.subject_label = ttk.Label(self.viewer_frame, text="", font=("Noto Sans", 14, "bold"))
        self.subject_label.pack(anchor="w", padx=15, pady=(15, 2))

        self.from_label = ttk.Label(self.viewer_frame, text="", font=("Noto Sans", 10, "italic"))
        self.from_label.pack(anchor="w", padx=15, pady=2)

        self.date_label = ttk.Label(self.viewer_frame, text="", font=("Noto Sans", 9))
        self.date_label.pack(anchor="w", padx=15, pady=(0, 10))

        ttk.Separator(self.viewer_frame).pack(fill="x", padx=15)

        self.body = HtmlFrame(
            self.viewer_frame,
            messages_enabled=False,
            
        )
        
        

        self.body.pack(fill="both", expand=True, padx=15, pady=15)
        self.body.load_html(
            self.get_blank_themed_page(self.dark_mode)
        )
        self.content.add(self.viewer_frame, weight=3)

    def build_statusbar(self):
        self.status = ttk.Label(self.root, text="Ready.", anchor="w", padding=4)
        self.status.pack(fill="x")

    def set_status(self, message):
        self.status.config(text=message)

    def toggle_theme(self):
        if not HAS_THEME: return
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            sv_ttk.set_theme("dark")
            self.theme_btn.config(text="🌙")
        else:
            sv_ttk.set_theme("light")
            self.theme_btn.config(text="☀")
        if self.current_email:
            self._ui_display_email_body(self.current_email)
        # if no email is there
        if not self.subject_label["text"]:
            self.body.load_html(
                self.get_blank_themed_page(self.dark_mode)
            )

    def run(self):
        try:
            self.root.mainloop()
        finally:
            self.executor.shutdown(wait=False)
            if self.backend.mail:
                try: self.backend.mail.logout()
                except: pass


if __name__ == "__main__":
    app = WebmailApp()
    app.run()