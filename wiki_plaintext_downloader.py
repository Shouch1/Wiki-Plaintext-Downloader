import time
from urllib.parse import urlparse
from flask import Flask, request, Response, stream_with_context, render_template_string
import requests

app = Flask(__name__)

# The HTML interface served by the Python backend
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wiki Plaintext Downloader</title>
    <style>
        body { 
            font-family: system-ui, -apple-system, sans-serif; 
            max-width: 800px; 
            margin: 3rem auto; 
            padding: 0 1rem; 
            background: #0f172a; 
            color: #f8fafc; 
        }
        h1 { color: #38bdf8; }
        .container {
            background: #1e293b;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        input[type="url"] { 
            width: 100%; 
            padding: 1rem; 
            margin: 1rem 0; 
            box-sizing: border-box; 
            background: #0f172a; 
            color: white; 
            border: 1px solid #475569; 
            border-radius: 4px; 
            font-size: 1rem;
        }
        button { 
            background: #0284c7; 
            color: white; 
            border: none; 
            padding: 1rem 2rem; 
            cursor: pointer; 
            border-radius: 4px; 
            font-size: 1rem; 
            font-weight: bold;
            width: 100%;
        }
        button:hover { background: #0369a1; }
        .note { 
            font-size: 0.9rem; 
            color: #94a3b8; 
            margin-top: 1.5rem; 
            line-height: 1.5;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Wiki Plaintext Downloader</h1>
        <p>Enter the URL of a Fandom, Telepedia, or MediaWiki site.</p>
        <form method="POST" action="/download">
            <input type="url" name="wiki_url" placeholder="https://witch-hat-atelier.fandom.com/wiki/" required>
            <button type="submit">Download as Plaintext</button>
        </form>
        <p class="note">
            <strong>Note:</strong> The download will start immediately and stream to a text file. Keep the browser tab open. 
            Large wikis may take several minutes. The script waits a fraction of a second between page requests to avoid getting IP-banned by the wiki's servers.
        </p>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('wiki_url')
    
    # Extract the base domain to target the MediaWiki API
    parsed = urlparse(url)
    api_url = f"{parsed.scheme}://{parsed.netloc}/api.php"

    def generate_wiki_dump():
        session = requests.Session()
        session.headers.update({'User-Agent': 'WikiPlaintextDownloader/1.0'})

        yield f"=== WIKI DUMP: {parsed.netloc} ===\n\n"

        apcontinue = None
        page_count = 0

        while True:
            # 1. Fetch a list of all pages in the main namespace
            list_params = {
                "action": "query",
                "list": "allpages",
                "aplimit": "50", # Fetch 50 titles at a time
                "format": "json"
            }
            if apcontinue:
                list_params['apcontinue'] = apcontinue

            try:
                list_resp = session.get(api_url, params=list_params, timeout=10)
                list_data = list_resp.json()
            except Exception as e:
                yield f"\n\n[ERROR FETCHING PAGE LIST: {str(e)}]\n"
                break

            pages = list_data.get('query', {}).get('allpages', [])
            if not pages:
                break

            # 2. Iterate through the fetched page IDs and request their plaintext extracts
            for page in pages:
                title = page['title']
                page_id = page['pageid']

                content_params = {
                    "action": "query",
                    "prop": "extracts",
                    "explaintext": "1", # Strips out wikitext markup to return raw text
                    "pageids": str(page_id),
                    "format": "json"
                }

                try:
                    content_resp = session.get(api_url, params=content_params, timeout=10)
                    content_data = content_resp.json()
                    extract = content_data.get('query', {}).get('pages', {}).get(str(page_id), {}).get('extract', '')

                    yield f"--- PAGE: {title} ---\n"
                    if extract and extract.strip():
                        yield extract + "\n\n"
                    else:
                        yield "[No plaintext extract available, page is a redirect, or page is empty]\n\n"

                    page_count += 1
                    time.sleep(0.1) # Throttle to avoid rate limiting or blocking
                    
                except Exception as e:
                    yield f"\n[ERROR FETCHING CONTENT FOR {title}: {str(e)}]\n\n"

            # 3. Handle MediaWiki pagination
            if 'continue' in list_data and 'apcontinue' in list_data['continue']:
                apcontinue = list_data['continue']['apcontinue']
            else:
                break

        yield f"\n=== END OF DUMP (Total Main Pages: {page_count}) ===\n"

    # Stream the generator output directly to the user as a downloadable file
    response = Response(stream_with_context(generate_wiki_dump()), mimetype='text/plain')
    safe_filename = parsed.netloc.replace('.', '_')
    response.headers['Content-Disposition'] = f'attachment; filename="{safe_filename}_dump.txt"'
    
    return response

if __name__ == '__main__':
    print("Starting server...")
    print("Open http://127.0.0.1:5000 in your browser to access the application.")
    app.run(debug=True, port=5000)