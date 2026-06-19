## 📺 EDUCATIONAL VIDEO COMING SOON!

> This project was built under the supervision of Artificial Intelligence, with minimal human involvement.
>
> Special thanks to aistudio.google.com and everyone else who contributes to making the world a better place. 🌍

---

# 🪐 ConfiGodZilla Subscription Tool

A modern, lightweight desktop GUI that takes a V2Ray/Xray‑style subscription (URL or raw configs), renames every config remark exactly the way you want, and gives you back either a fresh subscription link or a local `.txt` file — all with a clean white & gold interface.

![Python](https://img.shields.io/badge/python-3.8%2B-blue) ![License](https://img.shields.io/badge/license-MIT-green)

## Screenshots

<table>
  <tr>
    <td align="center" style="padding: 10px 20px;">
      <strong>Windows Version</strong><br><br>
      <img width="493" alt="Screenshot (6)" src="https://github.com/user-attachments/assets/47f2cf45-cb28-4304-aaed-36fc8a12f494" />
    </td>
    <td align="center" style="padding: 10px 20px;">
      <strong>📱 Android Version</strong><br><br>
      <img width="288" alt="photo_2026-06-19_07-08-41" src="https://github.com/user-attachments/assets/ec26654a-2795-44d1-a097-57e1e6bf32d6" />
    </td>
  </tr>
</table>

## ✨ Features

- **Smart input** – paste a subscription URL *or* raw config lines; the tool auto‑detects and decodes base64 content
- **Two renaming modes**
  - **Custom name + numbering** – every config becomes `YourName‑1`, `YourName‑2`, … (keeps your list tidy)
  - **Keyword replacement** – find a specific word inside existing remarks and replace it with a new one, without adding any numbers (useful for quick label updates)
- **Choice of output**
  - **Subscription Link** – base64‑encodes the renamed configs, uploads them to [paste.rs](https://paste.rs), and copies the link to your clipboard (valid ~30 days)
  - **TXT File** – saves all configs to a local `.txt` file and also copies the content to the clipboard
- **Built‑in help** – a handy (?) button opens an embedded guide right inside the app, so you never leave the window
- **Modern UI** – clean white background with dark‑gold accents, larger readable fonts, and a fully responsive layout
- **Custom app icon** – place your own `myico.ico` next to the script and the program will use it
- **Clipboard integration** – both the subscription link and the TXT content are automatically copied to your clipboard

## 🧩 Supported Config Types

| Protocol | Where the title lives | Renamed? |
|---|---|---|
| `vless://` | URI fragment (`#...`) | ✅ |
| `trojan://` | URI fragment (`#...`) | ✅ |
| `ss://` | URI fragment (`#...`) | ✅ |
| `vmess://` | `ps` field inside the base64 JSON payload | ✅ |
| `hysteria2://` / `hy2://` | URI fragment (`#...`) | ✅ |
| `tuic://` | URI fragment (`#...`) | ✅ |
| Anything else | — | Passed through unchanged (never corrupted) |

## 📦 Requirements

- Python 3.8+
- [`requests`](https://pypi.org/project/requests/)
- [`customtkinter`](https://pypi.org/project/customtkinter/) – the modern GUI toolkit
- `tkinter` – ships with most Python installs. On Linux, if missing:
  ```bash
  sudo apt install python3-tk
  ```

Install everything with: 
```bash
pip install -r requirements.txt
```

## 🚀 Installation & Usage
You can download the executable file from the Releases section, or follow the steps below:

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
pip install -r requirements.txt
python configgodzilla.py
```

1. **Input** – paste a subscription URL (starting with `https://`) **or** raw config lines directly into the top box.
2. **Custom Name** – choose a base name (e.g., `MyVPN`) to rename all configs with a sequence number.
3. **(Optional) Keyword Replacement** – tick the checkbox to replace a specific word inside existing remarks instead of adding a new name. The custom name field will disappear and you can type the keyword to find and its replacement.
4. **Output Format** – pick **Subscription Link** (paste.rs) or **TXT File**.
5. Click **⚡ Process Configs**.
6. The result appears in the bottom box and is automatically copied to your clipboard. If you chose TXT, a save dialog will ask where to store the file.
7. Use the **?** button in the top‑right corner for detailed help at any time.

## ⏳ Link Lifetime

Generated links are hosted on the free, open‑source [paste.rs](https://paste.rs) service. Based on its publicly documented default configuration, pastes are kept for approximately **30 days** before automatic deletion. This is paste.rs's own default setting — it isn't something this tool controls or guarantees, so treat it as an estimate.

If you need a link that stays alive indefinitely, consider swapping the upload step for a permanent host such as a GitHub Gist.

## ⚠️ Limitations

- **Upload size:** paste.rs limits individual pastes to ~384 KB. If your renamed subscription exceeds that, the app will warn you that the link was truncated.
- **Network dependency:** both fetching the source subscription and uploading the result require an active internet connection.
- **Rate limiting:** paste.rs heavily rate‑limits the upload endpoint; generating links too frequently may temporarily fail.

## 🛠️ How It Works (under the hood)

1. The input is fetched (URL) or used directly (raw text).
2. If the content is base64‑encoded, it's decoded back into plain config lines.
3. Each line is parsed by protocol and its remark is rewritten according to the chosen mode.
4. **Subscription mode** – all renamed lines are joined, base64‑encoded, `POST`ed to `https://paste.rs/`, and the returned link is copied.
5. **TXT mode** – the renamed lines are saved to a `.txt` file of your choice, and also copied as plain text.
6. The modern GUI is built with `customtkinter`, providing a responsive white & dark‑gold interface with an integrated help panel.

## 🔒 Privacy Note

Subscription links generated by this tool are hosted on paste.rs's **public** instance. Anyone who has the link can view its raw contents — there's no authentication, only the unpredictability of the random paste ID. Treat generated links as public: only share them with people you actually intend to give access to.

## 🙏 Credits

This tool depends on the free, open‑source **[paste.rs](https://paste.rs)** pastebin service, created by [Sergio Benitez](https://github.com/SergioBenitez) ([source code](https://github.com/SergioBenitez/rktpb), licensed under AGPLv3). This project only calls paste.rs's public HTTP API as a client — it doesn't include, modify, or redistribute any of paste.rs's own source code, so no AGPL obligations apply to this repository. Crediting it here is just good practice, not a license requirement.

## 📄 License

MIT — feel free to use, modify, and share.
