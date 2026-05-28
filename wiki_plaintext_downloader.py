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
    if not html_content: return ""
    soup = BeautifulSoup(html_content, 'lxml')
    for element in soup(['script', 'style', 'noscript', 'figure', 'blockquote']):
        element.decompose()
    for class_to_hide in ['mw-editsection', 'reference', 'toc', 'infobox', 'navbox']:
        for element in soup.find_all(class_=class_to_hide):
            element.decompose()
    text = soup.get_text(separator='\n')
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wiki Plaintext Extractor</title>
    <style>
        body { font-family: Tahoma, Verdana, sans-serif; background: #f4f1ea; color: #000; line-height: 1.4; padding: 30px; margin: 0; }
        h1 { font-size: 24px; text-decoration: underline; margin: 0 0 5px 0; font-weight: bold; }
        h2 { font-size: 18px; margin: 20px 0 10px 0; font-weight: bold; border-bottom: 1px solid #000; display: inline-block; }
        p, li, td { font-size: 14px; margin: 5px 0; }
        hr { border: 0; border-top: 1px solid #000; margin: 20px 0; }
        input[type="url"] { width: 400px; padding: 4px; border: 1px solid #000; font-family: Tahoma, sans-serif; font-size: 14px; }
        button { background: #eee; border: 1px solid #000; padding: 4px 15px; cursor: pointer; font-family: Tahoma, sans-serif; font-size: 14px; }
        button:hover { background: #ddd; }
        #log { border: 1px solid #000; padding: 10px; height: 350px; overflow-y: scroll; background: #fff; white-space: pre-wrap; font-size: 12px; font-family: monospace; width: 100%; box-sizing: border-box; }
        .meta { color: #444; font-size: 12px; }
        a { color: blue; }
        ul { padding-left: 20px; margin: 10px 0; }
        ol { padding-left: 20px; margin: 10px 0; }
    </style>
</head>
<body>
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 800px;">
        <tr>
            <td align="left">
                <h1>Wiki Plaintext Extractor</h1>
                <p class="meta">Version 4.0.6 | Build 2026-05-28 | <a href="https://github.com/Shouch1/Wiki-Plaintext-Downloader">Source Code</a></p>
                <hr>
            </td>
        </tr>
        <tr>
            <td align="left">
                <form id="execForm">
                    <table border="0" cellpadding="0" cellspacing="0">
                        <tr>
                            <td>Target URL:&nbsp;</td>
                            <td><input type="url" id="wiki_url" name="wiki_url" placeholder="https://witchhatatelier.telepedia.net/" required autofocus>&nbsp;</td>
                            <td><button type="submit">Execute</button></td>
                        </tr>
                    </table>
                </form>
                <br>
            </td>
        </tr>
        <tr>
            <td align="left">
                <div id="log">Status: Idle</div>
            </td>
        </tr>
        <tr>
            <td align="left">
                <hr>
                <h2>Project Overview</h2>
                <p>A high-speed, multi-threaded extraction tool for MediaWiki, Fandom, and Telepedia platforms. This utility converts entire wiki databases into clean, structured plaintext files suitable for archival, search indexing, or LLM training.</p>
                
                <h2>Core Functionality</h2>
                <ul>
                    <li><b>Parallel Processing:</b> Utilizes 8 concurrent workers for rapid page retrieval.</li>
                    <li><b>Direct Streaming:</b> Data is streamed directly to the browser to handle large datasets without server timeouts.</li>
                    <li><b>Real-time Monitoring:</b> Live download logs provide immediate feedback on extraction progress.</li>
                    <li><b>Content Sanitization:</b> Automatically strips HTML, scripts, and wiki-specific technical metadata.</li>
                </ul>

                <h2>Usage Instructions</h2>
                <ol>
                    <li>Provide the base URL of a MediaWiki-powered site.</li>
                    <li>Click <b>Execute</b> to begin the multi-threaded extraction.</li>
                    <li>Monitor the log box for active downloads.</li>
                    <li>The system will automatically trigger a .txt download upon completion.</li>
                </ol>

                <h2>Technical Implementation</h2>
                <p>The system is built on a Python backend using Flask and Requests, with a lightweight JavaScript frontend for stream handling. Local execution ensures that extraction remains stable even for wikis with thousands of pages.</p>
                
                <p class="meta">This tool is provided under the MIT License. No tracking or external frameworks are used.</p>
            </td>
        </tr>
    </table>

    <script>
        const form = document.getElementById('execForm');
        const log = document.getElementById('log');
        const btn = form.querySelector('button');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const url = document.getElementById('wiki_url').value;
            const formData = new FormData();
            formData.append('wiki_url', url);

            log.textContent = 'Status: Initializing stream...\\n';
            btn.disabled = true;

            try {
                const response = await fetch('/download', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) throw new Error('Server Error');

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let fullContent = '';
                
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    const chunk = decoder.decode(value, { stream: true });
                    fullContent += chunk;
                    
                    const lines = chunk.split('\\n');
                    lines.forEach(line => {
                        if (line.startsWith('--- PAGE START:')) {
                            const title = line.replace('--- PAGE START: ', '').replace(' ---', '');
                            log.textContent += `[Success] Downloaded: ${title}\\n`;
                            log.scrollTop = log.scrollHeight;
                        } else if (line.startsWith('=== END OF DUMP')) {
                            log.textContent += `\\n${line}\\n`;
                            log.scrollTop = log.scrollHeight;
                        }
                    });
                }

                log.textContent += 'Status: Job finished.';
                
                const blob = new Blob([fullContent], { type: 'text/plain' });
                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                const safeName = new URL(url).hostname.replace(/\\./g, '_');
                a.href = downloadUrl;
                a.download = `FULL_DUMP_${safeName}.txt`;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(downloadUrl);

            } catch (err) {
                log.textContent += `\\n[Error] ${err.message}\\n`;
            } finally {
                btn.disabled = false;
            }
        });
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
        session.headers.update({'User-Agent': 'WikiExtractor/4.0 (Parallel)'})

        yield f"=== SOURCE: {netloc} ===\\n"
        yield f"=== EXPORTED: {time.strftime('%Y-%m-%d %H:%M:%S')} ===\\n\\n"

        apcontinue = None
        total_extracted = 0

        def fetch_page(title):
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
            except:
                return title, "[ERROR_FETCHING]"

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
            except:
                yield "\\n[FATAL_ERROR_FETCHING_LIST]\\n"
                break

            pages = list_data.get('query', {}).get('allpages', [])
            if not pages: break
            
            titles = [p['title'] for p in pages]
            
            with ThreadPoolExecutor(max_workers=8) as executor:
                future_to_title = {executor.submit(fetch_page, title): title for title in titles}
                for future in as_completed(future_to_title):
                    title, content = future.result()
                    yield f"--- PAGE START: {title} ---\\n"
                    yield content + "\\n"
                    yield f"--- PAGE END: {title} ---\\n\\n"
                    total_extracted += 1

            if 'continue' in list_data and 'apcontinue' in list_data['continue']:
                apcontinue = list_data['continue']['apcontinue']
            else:
                break

        yield f"=== END OF DUMP (Total Extracted: {total_extracted}) ===\\n"

    return Response(stream_with_context(generate_dump()), mimetype='text/plain')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
