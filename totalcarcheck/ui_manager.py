import tkinter as tk
from tkinter import messagebox, filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD
import pandas as pd
import os
import time
from scrape_backend import login_totalcarcheck, fetch_vehicle_info  # backend functions

if not os.path.exists("done"):
    os.makedirs("done")


class CSVManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Total Car Check Scraper")
        self.root.geometry("700x500")

        tk.Label(root, text="Total Car Check Scraper", font=("Arial", 16)).pack(pady=10)

        # Login Frame
        login_frame = tk.Frame(root)
        login_frame.pack(pady=5)
        tk.Label(login_frame, text="Email:").grid(row=0, column=0, padx=5, sticky="e")
        tk.Label(login_frame, text="Password:").grid(row=1, column=0, padx=5, sticky="e")

        self.email_var = tk.StringVar(value="sultanmirza0501@icloud.com")  # default email
        self.pass_var = tk.StringVar(value="Muhssan7865")                  # default password

        tk.Entry(login_frame, textvariable=self.email_var, width=40).grid(row=0, column=1, padx=5)
        tk.Entry(login_frame, textvariable=self.pass_var, width=40, show="*").grid(row=1, column=1, padx=5)
        tk.Button(login_frame, text="Login", command=self.login_driver, bg="#2196F3", fg="white", width=15).grid(row=0, column=2, rowspan=2, padx=5)

        # CSV Drop / Listbox
        self.drop_area = tk.Label(root, text="Drop CSV files here", relief="ridge", width=70, height=5, bg="#f0f0f0")
        self.drop_area.pack(pady=10)
        self.drop_area.drop_target_register(DND_FILES)
        self.drop_area.dnd_bind('<<Drop>>', self.drop_files)

        self.listbox = tk.Listbox(root, width=80, height=10, selectmode=tk.MULTIPLE)
        self.listbox.pack(pady=10)

        # Buttons
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Browse CSV", command=self.browse_files, bg="#4CAF50", fg="white", width=15).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Remove Selected", command=self.remove_selected, bg="#f44336", fg="white", width=15).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Save Selection", command=self.save_selection, bg="#FFC107", fg="white", width=15).grid(row=0, column=2, padx=5)

        # Scrape Button (hidden until files saved)
        self.scrape_btn = tk.Button(root, text="Start Scraping", command=self.start_scraping, bg="#2196F3", fg="white", font=("Arial", 12))
        self.scrape_btn.pack(pady=15)
        self.scrape_btn.pack_forget()

        self.files = []
        self.saved_files = []
        self.driver = None
        self.logged_in = False

    def login_driver(self):
        email = self.email_var.get().strip()
        password = self.pass_var.get().strip()
        if not email or not password:
            messagebox.showwarning("Login", "Please enter both email and password.")
            return
        try:
            self.driver = login_totalcarcheck(email, password)
            self.logged_in = True
            messagebox.showinfo("Login", f"Logged in successfully as {email}!")
        except Exception as e:
            messagebox.showerror("Login Failed", f"Could not login:\n{e}")

    def drop_files(self, event):
        files = self.root.splitlist(event.data)
        for f in files:
            if f.endswith(".csv") and f not in self.files:
                self.files.append(f)
                self.listbox.insert(tk.END, os.path.basename(f))

    def browse_files(self):
        files = filedialog.askopenfilenames(title="Select CSV files", filetypes=(("CSV files", "*.csv"),))
        for f in files:
            if f not in self.files:
                self.files.append(f)
                self.listbox.insert(tk.END, os.path.basename(f))

    def remove_selected(self):
        selected_indices = list(self.listbox.curselection())
        for i in reversed(selected_indices):
            del self.files[i]
            self.listbox.delete(i)

    def save_selection(self):
        if not self.files:
            messagebox.showwarning("No files", "No CSV files added!")
            return
        self.saved_files = self.files.copy()
        messagebox.showinfo("Saved", f"{len(self.saved_files)} files saved for scraping.")
        self.scrape_btn.pack(pady=15)

    def start_scraping(self):
        if not self.logged_in:
            messagebox.showwarning("Not Logged In", "Please login first!")
            return
        if not self.saved_files:
            messagebox.showwarning("No files saved", "Please save files first!")
            return

        for file_path in self.saved_files:
            try:
                df = pd.read_csv(file_path)

                for col in ["MOT Status", "Road Tax Status", "Road Tax Expiry", "Days Left",
                            "12 Months Cost", "6 Months Cost", "CO2 Output", "Body Style"]:
                    if col not in df.columns:
                        df[col] = ""

                output_file = os.path.join("done", os.path.basename(file_path))

                for idx, row in df.iterrows():
                    reg = str(row["Reg"]).strip()
                    if not reg or reg.lower() == "nan":
                        continue

                    mot, tax, expiry, days, cost12, cost6, co2, body, extra = fetch_vehicle_info(reg, self.driver)

                    df.at[idx, "MOT Status"] = mot
                    df.at[idx, "Road Tax Status"] = tax
                    df.at[idx, "Road Tax Expiry"] = expiry
                    df.at[idx, "Days Left"] = days
                    df.at[idx, "12 Months Cost"] = cost12
                    df.at[idx, "6 Months Cost"] = cost6
                    df.at[idx, "CO2 Output"] = co2
                    df.at[idx, "Body Style"] = body

                    for k, v in extra.items():
                        if k in df.columns and str(df.at[idx, k]).strip() in ["", "N/A", "na", " "]:
                            df.at[idx, k] = v

                    df.to_csv(output_file, index=False)
                    time.sleep(2)

                messagebox.showinfo("Done", f"{os.path.basename(file_path)} scraped and saved to done folder.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed scraping {os.path.basename(file_path)}:\n{e}")

        messagebox.showinfo("All Done", "Scraping completed for all saved files.")


if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = CSVManagerApp(root)
    root.mainloop()
