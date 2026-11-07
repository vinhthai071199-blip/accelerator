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
EXTRA_FILES = ["admin.html", "avatar.jpg", "avatar.ico", "shop-logo.jpg", "robots.txt"]
SRC_DIR = os.path.dirname(DEFAULT_HTML)
VERSION = "v3.7"
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


def vercel_exe():
    return "vercel.cmd" if shutil.which("vercel.cmd") else "vercel"

BG = "#eef1f6"
PANEL = "#ffffff"
CARD = "#eef2f7"
GOLD = "#2563eb"
GOLD_LT = "#1d4ed8"
TXT = "#1f2937"
MUTED = "#64748b"
SIDE = "#0f172a"
SIDE_HOV = "#1e293b"
EDGE = "#d9e1ea"
GREEN = "#16a34a"
RED = "#dc2626"


def run(cmd, cwd=None):
    p = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True,
                        encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


GIT_NAME = "vinhthai071199-blip"
GIT_MAIL = "vinhthai071199-blip@users.noreply.github.com"


def ensure_git_identity():
    """May chua co git user.name/user.email thi moi lenh commit deu that bai (exit 128),
    nen app bao 'XONG' trong khi web van la ban cu. Tu cau hinh neu thieu."""
    code, out = run("git var GIT_AUTHOR_IDENT", REPO_DIR)
    if code == 0:
        return
    run('git config user.name "' + GIT_NAME + '"', REPO_DIR)
    run('git config user.email "' + GIT_MAIL + '"', REPO_DIR)
    code, out = run("git var GIT_AUTHOR_IDENT", REPO_DIR)
    if code != 0:
        raise RuntimeError("Khong cau hinh duoc git user.name/user.email:\n" + out[-400:])


class App:
    def __init__(self, root):
        self.root = root
        self.html_file = DEFAULT_HTML
        self.busy = False
        self.yt_proc = None
        self.yt_tun = None
        self.yt_url = ""
        self.yt_pushed = ""
        self.auto_var = tk.BooleanVar(value=load_cfg().get("auto_backup", True))
        root.title("AcceleratorAres Deploy " + VERSION)
        root.geometry("820x680")
        root.minsize(760, 620)
        root.configure(bg=BG)

        s = ttk.Style()
        try:
            s.theme_use("clam")
        except Exception:
            pass
        s.configure("TNotebook", background=BG, borderwidth=0)
        s.configure("TFrame", background=BG)
        s.configure("TLabel", background=BG, foreground=TXT, font=("Segoe UI", 10))
        s.configure("Blue.Horizontal.TProgressbar", background=GOLD, troughcolor="#e2e8f0",
                    borderwidth=0, thickness=9)

        # ===== KHUNG CHINH: MENU TRAI + NOI DUNG =====
        shell = tk.Frame(root, bg=BG)
        shell.pack(fill="both", expand=True)

        side = tk.Frame(shell, bg=SIDE, width=205)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)

        brand = tk.Frame(side, bg=SIDE)
        brand.pack(fill="x", padx=18, pady=(20, 16))
        tk.Label(brand, text="⬢ ACCELERATORARES", font=("Segoe UI", 12, "bold"),
                 fg="#ffffff", bg=SIDE).pack(anchor="w")
        tk.Label(brand, text="Công cụ quản lý website", font=("Segoe UI", 8),
                 fg="#94a3b8", bg=SIDE).pack(anchor="w", pady=(2, 0))

        body = tk.Frame(shell, bg=BG)
        body.pack(side="left", fill="both", expand=True)
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)

        pages = {}
        nav_btns = {}
        cur = {"name": ""}

        def show(name):
            cur["name"] = name
            for n, b in nav_btns.items():
                if n == name:
                    b.configure(bg=GOLD, fg="#ffffff")
                else:
                    b.configure(bg=SIDE, fg="#cbd5e1")
            pages[name].tkraise()

        for n, label in [("web", "  🚀   Đăng web"),
                         ("sua", "  ✏️   Sửa web"),
                         ("maychu", "  🖥️   Máy chủ"),
                         ("lichsu", "  🕘   Lịch sử"),
                         ("mo", "  🔗   Mở nhanh"),
                         ("suckhoe", "  🩺   Sức khỏe")]:
            b = tk.Button(side, text=label, font=("Segoe UI", 10, "bold"),
                          bg=SIDE, fg="#cbd5e1", activebackground=SIDE_HOV,
                          activeforeground="#ffffff", relief="flat", bd=0,
                          anchor="w", padx=14, pady=10, cursor="hand2")
            b.configure(command=lambda k=n: show(k))
            b.pack(fill="x", padx=10, pady=1)
            b.bind("<Enter>", lambda e, k=n, btn=b: btn.configure(bg=SIDE_HOV)
                   if cur["name"] != k else None)
            b.bind("<Leave>", lambda e, k=n, btn=b: btn.configure(bg=SIDE)
                   if cur["name"] != k else None)
            nav_btns[n] = b

        stat = tk.Frame(side, bg=SIDE)
        stat.pack(side="bottom", fill="x", padx=16, pady=14)
        self.dot = tk.Label(stat, text="●", font=("Segoe UI", 13), fg=GREEN, bg=SIDE)
        self.dot.pack(side="left")
        self.status = tk.Label(stat, text="Sẵn sàng", font=("Segoe UI", 10, "bold"),
                               fg="#ffffff", bg=SIDE)
        self.status.pack(side="left", padx=(6, 0))

        def make_page(name):
            p = tk.Frame(body, bg=BG)
            p.grid(row=0, column=0, sticky="nsew")
            pages[name] = p
            return p

        def head(parent, title, sub):
            tk.Label(parent, text=title, font=("Segoe UI", 16, "bold"),
                     fg=TXT, bg=BG).pack(anchor="w", padx=20, pady=(16, 0))
            tk.Label(parent, text=sub, font=("Segoe UI", 9), fg=MUTED, bg=BG,
                     wraplength=540, justify="left").pack(anchor="w", padx=20, pady=(2, 0))

        def card(parent, pady=8):
            c = tk.Frame(parent, bg=PANEL, highlightthickness=1,
                         highlightbackground=EDGE)
            c.pack(fill="x", padx=20, pady=(8, pady))
            return c

        def btn_primary(parent, text, cmd, font_size=13, **kw):
            return tk.Button(parent, text=text, command=cmd,
                             font=("Segoe UI", font_size, "bold"),
                             bg=GOLD, fg="#ffffff", activebackground=GOLD_LT,
                             activeforeground="#ffffff", disabledforeground="#bfdbfe",
                             relief="flat", cursor="hand2", bd=0, **kw)

        def btn_ghost(parent, text, cmd, **kw):
            return tk.Button(parent, text=text, command=cmd,
                             font=("Segoe UI", 9, "bold"),
                             bg=CARD, fg=TXT, activebackground="#dfe6ef",
                             activeforeground=TXT, relief="flat", cursor="hand2",
                             bd=0, padx=12, pady=7, **kw)

        # ===== TRANG: DANG WEB =====
        p_web = make_page("web")
        head(p_web, "Đăng web",
             "Chọn file → ghi chú → bấm nút xanh. App tự sao lưu, đẩy lên GitHub và cập nhật web.")

        c1 = card(p_web, pady=4)
        tk.Label(c1, text="BƯỚC 1 — CHỌN FILE HTML", font=("Segoe UI", 8, "bold"),
                 fg=MUTED, bg=PANEL).pack(anchor="w", padx=14, pady=(10, 2))
        r1 = tk.Frame(c1, bg=PANEL)
        r1.pack(fill="x", padx=14, pady=(0, 10))
        self.file_lbl = tk.Label(r1, text=os.path.basename(self.html_file),
                                 font=("Segoe UI", 11, "bold"), fg=GOLD, bg=PANEL)
        self.file_lbl.pack(side="left", fill="x", expand=True)
        btn_ghost(r1, "Chọn file...", self.pick_file).pack(side="right")

        c2 = card(p_web, pady=10)
        tk.Label(c2, text="BƯỚC 2 — GHI CHÚ BẢN ĐĂNG", font=("Segoe UI", 8, "bold"),
                 fg=MUTED, bg=PANEL).pack(anchor="w", padx=14, pady=(10, 2))
        self.msg = tk.Entry(c2, font=("Segoe UI", 11), bg="#f8fafc", fg=TXT,
                            insertbackground=GOLD, relief="flat",
                            highlightthickness=1, highlightbackground=EDGE,
                            highlightcolor=GOLD)
        self.msg.insert(0, "Cap nhat web")
        self.msg.pack(fill="x", padx=14, ipady=7, pady=(0, 12))

        self.btn = btn_primary(p_web, "🚀  ĐĂNG LÊN WEB NGAY", self.start, font_size=14)
        self.btn.pack(fill="x", padx=20, pady=(2, 4), ipady=6)

        r2 = tk.Frame(p_web, bg=BG)
        r2.pack(fill="x", padx=20, pady=(4, 0))
        btn_ghost(r2, "Đăng nhanh: Trang chính",
                  lambda: self.start_one("Acceleratorares.html", "trang chính")
                  ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        btn_ghost(r2, "Đăng nhanh: Trang admin",
                  lambda: self.start_one("admin.html", "trang admin")
                  ).pack(side="left", fill="x", expand=True, padx=(4, 0))

        r3 = tk.Frame(p_web, bg=BG)
        r3.pack(fill="x", padx=20, pady=(8, 0))
        tk.Checkbutton(r3, text="Tự động sao lưu trước khi đăng / khôi phục",
                       variable=self.auto_var, command=self.save_auto,
                       font=("Segoe UI", 9), bg=BG, fg=TXT,
                       selectcolor="#ffffff", activebackground=BG,
                       activeforeground=TXT, cursor="hand2").pack(side="left")
        self.backup_btn = btn_ghost(r3, "💾  Sao lưu ngay", self.backup)
        self.backup_btn.pack(side="right")

        self.prog = ttk.Progressbar(p_web, style="Blue.Horizontal.TProgressbar",
                                    mode="determinate", maximum=100, value=0)
        self.prog.pack(fill="x", padx=20, pady=(8, 8))

        lc = tk.Frame(p_web, bg=PANEL, highlightthickness=1, highlightbackground=EDGE)
        lc.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        tk.Label(lc, text="NHẬT KÝ HOẠT ĐỘNG", font=("Segoe UI", 8, "bold"),
                 fg=MUTED, bg=PANEL).pack(anchor="w", padx=14, pady=(10, 4))
        self.log = scrolledtext.ScrolledText(lc, font=("Consolas", 9),
                                             bg="#0f172a", fg="#e2e8f0",
                                             insertbackground="#e2e8f0",
                                             relief="flat", height=8)
        self.log.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        self.log.configure(state="disabled")

        # ===== TRANG: SUA WEB =====
        p_sua = make_page("sua")
        head(p_sua, "Sửa web",
             "Chọn phần cần sửa. Sửa xong nhớ sang “Đăng web” để đưa lên.")

        seg = tk.Frame(p_sua, bg=BG)
        seg.pack(fill="x", padx=20, pady=(10, 0))
        seg_btns = {}
        subc = tk.Frame(p_sua, bg=BG)
        subc.pack(fill="both", expand=True, padx=20, pady=(8, 16))
        subc.grid_rowconfigure(0, weight=1)
        subc.grid_columnconfigure(0, weight=1)
        sp1 = tk.Frame(subc, bg=BG)
        sp2 = tk.Frame(subc, bg=BG)
        sp3 = tk.Frame(subc, bg=BG)
        for sp in (sp1, sp2, sp3):
            sp.grid(row=0, column=0, sticky="nsew")

        def pick_seg(k):
            for kk, bb in seg_btns.items():
                if kk == k:
                    bb.configure(bg=GOLD, fg="#ffffff", highlightbackground=GOLD)
                else:
                    bb.configure(bg=PANEL, fg=TXT, highlightbackground=EDGE)
            {"chu": sp1, "anh": sp2, "video": sp3}[k].tkraise()

        for k, label in [("chu", "📝  Chữ trên web"), ("anh", "🖼️  Ảnh"),
                         ("video", "🎬  Video")]:
            b = tk.Button(seg, text=label, font=("Segoe UI", 10, "bold"),
                          bg=PANEL, fg=TXT, activebackground="#dfe6ef",
                          activeforeground=TXT, relief="flat", bd=0,
                          padx=16, pady=8, cursor="hand2",
                          highlightthickness=1, highlightbackground=EDGE)
            b.configure(command=lambda kk=k: pick_seg(kk))
            b.pack(side="left", padx=(0, 6))
            seg_btns[k] = b

        cA = tk.Frame(sp1, bg=PANEL, highlightthickness=1, highlightbackground=EDGE)
        cA.pack(fill="both", expand=True)
        tk.Label(cA, text="CHỮ HIỂN THỊ TRÊN WEB", font=("Segoe UI", 8, "bold"),
                 fg=MUTED, bg=PANEL).pack(anchor="w", padx=14, pady=(10, 2))
        self.content_vars = {}
        cf = tk.Frame(cA, bg=PANEL)
        cf.pack(fill="both", expand=True, padx=14)
        for key, label in [("title", "Tiêu đề (cạnh avatar)"),
                           ("welcome", "Dòng chào mừng"),
                           ("shopname", "Tên shop"),
                           ("shopdesc", "Mô tả shop"),
                           ("shoplink", "Link shop"),
                           ("cskhlink", "Link CSKH")]:
            tk.Label(cf, text=label, font=("Segoe UI", 9, "bold"),
                     fg=MUTED, bg=PANEL).pack(anchor="w", pady=(5, 2))
            var = tk.StringVar()
            self.content_vars[key] = var
            tk.Entry(cf, textvariable=var, font=("Segoe UI", 10),
                     bg="#f8fafc", fg=TXT, insertbackground=GOLD, relief="flat",
                     highlightthickness=1, highlightbackground=EDGE,
                     highlightcolor=GOLD).pack(fill="x", ipady=6)
        fr6 = tk.Frame(cA, bg=PANEL)
        fr6.pack(fill="x", padx=14, pady=12)
        btn_ghost(fr6, "↻  Tải nội dung hiện tại", self.content_load).pack(side="left")
        btn_primary(fr6, "💾  LƯU THAY ĐỔI", self.content_save, font_size=10,
                    padx=14, pady=8).pack(side="right")
        self.content_msg = tk.Label(cA, text="", font=("Segoe UI", 9),
                                    fg=GOLD, bg=PANEL)
        self.content_msg.pack(padx=14, pady=(0, 10), anchor="w")

        cB = tk.Frame(sp2, bg=PANEL, highlightthickness=1, highlightbackground=EDGE)
        cB.pack(fill="x")
        tk.Label(cB, text="AVATAR & LOGO", font=("Segoe UI", 8, "bold"),
                 fg=MUTED, bg=PANEL).pack(anchor="w", padx=14, pady=(10, 4))
        self.img_rows = {}
        for key, label, fname in [("avatar", "Avatar (cạnh tiêu đề + icon tab)", "avatar.jpg"),
                                  ("logo", "Logo Teyvat Store", "shop-logo.jpg")]:
            row = tk.Frame(cB, bg=PANEL)
            row.pack(fill="x", padx=14, pady=(2, 10))
            tk.Label(row, text=label, font=("Segoe UI", 10, "bold"),
                     fg=TXT, bg=PANEL).pack(anchor="w")
            subrow = tk.Frame(row, bg=PANEL)
            subrow.pack(fill="x", pady=(4, 0))
            lbl = tk.Label(subrow, text=fname, font=("Segoe UI", 9), fg=MUTED, bg=PANEL)
            lbl.pack(side="left", fill="x", expand=True)
            self.img_rows[key] = (fname, lbl)
            btn_ghost(subrow, "Chọn ảnh...",
                      lambda k=key: self.pick_image(k)).pack(side="right")
        self.img_msg = tk.Label(sp2, text="", font=("Segoe UI", 9), fg=GOLD, bg=BG)
        self.img_msg.pack(padx=2, pady=8, anchor="w")

        cC = tk.Frame(sp3, bg=PANEL, highlightthickness=1, highlightbackground=EDGE)
        cC.pack(fill="x")
        tk.Label(cC, text="UPLOAD VIDEO LÊN WEB (tối đa 100MB)", font=("Segoe UI", 8, "bold"),
                 fg=MUTED, bg=PANEL).pack(anchor="w", padx=14, pady=(10, 2))
        cfg = load_cfg()
        vf = tk.Frame(cC, bg=PANEL)
        vf.pack(fill="x", padx=14)
        tk.Label(vf, text="Tên video", font=("Segoe UI", 9, "bold"),
                 fg=MUTED, bg=PANEL).pack(anchor="w", pady=(2, 2))
        self.vd_title = tk.Entry(vf, font=("Segoe UI", 10), bg="#f8fafc", fg=TXT,
                                 insertbackground=GOLD, relief="flat",
                                 highlightthickness=1, highlightbackground=EDGE,
                                 highlightcolor=GOLD)
        self.vd_title.pack(fill="x", ipady=6)
        self.vd_file_lbl = tk.Label(vf, text="File video: chưa chọn", font=("Segoe UI", 9),
                                      fg=MUTED, bg=PANEL, wraplength=520, justify="left")
        self.vd_file_lbl.pack(anchor="w", pady=(8, 0))
        self.vd_file = None
        fr7 = tk.Frame(cC, bg=PANEL)
        fr7.pack(fill="x", padx=14, pady=10)
        btn_ghost(fr7, "Chọn video...", self.pick_video).pack(side="left")
        self.vd_btn = btn_primary(fr7, "⬆️  UPLOAD", self.start_vdupload, font_size=10,
                                  padx=14, pady=8)
        self.vd_btn.pack(side="right")
        self.vd_prog = ttk.Progressbar(cC, style="Blue.Horizontal.TProgressbar",
                                       mode="determinate", maximum=100, value=0)
        self.vd_prog.pack(fill="x", padx=14, pady=(0, 10))
        tk.Label(cC, text="Tài khoản admin (để lưu video vào web)", font=("Segoe UI", 9, "bold"),
                 fg=MUTED, bg=PANEL).pack(anchor="w", padx=14, pady=(2, 2))
        af = tk.Frame(cC, bg=PANEL)
        af.pack(fill="x", padx=14, pady=(0, 12))
        self.vd_email = tk.Entry(af, font=("Segoe UI", 10), bg="#f8fafc", fg=TXT,
                                 insertbackground=GOLD, relief="flat", width=26,
                                 highlightthickness=1, highlightbackground=EDGE,
                                 highlightcolor=GOLD)
        self.vd_email.insert(0, cfg.get("admin_email", ""))
        self.vd_email.pack(side="left", ipady=6)
        self.vd_pass = tk.Entry(af, font=("Segoe UI", 10), bg="#f8fafc", fg=TXT,
                                insertbackground=GOLD, relief="flat", width=18, show="•",
                                highlightthickness=1, highlightbackground=EDGE,
                                highlightcolor=GOLD)
        self.vd_pass.insert(0, cfg.get("admin_pass", ""))
        self.vd_pass.pack(side="left", padx=(8, 0), ipady=6)
        tk.Label(sp3, text="Mật khẩu chỉ lưu trên máy bạn.", font=("Segoe UI", 8),
                 fg=MUTED, bg=BG).pack(anchor="w", pady=(6, 2))
        self.vd_msg = tk.Label(sp3, text="", font=("Segoe UI", 9),
                               fg=GOLD, bg=BG, wraplength=540, justify="left")
        self.vd_msg.pack(padx=2, pady=4, anchor="w", fill="x")

        # ===== TRANG: MAY CHU =====
        p_mc = make_page("maychu")
        head(p_mc, "Máy chủ tải video",
             "Bật khi muốn dùng nút “Gửi máy nhà tải” trong trang admin. Server tự mở tunnel cho web và điện thoại.")

        cD = tk.Frame(p_mc, bg=PANEL, highlightthickness=1, highlightbackground=EDGE)
        cD.pack(fill="x", padx=20, pady=(12, 8))
        srow = tk.Frame(cD, bg=PANEL)
        srow.pack(fill="x", padx=14, pady=(12, 0))
        self.yt_dot = tk.Label(srow, text="●", font=("Segoe UI", 14), fg=MUTED, bg=PANEL)
        self.yt_dot.pack(side="left")
        self.yt_lbl = tk.Label(srow, text="Đang kiểm tra...", font=("Segoe UI", 11, "bold"),
                              fg=TXT, bg=PANEL)
        self.yt_lbl.pack(side="left", padx=(8, 0))
        tk.Label(cD, text="BẬT SERVER sẽ tự mở tunnel, web Vercel và điện thoại gọi được ngay.\n"
                          "Địa chỉ tunnel tự ghi vào Firebase, không cần cấu hình gì thêm.",
                 font=("Segoe UI", 9), fg=MUTED, bg=PANEL, wraplength=520,
                 justify="left").pack(anchor="w", padx=14, pady=(12, 0))
        bfr = tk.Frame(cD, bg=PANEL)
        bfr.pack(fill="x", padx=14, pady=(12, 0))
        btn_primary(bfr, "▶  BẬT SERVER", self.yt_start, font_size=11,
                    padx=14, pady=8).pack(side="left", fill="x", expand=True, padx=(0, 4))
        btn_ghost(bfr, "⏹  TẮT SERVER", self.yt_stop).pack(side="left", fill="x", expand=True, padx=(4, 0))
        urow = tk.Frame(cD, bg=PANEL)
        urow.pack(fill="x", padx=14, pady=(10, 12))
        self.yt_url_lbl = tk.Label(urow, text="", font=("Segoe UI", 9), fg=GOLD, bg=PANEL,
                                  wraplength=430, justify="left")
        self.yt_url_lbl.pack(side="left", fill="x", expand=True)
        btn_ghost(urow, "📋 Copy", self.yt_copy_url).pack(side="right")
        self.yt_msg = tk.Label(p_mc, text="", font=("Segoe UI", 9), fg=GOLD, bg=BG,
                               wraplength=540, justify="left")
        self.yt_msg.pack(padx=22, pady=(4, 0), anchor="w", fill="x")

        lc2 = tk.Frame(p_mc, bg=PANEL, highlightthickness=1, highlightbackground=EDGE)
        lc2.pack(fill="both", expand=True, padx=20, pady=(8, 16))
        hdr2 = tk.Frame(lc2, bg=PANEL)
        hdr2.pack(fill="x", padx=14, pady=(10, 4))
        tk.Label(hdr2, text="NHẬT KÝ MÁY CHỦ  (lưu vào yt-server\\server.log)",
                 font=("Segoe UI", 8, "bold"), fg=MUTED, bg=PANEL).pack(side="left")
        btn_ghost(hdr2, "Xóa log", self.yt_log_clear).pack(side="right")
        self.slog_box = scrolledtext.ScrolledText(lc2, font=("Consolas", 9),
                                                  bg="#0f172a", fg="#e2e8f0",
                                                  insertbackground="#e2e8f0",
                                                  relief="flat", height=9)
        self.slog_box.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        self.slog_box.configure(state="disabled")
        self.yt_slog_load()
        threading.Thread(target=self.yt_refresh, daemon=True).start()

        # ===== TRANG: LICH SU =====
        p_ls = make_page("lichsu")
        head(p_ls, "Lịch sử & Khôi phục",
             "Chọn 1 bản trong danh sách rồi bấm “Khôi phục bản này” để đưa web về đúng bản đó.")

        cE = tk.Frame(p_ls, bg=PANEL, highlightthickness=1, highlightbackground=EDGE)
        cE.pack(fill="both", expand=True, padx=20, pady=(12, 8))
        self.hist = tk.Listbox(cE, font=("Consolas", 10), bg="#ffffff", fg=TXT,
                               selectbackground="#dbeafe", selectforeground="#1e3a8a",
                               relief="flat", activestyle="none", height=12,
                               highlightthickness=0)
        self.hist.pack(side="left", fill="both", expand=True, padx=(2, 0), pady=2)
        sb = tk.Scrollbar(cE, command=self.hist.yview)
        sb.pack(side="right", fill="y", pady=2)
        self.hist.configure(yscrollcommand=sb.set)

        r4 = tk.Frame(p_ls, bg=BG)
        r4.pack(fill="x", padx=20, pady=(0, 16))
        btn_ghost(r4, "↻  Làm mới",
                  lambda: threading.Thread(target=self.load_hist, daemon=True).start()
                  ).pack(side="left")
        tk.Button(r4, text="⏪  KHÔI PHỤC BẢN NÀY", font=("Segoe UI", 10, "bold"),
                  bg="#fee2e2", fg="#b91c1c", activebackground="#fecaca",
                  activeforeground="#b91c1c", relief="flat", bd=0, padx=14, pady=8,
                  cursor="hand2", command=self.ask_restore).pack(side="right")
        threading.Thread(target=self.load_hist, daemon=True).start()

        # ===== TRANG: MO NHANH =====
        p_mo = make_page("mo")
        head(p_mo, "Mở nhanh", "Bấm để mở các trang liên quan.")
        for i, (label, url) in enumerate(URLS):
            tk.Button(p_mo, text=label, font=("Segoe UI", 11, "bold"),
                      bg=PANEL, fg=TXT, activebackground="#dfe6ef",
                      activeforeground=GOLD, relief="flat", bd=0, anchor="w",
                      cursor="hand2", padx=16, pady=10,
                      highlightthickness=1, highlightbackground=EDGE,
                      command=lambda u=url: webbrowser.open(u)
                      ).pack(fill="x", padx=20, pady=3)

        # ===== TRANG: SUC KHOE =====
        p_sk = make_page("suckhoe")
        head(p_sk, "Sức khỏe",
             "Kiểm tra máy có đủ đồ nghề để deploy không. Thiếu gì app sẽ báo.")
        r5 = tk.Frame(p_sk, bg=BG)
        r5.pack(fill="x", padx=20, pady=(12, 8))
        btn_ghost(r5, "🩺  KIỂM TRA MÁY", self.health_check).pack(side="left")
        tk.Button(r5, text="🔨  BUILD LẠI FILE EXE", font=("Segoe UI", 9, "bold"),
                  bg="#dcfce7", fg="#166534", activebackground="#bbf7d0",
                  activeforeground="#166534", relief="flat", bd=0, padx=14, pady=7,
                  cursor="hand2", command=self.rebuild_exe).pack(side="right")
        cF = tk.Frame(p_sk, bg=PANEL, highlightthickness=1, highlightbackground=EDGE)
        cF.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        self.hlog_box = scrolledtext.ScrolledText(cF, font=("Consolas", 10),
                                                  bg="#0f172a", fg="#e2e8f0",
                                                  insertbackground="#e2e8f0",
                                                  relief="flat", height=14)
        self.hlog_box.pack(fill="both", expand=True, padx=2, pady=2)
        self.hlog_box.configure(state="disabled")

        pick_seg("chu")
        show("web")


        # ===== STATUS BAR =====
        bar = tk.Frame(root, bg=PANEL)
        bar.pack(fill="x", side="bottom")
        tk.Frame(root, bg=EDGE, height=1).pack(fill="x", side="bottom")
        tk.Label(bar, text=SITE_URL, font=("Segoe UI", 9, "bold"), fg=GOLD, bg=PANEL,
                 cursor="hand2").pack(side="left", padx=14, pady=7)
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
        ensure_git_identity()
        if files:
            code, out = run("git add " + " ".join(files), REPO_DIR)
        else:
            code, out = run("git add -A", REPO_DIR)
        if code != 0:
            self.write("LOI git add:\n" + out[-800:])
            return False
        code, out = run('git commit -m "' + note.replace('"', '') + '"', REPO_DIR)
        line = out.strip().splitlines()
        self.write("  " + (line[0] if line else "khong co gi moi"))
        nothing = "nothing to commit" in out.lower() or "khong co gi de commit" in out.lower()
        if code != 0 and not nothing:
            self.write("LOI commit GitHub:\n" + out[-800:])
            return False
        self.set_prog(55)
        code, out = run("git push origin master", REPO_DIR)
        if code != 0:
            self.write("LOI push GitHub:\n" + out[-800:])
            return False
        self.write("  Push GitHub xong.")
        self.set_prog(65)
        self.write("[3/4] Deploy Vercel (cho ~30s)...")
        vx = vercel_exe()
        code, out = run(vx + " deploy --prod --yes", REPO_DIR)
        if code != 0 and "Not authorized" in out:
            self.write("  Gap 'Not authorized' - thu lai sau 8 giay...")
            time.sleep(8)
            code, out = run(vx + " deploy --prod --yes", REPO_DIR)
        ok = code == 0 and ("Aliased" in out or '"status": "ok"' in out
                            or '"readyState": "READY"' in out or "ready." in out)
        if not ok:
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
            for f in ["Acceleratorares.html", "admin.html", "avatar.jpg", "avatar.ico", "shop-logo.jpg", "robots.txt"]:
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
        try:
            self.hist.delete(0, "end")
        except RuntimeError:
            self.root.after(300, self.load_hist)
            return
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

    # ---------- may chu tai video ----------
    YT_PORT = 8799

    def yt_dir(self):
        return os.path.join(REPO_DIR, "yt-server")

    def yt_ping(self):
        try:
            with urllib.request.urlopen("http://127.0.0.1:%d/ping" % self.YT_PORT, timeout=4) as r:
                return json.loads(r.read().decode()).get("ok", False)
        except Exception:
            return False

    def yt_port_busy(self):
        import socket
        try:
            c = socket.create_connection(("127.0.0.1", self.YT_PORT), timeout=2)
            c.close()
            return True
        except Exception:
            return False

    def yt_refresh(self):
        on = self.yt_ping()
        try:
            self.yt_dot.configure(fg="#4caf6d" if on else MUTED)
            self.yt_lbl.configure(text=("Đang chạy (cổng %d)" % self.YT_PORT) if on else "Đang tắt")
        except Exception:
            pass

    def yt_log_path(self):
        return os.path.join(self.yt_dir(), "server.log")

    def yt_log_write(self, line):
        try:
            with open(self.yt_log_path(), "a", encoding="utf-8") as f:
                f.write(datetime.now().strftime("[%d/%m %H:%M:%S] ") + line.rstrip() + "\n")
        except Exception:
            pass

    def yt_slog(self, line):
        try:
            self.slog_box.configure(state="normal")
            self.slog_box.insert("end", datetime.now().strftime("[%H:%M:%S] ")
                                 + line.rstrip() + "\n")
            if int(self.slog_box.index("end-1c").split(".")[0]) > 400:
                self.slog_box.delete("1.0", "100.0")
            self.slog_box.see("end")
            self.slog_box.configure(state="disabled")
        except Exception:
            pass
        self.yt_log_write(line)

    def yt_slog_load(self):
        try:
            p = self.yt_log_path()
            if not os.path.exists(p):
                return
            with open(p, encoding="utf-8", errors="replace") as f:
                lines = f.readlines()[-80:]
            self.slog_box.configure(state="normal")
            for ln in lines:
                self.slog_box.insert("end", ln if ln.endswith("\n") else ln + "\n")
            self.slog_box.see("end")
            self.slog_box.configure(state="disabled")
        except Exception:
            pass

    def yt_log_clear(self):
        try:
            self.slog_box.configure(state="normal")
            self.slog_box.delete("1.0", "end")
            self.slog_box.configure(state="disabled")
            with open(self.yt_log_path(), "w", encoding="utf-8"):
                pass
        except Exception:
            pass

    def yt_log_reader(self, proc):
        try:
            for line in iter(proc.stdout.readline, ""):
                if line == "":
                    break
                self.yt_slog(line)
        except Exception:
            pass
        self.yt_slog("(server đã dừng)")

    def yt_need(self):
        missing = []
        if not shutil.which("node"):
            missing.append("Node.js")
        if not os.path.exists(os.path.join(self.yt_dir(), "server.js")):
            missing.append("yt-server/server.js")
        if not os.path.exists(os.path.join(REPO_DIR, "tools", "yt-dlp.exe")):
            missing.append("tools/yt-dlp.exe")
        if not os.path.exists(os.path.join(REPO_DIR, "tools", "ffmpeg.exe")):
            missing.append("tools/ffmpeg.exe")
        if not os.path.exists(os.path.join(REPO_DIR, "tools", "cloudflared.exe")):
            missing.append("tools/cloudflared.exe")
        return missing

    def yt_start(self):
        miss = self.yt_need()
        if miss:
            try:
                self.yt_msg.configure(text="Thiếu: " + ", ".join(miss))
            except Exception:
                pass
            return
        if self.yt_port_busy():
            try:
                self.yt_msg.configure(text="Cổng %d đang bận (server cũ vẫn chạy)! Bấm TẮT trước." % self.YT_PORT)
            except Exception:
                pass
            self.yt_refresh()
            return
        try:
            env = dict(os.environ)
            env["YT_TUNNEL"] = "1"
            if os.path.exists(self.yt_log_path()):
                try:
                    if os.path.getsize(self.yt_log_path()) > 1000000:
                        os.remove(self.yt_log_path())
                except Exception:
                    pass
            self.yt_proc = subprocess.Popen(
                [shutil.which("node"), "server.js"], cwd=self.yt_dir(), env=env,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", bufsize=1)
            self.yt_slog("=== BẮT ĐẦU SERVER (kem tunnel) ===")
            threading.Thread(target=self.yt_log_reader, args=(self.yt_proc,),
                             daemon=True).start()
        except Exception as e:
            try:
                self.yt_msg.configure(text="Không mở được server: " + str(e))
            except Exception:
                pass
            return
        try:
            self.yt_msg.configure(text="Đang mở server...")
            self.yt_url_lbl.configure(text="")
        except Exception:
            pass
        threading.Thread(target=self.yt_watch_base, daemon=True).start()
        threading.Thread(target=self.yt_wait_up, daemon=True).start()

    def yt_wait_up(self):
        for _ in range(20):
            time.sleep(1)
            if self.yt_ping():
                break
        self.yt_refresh()
        try:
            if self.yt_ping():
                self.yt_msg.configure(text="Server ĐANG CHẠY. Vào /admin bấm 'Tải bằng máy nhà' được rồi.")
            else:
                self.yt_msg.configure(text="Server không lên! Kiểm tra lại Node/tools.")
        except Exception:
            pass

    def yt_watch_base(self):
        for _ in range(40):
            time.sleep(5)
            try:
                with urllib.request.urlopen(FB_DB_URL + "/settings/ytServerBase.json", timeout=20) as r:
                    url = json.loads(r.read().decode())
                if url:
                    self.yt_url = url
                    try:
                        self.yt_url_lbl.configure(text="Địa chỉ chung: " + url)
                        self.yt_msg.configure(text="Tunnel đã lên, địa chỉ tự vào web rồi ✔")
                    except Exception:
                        pass
                    return
            except Exception:
                pass
        try:
            self.yt_msg.configure(text="Chưa thấy tunnel lên (quá 3 phút). Kiểm tra cửa sổ server.")
        except Exception:
            pass

    def yt_watch_tunnel(self):
        # Khong dung nua: server tu nuoi tunnel (YT_TUNNEL=1), app chi hien thi qua yt_watch_base.
        return

    def yt_copy_url(self):
        url = getattr(self, "yt_url", "")
        if not url:
            try:
                self.yt_msg.configure(text="Chưa có địa chỉ tunnel (đợi vài giây sau khi bật server).")
            except Exception:
                pass
            return
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(url)
            self.yt_msg.configure(text="Đã copy: " + url)
        except Exception as e:
            try:
                self.yt_msg.configure(text="Không copy được: " + str(e))
            except Exception:
                pass

    def yt_push_base(self, url):
        try:
            cfg = load_cfg()
            email = cfg.get("admin_email", "")
            pw = cfg.get("admin_pass", "")
            if not email or not pw:
                return "chưa tự dán được (nhập email/pass ở tab Video một lần để tự dán)"
            token = self.fb_token(email, pw)
            if not token:
                return "chưa tự dán được (sai email/pass admin)"
            req = urllib.request.Request(
                FB_DB_URL + "/settings/ytServerBase.json?auth=" + token,
                data=json.dumps(url).encode(),
                headers={"Content-Type": "application/json"}, method="PUT")
            urllib.request.urlopen(req, timeout=30).read()
            return "đã tự dán vào web ✔" if url else "đã gỡ khỏi web ✔"
        except Exception as e:
            return "chưa tự dán được (" + str(e)[:80] + ")"

    def yt_unpush(self):
        url = getattr(self, "yt_pushed", "")
        if not url:
            return
        try:
            with urllib.request.urlopen(FB_DB_URL + "/settings/ytServerBase.json", timeout=20) as r:
                cur = json.loads(r.read().decode())
        except Exception:
            return
        if cur != url:
            return
        self.yt_pushed = ""
        self.yt_push_base("")

    def yt_stop(self):
        killed = self.yt_kill_port()
        for attr in ("yt_proc", "yt_tun"):
            try:
                pr = getattr(self, attr, None)
                if pr is not None and pr.poll() is None:
                    pr.terminate()
            except Exception:
                pass
        try:
            self.yt_url = ""
            self.yt_pushed = ""
            self.yt_url_lbl.configure(text="")
            self.yt_msg.configure(text="Đang tắt + gỡ địa chỉ khỏi web...")
        except Exception:
            pass
        self.yt_slog("=== ĐÃ TẮT SERVER ===")
        threading.Thread(target=self.yt_unpush, daemon=True).start()
        self.yt_refresh()

    def yt_kill_port(self):
        try:
            code, out = run("netstat -ano -p TCP", REPO_DIR)
            pids = set()
            for line in out.splitlines():
                if (":%d" % self.YT_PORT) in line:
                    parts = line.split()
                    if parts and parts[-1].isdigit():
                        pids.add(parts[-1])
            hit = False
            for pid in pids:
                c2, nm = run("tasklist /FI \"PID eq %s\" /FO CSV /NH" % pid, REPO_DIR)
                low = nm.lower()
                if "node.exe" in low or "cloudflared.exe" in low:
                    run("taskkill /F /PID %s" % pid, REPO_DIR)
                    hit = True
            return hit
        except Exception:
            return False

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
                          ("Vercel CLI", vercel_exe() + " --version"),
                          ("Python", "python --version")]:
            code, out = run(cmd)
            ver = (out.strip().splitlines()[0] if out.strip() else "")
            good = (code == 0 and ver != "")
            ok_all = ok_all and good
            self.hlog(("✔ " if good else "✘ THIEU ") + name + ((" — " + ver) if good else " (can cai dat)"))
        code, out = run(vercel_exe() + " whoami")
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
        for name, p in [("yt-dlp", "tools/yt-dlp.exe"), ("ffmpeg", "tools/ffmpeg.exe"),
                        ("cloudflared", "tools/cloudflared.exe")]:
            ok = os.path.exists(os.path.join(REPO_DIR, p))
            self.hlog(("✔ " if ok else "○ ") + name + ("" if ok else " (thieu - tab May chu can)"))

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
            code, out = run("python -m PyInstaller --onefile --windowed --name DeployWeb --icon avatar.ico --noconfirm --distpath dist_app deploy_app.py", REPO_DIR)
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
            self.btn.configure(text="🚀  ĐĂNG LÊN WEB NGAY")
        else:
            self.set_state(False, "Có lỗi!", "#e05a5a")
            self.set_prog(0)


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
