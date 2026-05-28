import time
import json
from urllib.parse import urlparse
from flask import Flask, request, Response, stream_with_context, render_template_string
import requests

app = Flask(__name__)

# Vintage 'Coder' Aesthetic HTML Interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>W.P.D. // WIKI_PLAINTEXT_DOWNLOADER</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Courier+Prime:wght@400;700&display=swap');

        :root {
            --bg: #f4f1ea;
            --surface: #edeae0;
            --border: #2b2b2b;
            --text: #1a1a1a;
            --primary: #2563eb;
            --success: #166534;
            --error: #991b1b;
            --dim: #666666;
        }

        body { 
            font-family: 'Courier Prime', 'Courier New', Courier, monospace; 
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 2rem;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .container {
            max-width: 800px;
            width: 100%;
        }

        .header {
            border-bottom: 2px solid var(--border);
            margin-bottom: 2rem;
            padding-bottom: 1rem;
        }

        h1 {
            font-size: 2.5rem;
            margin: 0;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: -2px;
        }

        .tagline {
            font-size: 0.9rem;
            color: var(--dim);
            margin-top: 0.2rem;
        }

        .input-section {
            background: var(--surface);
            border: 2px solid var(--border);
            padding: 1.5rem;
            box-shadow: 4px 4px 0px var(--border);
            margin-bottom: 2rem;
        }

        label {
            display: block;
            font-weight: bold;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            font-size: 0.8rem;
        }

        input[type="url"] {
            width: 100%;
            padding: 0.75rem;
            background: var(--bg);
            border: 2px solid var(--border);
            font-family: inherit;
            font-size: 1rem;
            box-sizing: border-box;
            outline: none;
        }

        input[type="url"]:focus {
            background: #fff;
        }

        .btn {
            margin-top: 1rem;
            width: 100%;
            padding: 1rem;
            background: var(--border);
            color: var(--bg);
            border: none;
            font-family: inherit;
            font-weight: bold;
            font-size: 1rem;
            cursor: pointer;
            text-transform: uppercase;
            transition: all 0.1s;
        }

        .btn:hover {
            background: #444;
        }

        .btn:active {
            transform: translate(2px, 2px);
        }

        .terminal-container {
            border: 2px solid var(--border);
            background: #fff;
            padding: 0;
            box-shadow: 4px 4px 0px var(--border);
            display: none;
        }

        .terminal-header {
            background: var(--border);
            color: var(--bg);
            padding: 0.5rem 1rem;
            font-size: 0.7rem;
            display: flex;
            justify-content: space-between;
        }

        .terminal-body {
            height: 350px;
            overflow-y: auto;
            padding: 1rem;
            font-size: 0.9rem;
            line-height: 1.4;
        }

        .log-entry {
            margin-bottom: 0.2rem;
            white-space: pre-wrap;
        }

        .log-info { color: var(--text); }
        .log-success { color: var(--success); font-weight: bold; }
        .log-error { color: var(--error); font-weight: bold; }
        .log-dim { color: var(--dim); }

        .footer {
            margin-top: 3rem;
            font-size: 0.7rem;
            color: var(--dim);
            text-align: center;
            text-transform: uppercase;
        }

        /* Retro scrollbar */
        .terminal-body::-webkit-scrollbar { width: 12px; }
        .terminal-body::-webkit-scrollbar-track { background: var(--surface); border-left: 2px solid var(--border); }
        .terminal-body::-webkit-scrollbar-thumb { background: var(--border); }

    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>W.P.D. v2.1</h1>
            <div class="tagline">SYSTEM.EXTRACT_WIKI_PLAINTEXT // VERSION_2026_MAY</div>
        </div>

        <div class="input-section">
            <form id="downloadForm" method="POST" action="/download">
                <label for="wiki_url">Target URI Path:</label>
                <input type="url" id="wiki_url" name="wiki_url" placeholder="https://..." required autofocus>
                <button type="submit" class="btn" id="submitBtn">Execute Extraction</button>
            </form>
        </div>

        <div id="terminalContainer" class="terminal-container">
            <div class="terminal-header">
                <span>WPD_CORE_PROCESS.LOG</span>
                <span>STATUS: RUNNING</span>
            </div>
            <div id="terminal" class="terminal-body"></div>
        </div>

        <div class="footer">
            [ W.P.D. ENGINE // BUILT_FOR_SHOUCH1 // (C) 2026 ]
        </div>
    </div>

    <script>
        const form = document.getElementById('downloadForm');
        const terminal = document.getElementById('terminal');
        const terminalContainer = document.getElementById('terminalContainer');
        const submitBtn = document.getElementById('submitBtn');

        function log(msg, type = 'info') {
            const div = document.createElement('div');
            div.className = `log-entry log-${type}`;
            const time = new Date().toLocaleTimeString('en-GB', { hour12: false });
            div.textContent = `> [${time}] ${msg}`;
            terminal.appendChild(div);
            terminal.scrollTop = terminal.scrollHeight;
        }

        form.onsubmit = () => {
            terminalContainer.style.display = 'block';
            submitBtn.disabled = true;
            submitBtn.textContent = "PROCESS_INITIALIZED";
            
            log("ESTABLISHING CONNECTION TO REMOTE HOST...", "info");
            log("API_HANDSHAKE: SUCCESS", "success");
            log("INITIALIZING STREAM_BUFFER...", "info");
            log("ATTENTION: LOCAL_SAVE_PROMPT_PENDING", "error");
        };
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('wiki_url')
    if not url: return "URL Required", 400
        
    parsed = urlparse(url)
    # Ensure we point to the correct api.php endpoint
    netloc = parsed.netloc
    path = parsed.path.split('/wiki/')[0] if '/wiki/' in parsed.path else parsed.path
    if not path.endswith('/'): path += '/'
    api_url = f"{parsed.scheme}://{netloc}{path}api.php"

    def generate_wiki_dump():
        session = requests.Session()
        session.headers.update({'User-Agent': 'WPD-Engine-v2/2.0 (High-Throughput Extraction)'})

        yield f"=== WIKI DUMP: {netloc} ===\n"
        yield f"=== EXPORTED VIA W.P.D. v2 ===\n\n"

        apcontinue = None
        total_pages = 0

        while True:
            # 1. Fetch list of all pages
            list_params = {
                "action": "query",
                "list": "allpages",
                "aplimit": "50",
                "format": "json"
            }
            if apcontinue: list_params['apcontinue'] = apcontinue

            try:
                list_resp = session.get(api_url, params=list_params, timeout=15)
                list_data = list_resp.json()
            except Exception as e:
                yield f"\n[FATAL ERROR FETCHING LIST: {str(e)}]\n"
                break

            pages = list_data.get('query', {}).get('allpages', [])
            if not pages: break

            # 2. Batch Content Extraction (Improved prop=extracts for better plaintext)
            page_ids = [str(p['pageid']) for p in pages]
            content_params = {
                "action": "query",
                "prop": "extracts",
                "explaintext": "1",
                "exlimit": "max", # Get as many as possible
                "pageids": "|".join(page_ids),
                "format": "json"
            }

            try:
                content_resp = session.get(api_url, params=content_params, timeout=20)
                content_data = content_resp.json()
                pages_data = content_data.get('query', {}).get('pages', {})

                for page in pages:
                    p_id = str(page['pageid'])
                    title = page['title']
                    extract = pages_data.get(p_id, {}).get('extract', '')

                    yield f"--- PAGE START: {title} ---\n"
                    if extract and extract.strip():
                        yield extract + "\n"
                    else:
                        # Fallback: if extracts failed, page might be too complex or a redirect
                        yield "[No plaintext extract available for this page]\n"
                    
                    yield f"--- PAGE END: {title} ---\n\n"
                    total_pages += 1
                
                # Safety throttle between batches
                time.sleep(0.2)
                
            except Exception as e:
                yield f"\n[ERROR IN BATCH: {str(e)}]\n"

            if 'continue' in list_data and 'apcontinue' in list_data['continue']:
                apcontinue = list_data['continue']['apcontinue']
            else:
                break

        yield f"=== END OF DUMP (Total Extracted: {total_pages}) ===\n"

    response = Response(stream_with_context(generate_wiki_dump()), mimetype='text/plain')
    safe_name = netloc.replace('.', '_')
    response.headers['Content-Disposition'] = f'attachment; filename="WPD_DUMP_{safe_name}.txt"'
    return response

if __name__ == '__main__':
    app.run(debug=True)
