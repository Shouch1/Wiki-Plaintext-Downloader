import time
import json
import re
from urllib.parse import urlparse
from flask import Flask, request, Response, stream_with_context, render_template_string
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)

def clean_html(html_content):
    """
    Converts MediaWiki HTML output into clean, structured plaintext.
    Handles tables, lists, and hidden elements correctly.
    """
    if not html_content: return ""
    soup = BeautifulSoup(html_content, 'lxml')
    
    # Remove technical elements that shouldn't be in a plaintext dump
    for element in soup(['script', 'style', 'noscript', 'figure', 'blockquote']):
        element.decompose()
        
    # Remove specific wiki elements
    for class_to_hide in ['mw-editsection', 'reference', 'toc', 'infobox', 'navbox']:
        for element in soup.find_all(class_=class_to_hide):
            element.decompose()

    # Get text and clean up whitespace
    text = soup.get_text(separator='\n')
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

# Universal Plaintext Extractor - Raw HTML
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Universal Plaintext Extractor</title>
    <style>
        body { font-family: sans-serif; background-color: #f4f1ea; color: #000; margin: 20px; }
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
        .progress { color: blue; font-weight: bold; }
        hr { border: 0; border-top: 1px solid #000; }
    </style>
</head>
<body>
    <table border="0">
        <tr>
            <td>
                <h1>Universal Plaintext Extractor</h1>
                <p><b>Deep multi-threaded extraction for MediaWiki & Fandom.</b></p>
                <hr>
            </td>
        </tr>
        <tr>
            <td>
                <form id="downloadForm" method="POST" action="/download">
                    <p>
                        Target URL:<br>
                        <input type="url" id="wiki_url" name="wiki_url" size="60" placeholder="https://..." required autofocus>
                    </p>
                    <p>
                        <input type="submit" id="submitBtn" value="Execute Extraction">
                    </p>
                </form>
            </td>
        </tr>
        <tr>
            <td>
                <div id="logHeader" style="display:none;"><p><b>log:</b></p></div>
                <div id="terminal" class="log-box"></div>
            </td>
        </tr>
        <tr>
            <td>
                <hr>
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
            
            log("INITIALIZING PARALLEL ENGINE...", "info");
            log("ESTABLISHING HIGH-SPEED CONNECTION...", "success");
            log("DOWNLOADING FULL CONTENT (CHECK FOLDER)...", "progress");
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
    netloc = parsed.netloc
    path = parsed.path.split('/wiki/')[0] if '/wiki/' in parsed.path else parsed.path
    if not path.endswith('/'): path += '/'
    api_url = f"{parsed.scheme}://{netloc}{path}api.php"

    def generate_dump():
        session = requests.Session()
        session.headers.update({'User-Agent': 'UniversalPlaintextExtractor/4.0 (Parallel-Deep)'})

        yield f"=== SOURCE: {netloc} ===\n"
        yield f"=== EXPORTED VIA UNIVERSAL PLAINTEXT EXTRACTOR v4 (PARALLEL-DEEP) ===\n\n"

        apcontinue = None
        total_extracted = 0

        # Create a persistent session for threads
        def fetch_and_clean_page(title):
            try:
                params = {
                    "action": "parse",
                    "page": title,
                    "prop": "text",
                    "format": "json",
                    "disablelimitreport": 1,
                    "disableeditsection": 1
                }
                resp = session.get(api_url, params=params, timeout=20)
                data = resp.json()
                html = data.get('parse', {}).get('text', {}).get('*', '')
                return title, clean_html(html)
            except Exception as e:
                return title, f"[ERROR PARSING PAGE: {str(e)}]"

        while True:
            # 1. Fetch titles list (50 at a time)
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
            
            titles = [p['title'] for p in pages]
            
            # 2. Parallel Extraction (8 threads for maximum speed)
            with ThreadPoolExecutor(max_workers=8) as executor:
                future_to_title = {executor.submit(fetch_and_clean_page, title): title for title in titles}
                
                # We want to yield results as they complete to keep the stream alive
                for future in as_completed(future_to_title):
                    title, content = future.result()
                    yield f"--- PAGE START: {title} ---\n"
                    if content:
                        yield content + "\n"
                    else:
                        yield "[No readable content found on this page]\n"
                    yield f"--- PAGE END: {title} ---\n\n"
                    total_extracted += 1

            if 'continue' in list_data and 'apcontinue' in list_data['continue']:
                apcontinue = list_data['continue']['apcontinue']
                time.sleep(0.05)
            else:
                break

        yield f"\n=== END OF DUMP (Total Extracted: {total_extracted}) ===\n"

    response = Response(stream_with_context(generate_dump()), mimetype='text/plain')
    safe_name = netloc.replace('.', '_')
    response.headers['Content-Disposition'] = f'attachment; filename="FULL_DUMP_{safe_name}.txt"'
    return response

if __name__ == '__main__':
    app.run(debug=True, port=5000)
