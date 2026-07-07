import customtkinter as ctk
from tkinter import messagebox

# Setup appearance
ctk.set_appearance_mode("dark")  # Modes: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue", "green", "dark-blue"

class ModernInstallApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Setup Wizard")
        self.geometry("600x450")
        self.resizable(False, False)

        # Grid layout config
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.frames = {}
        for F in (WelcomeFrame, ConfigFrame, ProgressFrame):
            frame = F(self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(WelcomeFrame)

    def show_frame(self, cont):
        self.frames[cont].tkraise()

class WelcomeFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self, text="Welcome", font=("Arial", 24, "bold")).pack(pady=40)
        ctk.CTkLabel(self, text="Professional Installation Wizard", text_color="gray").pack(pady=(0, 40))
        
        ctk.CTkButton(self, text="Next", width=150, command=lambda: parent.show_frame(ConfigFrame)).pack()

class ConfigFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self, text="Configuration", font=("Arial", 20, "bold")).pack(pady=20)
        
        # Modern Entry with placeholder
        self.path_entry = ctk.CTkEntry(self, placeholder_text="C:\\Program Files\\App", width=300)
        self.path_entry.pack(pady=10)
        self.path_entry.insert(0, "C:\\Program Files\\MyApp")
        
        self.user_entry = ctk.CTkEntry(self, placeholder_text="Username", width=300)
        self.user_entry.pack(pady=10)
        
        # Modern Switch instead of Checkbox
        self.switch_var = ctk.StringVar(value="on")
        ctk.CTkSwitch(self, text="Create Desktop Shortcut", variable=self.switch_var).pack(pady=20)
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text="Back", width=100, command=lambda: parent.show_frame(WelcomeFrame)).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Install", width=100, fg_color="green", hover_color="darkgreen", 
                      command=lambda: self.start_install(parent)).pack(side="left", padx=10)

    def start_install(self, parent):
        if not self.user_entry.get():
            messagebox.showerror("Error", "Username is required")
            return
        parent.show_frame(ProgressFrame)

class ProgressFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self, text="Installing...", font=("Arial", 20, "bold")).pack(pady=20)
        
        self.progress = ctk.CTkProgressBar(self, width=300)
        self.progress.pack(pady=20)
        self.progress.set(0)
        
        # Simulate installation
        self.after(500, self.update_progress)

    def update_progress(self):
        # Simple animation logic
        current = self.progress.get()
        if current < 1.0:
            self.progress.set(current + 0.1)
            self.after(200, self.update_progress)
        else:
            ctk.CTkLabel(self, text="Complete!", text_color="green").pack(pady=10)
            ctk.CTkButton(self, text="Finish", command=self.quit).pack(pady=20)

if __name__ == "__main__":
    app = ModernInstallApp()
    app.mainloop()   
    