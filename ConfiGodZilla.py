"""
ConfiGodZilla Subscription Tool
--------------------------------
Fetches configs from a V2Ray/Xray-style subscription URL, renames every
config's title (remark) to a custom name chosen by the user + a sequence
number, re-encodes everything as a standard base64 subscription, uploads
it to paste.rs, and copies the resulting subscription link to the
clipboard.

Requirements:
    pip install requests

Note: tkinter normally ships with Python. On Linux, if missing:
    sudo apt install python3-tk
"""

import tkinter as tk
from tkinter import ttk, messagebox
import requests
import base64
import json
import threading
import itertools
import urllib.parse


# Public API of paste.rs, created by Sergio Benitez — https://github.com/SergioBenitez/rktpb
PASTE_URL = "https://paste.rs/"
LINK_VALIDITY_NOTE = "valid ~30 days (paste.rs default retention)"

# Schemes whose display title lives in the URI fragment, after "#"
FRAGMENT_BASED_SCHEMES = (
    "vless://", "trojan://", "ss://", "hysteria2://", "hy2://", "tuic://"
)


# ------------------ Config Renaming ------------------

def rename_config(config: str, base_name: str, index: int) -> str:
    """Sets the display title (remark) of a single config line to
    '<base_name>-<index>', so configs stay easy to tell apart in a
    client app, while every other field (server, port, credentials,
    etc.) stays untouched."""
    new_title = f"{base_name}-{index}"

    if config.startswith("vmess://"):
        try:
            payload = config[len("vmess://"):]
            padded = payload + "=" * (-len(payload) % 4)
            data = json.loads(base64.b64decode(padded).decode("utf-8"))
            data["ps"] = new_title
            new_payload = base64.b64encode(
                json.dumps(data, ensure_ascii=False).encode("utf-8")
            ).decode("utf-8")
            return "vmess://" + new_payload
        except Exception:
            return config  # malformed/unsupported vmess payload: leave untouched

    if config.startswith(FRAGMENT_BASED_SCHEMES):
        base = config.split("#", 1)[0]
        return f"{base}#{urllib.parse.quote(new_title)}"

    return config  # unrecognized scheme: keep as-is rather than risk breaking it


# ------------------ Logic ------------------

def process_subscription_thread():
    url = url_entry.get().strip()
    base_name = name_entry.get().strip()

    if not url:
        messagebox.showerror("Error", "Please enter a subscription URL")
        return

    if not base_name:
        messagebox.showerror("Error", "Please enter a custom config name")
        return

    try:
        set_status("Connecting...", "#f1c40f")
        progress.start(10)
        start_spinner()

        response = requests.get(url, timeout=15)
        response.raise_for_status()
        content = response.text.strip()

        set_status("Decoding content...", "#f1c40f")

        try:
            decoded = base64.b64decode(content).decode("utf-8")
            if "vless://" in decoded or "vmess://" in decoded or "trojan://" in decoded:
                content = decoded
        except Exception:
            pass

        configs = [c for c in content.splitlines() if c.strip()]

        if not configs:
            set_status("No configs found", "#e67e22")
            stop_spinner()
            progress.stop()
            return

        set_status("Renaming configs...", "#f1c40f")

        renamed_configs = [
            rename_config(c, base_name, i + 1) for i, c in enumerate(configs)
        ]

        set_status("Building subscription link...", "#f1c40f")

        # The full renamed config list must be base64-encoded as one
        # block, exactly like a standard subscription payload.
        joined = "\n".join(renamed_configs)
        encoded = base64.b64encode(joined.encode("utf-8")).decode("utf-8")

        sub_link, truncated = upload_to_pastebin(encoded)

        link_var.set(sub_link)
        copy_to_clipboard(sub_link)

        if truncated:
            set_status(
                f"⚠️ {len(renamed_configs)} configs (link truncated: too large)",
                "#e67e22",
            )
        else:
            set_status(
                f"✅ {len(renamed_configs)} configs renamed - link copied ({LINK_VALIDITY_NOTE})",
                "#2ecc71",
            )

    except Exception as e:
        set_status("Operation failed ❌", "#e74c3c")
        messagebox.showerror("Error", str(e))

    finally:
        stop_spinner()
        progress.stop()


def upload_to_pastebin(text: str):
    """Uploads text to paste.rs and returns (link, was_truncated)."""
    response = requests.post(PASTE_URL, data=text.encode("utf-8"), timeout=15)
    response.raise_for_status()
    link = response.text.strip()
    truncated = response.status_code == 206  # paste exceeded server size limit
    return link, truncated


def copy_to_clipboard(text: str):
    root.clipboard_clear()
    root.clipboard_append(text)
    root.update()


def copy_link_again():
    link = link_var.get()
    if link:
        copy_to_clipboard(link)
        set_status("📋 Link copied again", "#2ecc71")


def process_subscription():
    threading.Thread(target=process_subscription_thread, daemon=True).start()


# ------------------ Spinner ------------------

spinner_cycle = itertools.cycle(["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"])
spinner_running = False


def animate_spinner():
    if spinner_running:
        spinner_label.config(text=next(spinner_cycle))
        root.after(100, animate_spinner)


def start_spinner():
    global spinner_running
    spinner_running = True
    animate_spinner()


def stop_spinner():
    global spinner_running
    spinner_running = False
    spinner_label.config(text="")


# ------------------ UI Helpers ------------------

def set_status(text, color):
    status_label.config(text=text, fg=color)
    root.update_idletasks()


def create_rounded_button(parent, text, command, width=220):

    canvas = tk.Canvas(parent, width=width, height=45,
                        bg="#121212", highlightthickness=0)

    def draw_button(color):
        canvas.delete("all")
        canvas.create_oval(5, 5, 45, 45, fill=color, outline=color)
        canvas.create_oval(width - 45, 5, width - 5, 45, fill=color, outline=color)
        canvas.create_rectangle(25, 5, width - 25, 45, fill=color, outline=color)
        canvas.create_text(width // 2, 23, text=text,
                            fill="white",
                            font=("Segoe UI", 11, "bold"))

    draw_button("#6c5ce7")

    def on_enter(e):
        draw_button("#5a4bcf")

    def on_leave(e):
        draw_button("#6c5ce7")

    canvas.bind("<Enter>", on_enter)
    canvas.bind("<Leave>", on_leave)
    canvas.bind("<Button-1>", lambda e: command())

    return canvas


# ------------------ UI ------------------

root = tk.Tk()
root.title("ConfiGodZilla Subscription Tool")
root.geometry("600x520")
root.resizable(False, False)
root.configure(bg="#121212")

title = tk.Label(root,
                  text="🪐 ConfiGodZilla Subscription Tool",
                  bg="#121212",
                  fg="white",
                  font=("Segoe UI", 14, "bold"))
title.pack(pady=(15, 5))

# ---------- Subscription URL ----------
tk.Label(root, text="Subscription URL", bg="#121212", fg="#aaaaaa",
          font=("Segoe UI", 9)).pack(pady=(10, 2))

url_entry = tk.Entry(root,
                      width=70,
                      font=("Segoe UI", 11),
                      bg="#1e1e1e",
                      fg="white",
                      insertbackground="white",
                      relief="flat")
url_entry.pack(ipady=8)

# ---------- Custom Config Name ----------
tk.Label(root, text="Custom Config Name", bg="#121212", fg="#aaaaaa",
          font=("Segoe UI", 9)).pack(pady=(15, 2))

name_entry = tk.Entry(root,
                       width=70,
                       font=("Segoe UI", 11),
                       bg="#1e1e1e",
                       fg="white",
                       insertbackground="white",
                       relief="flat")
name_entry.pack(ipady=8)

tk.Label(root,
          text="Every config will be titled like this: YourName-1, YourName-2, ...",
          bg="#121212", fg="#666666",
          font=("Segoe UI", 8)).pack(pady=(4, 0))

process_btn = create_rounded_button(root,
                                     "Generate Subscription Link",
                                     process_subscription,
                                     width=260)
process_btn.pack(pady=20)

progress = ttk.Progressbar(root, mode="indeterminate", length=400)
progress.pack(pady=5)

spinner_label = tk.Label(root,
                          text="",
                          bg="#121212",
                          fg="#6c5ce7",
                          font=("Segoe UI", 16))
spinner_label.pack()

# ---------- Output subscription link ----------
link_frame = tk.Frame(root, bg="#121212")
link_frame.pack(pady=10, fill="x", padx=30)

link_var = tk.StringVar()
link_entry = tk.Entry(link_frame,
                       textvariable=link_var,
                       font=("Segoe UI", 10),
                       bg="#1e1e1e",
                       fg="#6c5ce7",
                       insertbackground="white",
                       relief="flat",
                       state="readonly",
                       readonlybackground="#1e1e1e")
link_entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))

copy_btn = create_rounded_button(link_frame, "📋 Copy", copy_link_again, width=100)
copy_btn.pack(side="right")

status_label = tk.Label(root,
                         text="Status: Idle",
                         bg="#121212",
                         fg="#aaaaaa",
                         font=("Segoe UI", 10))
status_label.pack(pady=10)

info_label = tk.Label(
    root,
    text="ℹ️ Links are hosted on paste.rs and remain active for ~30 days by default.",
    bg="#121212",
    fg="#555555",
    font=("Segoe UI", 8),
)
info_label.pack(pady=(0, 10))

root.mainloop()
