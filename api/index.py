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
        hr { border: 0; border-top: 1px solid #000; }
    </style>
</head>
<body>
    <table border="0">
        <tr>
            <td>
                <h1>Universal Plaintext Extractor</h1>
                <p><b>Extract deep plaintext content from MediaWiki, Fandom, and Telepedia sites.</b></p>
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
            
            log("INITIATING DEEP EXTRACTION...", "info");
            log("ESTABLISHING HANDSHAKE...", "success");
            log("CHECK DOWNLOADS FOLDER FOR OUTPUT", "error");
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
        session.headers.update({'User-Agent': 'UniversalPlaintextExtractor/3.0'})

        yield f"=== SOURCE: {netloc} ===\n"
        yield f"=== EXTRACTED VIA UNIVERSAL PLAINTEXT EXTRACTOR ===\n\n"

        apcontinue = None
        total_pages = 0

        while True:
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

            # DEEP EXTRACTION: Using revisions and parsoid/plaintext methods if available
            # We use 'revisions' with 'content' and 'rvslots=main' as a fallback to 'extracts'
            page_ids = [str(p['pageid']) for p in pages]
            
            # 1. Try 'extracts' first as it's cleaner
            content_params = {
                "action": "query",
                "prop": "extracts|revisions",
                "explaintext": "1",
                "rvprop": "content",
                "rvslots": "main",
                "pageids": "|".join(page_ids),
                "format": "json"
            }

            try:
                content_resp = session.get(api_url, params=content_params, timeout=25)
                content_data = content_resp.json()
                pages_data = content_data.get('query', {}).get('pages', {})

                for page in pages:
                    p_id = str(page['pageid'])
                    title = page['title']
                    p_data = pages_data.get(p_id, {})
                    
                    # Try extract first
                    text = p_data.get('extract', '')
                    
                    # If extract is missing or too short, fallback to revision content
                    if not text or len(text) < 50:
                        revisions = p_data.get('revisions', [])
                        if revisions:
                            # This is raw wikitext, but it's better than nothing
                            text = revisions[0].get('slots', {}).get('main', {}).get('*', '')
                            if not text: # Legacy MediaWiki support
                                text = revisions[0].get('*', '')

                    yield f"--- PAGE START: {title} ---\n"
                    if text and text.strip():
                        yield text + "\n"
                    else:
                        yield "[Content could not be retrieved - possibly protected or empty]\n"
                    
                    yield f"--- PAGE END: {title} ---\n\n"
                    total_pages += 1
                
                time.sleep(0.2)
                
            except Exception as e:
                yield f"\n[ERROR IN BATCH: {str(e)}]\n"

            if 'continue' in list_data and 'apcontinue' in list_data['continue']:
                apcontinue = list_data['continue']['apcontinue']
            else:
                break

        yield f"=== END OF DUMP (Total Extracted: {total_pages}) ===\n"

    response = Response(stream_with_context(generate_dump()), mimetype='text/plain')
    safe_name = netloc.replace('.', '_')
    response.headers['Content-Disposition'] = f'attachment; filename="EXTRACT_{safe_name}.txt"'
    return response

if __name__ == '__main__':
    app.run(debug=True)

if __name__ == '__main__':
    app.run(debug=True)
