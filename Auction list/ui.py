import tkinter as tk
from tkcalendar import DateEntry
from datetime import datetime, timedelta
import subprocess
import sys
import os
from tkinter import ttk, messagebox

# ==================== CONFIG ====================
ACCENT = "#0a84ff"
BG = "#0e1117"
CARD_BG = "#1a1f27"
LOG_BG = "#111418"
FG = "#ffffff"
BORDER = "#2a2f36"
DAYS_LIMIT = 6

# ==================== MAIN WINDOW ====================
root = tk.Tk()
root.title("🚗 AutoBoli – Auction Scraper")
root.geometry("680x600")
root.resizable(False, False)
root.config(bg=BG)

# ==================== HEADER ====================
header = tk.Canvas(root, height=80, bg=BG, highlightthickness=0)
header.pack(fill="x")
header.create_rectangle(0, 0, 700, 80, fill=ACCENT)
header.create_text(340, 40, text="🚗 AutoBoli Auction Scraper",
                   font=("Segoe UI Semibold", 20), fill="white")

# ==================== CONTAINER ====================
container = tk.Frame(root, bg=BG)
container.pack(fill="both", expand=True, pady=20)

# ==================== CARD ====================
card = tk.Frame(container, bg=CARD_BG, bd=0, relief="solid")
card.pack(padx=25, pady=10, fill="both", expand=False, ipadx=10, ipady=15)
card.configure(highlightbackground=BORDER, highlightthickness=1)
card.grid_propagate(False)

# ==================== AUCTION SELECTOR ====================
auction_frame = tk.Frame(card, bg=CARD_BG)
auction_frame.pack(pady=10)
tk.Label(auction_frame, text="Select Auction:", font=("Segoe UI", 12), fg=FG, bg=CARD_BG).pack(side=tk.LEFT, padx=10)
auction_choice = ttk.Combobox(
    auction_frame,
    values=["Select Auction", "BCA", "Aston Barclay", "Manheim"],
    state="readonly",
    width=28,
    font=("Segoe UI", 10)
)
auction_choice.set("Select Auction")
auction_choice.pack(side=tk.LEFT, padx=10)

# ==================== DATE PICKER ====================
date_frame = tk.Frame(card, bg=CARD_BG)
date_frame.pack(pady=10)
today = datetime.today()
max_day = today + timedelta(days=DAYS_LIMIT)
tk.Label(date_frame, text="Select Date:", font=("Segoe UI", 12), fg=FG, bg=CARD_BG).pack(side=tk.LEFT, padx=10)
date_picker = DateEntry(date_frame, width=20, background=ACCENT, foreground="white",
                        borderwidth=2, date_pattern="yyyy-mm-dd",
                        mindate=today, maxdate=max_day, font=("Segoe UI", 10))
date_picker.pack(side=tk.LEFT, padx=10)

# ==================== SCRAPER HANDLER ====================
def start_process():
    selected_date = date_picker.get_date().strftime("%Y-%m-%dT00:00:00Z")
    selected_auction = auction_choice.get()

    if selected_auction == "Select Auction":
        messagebox.showwarning("Missing Selection", "Please select an auction first.")
        return

    log_box.insert(tk.END, f"\n📅 Date: {selected_date}\n🏷️ Auction: {selected_auction}\n🚀 Starting scraper...\n\n")
    log_box.see(tk.END)

    try:
        if selected_auction == "BCA":
            script_name = "auction_list.py"
        elif selected_auction == "Aston Barclay":
            script_name = "aston_list.py"
        elif selected_auction == "Manheim":
            script_name = "manheim_list.py"
        else:
            messagebox.showerror("Error", "Invalid auction selection!")
            return

        script_path = os.path.join(os.path.dirname(__file__), script_name)
        if not os.path.exists(script_path):
            log_box.insert(tk.END, f"❌ Script not found: {script_name}\n")
            return

        subprocess.run([sys.executable, script_path, selected_date], check=True)
        log_box.insert(tk.END, f"✅ {selected_auction} data scraped and uploaded!\n")
    except subprocess.CalledProcessError as e:
        log_box.insert(tk.END, f"❌ Error running scraper: {e}\n")

    log_box.see(tk.END)

# ==================== BUTTON (STYLISH) ====================
btn_frame = tk.Frame(card, bg=CARD_BG)
btn_frame.pack(pady=25)

def on_enter(e):
    scrape_button.config(bg="#5b3fff", activebackground="#5b3fff")
def on_leave(e):
    scrape_button.config(bg="#0a84ff", activebackground="#0a84ff")

scrape_button = tk.Button(
    btn_frame,
    text="🔍 Start Scraping",
    font=("Segoe UI Semibold", 13),
    bg="#0a84ff",
    fg="white",
    activeforeground="white",
    activebackground="#0a84ff",
    relief="flat",
    bd=0,
    padx=40,
    pady=12,
    cursor="hand2",
    command=start_process
)
scrape_button.pack(pady=5)
scrape_button.bind("<Enter>", on_enter)
scrape_button.bind("<Leave>", on_leave)

# ==================== LOG SECTION ====================
log_card = tk.Frame(container, bg=CARD_BG, bd=1, highlightbackground=BORDER, highlightthickness=1)
log_card.pack(padx=25, pady=10, fill="both", expand=True)
tk.Label(log_card, text="📜 Logs", font=("Segoe UI", 12, "bold"), fg=FG, bg=CARD_BG).pack(anchor="w", padx=15, pady=(10, 0))

log_box = tk.Text(
    log_card, height=15, width=70, wrap="word",
    font=("Consolas", 10),
    bg=LOG_BG, fg=FG, relief="flat",
    borderwidth=0,
    highlightbackground=BORDER, highlightcolor=BORDER,
    insertbackground=FG
)
log_box.pack(padx=15, pady=10, fill="both", expand=True)
log_box.insert(tk.END, "🟢 Ready to start AutoBoli Scraper...\n")

# ==================== FOOTER ====================
footer = tk.Label(root, text="© 2025 AutoBoli Automation System",
                  font=("Segoe UI", 9), fg="#888888", bg=BG)
footer.pack(side="bottom", pady=8)

# ==================== MAINLOOP ====================
root.mainloop()
