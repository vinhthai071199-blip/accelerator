import subprocess
import threading
import shutil
import os
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox

DEFAULT_HTML = r"C:\Users\HP\OneDrive\Documents\Default Project\Acceleratorares.html"
REPO_DIR = r"D:\Opencode Project"
SITE_URL = "https://acceleratorares.vercel.app/"
EXTRA_FILES = ["admin.html", "avatar.jpg", "shop-logo.jpg"]
SRC_DIR = os.path.dirname(DEFAULT_HTML)


def run(cmd, cwd=None):
    p = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True,
                        encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


class App:
    def __init__(self, root):
        self.html_file = DEFAULT_HTML
        root.title("AcceleratorAres - Deploy Web")
        root.geometry("580x640")
        root.resizable(False, False)
        root.configure(bg="#0d0f14")

        tk.Label(root, text="ACCELERATORARES", font=("Segoe UI", 16, "bold"),
                 fg="#c8a864", bg="#0d0f14").pack(pady=(14, 2))
        tk.Label(root, text=SITE_URL, font=("Segoe UI", 10),
                 fg="#8a8478", bg="#0d0f14").pack(pady=(0, 8))

        # --- chon file html ---
        f1 = tk.Frame(root, bg="#0d0f14")
        f1.pack(fill="x", padx=18, pady=4)
        tk.Label(f1, text="File HTML:", font=("Segoe UI", 10),
                 fg="#e8e4da", bg="#0d0f14").pack(side="left")
        self.file_lbl = tk.Label(f1, text=os.path.basename(self.html_file),
                                 font=("Segoe UI", 10, "bold"), fg="#c8a864", bg="#0d0f14")
        self.file_lbl.pack(side="left", padx=(8, 0))
        tk.Button(f1, text="Chon file...", font=("Segoe UI", 9),
                  bg="#1a1e27", fg="#e8e4da", relief="flat", padx=10,
                  command=self.pick_file).pack(side="right")

        # --- ghi chu ---
        f2 = tk.Frame(root, bg="#0d0f14")
        f2.pack(fill="x", padx=18, pady=4)
        tk.Label(f2, text="Ghi chu:", font=("Segoe UI", 10),
                 fg="#e8e4da", bg="#0d0f14").pack(side="left")
        self.msg = tk.Entry(f2, font=("Segoe UI", 10), width=40)
        self.msg.insert(0, "Cap nhat web")
        self.msg.pack(side="left", padx=(8, 0), fill="x", expand=True)

        self.btn = tk.Button(root, text="DEPLOY NGAY", font=("Segoe UI", 13, "bold"),
                             bg="#c8a864", fg="#161005", activebackground="#e0c078",
                             relief="flat", padx=10, pady=10, cursor="hand2",
                             command=self.start)
        self.btn.pack(fill="x", padx=18, pady=8)

        # --- lich su ---
        tk.Label(root, text="Lich su cac ban deploy (chon de khoi phuc):",
                 font=("Segoe UI", 10, "bold"), fg="#e8e4da", bg="#0d0f14",
                 anchor="w").pack(fill="x", padx=18, pady=(4, 2))
        f3 = tk.Frame(root, bg="#0d0f14")
        f3.pack(fill="x", padx=18)
        self.hist = tk.Listbox(f3, font=("Consolas", 9), bg="#12151d", fg="#d6d0c2",
                               selectbackground="#8a6d3b", height=6)
        self.hist.pack(side="left", fill="x", expand=True)
        sb = tk.Scrollbar(f3, command=self.hist.yview)
        sb.pack(side="right", fill="y")
        self.hist.configure(yscrollcommand=sb.set)

        f4 = tk.Frame(root, bg="#0d0f14")
        f4.pack(fill="x", padx=18, pady=6)
        tk.Button(f4, text="Lam moi", font=("Segoe UI", 9),
                  bg="#1a1e27", fg="#e8e4da", relief="flat", padx=10,
                  command=lambda: threading.Thread(target=self.load_hist, daemon=True).start()
                  ).pack(side="left")
        tk.Button(f4, text="KHOI PHUC BAN NAY", font=("Segoe UI", 10, "bold"),
                  bg="#7a4a3a", fg="#ffffff", activebackground="#9a5a48",
                  relief="flat", padx=10, pady=4, cursor="hand2",
                  command=self.ask_restore).pack(side="right")

        self.log = scrolledtext.ScrolledText(root, font=("Consolas", 9),
                                             bg="#12151d", fg="#d6d0c2",
                                             insertbackground="#c8a864", height=8)
        self.log.pack(fill="both", expand=True, padx=18, pady=(0, 14))
        self.log.configure(state="disabled")
        threading.Thread(target=self.load_hist, daemon=True).start()

    def write(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def set_busy(self, busy, text=None):
        self.btn.configure(state="disabled" if busy else "normal")
        if text:
            self.btn.configure(text=text)

    def pick_file(self):
        f = filedialog.askopenfilename(title="Chon file HTML de deploy",
                                       filetypes=[("HTML", "*.html"), ("All", "*.*")],
                                       initialdir=SRC_DIR)
        if f:
            self.html_file = f
            self.file_lbl.configure(text=os.path.basename(f))
            self.write("Da chon file: " + f)

    def load_hist(self):
        code, out = run("git log --oneline -15", REPO_DIR)
        self.hist.delete(0, "end")
        if code != 0 or not out.strip():
            self.hist.insert("end", "(khong doc duoc lich su)")
            return
        for line in out.strip().splitlines():
            self.hist.insert("end", line)

    def start(self):
        if not os.path.exists(self.html_file):
            messagebox.showerror("Loi", "Khong tim thay file:\n" + self.html_file)
            return
        self.set_busy(True, "DANG DEPLOY...")
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        threading.Thread(target=self.deploy, daemon=True).start()

    def push_and_deploy(self, note):
        code, out = run("git add -A", REPO_DIR)
        code, out = run('git commit -m "' + note.replace('"', '') + '"', REPO_DIR)
        line = out.strip().splitlines()
        self.write("  " + (line[0] if line else "khong co gi moi"))
        code, out = run("git push origin master", REPO_DIR)
        if code != 0:
            self.write("LOI push GitHub:\n" + out[-800:])
            return False
        self.write("  Push xong.")
        self.write("[3/4] Deploy Vercel (cho ~30s)...")
        code, out = run("vercel deploy --prod --yes", REPO_DIR)
        if code != 0 or "Aliased" not in out:
            self.write("LOI deploy:\n" + out[-1200:])
            return False
        return True

    def deploy(self):
        try:
            self.write("[1/4] Copy file...")
            shutil.copy2(self.html_file, os.path.join(REPO_DIR, "index.html"))
            self.write("  + " + os.path.basename(self.html_file) + " -> index.html")
            for f in EXTRA_FILES:
                src = os.path.join(SRC_DIR, f)
                if os.path.exists(src):
                    shutil.copy2(src, os.path.join(REPO_DIR, f))
                    self.write("  + " + f)
            self.write("[2/4] Luu GitHub...")
            if not self.push_and_deploy(self.msg.get().strip() or "Cap nhat web"):
                return self.done(False)
            self.write("[4/4] XONG! Web da cap nhat:")
            self.write("  " + SITE_URL)
            self.write("  (Chua thay doi? Nhan Ctrl+F5)")
            os.startfile(SITE_URL + "?v=new")
            self.done(True)
            threading.Thread(target=self.load_hist, daemon=True).start()
        except Exception as e:
            self.write("LOI: " + str(e))
            self.done(False)

    def ask_restore(self):
        sel = self.hist.curselection()
        if not sel:
            messagebox.showinfo("Chua chon", "Hay chon 1 ban trong lich su truoc.")
            return
        line = self.hist.get(sel[0])
        h = line.split()[0]
        if not messagebox.askyesno("Xac nhan",
                "Khoi phuc web ve ban:\n" + line + "\n\nWeb se tro ve trang thai cua ban nay.") :
            return
        self.set_busy(True, "DANG KHOI PHUC...")
        threading.Thread(target=self.restore, args=(h,), daemon=True).start()

    def restore(self, h):
        try:
            self.write("Dang lay noi dung ban " + h + "...")
            code, out = run("git show " + h + ":index.html", REPO_DIR)
            if code != 0 or not out.strip().startswith("<"):
                self.write("LOI: khong lay duoc noi dung ban nay.")
                return self.done(False)
            with open(os.path.join(REPO_DIR, "index.html"), "w",
                      encoding="utf-8") as f:
                f.write(out)
            with open(self.html_file, "w", encoding="utf-8") as f:
                f.write(out)
            self.write("  Da chep ve index.html + file nguon.")
            self.write("Dang day ban khoi phuc len...")
            if not self.push_and_deploy("Khoi phuc ve " + h):
                return self.done(False)
            self.write("KHOI PHUC XONG: " + SITE_URL)
            os.startfile(SITE_URL + "?v=new")
            self.done(True)
            threading.Thread(target=self.load_hist, daemon=True).start()
        except Exception as e:
            self.write("LOI: " + str(e))
            self.done(False)

    def done(self, ok):
        self.set_busy(False, "DEPLOY THANH CONG ✔" if ok else "THU LAI")


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
