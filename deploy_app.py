import subprocess
import threading
import shutil
import os
import re
from datetime import datetime
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import webbrowser

DEFAULT_HTML = r"C:\Users\HP\OneDrive\Documents\Default Project\Acceleratorares.html"
REPO_DIR = r"D:\Opencode Project"
SITE_URL = "https://acceleratorares.vercel.app/"
EXTRA_FILES = ["admin.html", "avatar.jpg", "shop-logo.jpg"]
SRC_DIR = os.path.dirname(DEFAULT_HTML)
VERSION = "v2.0"
CONFIG = os.path.join(REPO_DIR, "deploy_config.json")


def load_cfg():
    try:
        import json
        with open(CONFIG, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_cfg(d):
    try:
        import json
        with open(CONFIG, "w", encoding="utf-8") as f:
            json.dump(d, f)
    except Exception:
        pass

BG = "#0d0f14"
PANEL = "#12151d"
CARD = "#1a1e27"
GOLD = "#c8a864"
GOLD_LT = "#e0c078"
TXT = "#e8e4da"
MUTED = "#8a8478"


def run(cmd, cwd=None):
    p = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True,
                        encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


class App:
    def __init__(self, root):
        self.root = root
        self.html_file = DEFAULT_HTML
        self.busy = False
        self.auto_var = tk.BooleanVar(value=load_cfg().get("auto_backup", True))
        root.title("AcceleratorAres Deploy " + VERSION)
        root.geometry("640x700")
        root.minsize(600, 640)
        root.configure(bg=BG)

        s = ttk.Style()
        try:
            s.theme_use("clam")
        except Exception:
            pass
        s.configure("TNotebook", background=BG, borderwidth=0)
        s.configure("TNotebook.Tab", background=CARD, foreground=MUTED,
                    padding=(18, 9), font=("Segoe UI", 10, "bold"), borderwidth=0)
        s.map("TNotebook.Tab", background=[("selected", PANEL)],
              foreground=[("selected", GOLD)])
        s.configure("TFrame", background=BG)
        s.configure("Card.TFrame", background=PANEL)
        s.configure("TLabel", background=BG, foreground=TXT, font=("Segoe UI", 10))
        s.configure("Card.TLabel", background=PANEL, foreground=TXT, font=("Segoe UI", 10))
        s.configure("Muted.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 9))
        s.configure("Gold.Horizontal.TProgressbar", background=GOLD, troughcolor=CARD,
                    borderwidth=0, thickness=8)

        # ===== BANNER =====
        banner = tk.Frame(root, bg=PANEL)
        banner.pack(fill="x")
        tk.Frame(root, bg=GOLD, height=2).pack(fill="x")
        left = tk.Frame(banner, bg=PANEL)
        left.pack(side="left", padx=(18, 0), pady=12)
        tk.Label(left, text="⬢ ACCELERATORARES", font=("Segoe UI", 15, "bold"),
                 fg=GOLD, bg=PANEL).pack(anchor="w")
        tk.Label(left, text="Công cụ deploy website  •  " + VERSION,
                 font=("Segoe UI", 9), fg=MUTED, bg=PANEL).pack(anchor="w")
        right = tk.Frame(banner, bg=PANEL)
        right.pack(side="right", padx=18)
        self.dot = tk.Label(right, text="●", font=("Segoe UI", 16), fg="#4caf6d", bg=PANEL)
        self.dot.pack(side="left")
        self.status = tk.Label(right, text="Sẵn sàng", font=("Segoe UI", 10, "bold"),
                               fg=TXT, bg=PANEL)
        self.status.pack(side="left", padx=(6, 0))

        # ===== TABS =====
        nb = ttk.Notebook(root)
        nb.pack(fill="both", expand=True, padx=12, pady=12)

        # ---- Tab Deploy ----
        tab1 = ttk.Frame(nb)
        nb.add(tab1, text="  🚀  Deploy  ")

        card1 = ttk.Frame(tab1, style="Card.TFrame", padding=14)
        card1.pack(fill="x", padx=14, pady=(14, 8))
        tk.Label(card1, text="FILE HTML", font=("Segoe UI", 9, "bold"),
                 fg=MUTED, bg=PANEL).pack(anchor="w", pady=(0, 6))
        fr = tk.Frame(card1, bg=PANEL)
        fr.pack(fill="x")
        self.file_lbl = tk.Label(fr, text=os.path.basename(self.html_file),
                                 font=("Segoe UI", 11, "bold"), fg=GOLD, bg=PANEL)
        self.file_lbl.pack(side="left", fill="x", expand=True)
        tk.Button(fr, text="Chọn file...", font=("Segoe UI", 9, "bold"),
                  bg=CARD, fg=TXT, activebackground="#242a37", activeforeground=TXT,
                  relief="flat", padx=12, pady=6, cursor="hand2",
                  command=self.pick_file).pack(side="right")

        card2 = ttk.Frame(tab1, style="Card.TFrame", padding=14)
        card2.pack(fill="x", padx=14, pady=8)
        tk.Label(card2, text="GHI CHÚ BẢN DEPLOY", font=("Segoe UI", 9, "bold"),
                 fg=MUTED, bg=PANEL).pack(anchor="w", pady=(0, 6))
        self.msg = tk.Entry(card2, font=("Segoe UI", 11), bg=CARD, fg=TXT,
                            insertbackground=GOLD, relief="flat")
        self.msg.insert(0, "Cap nhat web")
        self.msg.pack(fill="x", ipady=8, ipadx=8)

        self.btn = tk.Button(tab1, text="🚀  DEPLOY NGAY", font=("Segoe UI", 14, "bold"),
                             bg=GOLD, fg="#161005", activebackground=GOLD_LT,
                             relief="flat", pady=12, cursor="hand2",
                             command=self.start)
        self.btn.pack(fill="x", padx=14, pady=(8, 4))
        tk.Checkbutton(tab1, text="Tự động sao lưu trước khi deploy / khôi phục",
                       variable=self.auto_var, command=self.save_auto,
                       font=("Segoe UI", 10), bg=BG, fg=TXT,
                       selectcolor=CARD, activebackground=BG, activeforeground=TXT,
                       cursor="hand2").pack(anchor="w", padx=18, pady=(0, 2))
        self.backup_btn = tk.Button(tab1, text="💾  SAO LƯU BẢN HIỆN TẠI", font=("Segoe UI", 11, "bold"),
                                    bg=CARD, fg=TXT, activebackground="#242a37", activeforeground=TXT,
                                    relief="flat", pady=9, cursor="hand2",
                                    command=self.backup)
        self.backup_btn.pack(fill="x", padx=14, pady=(0, 4))
        self.prog = ttk.Progressbar(tab1, style="Gold.Horizontal.TProgressbar",
                                    mode="determinate", maximum=100, value=0)
        self.prog.pack(fill="x", padx=14, pady=(0, 8))

        tk.Label(tab1, text="NHẬT KÝ", font=("Segoe UI", 9, "bold"),
                 fg=MUTED, bg=BG).pack(anchor="w", padx=16)
        self.log = scrolledtext.ScrolledText(tab1, font=("Consolas", 9),
                                             bg=PANEL, fg="#d6d0c2",
                                             insertbackground=GOLD, relief="flat",
                                             height=10)
        self.log.pack(fill="both", expand=True, padx=14, pady=(4, 14))
        self.log.configure(state="disabled")

        # ---- Tab Lich su ----
        tab2 = ttk.Frame(nb)
        nb.add(tab2, text="  🕘  Lịch sử & Khôi phục  ")

        tk.Label(tab2, text="Chọn 1 bản trong lịch sử để đưa web về đúng bản đó.",
                 font=("Segoe UI", 9), fg=MUTED, bg=BG,
                 wraplength=560, justify="left").pack(anchor="w", padx=16, pady=(14, 6))
        fr2 = tk.Frame(tab2, bg=BG)
        fr2.pack(fill="both", expand=True, padx=14)
        self.hist = tk.Listbox(fr2, font=("Consolas", 10), bg=PANEL, fg="#d6d0c2",
                               selectbackground="#8a6d3b", relief="flat",
                               activestyle="none", height=12)
        self.hist.pack(side="left", fill="both", expand=True)
        sb = tk.Scrollbar(fr2, command=self.hist.yview)
        sb.pack(side="right", fill="y")
        self.hist.configure(yscrollcommand=sb.set)

        fr3 = tk.Frame(tab2, bg=BG)
        fr3.pack(fill="x", padx=14, pady=10)
        tk.Button(fr3, text="↻  Làm mới", font=("Segoe UI", 10, "bold"),
                  bg=CARD, fg=TXT, activebackground="#242a37", activeforeground=TXT,
                  relief="flat", padx=14, pady=8, cursor="hand2",
                  command=lambda: threading.Thread(target=self.load_hist, daemon=True).start()
                  ).pack(side="left")
        tk.Button(fr3, text="⏪  KHÔI PHỤC BẢN NÀY", font=("Segoe UI", 10, "bold"),
                  bg="#7a4a3a", fg="#ffffff", activebackground="#9a5a48",
                  relief="flat", padx=14, pady=8, cursor="hand2",
                  command=self.ask_restore).pack(side="right")
        threading.Thread(target=self.load_hist, daemon=True).start()

        # ---- Tab Suc khoe ----
        tab3 = ttk.Frame(nb)
        nb.add(tab3, text="  🩺  Sức khỏe  ")

        tk.Label(tab3, text="Kiểm tra máy có đủ đồ nghề để deploy không. Thiếu gì app sẽ báo.",
                 font=("Segoe UI", 9), fg=MUTED, bg=BG,
                 wraplength=560, justify="left").pack(anchor="w", padx=16, pady=(14, 6))
        fr5 = tk.Frame(tab3, bg=BG)
        fr5.pack(fill="x", padx=14, pady=4)
        tk.Button(fr5, text="🩺  KIỂM TRA", font=("Segoe UI", 10, "bold"),
                  bg=CARD, fg=TXT, activebackground="#242a37", activeforeground=TXT,
                  relief="flat", padx=14, pady=8, cursor="hand2",
                  command=self.health_check).pack(side="left")
        tk.Button(fr5, text="🔨  BUILD LẠI FILE EXE", font=("Segoe UI", 10, "bold"),
                  bg="#3a5a3a", fg="#ffffff", activebackground="#4a704a",
                  relief="flat", padx=14, pady=8, cursor="hand2",
                  command=self.rebuild_exe).pack(side="right")
        self.hlog_box = scrolledtext.ScrolledText(tab3, font=("Consolas", 10),
                                                  bg=PANEL, fg="#d6d0c2",
                                                  relief="flat", height=14)
        self.hlog_box.pack(fill="both", expand=True, padx=14, pady=(4, 14))
        self.hlog_box.configure(state="disabled")

        # ===== STATUS BAR =====
        bar = tk.Frame(root, bg=PANEL)
        bar.pack(fill="x", side="bottom")
        tk.Frame(root, bg=GOLD, height=1).pack(fill="x", side="bottom")
        tk.Label(bar, text=SITE_URL, font=("Segoe UI", 9), fg=MUTED, bg=PANEL,
                 cursor="hand2").pack(side="left", padx=14, pady=8)
        bar.children[list(bar.children.keys())[0]].bind("<Button-1>", lambda e: webbrowser.open(SITE_URL))
        tk.Label(bar, text="Nhấn Ctrl+F5 nếu chưa thấy đổi", font=("Segoe UI", 9),
                 fg=MUTED, bg=PANEL).pack(side="right", padx=14)

    # ---------- helpers ----------
    def write(self, text):
        stamp = datetime.now().strftime("[%H:%M:%S] ")
        self.log.configure(state="normal")
        self.log.insert("end", stamp + text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def set_state(self, busy, label, color):
        self.busy = busy
        self.dot.configure(fg=color)
        self.status.configure(text=label)
        self.btn.configure(state="disabled" if busy else "normal")

    def set_prog(self, v):
        self.prog.configure(value=v)
        self.prog.update_idletasks()

    def save_auto(self):
        save_cfg({"auto_backup": bool(self.auto_var.get())})

    def maybe_auto_backup(self):
        if self.auto_var.get():
            self.write("[0/4] Tu dong sao luu ban dang chay...")
            self.auto_backup()
        else:
            self.write("[0/4] Bo qua sao luu tu dong (dang TAT).")

    # ---------- deploy ----------
    def pick_file(self):
        if self.busy:
            return
        f = filedialog.askopenfilename(title="Chon file HTML de deploy",
                                       filetypes=[("HTML", "*.html"), ("All", "*.*")],
                                       initialdir=SRC_DIR)
        if f:
            self.html_file = f
            self.file_lbl.configure(text=os.path.basename(f))
            self.write("Da chon file: " + f)

    def start(self):
        if self.busy:
            return
        if not os.path.exists(self.html_file):
            messagebox.showerror("Loi", "Khong tim thay file:\n" + self.html_file)
            return
        self.set_state(True, "Đang deploy...", GOLD)
        self.set_prog(5)
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        threading.Thread(target=self.deploy, daemon=True).start()

    def push_and_deploy(self, note):
        code, out = run("git add -A", REPO_DIR)
        code, out = run('git commit -m "' + note.replace('"', '') + '"', REPO_DIR)
        line = out.strip().splitlines()
        self.write("  " + (line[0] if line else "khong co gi moi"))
        self.set_prog(55)
        code, out = run("git push origin master", REPO_DIR)
        if code != 0:
            self.write("LOI push GitHub:\n" + out[-800:])
            return False
        self.write("  Push GitHub xong.")
        self.set_prog(65)
        self.write("[3/4] Deploy Vercel (cho ~30s)...")
        code, out = run("vercel deploy --prod --yes", REPO_DIR)
        if code != 0 or "Aliased" not in out:
            self.write("LOI deploy:\n" + out[-1200:])
            return False
        self.set_prog(100)
        return True

    def deploy(self):
        try:
            self.maybe_auto_backup()
            self.write("[1/4] Copy file...")
            shutil.copy2(self.html_file, os.path.join(REPO_DIR, "index.html"))
            self.write("  + " + os.path.basename(self.html_file) + "  →  index.html")
            for f in EXTRA_FILES:
                src = os.path.join(SRC_DIR, f)
                if os.path.exists(src):
                    shutil.copy2(src, os.path.join(REPO_DIR, f))
                    self.write("  + " + f)
            self.set_prog(30)
            self.write("[2/4] Luu GitHub...")
            if not self.push_and_deploy(self.msg.get().strip() or "Cap nhat web"):
                return self.done(False)
            self.write("[4/4] XONG! Web da cap nhat:")
            self.write("  " + SITE_URL)
            webbrowser.open(SITE_URL + "?v=new")
            self.done(True)
            threading.Thread(target=self.load_hist, daemon=True).start()
        except Exception as e:
            self.write("LOI: " + str(e))
            self.done(False)

    # ---------- backup ----------
    def next_ver(self, auto):
        mx = 0
        bdir = os.path.join(REPO_DIR, "backups")
        if os.path.isdir(bdir):
            for x in os.listdir(bdir):
                m = re.match(r"^v(\d+)(?:-auto)?$", x)
                if m:
                    mx = max(mx, int(m.group(1)))
        return ("v%d-auto" if auto else "v%d") % (mx + 1)

    def auto_backup(self):
        try:
            stamp = self.next_ver(True)
            dest = os.path.join(REPO_DIR, "backups", stamp)
            os.makedirs(dest, exist_ok=True)
            n = 0
            for f in ["index.html", "admin.html", "avatar.jpg", "shop-logo.jpg"]:
                p = os.path.join(REPO_DIR, f)
                if os.path.exists(p):
                    shutil.copy2(p, os.path.join(dest, f))
                    n += 1
            self.write("Tu dong sao luu ban cu: backups\\" + stamp + " (" + str(n) + " file)")
            return True
        except Exception as e:
            self.write("Khong sao luu tu dong duoc: " + str(e))
            return True

    def backup(self):
        if self.busy:
            return
        self.set_state(True, "Đang sao lưu...", GOLD)
        self.set_prog(10)
        threading.Thread(target=self.do_backup, daemon=True).start()

    def do_backup(self):
        try:
            stamp = self.next_ver(False)
            dest = os.path.join(REPO_DIR, "backups", stamp)
            os.makedirs(dest, exist_ok=True)
            self.write("Dang sao luu vao: backups\\" + stamp)
            names = [("index.html", self.html_file)]
            names += [(f, os.path.join(SRC_DIR, f)) for f in EXTRA_FILES]
            n = 0
            for dst_name, src in names:
                if os.path.exists(src):
                    shutil.copy2(src, os.path.join(dest, dst_name))
                    n += 1
                    self.write("  + " + os.path.basename(src))
            self.set_prog(100)
            self.write("SAO LUU XONG (" + str(n) + " file). Xem trong tab Lich su de khoi phuc.")
            self.done(True)
            threading.Thread(target=self.load_hist, daemon=True).start()
        except Exception as e:
            self.write("LOI: " + str(e))
            self.done(False)

    # ---------- history / restore ----------
    def load_hist(self):
        self.hist.delete(0, "end")
        # 1. cac ban sao luu tren may (moi nhat truoc)
        bdir = os.path.join(REPO_DIR, "backups")
        bk = []
        if os.path.isdir(bdir):
            bk = sorted([x for x in os.listdir(bdir)
                         if os.path.isdir(os.path.join(bdir, x))], reverse=True)
        for stamp in bk[:15]:
            auto = stamp.endswith("-auto")
            try:
                dt = datetime.fromtimestamp(os.path.getmtime(os.path.join(bdir, stamp))).strftime("%d/%m %H:%M")
            except Exception:
                dt = stamp
            try:
                n = len([x for x in os.listdir(os.path.join(bdir, stamp)) if os.path.isfile(os.path.join(bdir, stamp, x))])
            except Exception:
                n = 0
            tag = "Tu dong" if auto else "Sao luu tay"
            self.hist.insert("end", "BKUP:" + stamp + " | " + dt + " | " + tag + " (" + str(n) + " file)")
        # 2. cac ban da deploy (git)
        code, out = run('git log --date=format:"%d/%m %H:%M" --pretty=format:"%h | %ad | %s" -15', REPO_DIR)
        if code == 0 and out.strip():
            for line in out.strip().splitlines():
                self.hist.insert("end", line)
        if self.hist.size() == 0:
            self.hist.insert("end", "(chua co lich su)")

    def ask_restore(self):
        if self.busy:
            return
        sel = self.hist.curselection()
        if not sel:
            messagebox.showinfo("Chua chon", "Hay chon 1 ban trong lich su truoc.")
            return
        line = self.hist.get(sel[0])
        if line.startswith("BKUP:"):
            stamp = line.split()[0].replace("BKUP:", "")
            if not messagebox.askyesno("Xac nhan",
                    "Khoi phuc web tu ban sao luu:\n" + stamp + "\n\nWeb se tro ve trang thai luc sao luu."):
                return
            self.set_state(True, "Đang khôi phục...", GOLD)
            self.set_prog(10)
            self.log.configure(state="normal")
            self.log.delete("1.0", "end")
            self.log.configure(state="disabled")
            threading.Thread(target=self.restore_backup, args=(stamp,), daemon=True).start()
            return
        h = line.split()[0]
        if not messagebox.askyesno("Xac nhan",
                "Khoi phuc web ve ban:\n" + line + "\n\nWeb se tro ve trang thai cua ban nay."):
            return
        self.set_state(True, "Đang khôi phục...", GOLD)
        self.set_prog(10)
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        threading.Thread(target=self.restore, args=(h,), daemon=True).start()

    def restore(self, h):
        try:
            self.maybe_auto_backup()
            self.write("Dang lay noi dung ban " + h + "...")
            code, out = run("git show " + h + ":index.html", REPO_DIR)
            if code != 0 or not out.strip().startswith("<"):
                self.write("LOI: khong lay duoc noi dung ban nay.")
                return self.done(False)
            with open(os.path.join(REPO_DIR, "index.html"), "w", encoding="utf-8") as f:
                f.write(out)
            with open(self.html_file, "w", encoding="utf-8") as f:
                f.write(out)
            self.write("  Da chep ve index.html + file nguon.")
            self.set_prog(40)
            self.write("Dang day ban khoi phuc len...")
            if not self.push_and_deploy("Khoi phuc ve " + h):
                return self.done(False)
            self.write("KHOI PHUC XONG: " + SITE_URL)
            webbrowser.open(SITE_URL + "?v=new")
            self.done(True)
            threading.Thread(target=self.load_hist, daemon=True).start()
        except Exception as e:
            self.write("LOI: " + str(e))
            self.done(False)

    def restore_backup(self, stamp):
        try:
            self.maybe_auto_backup()
            src = os.path.join(REPO_DIR, "backups", stamp)
            idx = os.path.join(src, "index.html")
            if not os.path.exists(idx):
                self.write("LOI: khong tim thay ban sao luu " + stamp)
                return self.done(False)
            self.write("Dang lay file tu sao luu " + stamp + "...")
            shutil.copy2(idx, os.path.join(REPO_DIR, "index.html"))
            shutil.copy2(idx, self.html_file)
            self.write("  + index.html + file nguon")
            for f in EXTRA_FILES:
                p = os.path.join(src, f)
                if os.path.exists(p):
                    shutil.copy2(p, os.path.join(REPO_DIR, f))
                    shutil.copy2(p, os.path.join(SRC_DIR, f))
                    self.write("  + " + f)
            self.set_prog(40)
            self.write("Dang day ban khoi phuc len...")
            if not self.push_and_deploy("Khoi phuc tu sao luu " + stamp):
                return self.done(False)
            self.write("KHOI PHUC XONG: " + SITE_URL)
            webbrowser.open(SITE_URL + "?v=new")
            self.done(True)
            threading.Thread(target=self.load_hist, daemon=True).start()
        except Exception as e:
            self.write("LOI: " + str(e))
            self.done(False)

    # ---------- suc khoe / rebuild ----------
    def hlog(self, text):
        self.hlog_box.configure(state="normal")
        self.hlog_box.insert("end", text + "\n")
        self.hlog_box.see("end")
        self.hlog_box.configure(state="disabled")

    def health_check(self):
        if self.busy:
            return
        threading.Thread(target=self.do_health, daemon=True).start()

    def do_health(self):
        self.hlog_box.configure(state="normal")
        self.hlog_box.delete("1.0", "end")
        self.hlog_box.configure(state="disabled")
        self.hlog("=== KIEM TRA MOI TRUONG ===")
        ok_all = True
        for name, cmd in [("Git", "git --version"),
                          ("Node.js", "node --version"),
                          ("Vercel CLI", "vercel --version"),
                          ("Python", "python --version")]:
            code, out = run(cmd)
            ver = (out.strip().splitlines()[0] if out.strip() else "")
            good = (code == 0 and ver != "")
            ok_all = ok_all and good
            self.hlog(("✔ " if good else "✘ THIEU ") + name + ((" — " + ver) if good else " (can cai dat)"))
        code, out = run("vercel whoami")
        logged = (code == 0 and out.strip() != "")
        ok_all = ok_all and logged
        self.hlog(("✔ Da dang nhap Vercel (" + out.strip().splitlines()[0] + ")" if logged else "✘ Chua dang nhap Vercel (chay: vercel login)"))
        repo_ok = os.path.isdir(os.path.join(REPO_DIR, ".git"))
        ok_all = ok_all and repo_ok
        self.hlog(("✔ Folder lam viec OK" if repo_ok else "✘ Khong thay folder " + REPO_DIR))
        src_ok = os.path.exists(self.html_file)
        ok_all = ok_all and src_ok
        self.hlog(("✔ File nguon OK" if src_ok else "✘ Khong thay file " + self.html_file))
        self.hlog("=== " + ("MAY SAN SANG ✔" if ok_all else "CAN BO SUNG (xem dong ✘)"))
        try:
            import PyInstaller
            self.hlog("✔ PyInstaller san sang (build EXE duoc)")
        except Exception:
            self.hlog("○ PyInstaller chua cai (can khi build EXE: pip install pyinstaller)")

    def rebuild_exe(self):
        if self.busy:
            return
        if not messagebox.askyesno("Xac nhan",
                "Build lai file DeployWeb.exe (mat 3-5 phut)?\nApp se tu tat va mo lai ban moi."):
            return
        self.set_state(True, "Đang build EXE...", GOLD)
        threading.Thread(target=self.do_rebuild, daemon=True).start()

    def do_rebuild(self):
        try:
            self.write("Dang build file EXE moi (3-5 phut, dung tat app)...")
            self.set_prog(20)
            code, out = run("python -m PyInstaller --onefile --windowed --name DeployWeb --distpath dist_app deploy_app.py", REPO_DIR)
            new_exe = os.path.join(REPO_DIR, "dist_app", "DeployWeb.exe")
            if code != 0 or not os.path.exists(new_exe):
                self.write("LOI build:\n" + out[-1500:])
                return self.done(False)
            self.set_prog(90)
            self.write("Build xong. Dang thay file exe moi...")
            desk = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop", "DeployWeb.exe")
            bat = os.path.join(REPO_DIR, "dist_app", "_update.bat")
            with open(bat, "w") as f:
                f.write("@echo off\n"
                        + "timeout /t 3 /nobreak >nul\n"
                        + "taskkill /F /IM DeployWeb.exe >nul 2>&1\n"
                        + "timeout /t 2 /nobreak >nul\n"
                        + 'copy /Y "' + new_exe + '" "' + desk + '"\n'
                        + 'start "" "' + desk + '"\n'
                        + 'del "%~f0"\n')
            os.startfile(bat)
            self.write("App se tat va mo lai ban moi. Tam biet!")
            self.root.after(1500, self.root.destroy)
        except Exception as e:
            self.write("LOI: " + str(e))
            self.done(False)

    def done(self, ok):
        if ok:
            self.set_state(False, "Hoàn tất ✔", "#4caf6d")
            self.btn.configure(text="🚀  DEPLOY NGAY")
        else:
            self.set_state(False, "Có lỗi!", "#e05a5a")
            self.set_prog(0)


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
