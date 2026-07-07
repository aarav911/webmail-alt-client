import os
import sys
import html
import json
import tkinter as tk
from email import policy
from email.parser import BytesParser, HeaderParser
from concurrent.futures import ThreadPoolExecutor
import customtkinter as ctk
from tkinterweb import HtmlFrame

# Config File Location
CONFIG_FILE = "webmail_config.json"

try:
    from backend import MailBackend
except ImportError:
    class MailBackend:
        def __init__(self):
            self.token = ""
            self.email_address = ""
        def connect(self): 
            return True, "Connected"
        def get_mailboxes(self): 
            return ["INBOX", "Sent", "Drafts", "Trash"]
        def fetch_latest_headers(self, name, limit): 
            return []
        def save_credentials(self, e, t):
            self.email_address = e
            self.token = t
            with open(CONFIG_FILE, "w") as f:
                json.dump({"email": e, "token": t}, f)
        def load_credentials(self):
            if os.path.exists(CONFIG_FILE):
                try:
                    with open(CONFIG_FILE, "r") as f:
                        data = json.load(f)
                        self.email_address = data.get("email", "")
                        self.token = data.get("token", "")
                        return True
                except:
                    pass
            return False

# App Configuration Styles Optimization
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

FONT_FAMILY = "Segoe UI"
FONT_TITLE = (FONT_FAMILY, 22, "bold")
FONT_SUBTITLE = (FONT_FAMILY, 14, "italic")
FONT_HEADER = (FONT_FAMILY, 13, "bold")
FONT_BODY = (FONT_FAMILY, 14)
FONT_INTERFACE = (FONT_FAMILY, 13)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# ==============================================================================
# SETTINGS MODAL (FOR POST-SETUP CHANGES)
# ==============================================================================

class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, current_email, current_token):
        super().__init__(parent)
        self.title(title)
        self.geometry("500x280")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self.current_email = current_email
        self.current_token = current_token
        self.result = None

        frame = ctk.CTkFrame(self, corner_radius=16)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="IITB Email Address:", font=(FONT_FAMILY, 13, "bold")).grid(row=0, column=0, sticky="w", pady=(20, 8), padx=20)
        self.email_entry = ctk.CTkEntry(frame, width=260, font=FONT_INTERFACE, height=35)
        self.email_entry.insert(0, self.current_email)
        self.email_entry.grid(row=0, column=1, pady=(20, 8), padx=20)

        ctk.CTkLabel(frame, text="SSO Access Token:", font=(FONT_FAMILY, 13, "bold")).grid(row=1, column=0, sticky="w", pady=8, padx=20)
        self.token_entry = ctk.CTkEntry(frame, width=260, show="*", font=FONT_INTERFACE, height=35)
        self.token_entry.insert(0, self.current_token)
        self.token_entry.grid(row=1, column=1, pady=8, padx=20)
        
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, columnspan=2, pady=(25, 10), sticky="nsew")
        
        ctk.CTkButton(btn_frame, text="Save Settings", font=FONT_INTERFACE, width=130, height=35, command=self.apply).pack(side="right", padx=20)
        ctk.CTkButton(btn_frame, text="Cancel", font=FONT_INTERFACE, fg_color="gray", hover_color="#555555", width=100, height=35, command=self.destroy).pack(side="right")

        self.wait_window(self)

    def apply(self):
        self.result = (self.email_entry.get().strip(), self.token_entry.get().strip())
        self.destroy()


# ==============================================================================
# MAIN APPLICATION ENGINE WITH SETUP WIZARD
# ==============================================================================

class WebmailApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Webmail Alt Pro")
        self.root.geometry("1550x950")
        self.root.minsize(1150, 750)

        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):        
            try: self.root.iconbitmap(icon_path)
            except Exception: pass

        self.backend = MailBackend()
        self.current_emails = []
        self.selected_mailbox = ""
        self.current_email = None
        self.executor = ThreadPoolExecutor(max_workers=2)

        # Check if setup config exists natively
        has_config = self.backend.load_credentials()

        if not has_config or not self.backend.token:
            # First time user routing sequence -> Show Setup Screen
            self.build_setup_screen()
        else:
            # Config found -> Go straight to client
            self.initialize_main_client_ui()

    def start_async_task(self, target_func, *args):
        self.executor.submit(target_func, *args)

    def safe_ui_update(self, update_func, *args):
        self.root.after(0, update_func, *args)

    # --------------------------------------------------------------------------
    # FIRST TIME SETUP SCREEN LAYOUT
    # --------------------------------------------------------------------------
    def build_setup_screen(self):
        """Creates a modern center-aligned configuration welcome screen wrapper."""
        # Pass width and height right here inside the constructor
        self.setup_frame = ctk.CTkFrame(
            self.root, 
            width=550, 
            height=450, 
            corner_radius=24, 
            fg_color=("#F5F5F5", "#1E1E1E")
        )
        # Keep .place() clean of explicit width/height parameters
        self.setup_frame.place(relx=0.5, rely=0.5, anchor="center")
        # Decorative/Welcome Header Elements
        lbl_welcome = ctk.CTkLabel(self.setup_frame, text="Welcome to Webmail Alt", font=(FONT_FAMILY, 24, "bold"))
        lbl_welcome.pack(pady=(40, 5))
        
        lbl_hint = ctk.CTkLabel(self.setup_frame, text="Please complete initialization setup to link your environment.", font=(FONT_FAMILY, 12), text_color="gray")
        lbl_hint.pack(pady=(0, 30))

        # Forms Containers Block
        form_container = ctk.CTkFrame(self.setup_frame, fg_color="transparent")
        form_container.pack(fill="x", padx=40)

        ctk.CTkLabel(form_container, text="IITB Email Address", font=(FONT_FAMILY, 12, "bold"), text_color=("#333333", "#AAAAAA")).pack(anchor="w", pady=(5, 2))
        self.setup_email = ctk.CTkEntry(form_container, height=40, placeholder_text="e.g., rollnumber@iitb.ac.in", font=FONT_INTERFACE)
        self.setup_email.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(form_container, text="SSO Access Token", font=(FONT_FAMILY, 12, "bold"), text_color=("#333333", "#AAAAAA")).pack(anchor="w", pady=(5, 2))
        self.setup_token = ctk.CTkEntry(form_container, height=40, show="*", placeholder_text="Paste your secure SSO verification string", font=FONT_INTERFACE)
        self.setup_token.pack(fill="x", pady=(0, 25))

        self.btn_finish_setup = ctk.CTkButton(self.setup_frame, text="Complete Installation →", height=45, font=(FONT_FAMILY, 13, "bold"), command=self.process_initial_setup)
        self.btn_finish_setup.pack(fill="x", padx=40, pady=10)

    def process_initial_setup(self):
        email = self.setup_email.get().strip()
        token = self.setup_token.get().strip()

        if not email or not token:
            self.setup_email.configure(border_color="red")
            self.setup_token.configure(border_color="red")
            return

        # Save setup parameters cleanly
        self.backend.save_credentials(email, token)

        # Smooth transition effect: Destroy onboarding overlay & instantiate system vectors
        self.setup_frame.destroy()
        
        # Staging structural UI grids
        self.initialize_main_client_ui()

    # --------------------------------------------------------------------------
    # CORE INTERFACE INITIALIZATION
    # --------------------------------------------------------------------------
    def initialize_main_client_ui(self):
        """Assembles standard core multi-pane dynamic workspace layout view grid models."""
        self.root.grid_columnconfigure(0, weight=1) 
        self.root.grid_columnconfigure(1, weight=3) 
        self.root.grid_columnconfigure(2, weight=5) 
        self.root.grid_rowconfigure(1, weight=1)    

        self.build_toolbar()
        self.build_sidebar()
        self.build_email_list()
        self.build_email_viewer()
        self.build_statusbar()

        # Connect session directly
        self.start_async_task(self.initialize_mail_session)

    def initialize_mail_session(self):
        self.safe_ui_update(self.set_status, "Asynchronously linking connection paths...")
        success, info = self.backend.connect()
        
        if success:
            self.safe_ui_update(self.set_status, "Synchronizing folder system...")
            boxes = self.backend.get_mailboxes()
            self.safe_ui_update(self.update_sidebar_list, boxes)
        else:
            self.safe_ui_update(self.set_status, f"Authentication Refused: {info}")

    def update_sidebar_list(self, folders):
        for widget in self.scrollable_sidebar.winfo_children():
            widget.destroy()

        for box in folders:
            btn = ctk.CTkButton(
                self.scrollable_sidebar, 
                text=f"📁   {box}", 
                anchor="w", 
                font=FONT_INTERFACE,
                height=38,
                fg_color="transparent", 
                text_color=("black", "white"),
                hover_color=("#E0E0E0", "#2B2B2B"),
                command=lambda name=box: self.on_mailbox_selected(name)
            )
            btn.pack(fill="x", pady=3, padx=8)
        self.set_status("Ready.")

    def on_mailbox_selected(self, mailbox_name):
        self.selected_mailbox = mailbox_name
        self.set_status(f"Fetching updates from '{self.selected_mailbox}' headers table...")
        self.start_async_task(self._bg_load_mailbox, self.selected_mailbox)

    def _bg_load_mailbox(self, mailbox_name):
        self.current_emails = self.backend.fetch_latest_headers(mailbox_name, limit=30)
        self.safe_ui_update(self._ui_render_email_tree, mailbox_name)

    def _ui_render_email_tree(self, mailbox_name):
        for widget in self.scrollable_tree.winfo_children():
            widget.destroy()
            
        for idx, email in enumerate(self.current_emails):
            mail_card = ctk.CTkFrame(self.scrollable_tree, fg_color=("#F5F5F5", "#202020"), corner_radius=8)
            mail_card.pack(fill="x", pady=6, padx=8)
            
            lbl_from = ctk.CTkLabel(mail_card, text=email.sender, font=(FONT_FAMILY, 13, "bold"), anchor="w")
            lbl_from.pack(fill="x", padx=12, pady=(8, 2))
            
            lbl_sub = ctk.CTkLabel(mail_card, text=email.subject, font=(FONT_FAMILY, 13), anchor="w", wraplength=300)
            lbl_sub.pack(fill="x", padx=12, pady=2)
            
            lbl_date = ctk.CTkLabel(mail_card, text=email.date, font=(FONT_FAMILY, 11), text_color="gray", anchor="e")
            lbl_date.pack(fill="x", padx=12, pady=(2, 8))

            for component in (mail_card, lbl_from, lbl_sub, lbl_date):
                component.bind("<Button-1>", lambda event, i=idx: self.on_email_selected(i))
                
        self.set_status(f"Loaded {len(self.current_emails)} records inside '{mailbox_name}'.")

    def on_email_selected(self, index):
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
        self.subject_label.configure(text=email.subject)
        self.from_label.configure(text=f"From: {email.sender}")
        self.date_label.configure(text=f"Date: {email.date}")

        self.current_email = email
        is_dark = (ctk.get_appearance_mode() == "Dark")

        if hasattr(email, 'html_body') and email.html_body:
            render_content = email.html_body
        elif hasattr(email, 'text_body') and email.text_body:
            render_content = f"<html><body><pre style='font-family: sans-serif; font-size: 14px; white-space: pre-wrap;'>{html.escape(email.text_body)}</pre></body></html>"
        else:
            render_content = "<html><body><p style='color: gray; font-style: italic; font-size: 14px;'>No displayable payload variants found.</p></body></html>"
        
        themed_content = self.parse_and_thematize_html(render_content, is_dark)

        try:
            self.body.load_html(themed_content)
        except AttributeError:
            self.body.set_html(themed_content)
            
        self.animate_view_reveal()
        self.set_status("Done.")

    def animate_view_reveal(self):
        self.html_container.configure(fg_color=("#EAEAEA", "#252525"))
        def reset_bg():
            self.html_container.configure(fg_color="transparent")
        self.root.after(120, reset_bg)

    def parse_and_thematize_html(self, html_content, is_dark_mode):
        if not html_content: return ""
        bg_color = "#1a1a1a" if is_dark_mode else "#ffffff"
        text_color = "#f5f5f5" if is_dark_mode else "#1a1a1a"
        accent_link = "#4a9eff" if is_dark_mode else "#0066cc"
        
        theme_css = f"""
        <style>
            html, body, table, td, div, span, p {{
                background-color: {bg_color} !important;
                color: {text_color} !important;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 15px;
                line-height: 1.6;
            }}
            a {{
                color: {accent_link} !important;
                text-decoration: underline !important;
            }}
            img, video {{
                opacity: { '0.85' if is_dark_mode else '1.0' } !important;
                filter: { 'brightness(0.8) contrast(1.1)' if is_dark_mode else 'none' } !important;
            }}
            pre {{
                background-color: { '#2d2d2d' if is_dark_mode else '#f4f4f4' } !important;
                color: {text_color} !important;
                padding: 12px;
                border-radius: 6px;
                font-size: 14px;
                white-space: pre-wrap;
            }}
        </style>
        """
        if "<body" not in html_content.lower():
            html_content = f"<html><body>{html_content}</body></html>"
            
        body_idx = html_content.lower().find("<body")
        if body_idx != -1:
            closing_bracket_idx = html_content.find(">", body_idx)
            if closing_bracket_idx != -1:
                return html_content[:closing_bracket_idx+1] + theme_css + html_content[closing_bracket_idx+1:]
                
        return theme_css + html_content

    def get_blank_themed_page(self, is_dark_mode):
        bg_color = "#1a1a1a" if is_dark_mode else "#ffffff"
        text_color = "#f5f5f5" if is_dark_mode else "#1a1a1a"
        return f"<html><head><style>html,body{{margin:0;padding:0;background-color:{bg_color};color:{text_color};overflow:hidden;}}</style></head><body></body></html>"

    def prompt_credentials_setup(self):
        dialog = SettingsDialog(self.root, "Authentication Settings", self.backend.email_address, self.backend.token)
        if dialog.result:
            email, token = dialog.result
            if email and token:
                self.backend.save_credentials(email, token)
                self.start_async_task(self.initialize_mail_session)

    # --------------------------------------------------------------------------
    # LAYOUT STAGING PANE BUILDERS
    # --------------------------------------------------------------------------
    def build_toolbar(self):
        self.toolbar = ctk.CTkFrame(self.root, height=60, corner_radius=0)
        self.toolbar.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=0, pady=(0, 2))
        
        btn_refresh = ctk.CTkButton(self.toolbar, text="🔄  Refresh", font=FONT_INTERFACE, width=120, height=38, command=lambda: self.start_async_task(self._bg_load_mailbox, self.selected_mailbox) if self.selected_mailbox else None)
        btn_refresh.pack(side="left", padx=15, pady=10)
        
        btn_settings = ctk.CTkButton(self.toolbar, text="⚙  Settings", font=FONT_INTERFACE, width=120, height=38, fg_color=("#DBDBDB", "#2B2B2B"), text_color=("black", "white"), hover_color=("#CDCDCD", "#3A3A3A"), command=self.prompt_credentials_setup)
        btn_settings.pack(side="left", padx=5, pady=10)

        self.theme_btn = ctk.CTkButton(self.toolbar, text="🌙  Dark Mode", font=FONT_INTERFACE, width=110, height=38, command=self.toggle_theme)
        self.theme_btn.pack(side="right", padx=15, pady=10)

        self.search_entry = ctk.CTkEntry(self.toolbar, width=320, height=38, font=FONT_INTERFACE, placeholder_text="Search mail entries...")
        self.search_entry.pack(side="right", padx=10, pady=10)

    def build_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self.root, corner_radius=0)
        self.sidebar_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 2))
        
        lbl = ctk.CTkLabel(self.sidebar_frame, text="MAILBOXES", font=FONT_HEADER, text_color="gray")
        lbl.pack(anchor="w", padx=18, pady=(18, 8))
        
        self.scrollable_sidebar = ctk.CTkScrollableFrame(self.sidebar_frame, fg_color="transparent")
        self.scrollable_sidebar.pack(fill="both", expand=True, padx=5, pady=5)

    def build_email_list(self):
        self.list_frame = ctk.CTkFrame(self.root, corner_radius=0)
        self.list_frame.grid(row=1, column=1, sticky="nsew", padx=(0, 2))
        
        lbl = ctk.CTkLabel(self.list_frame, text="MESSAGES INDEX", font=FONT_HEADER, text_color="gray")
        lbl.pack(anchor="w", padx=18, pady=(18, 8))

        self.scrollable_tree = ctk.CTkScrollableFrame(self.list_frame, fg_color="transparent")
        self.scrollable_tree.pack(fill="both", expand=True, padx=5, pady=5)

    def build_email_viewer(self):
        self.viewer_frame = ctk.CTkFrame(self.root, corner_radius=0, fg_color=("#FFFFFF", "#1A1A1A"))
        self.viewer_frame.grid(row=1, column=2, sticky="nsew")
        
        self.subject_label = ctk.CTkLabel(self.viewer_frame, text="No message selected", font=FONT_TITLE, anchor="w", wraplength=650)
        self.subject_label.pack(fill="x", padx=25, pady=(25, 4))

        self.from_label = ctk.CTkLabel(self.viewer_frame, text="", font=FONT_SUBTITLE, text_color="gray", anchor="w")
        self.from_label.pack(fill="x", padx=25, pady=2)

        self.date_label = ctk.CTkLabel(self.viewer_frame, text="", font=(FONT_FAMILY, 12), text_color="gray", anchor="w")
        self.date_label.pack(fill="x", padx=25, pady=(0, 20))

        self.html_container = ctk.CTkFrame(self.viewer_frame, fg_color="transparent", corner_radius=12)
        self.html_container.pack(fill="both", expand=True, padx=20, pady=20)

        self.body = HtmlFrame(self.html_container, messages_enabled=False)
        self.body.pack(fill="both", expand=True, padx=2, pady=2)
        self.body.load_html(self.get_blank_themed_page(ctk.get_appearance_mode() == "Dark"))

    def build_statusbar(self):
        self.status_bar = ctk.CTkFrame(self.root, height=28, corner_radius=0)
        self.status_bar.grid(row=2, column=0, columnspan=3, sticky="nsew", pady=(2, 0))
        
        self.status = ctk.CTkLabel(self.status_bar, text="Status: Ready.", font=(FONT_FAMILY, 12), text_color="gray")
        self.status.pack(side="left", padx=15, pady=3)

    def set_status(self, message):
        self.status.configure(text="Status: " + message)

    def toggle_theme(self):
        if ctk.get_appearance_mode() == "Dark":
            ctk.set_appearance_mode("Light")
            self.theme_btn.configure(text="☀  Light Mode")
        else:
            ctk.set_appearance_mode("Dark")
            self.theme_btn.configure(text="🌙  Dark Mode")
            
        if self.current_email:
            self._ui_display_email_body(self.current_email)
        else:
            self.body.load_html(self.get_blank_themed_page(ctk.get_appearance_mode() == "Dark"))

    def run(self):
        try:
            self.root.mainloop()
        finally:
            self.executor.shutdown(wait=False)
            if hasattr(self.backend, 'mail') and self.backend.mail:
                try: self.backend.mail.logout()
                except: pass


if __name__ == "__main__":
    app = WebmailApp()
    app.run()