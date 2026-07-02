import tkinter as tk

def _on_mousewheel(event):
    # Windows/macOS: Divide delta by 120 for reasonable speed
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

def _on_linux_scroll(event):
    # Linux: Button-4 is up, Button-5 is down
    if event.num == 4:
        canvas.yview_scroll(-1, "units")
    elif event.num == 5:
        canvas.yview_scroll(1, "units")

def _bind_to_mousewheel(event):
    # Bind based on platform when mouse enters the frame
    if canvas.winfo_toplevel().tk.call('tk', 'windowingsystem') == 'x11':
        canvas.bind_all("<Button-4>", _on_linux_scroll)
        canvas.bind_all("<Button-5>", _on_linux_scroll)
    else:
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

def _unbind_from_mousewheel(event):
    # Unbind when mouse leaves to avoid conflicting scrolls
    if canvas.winfo_toplevel().tk.call('tk', 'windowingsystem') == 'x11':
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")
    else:
        canvas.unbind_all("<MouseWheel>")

root = tk.Tk()
canvas = tk.Canvas(root)
scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas)

scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

# --- Add these bindings for mouse wheel support ---
scrollable_frame.bind("<Enter>", _bind_to_mousewheel)
scrollable_frame.bind("<Leave>", _unbind_from_mousewheel)
# --------------------------------------------------

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

for i in range(50):
    tk.Label(scrollable_frame, text=f"Label {i}").pack()

root.mainloop()   