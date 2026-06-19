"""
ConfiGodZilla Subscription Tool
A lightweight utility to rename and repack VPN subscription configs.
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog, PhotoImage
import requests
import base64
import json
import threading
import urllib.parse
import os
import sys
import pyperclip

# ----------------------------------------------------------------------
# Path helper for PyInstaller bundled executables
# ----------------------------------------------------------------------
def resource_path(relative_path: str) -> str:
    """Return absolute path to resource, works for dev and for PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
PASTE_URL = "https://paste.rs/"
LINK_VALIDITY_NOTE = "valid ~30 days"

FRAGMENT_BASED_SCHEMES = (
    "vless://", "trojan://", "ss://", "hysteria2://", "hy2://", "tuic://"
)

# ----------------------------------------------------------------------
# Renaming logic
# ----------------------------------------------------------------------
def rename_config(config: str, base_name: str, index: int,
                  replace_keyword: str = "", replace_with: str = "") -> str:
    """
    Rename a single config line (vmess:// or fragment‑based).
    If replace_keyword is non‑empty, perform keyword substitution.
    Otherwise, number with base_name.
    """
    if config.startswith("vmess://"):
        try:
            payload = config[len("vmess://"):]
            padded = payload + "=" * (-len(payload) % 4)
            data = json.loads(base64.b64decode(padded).decode("utf-8"))
            current_ps = data.get("ps", "")
            if replace_keyword:
                if replace_keyword in current_ps:
                    data["ps"] = current_ps.replace(replace_keyword, replace_with)
            else:
                data["ps"] = f"{base_name}-{index}"
            new_payload = base64.b64encode(
                json.dumps(data, ensure_ascii=False).encode("utf-8")
            ).decode("utf-8")
            return "vmess://" + new_payload
        except Exception:
            return config

    if config.startswith(FRAGMENT_BASED_SCHEMES):
        base = config.split("#", 1)[0]
        try:
            current_remark = urllib.parse.unquote(config.split("#", 1)[1])
        except IndexError:
            current_remark = ""
        if replace_keyword:
            if replace_keyword in current_remark:
                new_remark = current_remark.replace(replace_keyword, replace_with)
            else:
                new_remark = current_remark
        else:
            new_remark = f"{base_name}-{index}"
        return f"{base}#{urllib.parse.quote(new_remark)}"

    return config

# ----------------------------------------------------------------------
# Decoding subscription content
# ----------------------------------------------------------------------
def decode_subscription(raw: str) -> list[str]:
    """Decode base64 if needed, return list of config lines."""
    content = raw.strip()
    try:
        decoded = base64.b64decode(content + "=" * (-len(content) % 4)).decode("utf-8")
        if any(p in decoded for p in ("vless://", "vmess://", "trojan://",
                                       "ss://", "hysteria", "tuic://")):
            content = decoded
    except Exception:
        pass
    return [line.strip() for line in content.splitlines() if line.strip()]

# ----------------------------------------------------------------------
# paste.rs upload
# ----------------------------------------------------------------------
def upload_to_pastebin(text: str):
    """Upload text to paste.rs and return (url, truncated_flag)."""
    resp = requests.post(PASTE_URL, data=text.encode("utf-8"), timeout=15)
    resp.raise_for_status()
    return resp.text.strip(), resp.status_code == 206

# ----------------------------------------------------------------------
# Background processing thread
# ----------------------------------------------------------------------
def process_thread(root, widgets):
    url_or_configs = widgets["input_text"].get("1.0", "end-1c").strip()
    base_name      = widgets["name_entry"].get().strip() if not widgets["replace_var"].get() else ""
    do_replace     = widgets["replace_var"].get()
    kw_find        = widgets["kw_find_entry"].get().strip()
    kw_replace     = widgets["kw_replace_entry"].get().strip()
    output_mode    = widgets["output_var"].get()

    if not url_or_configs:
        messagebox.showerror("Error", "Please enter a subscription URL or paste config lines.")
        return
    if not do_replace and not base_name:
        messagebox.showerror("Error", "Please enter a custom config name.")
        return
    if do_replace and not kw_find:
        messagebox.showerror("Error", "Please enter the keyword to find for replacement.")
        return

    def set_status(text, color="#b8860b"):
        widgets["status_label"].configure(text=text, text_color=color)
        root.update_idletasks()

    # Show progress bar
    root.after(0, lambda: widgets["progress"].grid())

    try:
        set_status("Parsing input…")
        widgets["progress"].start()

        if url_or_configs.startswith(("http://", "https://")):
            set_status("Fetching subscription…")
            resp = requests.get(url_or_configs, timeout=15)
            resp.raise_for_status()
            raw = resp.text.strip()
        else:
            raw = url_or_configs

        configs = decode_subscription(raw)
        if not configs:
            set_status("No configs found.", "#b8860b")
            return

        set_status(f"Renaming {len(configs)} configs…")

        renamed = []
        for i, cfg in enumerate(configs, 1):
            renamed.append(
                rename_config(
                    cfg,
                    base_name if not do_replace else "",
                    i,
                    replace_keyword=kw_find if do_replace else "",
                    replace_with=kw_replace if do_replace else "",
                )
            )

        if output_mode == "subscription":
            set_status("Uploading to paste.rs…")
            joined = "\n".join(renamed)
            encoded = base64.b64encode(joined.encode("utf-8")).decode("utf-8")
            link, truncated = upload_to_pastebin(encoded)

            widgets["output_var_display"].set(link)
            pyperclip.copy(link)

            if truncated:
                set_status(
                    f"⚠️ {len(renamed)} configs (link truncated)",
                    "#b8860b"
                )
            else:
                set_status(
                    f"✅ {len(renamed)} configs renamed — link copied ({LINK_VALIDITY_NOTE})",
                    "#2e8b57"
                )
        else:
            txt_content = "\n".join(renamed)
            save_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Save renamed configs",
                initialfile=f"{base_name or 'configs'}_configs.txt",
            )
            if save_path:
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(txt_content)
                pyperclip.copy(txt_content)
                widgets["output_var_display"].set(save_path)
                set_status(
                    f"✅ {len(renamed)} configs saved & copied",
                    "#2e8b57"
                )
            else:
                pyperclip.copy(txt_content)
                widgets["output_var_display"].set("(not saved — content copied)")
                set_status(
                    f"✅ {len(renamed)} configs copied to clipboard",
                    "#2e8b57"
                )
    except Exception as e:
        set_status("Operation failed ❌", "#b8860b")
        messagebox.showerror("Error", str(e))
    finally:
        widgets["progress"].stop()
        root.after(0, lambda: widgets["progress"].grid_remove())

# ----------------------------------------------------------------------
# UI Builder
# ----------------------------------------------------------------------
def build_ui():
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    GOLD = "#b8860b"
    GOLD_HOVER = "#daa520"
    BG_WHITE = "#ffffff"
    BG_CARD = "#f8f8f8"
    TEXT_BLACK = "#000000"
    TEXT_GRAY = "#555555"

    root = ctk.CTk()
    root.title("ConfiGodZilla Subscription Tool")
    root.geometry("600x680")
    root.minsize(500, 620)

    # ------------------------------------------------------------------
    # Set window icon (works for both dev and bundled executable)
    # ------------------------------------------------------------------
    def set_icon():
        ico_path = resource_path("myico.ico")

        # Windows taskbar / title bar (uses .ico)
        if os.path.exists(ico_path):
            try:
                root.iconbitmap(default=ico_path)
            except Exception as e:
                print(f"Warning: iconbitmap failed ({e})")

    # Call once immediately, then schedule delayed calls to ensure
    # customtkinter doesn't overwrite the icon later.
    set_icon()
    root.after(300, set_icon)
    root.after(800, set_icon)

    # ------------------------------------------------------------------
    # Grid configuration
    # ------------------------------------------------------------------
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=0)
    root.grid_rowconfigure(1, weight=0)
    root.grid_rowconfigure(2, weight=1)
    root.grid_rowconfigure(3, weight=0)
    root.grid_rowconfigure(4, weight=0)
    root.grid_rowconfigure(5, weight=0)
    root.grid_rowconfigure(6, weight=0)
    root.grid_rowconfigure(7, weight=0)
    root.grid_rowconfigure(8, weight=0)
    root.grid_rowconfigure(9, weight=0)

    widgets = {}

    # ------------------------------------------------------------------
    # Header + Help toggle
    # ------------------------------------------------------------------
    header_frame = ctk.CTkFrame(root, fg_color="transparent")
    header_frame.grid(row=0, column=0, padx=10, pady=(10, 2), sticky="ew")
    header_frame.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(
        header_frame, text="🪐 ConfiGodZilla Subscription Tool",
        font=ctk.CTkFont(size=18, weight="bold"),
        text_color=TEXT_BLACK
    ).grid(row=0, column=0, sticky="w", padx=(0, 10))

    help_visible = False
    def toggle_help():
        nonlocal help_visible
        help_visible = not help_visible
        if help_visible:
            help_frame.grid(row=1, column=0, padx=10, pady=(0, 6), sticky="ew")
            help_btn.configure(text="✖")
        else:
            help_frame.grid_forget()
            help_btn.configure(text="?")

    help_btn = ctk.CTkButton(
        header_frame, text="?", command=toggle_help,
        width=30, height=30, corner_radius=6,
        font=ctk.CTkFont(size=14, weight="bold"),
        fg_color=GOLD, hover_color=GOLD_HOVER, text_color="white"
    )
    help_btn.grid(row=0, column=1, sticky="e")

    # ------------------------------------------------------------------
    # Help frame (hidden by default)
    # ------------------------------------------------------------------
    help_frame = ctk.CTkFrame(root, corner_radius=8, fg_color=BG_CARD)
    help_frame.grid_columnconfigure(0, weight=1)

    help_text = (
        "📘 ConfiGodZilla Help\n\n"
        "1. Input: Paste a subscription URL (https://…) or raw config lines "
        "(vmess, vless, trojan, ss, ...). The tool auto-detects the format.\n\n"
        "2. Custom Name: Choose a base name; configs will be renamed to 'Name-1', 'Name-2', ...\n\n"
        "3. Keyword Replacement: Enable to replace a specific word inside existing remarks "
        "without numbering. The custom name field disappears, and you only specify the keyword "
        "to find and its replacement.\n\n"
        "4. Output:\n"
        "   - Subscription Link: Configs are base64-encoded and uploaded to paste.rs. "
        "The generated link is copied to clipboard (valid ~30 days).\n"
        "   - TXT File: Configs are saved to a local .txt file and also copied to clipboard.\n\n"
        "Note: paste.rs links remain active for approximately 30 days."
    )
    help_box = ctk.CTkTextbox(
        help_frame, corner_radius=6, font=ctk.CTkFont(size=12),
        wrap="word", height=160,
        fg_color=BG_WHITE, text_color=TEXT_BLACK,
        border_color=GOLD, border_width=1
    )
    help_box.insert("0.0", help_text)
    help_box.configure(state="disabled")
    help_box.grid(row=0, column=0, padx=8, pady=(8, 8), sticky="nsew")

    # ------------------------------------------------------------------
    # Input area
    # ------------------------------------------------------------------
    input_frame = ctk.CTkFrame(root, corner_radius=8, fg_color=BG_CARD)
    input_frame.grid(row=2, column=0, padx=10, pady=(0, 6), sticky="nsew")
    input_frame.grid_columnconfigure(0, weight=1)
    input_frame.grid_rowconfigure(2, weight=1)

    ctk.CTkLabel(
        input_frame, text="① Input – Subscription URL or Configs",
        font=ctk.CTkFont(weight="bold", size=13),
        text_color=TEXT_BLACK
    ).grid(row=0, column=0, padx=8, pady=(8, 2), sticky="w")

    ctk.CTkLabel(
        input_frame,
        text="Paste a URL or raw config lines (auto-detect)",
        font=ctk.CTkFont(size=11),
        text_color=TEXT_GRAY
    ).grid(row=1, column=0, padx=8, pady=(0, 4), sticky="w")

    input_text = ctk.CTkTextbox(
        input_frame, corner_radius=6, font=ctk.CTkFont(size=12), wrap="none",
        fg_color=BG_WHITE, text_color=TEXT_BLACK,
        border_color=GOLD, border_width=1
    )
    input_text.grid(row=2, column=0, padx=8, pady=(0, 8), sticky="nsew")
    input_text.configure(height=80)
    widgets["input_text"] = input_text

    # ------------------------------------------------------------------
    # Naming / Replacement area
    # ------------------------------------------------------------------
    name_frame = ctk.CTkFrame(root, corner_radius=8, fg_color=BG_CARD)
    name_frame.grid(row=3, column=0, padx=10, pady=(0, 6), sticky="ew")

    ctk.CTkLabel(
        name_frame, text="② Config Naming",
        font=ctk.CTkFont(weight="bold", size=13),
        text_color=TEXT_BLACK
    ).pack(anchor="w", padx=8, pady=(8, 2))

    custom_name_frame = ctk.CTkFrame(name_frame, fg_color="transparent")
    widgets["custom_name_frame"] = custom_name_frame

    ctk.CTkLabel(
        custom_name_frame, text="Custom Name (e.g. MyServer)",
        font=ctk.CTkFont(size=11),
        text_color=TEXT_GRAY
    ).pack(anchor="w", padx=0, pady=(0, 2))

    name_entry = ctk.CTkEntry(
        custom_name_frame, placeholder_text="MyServer",
        font=ctk.CTkFont(size=12), height=32,
        fg_color=BG_WHITE, text_color=TEXT_BLACK,
        border_color=GOLD
    )
    name_entry.pack(fill="x", padx=0, pady=(0, 4))
    widgets["name_entry"] = name_entry

    replace_var = ctk.BooleanVar(value=False)
    widgets["replace_var"] = replace_var

    replace_check = ctk.CTkCheckBox(
        name_frame,
        text="Enable Keyword Replacement (no numbering)",
        variable=replace_var,
        font=ctk.CTkFont(size=11),
        fg_color=GOLD, hover_color=GOLD_HOVER,
        text_color=TEXT_BLACK
    )
    replace_check.pack(anchor="w", padx=8, pady=(4, 2))

    kw_frame = ctk.CTkFrame(name_frame, fg_color="transparent")
    widgets["kw_frame"] = kw_frame

    ctk.CTkLabel(
        kw_frame, text="Find keyword in current remark:",
        font=ctk.CTkFont(size=11),
        text_color=TEXT_GRAY
    ).pack(anchor="w", pady=(2, 2))

    kw_find_entry = ctk.CTkEntry(
        kw_frame, placeholder_text="Keyword to find",
        font=ctk.CTkFont(size=12), height=30,
        fg_color=BG_WHITE, text_color=TEXT_BLACK,
        border_color=GOLD
    )
    kw_find_entry.pack(fill="x", pady=(0, 2))
    widgets["kw_find_entry"] = kw_find_entry

    ctk.CTkLabel(
        kw_frame, text="Replace with:",
        font=ctk.CTkFont(size=11),
        text_color=TEXT_GRAY
    ).pack(anchor="w", pady=(2, 2))

    kw_replace_entry = ctk.CTkEntry(
        kw_frame, placeholder_text="New keyword",
        font=ctk.CTkFont(size=12), height=30,
        fg_color=BG_WHITE, text_color=TEXT_BLACK,
        border_color=GOLD
    )
    kw_replace_entry.pack(fill="x", pady=(0, 4))
    widgets["kw_replace_entry"] = kw_replace_entry

    def toggle_replacement(*args):
        if replace_var.get():
            custom_name_frame.pack_forget()
            kw_frame.pack(fill="x", padx=8, pady=(0, 4))
        else:
            kw_frame.pack_forget()
            custom_name_frame.pack(fill="x", padx=8, pady=(0, 4))

    replace_var.trace_add("write", toggle_replacement)
    toggle_replacement()

    # ------------------------------------------------------------------
    # Output format
    # ------------------------------------------------------------------
    out_frame = ctk.CTkFrame(root, corner_radius=8, fg_color=BG_CARD)
    out_frame.grid(row=4, column=0, padx=10, pady=(0, 6), sticky="ew")

    ctk.CTkLabel(
        out_frame, text="③ Output Format",
        font=ctk.CTkFont(weight="bold", size=13),
        text_color=TEXT_BLACK
    ).grid(row=0, column=0, padx=8, pady=(8, 4), sticky="w")

    output_var = ctk.StringVar(value="subscription")
    widgets["output_var"] = output_var

    radio_frame = ctk.CTkFrame(out_frame, fg_color="transparent")
    radio_frame.grid(row=1, column=0, padx=8, pady=(0, 8), sticky="ew")

    ctk.CTkRadioButton(
        radio_frame, text="Subscription Link (paste.rs)",
        variable=output_var, value="subscription",
        font=ctk.CTkFont(size=11),
        fg_color=GOLD, hover_color=GOLD_HOVER,
        text_color=TEXT_BLACK
    ).pack(side="left", padx=(0, 20))

    ctk.CTkRadioButton(
        radio_frame, text="TXT File",
        variable=output_var, value="txt",
        font=ctk.CTkFont(size=11),
        fg_color=GOLD, hover_color=GOLD_HOVER,
        text_color=TEXT_BLACK
    ).pack(side="left")

    # ------------------------------------------------------------------
    # Progress bar
    # ------------------------------------------------------------------
    progress = ctk.CTkProgressBar(
        root, mode="indeterminate", height=10, corner_radius=4,
        fg_color="#e0e0e0", progress_color=GOLD
    )
    progress.grid(row=5, column=0, padx=10, pady=(4, 0), sticky="ew")
    progress.grid_remove()
    progress.set(0)
    widgets["progress"] = progress

    def on_process():
        threading.Thread(target=process_thread, args=(root, widgets), daemon=True).start()

    process_btn = ctk.CTkButton(
        root, text="⚡ Process Configs", command=on_process,
        height=34, corner_radius=6, font=ctk.CTkFont(size=13, weight="bold"),
        fg_color=GOLD, hover_color=GOLD_HOVER, text_color="white"
    )
    process_btn.grid(row=6, column=0, padx=10, pady=(8, 4))

    # ------------------------------------------------------------------
    # Result display
    # ------------------------------------------------------------------
    result_frame = ctk.CTkFrame(root, corner_radius=8, fg_color=BG_CARD)
    result_frame.grid(row=7, column=0, padx=10, pady=(0, 4), sticky="ew")

    ctk.CTkLabel(
        result_frame, text="④ Result",
        font=ctk.CTkFont(weight="bold", size=13),
        text_color=TEXT_BLACK
    ).pack(anchor="w", padx=8, pady=(8, 2))

    output_var_display = ctk.StringVar()
    widgets["output_var_display"] = output_var_display

    result_row = ctk.CTkFrame(result_frame, fg_color="transparent")
    result_row.pack(fill="x", padx=8, pady=(2, 8))

    link_entry = ctk.CTkEntry(
        result_row, textvariable=output_var_display,
        font=ctk.CTkFont(size=12), height=30,
        state="readonly", corner_radius=4,
        fg_color=BG_WHITE, text_color=TEXT_BLACK,
        border_color=GOLD
    )
    link_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

    def copy_again():
        val = output_var_display.get()
        if val:
            pyperclip.copy(val)
            widgets["status_label"].configure(text="📋 Copied again", text_color=GOLD)

    copy_btn = ctk.CTkButton(
        result_row, text="📋", command=copy_again,
        width=36, height=28, corner_radius=4, font=ctk.CTkFont(size=12),
        fg_color=GOLD, hover_color=GOLD_HOVER, text_color="white"
    )
    copy_btn.pack(side="right")

    # ------------------------------------------------------------------
    # Status bar
    # ------------------------------------------------------------------
    status_label = ctk.CTkLabel(
        root, text="Status: Idle",
        font=ctk.CTkFont(size=11),
        text_color=TEXT_GRAY
    )
    status_label.grid(row=8, column=0, padx=10, pady=(2, 4), sticky="ew")
    widgets["status_label"] = status_label

    # ------------------------------------------------------------------
    # Footer
    # ------------------------------------------------------------------
    ctk.CTkLabel(
        root,
        text="Subscription links on paste.rs remain active ~30 days.",
        font=ctk.CTkFont(size=10),
        text_color=TEXT_GRAY
    ).grid(row=9, column=0, padx=10, pady=(0, 8), sticky="ew")

    root.mainloop()

# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
if __name__ == "__main__":
    build_ui()

