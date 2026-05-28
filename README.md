# Wiki Plaintext Downloader

A high-speed, multi-threaded extraction tool for MediaWiki, Fandom, and Telepedia sites. It converts wiki content into clean, structured plaintext dumps.

## Features

*   **Deep Extraction:** Multi-threaded (8 workers) parallel engine for maximum speed.
*   **Brutalist UI:** Extremely lightweight, text-forward interface (1MB Club compliant).
*   **Real-time Logs:** See progress directly in the browser as pages are downloaded.
*   **Privacy First:** No tracking, no frameworks, no cookies.
*   **Legacy Design:** Robust table-based layout using Tahoma/Times New Roman.

## Usage

1.  Enter the URL of a MediaWiki, Fandom, or Telepedia site (e.g., `https://witchhatatelier.telepedia.net/`).
2.  Click **EXECUTE**.
3.  Monitor the real-time log output.
4.  The `.txt` dump will download automatically once the extraction is complete.

## Development

### Local Setup
```bash
pip install -r requirements.txt
python wiki_plaintext_downloader.py
```

### Vercel Deployment
The project is configured for Vercel via `vercel.json` and `api/index.py`.

## License
MIT
