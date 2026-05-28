import time
import json
from urllib.parse import urlparse
from flask import Flask, request, Response, stream_with_context, render_template_string
import requests

app = Flask(__name__)

# Raw 'Old School' HTML Interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>W.P.D. // WIKI_PLAINTEXT_DOWNLOADER</title>
    <style>
        body { 
            font-family: sans-serif; 
            background-color: #f4f1ea; 
            color: #000; 
            margin: 20px;
        }
        table { border-collapse: collapse; width: 100%; max-width: 800px; }
        .log-box { 
            border: 1px solid #000; 
            background: #fff; 
            height: 400px; 
            overflow-y: scroll; 
            font-family: monospace; 
            font-size: 12px;
            padding: 5px;
            display: none;
        }
        .info { color: #000; }
        .success { color: green; font-weight: bold; }
        .error { color: red; font-weight: bold; }
        hr { border: 0; border-top: 1px solid #000; }
    </style>
</head>
<body>
    <table border="0">
        <tr>
            <td>
                <h1>W.P.D. v2.2</h1>
                <p><b>Universal Wiki Plaintext Extraction Engine</b></p>
                <hr>
            </td>
        </tr>
        <tr>
            <td>
                <form id="downloadForm" method="POST" action="/download">
                    <p>
                        Target Wiki URL:<br>
                        <input type="url" id="wiki_url" name="wiki_url" size="60" required autofocus>
                    </p>
                    <p>
                        <input type="submit" id="submitBtn" value="Execute Extraction">
                    </p>
                </form>
            </td>
        </tr>
        <tr>
            <td>
                <div id="logHeader" style="display:none;"><p><b>SYSTEM_LOG:</b></p></div>
                <div id="terminal" class="log-box"></div>
            </td>
        </tr>
        <tr>
            <td>
                <hr>
                <p><small>[ W.P.D. ENGINE // VERSION 2.2 // NO_STYLING_STRICT_FUNCTIONAL ]</small></p>
            </td>
        </tr>
    </table>

    <script>
        const form = document.getElementById('downloadForm');
        const terminal = document.getElementById('terminal');
        const logHeader = document.getElementById('logHeader');
        const submitBtn = document.getElementById('submitBtn');

        function log(msg, type = 'info') {
            const div = document.createElement('div');
            div.className = type;
            const time = new Date().toLocaleTimeString();
            div.innerHTML = `&gt; [${time}] ${msg}`;
            terminal.appendChild(div);
            terminal.scrollTop = terminal.scrollHeight;
        }

        form.onsubmit = () => {
            terminal.style.display = 'block';
            logHeader.style.display = 'block';
            submitBtn.disabled = true;
            submitBtn.value = "RUNNING...";
            
            log("INITIATING API CONNECTION...", "info");
            log("HANDSHAKE SUCCESSFUL", "success");
            log("STREAMING DATA TO LOCAL DISK", "info");
            log("CHECK BROWSER DOWNLOADS FOR OUTPUT", "error");
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
