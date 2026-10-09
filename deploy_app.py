import subprocess
import threading
import shutil
import os
import re
import io
import json
import time
import uuid
import mimetypes
import urllib.request
import urllib.error
from datetime import datetime
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import webbrowser

DEFAULT_HTML = r"D:\Opencode Project\Acceleratorares.html"
REPO_DIR = r"D:\Opencode Project"
SITE_URL = "https://acceleratorares.vercel.app/"
EXTRA_FILES = ["admin.html", "avatar.jpg", "shop-logo.jpg"]
SRC_DIR = os.path.dirname(DEFAULT_HTML)
VERSION = "v3.2"
CONFIG = os.path.join(REPO_DIR, "deploy_config.json")
FB_API_KEY = "AIzaSyCvCjTJ30HSsHv-oM1H4nngEHhzMyqjLtw"
FB_DB_URL = "https://cinevault-ec9d1-default-rtdb.asia-southeast1.firebasedatabase.app"
URLS = [
    ("🌐  Trang chủ", SITE_URL),
    ("🛠️  Trang quản trị", SITE_URL + "admin"),
    ("🔥  Firebase Console", "https://console.firebase.google.com/project/cinevault-ec9d1/database"),
    ("☁️  Cloudinary", "https://cloudinary.com/console"),
    ("▲  Vercel", "https://vercel.com/dashboard"),
    ("🐙  GitHub", "https://github.com/vinhthai071199-blip/accelerator"),
]


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
        fr2 = tk.Frame(tab1, bg=BG)
        fr2.pack(fill="x", padx=14, pady=(0, 4))
        tk.Button(fr2, text="DEPLOY TRANG CHÍNH", font=("Segoe UI", 10, "bold"),
                  bg=CARD, fg=TXT, activebackground="#242a37", activeforeground=TXT,
                  relief="flat", padx=10, pady=8, cursor="hand2",
                  command=lambda: self.start_one("Acceleratorares.html", "trang chính")).pack(side="left", fill="x", expand=True, padx=(0, 4))
        tk.Button(fr2, text="DEPLOY TRANG ADMIN", font=("Segoe UI", 10, "bold"),
                  bg=CARD, fg=TXT, activebackground="#242a37", activeforeground=TXT,
                  relief="flat", padx=10, pady=8, cursor="hand2",
                  command=lambda: self.start_one("admin.html", "trang admin")).pack(side="left", fill="x", expand=True, padx=(4, 0))
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

        # ---- Tab Noi dung ----
        tab4 = ttk.Frame(nb)
        nb.add(tab4, text="  📝  Nội dung  ")

        tk.Label(tab4, text="Sửa chữ trên web. Lưu xong nhớ sang tab Deploy để đưa lên.",
                 font=("Segoe UI", 9), fg=MUTED, bg=BG,
                 wraplength=560, justify="left").pack(anchor="w", padx=16, pady=(14, 6))
        self.content_vars = {}
        cf = tk.Frame(tab4, bg=BG)
        cf.pack(fill="both", expand=True, padx=16)
        for key, label in [("title", "Tiêu đề (cạnh avatar)"),
                           ("welcome", "Dòng chào mừng"),
                           ("shopname", "Tên shop"),
                           ("shopdesc", "Mô tả shop"),
                           ("shoplink", "Link shop"),
                           ("cskhlink", "Link CSKH")]:
            tk.Label(cf, text=label, font=("Segoe UI", 9, "bold"),
                     fg=MUTED, bg=BG).pack(anchor="w", pady=(6, 2))
            var = tk.StringVar()
            self.content_vars[key] = var
            tk.Entry(cf, textvariable=var, font=("Segoe UI", 10),
                     bg=CARD, fg=TXT, insertbackground=GOLD,
                     relief="flat").pack(fill="x", ipady=7, ipadx=8)
        fr6 = tk.Frame(tab4, bg=BG)
        fr6.pack(fill="x", padx=14, pady=12)
        tk.Button(fr6, text="↻  Tải nội dung hiện tại", font=("Segoe UI", 10, "bold"),
                  bg=CARD, fg=TXT, activebackground="#242a37", activeforeground=TXT,
                  relief="flat", padx=14, pady=8, cursor="hand2",
                  command=self.content_load).pack(side="left")
        tk.Button(fr6, text="💾  LƯU THAY ĐỔI", font=("Segoe UI", 10, "bold"),
                  bg=GOLD, fg="#161005", activebackground=GOLD_LT,
                  relief="flat", padx=14, pady=8, cursor="hand2",
                  command=self.content_save).pack(side="right")
        self.content_msg = tk.Label(tab4, text="", font=("Segoe UI", 9),
                                    fg=GOLD, bg=BG)
        self.content_msg.pack(padx=16, pady=(0, 10), anchor="w")

        # ---- Tab Hinh anh ----
        tab5 = ttk.Frame(nb)
        nb.add(tab5, text="  🖼️  Hình ảnh  ")

        tk.Label(tab5, text="Đổi avatar và logo shop. Ảnh mới tự đi theo khi deploy.",
                 font=("Segoe UI", 9), fg=MUTED, bg=BG,
                 wraplength=560, justify="left").pack(anchor="w", padx=16, pady=(14, 6))
        self.img_rows = {}
        imgf = tk.Frame(tab5, bg=BG)
        imgf.pack(fill="x", padx=16)
        for key, label, fname in [("avatar", "Avatar (cạnh tiêu đề + icon tab)", "avatar.jpg"),
                                  ("logo", "Logo Teyvat Store", "shop-logo.jpg")]:
            row = ttk.Frame(tab5, style="Card.TFrame", padding=12)
            row.pack(fill="x", padx=14, pady=6)
            tk.Label(row, text=label, font=("Segoe UI", 10, "bold"),
                     fg=TXT, bg=PANEL).pack(anchor="w")
            sub = tk.Frame(row, bg=PANEL)
            sub.pack(fill="x", pady=(6, 0))
            lbl = tk.Label(sub, text=fname, font=("Segoe UI", 9), fg=MUTED, bg=PANEL)
            lbl.pack(side="left", fill="x", expand=True)
            self.img_rows[key] = (fname, lbl)
            tk.Button(sub, text="Chọn ảnh...", font=("Segoe UI", 9, "bold"),
                      bg=CARD, fg=TXT, activebackground="#242a37", activeforeground=TXT,
                      relief="flat", padx=12, pady=6, cursor="hand2",
                      command=lambda k=key: self.pick_image(k)).pack(side="right")
        self.img_msg = tk.Label(tab5, text="", font=("Segoe UI", 9),
                                fg=GOLD, bg=BG)
        self.img_msg.pack(padx=16, pady=8, anchor="w")

        # ---- Tab Video ----
        tab6 = ttk.Frame(nb)
        nb.add(tab6, text="  🎬  Video  ")

        tk.Label(tab6, text="Upload video lên Cloudinary, tự hiện lên web. Tối đa 100MB.",
                 font=("Segoe UI", 9), fg=MUTED, bg=BG,
                 wraplength=560, justify="left").pack(anchor="w", padx=16, pady=(14, 6))
        cfg = load_cfg()
        vf = tk.Frame(tab6, bg=BG)
        vf.pack(fill="x", padx=16)
        tk.Label(vf, text="Tên video", font=("Segoe UI", 9, "bold"),
                 fg=MUTED, bg=BG).pack(anchor="w", pady=(4, 2))
        self.vd_title = tk.Entry(vf, font=("Segoe UI", 10), bg=CARD, fg=TXT,
                                 insertbackground=GOLD, relief="flat")
        self.vd_title.pack(fill="x", ipady=7, ipadx=8)
        self.vd_file_lbl = tk.Label(vf, text="File video: chưa chọn", font=("Segoe UI", 9),
                                      fg=MUTED, bg=BG, wraplength=540, justify="left")
        self.vd_file_lbl.pack(anchor="w", pady=(8, 2))
        self.vd_file = None
        fr7 = tk.Frame(tab6, bg=BG)
        fr7.pack(fill="x", padx=14, pady=8)
        tk.Button(fr7, text="Chọn video...", font=("Segoe UI", 10, "bold"),
                  bg=CARD, fg=TXT, activebackground="#242a37", activeforeground=TXT,
                  relief="flat", padx=14, pady=8, cursor="hand2",
                  command=self.pick_video).pack(side="left")
        self.vd_btn = tk.Button(fr7, text="⬆️  UPLOAD", font=("Segoe UI", 10, "bold"),
                                bg=GOLD, fg="#161005", activebackground=GOLD_LT,
                                relief="flat", padx=14, pady=8, cursor="hand2",
                                command=self.start_vdupload)
        self.vd_btn.pack(side="right")
        self.vd_prog = ttk.Progressbar(tab6, style="Gold.Horizontal.TProgressbar",
                                       mode="determinate", maximum=100, value=0)
        self.vd_prog.pack(fill="x", padx=14, pady=(0, 8))
        tk.Label(tab6, text="Tài khoản admin (để lưu video vào web)", font=("Segoe UI", 9, "bold"),
                 fg=MUTED, bg=BG).pack(anchor="w", padx=16, pady=(4, 2))
        af = tk.Frame(tab6, bg=BG)
        af.pack(fill="x", padx=16)
        self.vd_email = tk.Entry(af, font=("Segoe UI", 10), bg=CARD, fg=TXT,
                                 insertbackground=GOLD, relief="flat", width=28)
        self.vd_email.insert(0, cfg.get("admin_email", ""))
        self.vd_email.pack(side="left", ipady=7, ipadx=8)
        self.vd_pass = tk.Entry(af, font=("Segoe UI", 10), bg=CARD, fg=TXT,
                                insertbackground=GOLD, relief="flat", width=20, show="•")
        self.vd_pass.insert(0, cfg.get("admin_pass", ""))
        self.vd_pass.pack(side="left", padx=(8, 0), ipady=7, ipadx=8)
        tk.Label(tab6, text="Mật khẩu chỉ lưu trên máy bạn.", font=("Segoe UI", 8),
                 fg=MUTED, bg=BG).pack(anchor="w", padx=16)
        self.vd_msg = tk.Label(tab6, text="", font=("Segoe UI", 9),
                               fg=GOLD, bg=BG, wraplength=560, justify="left")
        self.vd_msg.pack(padx=16, pady=8, anchor="w", fill="x")

        # ---- Tab Mo nhanh ----
        tab7 = ttk.Frame(nb)
        nb.add(tab7, text="  🔗  Mở nhanh  ")

        tk.Label(tab7, text="Bấm để mở các trang liên quan.", font=("Segoe UI", 9),
                 fg=MUTED, bg=BG).pack(anchor="w", padx=16, pady=(14, 6))
        lkf = tk.Frame(tab7, bg=BG)
        lkf.pack(fill="x", padx=16)
        for i, (label, url) in enumerate(URLS):
            tk.Button(lkf, text=label, font=("Segoe UI", 11, "bold"),
                      bg=CARD, fg=TXT, activebackground="#242a37", activeforeground=GOLD,
                      relief="flat", pady=12, cursor="hand2", anchor="w",
                      command=lambda u=url: webbrowser.open(u)
                      ).pack(fill="x", pady=4)

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

    def start_one(self, fname, label):
        if self.busy:
            return
        if not os.path.exists(os.path.join(REPO_DIR, fname)):
            messagebox.showerror("Loi", "Khong tim thay file:\n" + fname)
            return
        self.set_state(True, "Đang deploy " + label + "...", GOLD)
        self.set_prog(5)
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        threading.Thread(target=self.deploy_one, args=(fname, label), daemon=True).start()

    def deploy_one(self, fname, label):
        try:
            self.maybe_auto_backup()
            self.write("[1/2] Chi deploy " + label + " (" + fname + "), khong copy de file...")
            self.set_prog(30)
            self.write("[2/2] Luu GitHub...")
            if not self.push_and_deploy((self.msg.get().strip() or "Cap nhat ") + label, [fname]):
                return self.done(False)
            self.write("[4/4] XONG! Web da cap nhat:")
            self.write("  " + SITE_URL)
            webbrowser.open(SITE_URL + "?v=new")
            self.done(True)
            threading.Thread(target=self.load_hist, daemon=True).start()
        except Exception as e:
            self.write("LOI: " + str(e))
            self.done(False)

    def push_and_deploy(self, note, files=None):
        if files:
            code, out = run("git add " + " ".join(files), REPO_DIR)
        else:
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
            _dst = os.path.join(REPO_DIR, "Acceleratorares.html")
            try:
                if os.path.normcase(os.path.abspath(self.html_file)) != os.path.normcase(os.path.abspath(_dst)):
                    shutil.copy2(self.html_file, _dst)
                    self.write("  + " + os.path.basename(self.html_file) + "  →  Acceleratorares.html")
                else:
                    self.write("  (file nguồn chính là file web, bỏ qua copy)")
            except OSError as e:
                self.write("  (bỏ qua copy: " + str(e) + ")")
            for f in EXTRA_FILES:
                src = os.path.join(SRC_DIR, f)
                dst = os.path.join(REPO_DIR, f)
                if os.path.exists(src) and os.path.normcase(os.path.abspath(src)) != os.path.normcase(os.path.abspath(dst)):
                    shutil.copy2(src, dst)
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
            for f in ["Acceleratorares.html", "admin.html", "avatar.jpg", "shop-logo.jpg"]:
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
            names = [("Acceleratorares.html", self.html_file)]
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
            code, out = run("git show " + h + ":Acceleratorares.html", REPO_DIR)
            if code != 0 or not out.strip().startswith("<"):
                self.write("LOI: khong lay duoc noi dung ban nay.")
                return self.done(False)
            with open(os.path.join(REPO_DIR, "Acceleratorares.html"), "w", encoding="utf-8") as f:
                f.write(out)
            with open(self.html_file, "w", encoding="utf-8") as f:
                f.write(out)
            self.write("  Da chep ve Acceleratorares.html + file nguon.")
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
            idx = os.path.join(src, "Acceleratorares.html")
            if not os.path.exists(idx):
                self.write("LOI: khong tim thay ban sao luu " + stamp)
                return self.done(False)
            self.write("Dang lay file tu sao luu " + stamp + "...")
            shutil.copy2(idx, os.path.join(REPO_DIR, "Acceleratorares.html"))
            shutil.copy2(idx, self.html_file)
            self.write("  + Acceleratorares.html + file nguon")
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

    # ---------- noi dung ----------
    CONTENT_PATS = [
        ("title", "Tiêu đề",
         r"(<h1><img class=\"head-avatar\" src=\"avatar\.jpg\" alt=\"\"><em>)(.*?)(</em></h1>)"),
        ("welcome", "Dòng chào mừng",
         r"(<p class=\"welcome\">)(.*?)(</p>)"),
        ("shopname", "Tên shop",
         r"(<section id=\"shop\">[\s\S]*?<h3>)(.*?)(</h3>)"),
        ("shopdesc", "Mô tả shop",
         r"(<section id=\"shop\">[\s\S]*?<h3>.*?</h3>\s*<p>)(.*?)(</p>)"),
        ("shoplink", "Link shop",
         r"(<a class=\"btn solid\" href=\")(.*?)(\" target=\"_blank\">[\s\S]*?Vào shop)"),
        ("cskhlink", "Link CSKH",
         r"(<a class=\"btn\" href=\")(.*?)(\" target=\"_blank\">[\s\S]*?Liên hệ CSKH)"),
    ]

    def content_load(self):
        try:
            with open(self.html_file, encoding="utf-8") as f:
                t = f.read()
        except Exception as e:
            self.content_msg.configure(text="Không đọc được file: " + str(e));
            return
        n = 0
        for key, label, pat in self.CONTENT_PATS:
            m = re.search(pat, t)
            if m:
                self.content_vars[key].set(m.group(2))
                n += 1
        self.content_msg.configure(text="Đã tải %d/6 mục từ %s" % (n, os.path.basename(self.html_file)))

    def content_save(self):
        try:
            with open(self.html_file, encoding="utf-8") as f:
                t = f.read()
        except Exception as e:
            self.content_msg.configure(text="Không đọc được file: " + str(e));
            return
        n = 0
        for key, label, pat in self.CONTENT_PATS:
            new = self.content_vars[key].get()
            if not new.strip():
                continue
            t2, c = re.subn(pat, lambda m: m.group(1) + new + m.group(3), t, count=1)
            if c:
                t = t2
                n += 1
        try:
            with open(self.html_file, "w", encoding="utf-8") as f:
                f.write(t)
        except Exception as e:
            self.content_msg.configure(text="Không lưu được: " + str(e));
            return
        self.content_msg.configure(text="Đã lưu %d mục. Sang tab Deploy để đưa lên web!" % n)

    # ---------- hinh anh ----------
    def pick_image(self, which):
        fname, lbl = self.img_rows[which]
        f = filedialog.askopenfilename(title="Chọn ảnh mới cho " + fname,
                                       filetypes=[("Ảnh", "*.png *.jpg *.jpeg *.webp"), ("All", "*.*")],
                                       initialdir=SRC_DIR)
        if not f:
            return
        if os.path.splitext(f)[1].lower() not in (".png", ".jpg", ".jpeg", ".webp"):
            self.img_msg.configure(text="Chỉ nhận file ảnh (png/jpg/webp)!");
            return
        try:
            shutil.copy2(f, os.path.join(SRC_DIR, fname))
            lbl.configure(text=fname + "  ✔ vừa đổi")
            self.img_msg.configure(text="Đã đổi %s. Deploy để lên web!" % fname)
        except Exception as e:
            self.img_msg.configure(text="Lỗi: " + str(e))

    # ---------- video upload ----------
    def pick_video(self):
        f = filedialog.askopenfilename(title="Chọn video (tối đa 100MB)",
                                       filetypes=[("Video", "*.mp4 *.mov *.webm *.mkv"), ("All", "*.*")])
        if not f:
            return
        size = os.path.getsize(f)
        if size > 100 * 1024 * 1024:
            self.vd_msg.configure(text="Video quá lớn (%.1fMB)! Tối đa 100MB." % (size / 1024 / 1024));
            return
        self.vd_file = f
        if not self.vd_title.get().strip():
            base = os.path.splitext(os.path.basename(f))[0]
            self.vd_title.delete(0, "end")
            self.vd_title.insert(0, base)
        self.vd_file_lbl.configure(text="File: %s (%.1fMB)" % (os.path.basename(f), size / 1024 / 1024))

    def start_vdupload(self):
        if self.busy:
            return
        if not self.vd_file or not os.path.exists(self.vd_file):
            self.vd_msg.configure(text="Hãy chọn file video trước!");
            return
        title = self.vd_title.get().strip() or os.path.splitext(os.path.basename(self.vd_file))[0]
        email = self.vd_email.get().strip()
        pw = self.vd_pass.get()
        if not email or not pw:
            self.vd_msg.configure(text="Nhập email + mật khẩu admin để lưu video vào web!");
            return
        cfg = load_cfg()
        cfg.update({"admin_email": email, "admin_pass": pw})
        save_cfg(cfg)
        try:
            with open(os.path.join(SRC_DIR, "admin.html"), encoding="utf-8") as f:
                at = f.read()
            cm = re.search(r'const CLOUD_NAME = "(.*?)";', at)
            pm = re.search(r'const UPLOAD_PRESET = "(.*?)";', at)
            cloud = cm.group(1) if cm else ""
            preset = pm.group(1) if pm else ""
        except Exception:
            cloud, preset = "", ""
        if not cloud or "DANGKY" in cloud or not preset or "DANGKY" in preset:
            self.vd_msg.configure(text="Chưa cấu hình Cloudinary trong admin.html!");
            return
        self.set_state(True, "Đang upload video...", GOLD)
        self.vd_btn.configure(state="disabled")
        self.vd_prog.configure(value=0)
        threading.Thread(target=self.do_vdupload,
                         args=(self.vd_file, title, email, pw, cloud, preset),
                         daemon=True).start()

    def vd_progress(self, sent, total):
        try:
            self.vd_prog.configure(value=sent * 100 / total)
            self.vd_prog.update_idletasks()
        except Exception:
            pass

    def do_vdupload(self, path, title, email, pw, cloud, preset):
        try:
            size = os.path.getsize(path)
            self.vd_msg.configure(text="Đang tải lên Cloudinary...")
            boundary = uuid.uuid4().hex
            fname = os.path.basename(path)
            ctype = mimetypes.guess_type(fname)[0] or "video/mp4"
            pre = b""
            for k, v in [("upload_preset", preset)]:
                pre += b"--" + boundary.encode() + b"\r\n" \
                    + ('Content-Disposition: form-data; name="%s"\r\n\r\n%s\r\n' % (k, v)).encode()
            pre += b"--" + boundary.encode() + b"\r\n" \
                + ('Content-Disposition: form-data; name="file"; filename="%s"\r\nContent-Type: %s\r\n\r\n' % (fname, ctype)).encode()
            post = b"\r\n--" + boundary.encode() + b"--\r\n"

            fp = open(path, "rb")
            reader = self.MultiReader(pre, fp, size, post, self.vd_progress)
            req = urllib.request.Request(
                "https://api.cloudinary.com/v1_1/" + cloud + "/video/upload",
                data=reader,
                headers={"Content-Type": "multipart/form-data; boundary=" + boundary,
                         "Content-Length": str(len(reader))},
                method="POST")
            try:
                with urllib.request.urlopen(req, timeout=600) as r:
                    resp = json.loads(r.read().decode())
            finally:
                fp.close()
            url = resp.get("secure_url", "")
            if not url:
                self.vd_msg.configure(text="Cloudinary không trả link! Thử lại.");
                return self.done(False)
            self.vd_msg.configure(text="Tải lên xong. Đang lưu vào web...")
            token = self.fb_token(email, pw)
            if not token:
                self.vd_msg.configure(text="Sai email/mật khẩu admin!");
                return self.done(False)
            payload = {"title": title, "url": url,
                       "public_id": resp.get("public_id", ""),
                       "size": size, "time": int(time.time() * 1000)}
            req2 = urllib.request.Request(
                FB_DB_URL + "/videos.json?auth=" + token,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"}, method="POST")
            urllib.request.urlopen(req2, timeout=60).read()
            self.vd_msg.configure(text="XONG! Video '%s' đã lên web. 🎉" % title)
            self.vd_file = None
            self.vd_file_lbl.configure(text="File video: chưa chọn")
            self.vd_title.delete(0, "end")
            try:
                self.vd_prog.configure(value=100)
            except Exception:
                pass
            webbrowser.open(SITE_URL)
            self.done(True)
        except urllib.error.HTTPError as e:
            try:
                detail = e.read().decode()[:300]
            except Exception:
                detail = ""
            self.vd_msg.configure(text="Lỗi upload (%s). %s" % (e.code, detail))
            self.done(False)
        except Exception as e:
            self.vd_msg.configure(text="Lỗi: " + str(e))
            self.done(False)
        finally:
            try:
                self.vd_btn.configure(state="normal")
            except Exception:
                pass

    def fb_token(self, email, pw):
        try:
            data = json.dumps({"email": email, "password": pw,
                               "returnSecureToken": True}).encode()
            req = urllib.request.Request(
                "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=" + FB_API_KEY,
                data=data, headers={"Content-Type": "application/json"})
            return json.loads(urllib.request.urlopen(req, timeout=30).read().decode()).get("idToken", "")
        except Exception:
            return ""

    class MultiReader:
        def __init__(self, pre, fp, total, post, cb):
            self.parts = [io.BytesIO(pre), fp, io.BytesIO(post)]
            self.i = 0
            self.sent = 0
            self.total = len(pre) + total + len(post)
            self.cb = cb

        def __len__(self):
            return self.total

        def read(self, n=65536):
            if self.i >= len(self.parts):
                return b""
            chunk = self.parts[self.i].read(n)
            if chunk == b"":
                self.i += 1
                return self.read(n)
            self.sent += len(chunk)
            try:
                self.cb(self.sent, self.total)
            except Exception:
                pass
            return chunk

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
