# -- coding: utf-8 --
import os
import shutil
from http.server import SimpleHTTPRequestHandler, HTTPServer
import cgi
from datetime import datetime
import urllib.parse
import json
import html
import base64

UPLOAD_DIR = '/storage/emulated/0/Drive'
PORT = 8000
MAX_UPLOAD_SIZE = 100 * 1024 * 1024
ALLOW_DELETE_NON_EMPTY_DIRS = False

USERNAME = "username"
PASSWORD = "your_password"
REALM = "My Private Drive"

class GDriveHandler(SimpleHTTPRequestHandler):

    def _get_validated_path(self, path_param):
        if path_param is None:
            return None
        rel_path = urllib.parse.unquote(path_param).lstrip('/')
        abs_path = os.path.normpath(os.path.join(UPLOAD_DIR, rel_path))

        if os.path.commonpath([UPLOAD_DIR, abs_path]) != UPLOAD_DIR:
            print(f"Security Alert: Path traversal attempt denied for '{rel_path}'")
            return None
        return abs_path, rel_path

    def _send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def _redirect(self, path):
        if not path.startswith('/'):
            path = '/' + path
        self.send_response(303)
        self.send_header('Location', path)
        self.end_headers()

    def _is_authenticated(self):
        auth_header = self.headers.get('Authorization')
        if auth_header is None:
            return False

        if not auth_header.startswith('Basic '):
            return False

        try:
            encoded_credentials = auth_header.split(' ')[1]
            decoded_credentials_bytes = base64.b64decode(encoded_credentials)
            decoded_credentials_str = decoded_credentials_bytes.decode('utf-8')
            username, password = decoded_credentials_str.split(':', 1)
            return username == USERNAME and password == PASSWORD
        except Exception as e:
            print(f"Authentication parsing error: {e}")
            return False

    def _require_auth(self):
        self.send_response(401)
        self.send_header('WWW-Authenticate', f'Basic realm="{REALM}"')
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(f"""
        <!DOCTYPE html>
        <html>
        <head><title>401 Unauthorized</title></head>
        <body><h1>401 Unauthorized</h1><p>You need to provide credentials to access this resource.</p></body>
        </html>
        """.encode('utf-8'))

    def _generate_breadcrumbs(self, current_rel_path):
        breadcrumb_html = '<nav class="breadcrumbs"><a href="/">Root</a>'
        if current_rel_path:
            parts = current_rel_path.split(os.sep)
            accumulated_path = ""
            for i, part in enumerate(parts):
                if not part: continue
                accumulated_path = os.path.join(accumulated_path, part)
                link = '/' + urllib.parse.quote(accumulated_path)
                escaped_part = html.escape(part)
                if i == len(parts) - 1:
                    breadcrumb_html += f' > <span class="current-crumb">{escaped_part}</span>'
                else:
                    breadcrumb_html += f' > <a href="{link}">{escaped_part}</a>'
        breadcrumb_html += '</nav>'
        return breadcrumb_html

    def list_directory_html(self, current_abs_path):
        files = []
        dirs = []
        current_rel_path = os.path.relpath(current_abs_path, UPLOAD_DIR)
        if current_rel_path == '.':
            current_rel_path = ""

        try:
            for item in os.listdir(current_abs_path):
                item_abs_path = os.path.join(current_abs_path, item)
                item_rel_path = os.path.join(current_rel_path, item) if current_rel_path else item
                if os.path.isdir(item_abs_path):
                    dirs.append({'name': item, 'rel_path': item_rel_path})
                elif os.path.isfile(item_abs_path):
                    try:
                        size = os.path.getsize(item_abs_path) / (1024 * 1024)
                        mtime = datetime.fromtimestamp(os.path.getmtime(item_abs_path)).strftime('%d-%m-%Y %H:%M')
                        files.append({'name': item, 'size': size, 'mtime': mtime, 'rel_path': item_rel_path})
                    except OSError:
                         files.append({'name': f"{item} ( inaccessible )", 'size': 0, 'mtime': 'N/A', 'rel_path': item_rel_path})
        except PermissionError:
            self.send_error(403, "Permission Denied to list directory")
            return None
        except FileNotFoundError:
             self.send_error(404, "Directory Not Found")
             return None
        except Exception as e:
            self.send_error(500, f"Error listing directory: {e}")
            return None

        files.sort(key=lambda x: x['name'].lower())
        dirs.sort(key=lambda x: x['name'].lower())

        breadcrumb_nav_html = self._generate_breadcrumbs(current_rel_path)

        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>My Drive - {'/' + html.escape(current_rel_path) if current_rel_path else 'Root'}</title>
            <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
            <style>
                body {{
                    font-family: 'Poppins', sans-serif;
                    background-color: #f1f3f4;
                    margin: 0;
                    padding: 20px;
                    color: #333;
                }}
                h1 {{
                    color: #202124;
                    border-bottom: 1px solid #ddd;
                    padding-bottom: 10px;
                    margin-top: 0;
                    margin-bottom: 15px;
                    font-weight: 600;
                }}
                .container {{
                    background-color: white;
                    padding: 20px 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    max-width: 1200px;
                    margin: auto;
                }}
                a {{
                    color: #1a73e8;
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
                .breadcrumbs {{
                    margin-bottom: 20px;
                    font-size: 14px;
                    color: #5f6368;
                    word-wrap: break-word;
                }}
                .breadcrumbs a {{
                    color: #1a73e8;
                }}
                .breadcrumbs .current-crumb {{
                    font-weight: 600;
                    color: #202124;
                }}
                .upload-section, .search-section {{
                    margin-bottom: 25px;
                    padding: 15px;
                    background-color: #e8f0fe;
                    border-radius: 8px;
                }}
                .search-section {{
                     background-color: #f8f9fa;
                }}
                 .upload-btn {{
                    background: #1a73e8;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 20px;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: 600;
                    transition: background-color 0.2s ease;
                 }}
                 .upload-btn:hover {{
                    background: #1558b0;
                 }}
                 #upload-status {{
                     margin-left: 10px;
                     font-style: italic;
                     color: #1a73e8;
                     font-size: 13px;
                 }}
                #search-input {{
                    padding: 10px 15px;
                    font-size: 14px;
                    border-radius: 20px;
                    border: 1px solid #ccc;
                    width: 300px;
                    max-width: 90%;
                    box-sizing: border-box;
                }}
                #search-input:focus {{
                     outline: none;
                     border-color: #1a73e8;
                     box-shadow: 0 0 0 2px rgba(26, 115, 232, 0.2);
                }}
                .item-grid {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 20px;
                    margin-top: 20px;
                    padding-top: 10px;
                }}
                .item {{
                    width: 170px;
                    padding: 10px 15px 15px 15px;
                    border-radius: 8px;
                    background: #fff;
                    border: 1px solid #dadce0;
                    text-align: center;
                    font-size: 13px;
                    overflow: visible;
                    position: relative;
                    transition: box-shadow 0.2s ease-in-out, opacity 0.3s ease, transform 0.3s ease;
                    word-wrap: break-word;
                    display: flex;
                    flex-direction: column;
                    box-sizing: border-box;
                }}
                 .item:hover {{
                    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
                    transform: translateY(-2px);
                 }}
                 .item.hidden {{
                    opacity: 0;
                    pointer-events: none;
                    transform: scale(0.8);
                    height: 0;
                    padding: 0;
                    margin: 0;
                    border: none;
                    width: 0;
                    gap: 0;
                 }}
                 .item-link {{
                    text-decoration: none;
                    color: #1a0dab;
                    font-weight: 600;
                    display: block;
                    flex-grow: 1;
                    margin-bottom: 5px;
                 }}
                 .item img {{
                    width: 60px;
                    height: 60px;
                    object-fit: contain;
                    margin-bottom: 10px;
                    margin-top: 5px;
                 }}
                 .item-name {{
                    height: 40px;
                    overflow: hidden;
                    line-height: 1.4;
                    word-break: break-all;
                 }}
                 .meta {{
                    font-size: 11px;
                    color: #5f6368;
                    margin-top: auto;
                    padding-top: 5px;
                 }}
                .item-actions {{
                    position: absolute;
                    top: 5px;
                    right: 5px;
                    z-index: 11;
                }}
                .three-dots-btn {{
                    background: none;
                    border: none;
                    font-size: 20px;
                    line-height: 1;
                    font-weight: bold;
                    padding: 5px;
                    cursor: pointer;
                    color: #5f6368;
                    border-radius: 50%;
                    transition: background-color 0.2s ease;
                }}
                .three-dots-btn:hover {{
                    background-color: #eee;
                }}
                .action-menu {{
                    display: none;
                    position: absolute;
                    right: 0;
                    top: 100%;
                    background-color: white;
                    min-width: 120px;
                    box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.2);
                    z-index: 10;
                    border-radius: 4px;
                    overflow: hidden;
                    padding: 5px 0;
                }}
                .action-menu.show {{
                    display: block;
                }}
                .action-menu-item {{
                    font-family: 'Poppins', sans-serif;
                    font-size: 13px;
                    color: #333;
                    padding: 8px 16px;
                    text-decoration: none;
                    display: block;
                    cursor: pointer;
                    background: none;
                    border: none;
                    width: 100%;
                    text-align: left;
                    box-sizing: border-box;
                    white-space: nowrap;
                }}
                .action-menu-item:hover {{
                    background-color: #f1f1f1;
                }}
                .action-menu-item.delete {{
                    color: #d93025;
                    font-weight: 600;
                }}
                .rename-form {{
                    display: none;
                    padding: 10px 5px 5px 5px;
                    border-top: 1px solid #eee;
                    margin-top: 10px;
                }}
                .rename-form input[type=text] {{
                    width: calc(100% - 12px);
                    padding: 6px;
                    margin-bottom: 8px;
                    font-size: 12px;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    box-sizing: border-box;
                }}
                .rename-form button {{
                   font-size: 11px;
                   padding: 5px 10px;
                   border-radius: 15px;
                   cursor: pointer;
                   border: none;
                   margin-right: 5px;
                   font-weight: 600;
                   transition: background-color 0.2s ease, filter 0.2s ease;
                }}
                .rename-form .save-btn {{
                    background-color: #1a73e8;
                    color: white;
                }}
                .rename-form .cancel-btn {{
                    background-color: #eee;
                    color: #333;
                }}
                .rename-form .save-btn:hover {{ filter: brightness(90%); }}
                .rename-form .cancel-btn:hover {{ filter: brightness(95%); }}
            </style>
             <script>
                function toggleMenu(menuId) {{
                    var targetMenu = document.getElementById(menuId);
                    if (!targetMenu) return;
                    var currentlyShown = targetMenu.classList.contains('show');
                    var menus = document.getElementsByClassName('action-menu');
                    for (var i = 0; i < menus.length; i++) {{
                        menus[i].classList.remove('show');
                    }}
                    if (!currentlyShown) {{
                        targetMenu.classList.add('show');
                    }}
                }}
                window.onclick = function(event) {{
                    if (!event.target.matches('.three-dots-btn')) {{
                        var menus = document.getElementsByClassName("action-menu");
                        for (var i = 0; i < menus.length; i++) {{
                            var openMenu = menus[i];
                            if (openMenu.classList.contains('show')) {{
                                var parentItemActions = openMenu.closest('.item-actions');
                                if (!parentItemActions || !parentItemActions.contains(event.target)) {{
                                     openMenu.classList.remove('show');
                                }}
                            }}
                        }}
                    }}
                }}
                function showRenameForm(itemId, currentName) {{
                    var displayDiv = document.getElementById('item-display-' + itemId);
                    var formDiv = document.getElementById('rename-form-' + itemId);
                    var input = document.getElementById('rename-input-' + itemId);
                    if (!displayDiv || !formDiv || !input) return;
                    var menu = document.getElementById('menu-' + itemId);
                    if(menu) menu.classList.remove('show');
                    displayDiv.style.display = 'none';
                    formDiv.style.display = 'block';
                    input.value = currentName;
                    setTimeout(function() {{ input.focus(); input.select(); }}, 50);
                }}
                function hideRenameForm(itemId) {{
                    var displayDiv = document.getElementById('item-display-' + itemId);
                    var formDiv = document.getElementById('rename-form-' + itemId);
                    if (!displayDiv || !formDiv) return;
                    formDiv.style.display = 'none';
                    displayDiv.style.display = 'block';
                }}
                function confirmAndDelete(formId, itemName) {{
                     var formElement = document.getElementById(formId);
                     if (!formElement) return false;
                     var menu = formElement.closest('.item')?.querySelector('.action-menu');
                     if(menu) menu.classList.remove('show');
                     if (confirm(Are you sure you want to delete '${{itemName}}'? This cannot be undone.)) {{
                         formElement.submit();
                     }}
                     return false;
                }}
                 function handleMenuAction(menuId, actionFn) {{
                      actionFn();
                      var menu = document.getElementById(menuId);
                      if (menu) menu.classList.remove('show');
                 }}
                 function filterItems() {{
                    var searchTerm = document.getElementById('search-input').value.toLowerCase();
                    var items = document.getElementsByClassName('searchable-item');
                    var matchFound = false;
                    for (var i = 0; i < items.length; i++) {{
                        var itemName = items[i].getAttribute('data-name')?.toLowerCase() || '';
                        if (itemName.includes(searchTerm)) {{
                            items[i].classList.remove('hidden');
                            matchFound = true;
                        }} else {{
                            items[i].classList.add('hidden');
                        }}
                    }}
                 }}
            </script>
        </head>
        <body>
            <div class="container">
                <h1>📁 My Drive</h1>
                {breadcrumb_nav_html}
                <div class="upload-section">
                    <form enctype="multipart/form-data" method="post" action="/upload?path={urllib.parse.quote(current_rel_path)}">
                        <input type="file" name="file" id="file" style="display:none" onchange="document.getElementById('upload-status').innerText = 'Uploading ' + this.files[0].name + '...'; this.form.submit();">
                        <button type="button" class="upload-btn" onclick="document.getElementById('file').click()">⬆ Upload File Here</button>
                        <span id="upload-status"></span>
                    </form>
                </div>
                <div class="search-section">
                    <input type="search" id="search-input" placeholder="🔍 Search this folder..." oninput="filterItems()" aria-label="Search items in current folder">
                </div>
                <div class="item-grid">
        """
        item_counter = 0
        for item_list, item_type in [(dirs, 'folder'), (files, 'file')]:
            for item_info in item_list:
                name = item_info['name']
                html_safe_name = html.escape(name, quote=True)
                js_safe_name = name.replace("'", "\\'")
                rel_path = item_info['rel_path']
                link = '/' + urllib.parse.quote(rel_path)
                item_id = f"{item_type}-{item_counter}"
                menu_id = f"menu-{item_id}"
                delete_form_id = f"delete-form-{item_id}"
                rename_form_id = f"rename-form-{item_id}"
                item_counter += 1

                html_content += f"""
                    <div class="item {item_type} searchable-item" data-name="{html_safe_name}">
                        <div class="item-actions">
                            <button class="three-dots-btn" onclick="event.stopPropagation(); toggleMenu('{menu_id}');" aria-label="Actions for {html_safe_name}" title="Actions">⋮</button>
                            <div id="{menu_id}" class="action-menu">
                                <button type="button" class="action-menu-item" onclick="handleMenuAction('{menu_id}', function() {{ showRenameForm('{item_id}', '{js_safe_name}') }})">Rename</button>
                                <button type="button" class="action-menu-item delete" onclick="confirmAndDelete('{delete_form_id}', '{js_safe_name}')">Delete</button>
                            </div>
                        </div>
                        <div id="item-display-{item_id}">
                            <a href="{link}" {'target="_blank" rel="noopener noreferrer"' if item_type == 'file' else ''} class="item-link" title="{html_safe_name}">
                """
                if item_type == 'folder':
                     icon = "https://img.icons8.com/color/96/000000/folder-invoices.png"
                     html_content += f'<img src="{icon}" alt="Folder icon" loading="lazy"/>'
                     html_content += f'<div class="item-name">{html_safe_name}</div>'
                else:
                     size = item_info['size']
                     mtime = item_info['mtime']
                     ext = os.path.splitext(name)[1].lower()
                     file_icon = 'https://img.icons8.com/fluency/96/000000/document.png'
                     if ext == '.pdf': file_icon = 'https://img.icons8.com/fluency/96/000000/pdf.png'
                     elif ext in ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'): file_icon = 'https://img.icons8.com/fluency/96/000000/image.png'
                     elif ext in ('.mp3', '.wav', '.ogg', '.m4a'): file_icon = 'https://img.icons8.com/fluency/96/000000/audio-file.png'
                     elif ext in ('.mp4', '.mov', '.avi', '.mkv'): file_icon = 'https://img.icons8.com/fluency/96/000000/video-file.png'
                     elif ext in ('.zip', '.rar', '.7z', '.tar', '.gz'): file_icon = 'https://img.icons8.com/fluency/96/000000/zip.png'
                     elif ext in ('.txt', '.md', '.log'): file_icon = 'https://img.icons8.com/fluency/96/000000/txt.png'
                     html_content += f'<img src="{file_icon}" alt="File icon for {ext}" loading="lazy"/>'
                     html_content += f'<div class="item-name">{html_safe_name}</div>'
                     html_content += f'<div class="meta">{size:.2f} MB | {mtime}</div>'
                html_content += """
                            </a>
                        </div>
                        """
                html_content += f"""
                        <div id="{rename_form_id}" class="rename-form">
                             <form method="post" action="/rename" aria-labelledby="rename-heading-{item_id}">
                                 <input type="hidden" name="old_path" value="{urllib.parse.quote(rel_path)}">
                                 <label for="rename-input-{item_id}" style="display:none;" id="rename-heading-{item_id}">New name for {html_safe_name}</label>
                                 <input type="text" id="rename-input-{item_id}" name="new_name" required aria-required="true"><br>
                                 <button type="submit" class="save-btn">Save</button>
                                 <button type="button" class="cancel-btn" onclick="hideRenameForm('{item_id}')">Cancel</button>
                             </form>
                         </div>
                        """
                html_content += f"""
                         <form id="{delete_form_id}" method="post" action="/delete" style="display: none;" aria-hidden="true">
                             <input type="hidden" name="path" value="{urllib.parse.quote(rel_path)}">
                         </form>
                    </div>
                """
        html_content += """
                </div>
            </div>
        </body>
        </html>
        """
        return html_content.encode('utf-8')

    def do_GET(self):
        if not self._is_authenticated():
            self._require_auth()
            return

        parsed_path = urllib.parse.urlparse(self.path)
        lookup_rel_path = parsed_path.path
        validation_result = self._get_validated_path(lookup_rel_path)

        if validation_result is None:
             if lookup_rel_path in ('/', ''): abs_path, rel_path = UPLOAD_DIR, ""
             else: self.send_error(403, "Forbidden - Invalid Path"); return
        else:
             abs_path, rel_path = validation_result

        if os.path.isdir(abs_path):
            content = self.list_directory_html(abs_path)
            if content:
                 self.send_response(200)
                 self.send_header('Content-type', 'text/html; charset=utf-8')
                 self.send_header('Content-Length', str(len(content)))
                 self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                 self.send_header('Pragma', 'no-cache')
                 self.send_header('Expires', '0')
                 self.end_headers()
                 self.wfile.write(content)

        elif os.path.isfile(abs_path):
            try:
                file_size = os.path.getsize(abs_path)
                self.send_response(200)
                content_type = self.guess_type(abs_path)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(file_size))
                disposition = 'inline' if content_type.startswith(('image/', 'text/', 'application/pdf')) else 'attachment'
                safe_filename = os.path.basename(abs_path)
                try:
                     safe_filename.encode('latin-1')
                     filename_header = f'filename="{safe_filename}"'
                except UnicodeEncodeError:
                     encoded_filename = urllib.parse.quote(safe_filename)
                     filename_header = f"filename*=UTF-8''{encoded_filename}"
                self.send_header('Content-Disposition', f'{disposition}; {filename_header}')
                self.end_headers()
                with open(abs_path, 'rb') as f:
                    shutil.copyfileobj(f, self.wfile)
            except FileNotFoundError: self.send_error(404, "File Not Found")
            except PermissionError: self.send_error(403, "Permission Denied")
            except Exception as e:
                 print(f"Error serving file {abs_path}: {e}")
                 self.send_error(500, "Server error serving file")
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        if not self._is_authenticated():
            self._require_auth()
            return

        parsed_path = urllib.parse.urlparse(self.path)
        action_path = parsed_path.path
        content_type_header = self.headers.get('Content-Type', '')

        if not content_type_header.startswith(('multipart/form-data', 'application/x-www-form-urlencoded')):
             self.send_error(415, "Unsupported Media Type")
             return

        try:
            content_length = 0
            content_length_header = self.headers.get('Content-Length')
            if content_length_header:
                try: content_length = int(content_length_header)
                except ValueError:
                     if action_path == '/upload': self.send_error(400, "Invalid Content-Length header"); return
            if action_path == '/upload' and content_length <= 0 : self.send_error(411, "Length Required for Upload"); return

            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': content_type_header},
                keep_blank_values=True
            )

            if action_path == '/upload': self.handle_upload(form, content_length, parsed_path.query)
            elif action_path == '/delete': self.handle_delete(form)
            elif action_path == '/rename': self.handle_rename(form)
            else: self.send_error(404, "Invalid POST endpoint.")
        except Exception as e:
            print(f"Critical Error processing POST to {action_path}: {e}")
            import traceback
            traceback.print_exc()
            self.send_error(500, "Internal Server Error processing request.")

    def handle_upload(self, form, content_length, query_string):
        if content_length > MAX_UPLOAD_SIZE: self.send_error(413, f"File Too Large (Limit: {MAX_UPLOAD_SIZE // (1024*1024)} MB)"); return

        query_params = urllib.parse.parse_qs(query_string)
        target_rel_path = query_params.get('path', [''])[0]
        target_validation = self._get_validated_path(target_rel_path)
        if target_validation is None: self.send_error(400, "Invalid upload target directory."); return
        target_abs_path, _ = target_validation

        if not os.path.isdir(target_abs_path): self.send_error(404, "Upload target directory does not exist."); return
        if 'file' not in form: self.send_error(400, "Missing 'file' field in form data."); return

        file_item = form['file']
        if not hasattr(file_item, 'file') or not hasattr(file_item, 'filename') or not file_item.filename:
            self.send_error(400, "'file' field did not contain a valid file upload.")
            return

        filename = os.path.basename(file_item.filename)
        if not filename: filename = "uploaded_file"
        save_path = os.path.join(target_abs_path, filename)
        temp_save_path = save_path + ".uploading"

        try:
            print(f"Attempting upload to: {save_path} (via {temp_save_path})")
            bytes_written = 0
            with open(temp_save_path, 'wb') as f:
                chunk_size = 65536
                while True:
                    chunk = file_item.file.read(chunk_size)
                    if not chunk: break
                    bytes_written += len(chunk)
                    if bytes_written > MAX_UPLOAD_SIZE:
                        raise ValueError(f"File size exceeds limit ({MAX_UPLOAD_SIZE // (1024*1024)} MB) during transfer.")
                    f.write(chunk)
            os.rename(temp_save_path, save_path)
            print(f"Successfully saved {filename} to {target_abs_path}")
            redirect_path = '/' + urllib.parse.quote(target_rel_path if target_rel_path else '')
            self._redirect(redirect_path)
        except ValueError as e:
             print(f"Upload error (size limit) {save_path}: {e}")
             if os.path.exists(temp_save_path): os.remove(temp_save_path)
             self.send_error(413, f"Upload failed: {e}")
        except Exception as e:
            print(f"Upload error {save_path}: {e}")
            if os.path.exists(temp_save_path): os.remove(temp_save_path)
            self.send_error(500, f"Upload failed: {e}")

    def handle_delete(self, form):
        if 'path' not in form: self.send_error(400, "Missing 'path' parameter for delete operation."); return

        path_to_delete_rel = form.getvalue('path')
        validation_result = self._get_validated_path(path_to_delete_rel)
        if validation_result is None: self.send_error(403, "Forbidden: Invalid path specified for deletion."); return
        abs_path_to_delete, rel_path = validation_result

        if abs_path_to_delete == UPLOAD_DIR:
            self.send_error(400, "Cannot delete the root directory.")
            return

        if not os.path.exists(abs_path_to_delete): self.send_error(404, "Item to delete not found."); return

        parent_rel_path = os.path.dirname(rel_path) if rel_path else ""
        redirect_path = '/' + urllib.parse.quote(parent_rel_path if parent_rel_path else '')
        item_name_for_msg = html.escape(os.path.basename(abs_path_to_delete))

        try:
            if os.path.isfile(abs_path_to_delete):
                print(f"Attempting to delete file: {abs_path_to_delete}")
                os.remove(abs_path_to_delete)
                print(f"Deleted file: {item_name_for_msg}")
            elif os.path.isdir(abs_path_to_delete):
                print(f"Attempting to delete directory: {abs_path_to_delete}")
                try:
                    dir_contents = os.listdir(abs_path_to_delete)
                except PermissionError:
                     print(f"Permission error reading contents of directory {abs_path_to_delete}")
                     self.send_error(403, f"Permission denied reading contents of '{item_name_for_msg}' for deletion check.")
                     return

                if not dir_contents:
                    os.rmdir(abs_path_to_delete)
                    print(f"Deleted empty directory: {item_name_for_msg}")
                elif ALLOW_DELETE_NON_EMPTY_DIRS:
                     print(f"WARNING: Recursively deleting non-empty directory: {abs_path_to_delete}")
                     shutil.rmtree(abs_path_to_delete)
                     print(f"Deleted non-empty directory: {item_name_for_msg}")
                else:
                     print(f"Delete failed: Directory '{item_name_for_msg}' is not empty.")
                     self.send_error(400, f"Cannot delete non-empty directory '{item_name_for_msg}'.")
                     return
            self._redirect(redirect_path)
        except PermissionError:
            print(f"Permission denied trying to delete: {abs_path_to_delete}")
            self.send_error(403, f"Permission denied to delete '{item_name_for_msg}'.")
        except OSError as e:
            print(f"OS error deleting {abs_path_to_delete}: {e}")
            self.send_error(500, f"Error deleting '{item_name_for_msg}': {e}")
        except Exception as e:
            print(f"Unexpected error deleting {abs_path_to_delete}: {e}")
            self.send_error(500, f"Unexpected error deleting '{item_name_for_msg}'.")

    def handle_rename(self, form):
        if 'old_path' not in form or 'new_name' not in form: self.send_error(400, "Missing required parameters for rename."); return

        old_rel_path = form.getvalue('old_path')
        new_name = form.getvalue('new_name').strip()

        old_validation = self._get_validated_path(old_rel_path)
        if old_validation is None: self.send_error(403, "Forbidden: Invalid 'old_path' specified for rename."); return
        old_abs_path, old_rel = old_validation
        old_item_name_for_msg = html.escape(os.path.basename(old_abs_path))

        if old_abs_path == UPLOAD_DIR:
            self.send_error(400, "Cannot rename the root directory.")
            return

        if not os.path.exists(old_abs_path): self.send_error(404, f"Item '{old_item_name_for_msg}' not found to rename."); return

        if not new_name or '/' in new_name or '\\' in new_name or new_name in ('.', '..'):
            self.send_error(400, "Invalid new name. Cannot be empty, contain slashes, or be '.' or '..'.")
            return

        new_name_for_msg = html.escape(new_name)
        parent_dir_abs = os.path.dirname(old_abs_path)
        new_abs_path = os.path.join(parent_dir_abs, new_name)

        if os.path.exists(new_abs_path):
             if old_abs_path.lower() == new_abs_path.lower() and old_abs_path != new_abs_path:
                  pass
             else:
                  self.send_error(409, f"Cannot rename: '{new_name_for_msg}' already exists in this location.")
                  return

        parent_rel_path = os.path.dirname(old_rel) if old_rel else ""
        redirect_path = '/' + urllib.parse.quote(parent_rel_path if parent_rel_path else '')

        try:
            print(f"Attempting to rename '{old_abs_path}' to '{new_abs_path}'")
            os.rename(old_abs_path, new_abs_path)
            print(f"Successfully renamed '{old_item_name_for_msg}' to '{new_name}'")
            self._redirect(redirect_path)
        except PermissionError:
            print(f"Permission denied trying to rename: {old_abs_path}")
            self.send_error(403, f"Permission denied to rename '{old_item_name_for_msg}'.")
        except OSError as e:
            print(f"OS error renaming {old_abs_path} to {new_abs_path}: {e}")
            self.send_error(500, f"Error renaming '{old_item_name_for_msg}': {e}")
        except Exception as e:
            print(f"Unexpected error renaming {old_abs_path}: {e}")
            self.send_error(500, f"Unexpected error renaming '{old_item_name_for_msg}'.")

def run(server_class=HTTPServer, handler_class=GDriveHandler, port=PORT):
    try:
        if not os.path.exists(UPLOAD_DIR):
             print(f"Creating upload directory: {UPLOAD_DIR}")
             os.makedirs(UPLOAD_DIR)
        if not os.access(UPLOAD_DIR, os.W_OK | os.X_OK):
             print(f"WARNING: Directory {UPLOAD_DIR} might not be fully accessible (writable/listable) by Termux!")
             print("         Please check permissions using your device's file manager or Termux.")
    except OSError as e:
        print(f"ERROR: Could not create or access upload directory {UPLOAD_DIR}: {e}")
        print("Please ensure the base path exists and Termux has storage permissions ('termux-setup-storage').")
        return

    server_address = ('', port)
    try:
        httpd = server_class(server_address, handler_class)
    except OSError as e:
         print(f"ERROR: Could not bind to port {port}. It might be in use. ({e})")
         return

    print(f"🚀 Personal Cloud Server running (with Basic Authentication)...")
    print(f"   Username: {USERNAME}")
    print(f"   Directory: {UPLOAD_DIR}")
    print(f"   Mode: {'Allow delete non-empty dirs' if ALLOW_DELETE_NON_EMPTY_DIRS else 'Delete only files/empty dirs'}")
    print(f"   Access locally at: http://localhost:{port} or http://<your-device-ip>:{port}")
    print(f"   If using ngrok (for external access), run: ngrok http {port}")
    print("   WARNING: Basic Authentication over HTTP is not secure for internet exposure.")
    print("Press Ctrl+C to stop the server.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopping...")
        httpd.server_close()
        print("Server stopped.")
    except Exception as e:
         print(f"\n🚨 Server encountered an unexpected error: {e}")
         httpd.server_close()

if _name_ == "_main_":
    print("--- Starting Personal Cloud Server ---")
    print("Reminder: Ensure Termux has storage access ('termux-setup-storage' command) and")
    print(f"          that the directory '{UPLOAD_DIR}' exists and is accessible.")
    run()
