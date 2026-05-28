import time
import json
from urllib.parse import urlparse
from flask import Flask, request, Response, stream_with_context, render_template_string
import requests

app = Flask(__name__)

# Modern, feature-rich HTML interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>W.P.D. v2 - Wiki Plaintext Downloader</title>
    <style>
        :root {
            --bg: #0b0e14;
            --card-bg: #151921;
            --primary: #38bdf8;
            --text: #e2e8f0;
            --text-dim: #94a3b8;
            --accent: #10b981;
            --error: #ef4444;
        }
        body { 
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; 
            max-width: 900px; 
            margin: 2rem auto; 
            padding: 0 1rem; 
            background: var(--bg); 
            color: var(--text);
            line-height: 1.5;
        }
        .header { text-align: center; margin-bottom: 2rem; }
        h1 { color: var(--primary); font-size: 3rem; margin: 0; letter-spacing: -1px; }
        .tagline { color: var(--text-dim); font-size: 1.1rem; }
        
        .card {
            background: var(--card-bg);
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
            border: 1px solid #2d333f;
            margin-bottom: 2rem;
        }
        
        .input-group { margin-bottom: 1.5rem; }
        label { display: block; margin-bottom: 0.5rem; font-weight: 600; color: var(--text); }
        input[type="url"] { 
            width: 100%; 
            padding: 1rem; 
            box-sizing: border-box; 
            background: var(--bg); 
            color: white; 
            border: 2px solid #2d333f; 
            border-radius: 8px; 
            font-size: 1rem;
            transition: all 0.2s;
        }
        input[type="url"]:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 4px rgba(56, 189, 248, 0.1);
        }
        
        .btn { 
            background: var(--primary); 
            color: #000; 
            border: none; 
            padding: 1rem 2rem; 
            cursor: pointer; 
            border-radius: 8px; 
            font-size: 1.1rem; 
            font-weight: 800;
            width: 100%;
            transition: transform 0.1s, background 0.2s;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .btn:hover { background: #7dd3fc; transform: translateY(-1px); }
        .btn:active { transform: translateY(0); }
        
        .terminal {
            background: #000;
            border-radius: 8px;
            padding: 1rem;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.85rem;
            height: 300px;
            overflow-y: auto;
            border: 1px solid #333;
            margin-top: 1.5rem;
            display: none;
        }
        .log-entry { margin-bottom: 0.25rem; border-left: 2px solid #333; padding-left: 0.5rem; }
        .log-success { color: var(--accent); border-color: var(--accent); }
        .log-info { color: var(--primary); border-color: var(--primary); }
        .log-error { color: var(--error); border-color: var(--error); }
        
        .status-bar {
            display: flex;
            justify-content: space-between;
            font-size: 0.8rem;
            color: var(--text-dim);
            margin-top: 0.5rem;
            padding: 0 0.5rem;
        }

        .features {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            margin-top: 2rem;
        }
        .feature-item {
            font-size: 0.85rem;
            color: var(--text-dim);
            display: flex;
            align-items: flex-start;
            gap: 0.5rem;
        }
        .feature-item::before { content: "✓"; color: var(--accent); font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h1>W.P.D.</h1>
        <div class="tagline">Universal Wiki Plaintext Extraction Engine</div>
    </div>
    
    <div class="card">
        <form id="downloadForm" method="POST" action="/download">
            <div class="input-group">
                <label for="wiki_url">Target MediaWiki / Fandom URL</label>
                <input type="url" id="wiki_url" name="wiki_url" placeholder="https://example.fandom.com/wiki/" required>
            </div>
            <button type="submit" class="btn" id="submitBtn">Initialize Extraction</button>
        </form>
        
        <div id="terminal" class="terminal"></div>
        <div id="statusBar" class="status-bar" style="display: none;">
            <span id="pageCount">Pages: 0</span>
            <span id="statusText">Ready</span>
        </div>

        <div class="features">
            <div class="feature-item">Deep text extraction (handles hidden templates)</div>
            <div class="feature-item">Batch processing (fast & safe)</div>
            <div class="feature-item">Streams directly to file</div>
            <div class="feature-item">Real-time progress logging</div>
        </div>
    </div>

    <script>
        const form = document.getElementById('downloadForm');
        const terminal = document.getElementById('terminal');
        const submitBtn = document.getElementById('submitBtn');
        const statusBar = document.getElementById('statusBar');
        const pageCountEl = document.getElementById('pageCount');
        const statusTextEl = document.getElementById('statusText');

        function log(msg, type = 'info') {
            const div = document.createElement('div');
            div.className = `log-entry log-${type}`;
            div.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
            terminal.appendChild(div);
            terminal.scrollTop = terminal.scrollHeight;
        }

        // We use a custom submission handler to show the log, but let the browser handle the download stream
        form.onsubmit = async (e) => {
            terminal.style.display = 'block';
            statusBar.style.display = 'flex';
            submitBtn.disabled = true;
            submitBtn.textContent = "Extracting... Check Downloads";
            
            log("Starting connection to wiki API...", "info");
            log("Note: Browser will prompt for download. Keep this tab open.", "success");
            
            // Note: We don't preventDefault because we want the browser to trigger the file download
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
