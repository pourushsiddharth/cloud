<!DOCTYPE html>
<html lang="en">
<head>
  <meta name="robots" content="index, follow" />
  <meta name="description" content="Create a personal cloud file server using Python, Termux, and Ngrok. Host, upload, and manage files from Android with a browser-friendly UI.">
  <meta name="keywords" content="personal cloud drive, android file server, termux python server, build personal google drive, upload files with python, ngrok cloud host, android localhost file server">
  <meta name="author" content="Pourush Siddharth">
 
</head>
<body>

<h1>☁️ Personal Cloud Drive (for Android / Termux)</h1>

<p>This is a <strong>personal cloud file storage app</strong> built in Python. You can upload, download, rename, and delete files through a beautiful web interface — all hosted and running directly from your Android phone with <strong>Termux</strong>.</p>

<div class="section">
  <h2>✨ Features</h2>
  <ul>
    <li>🗂️ File browser (folders, files, types, sizes)</li>
    <li>⬆ Upload from browser (no app required)</li>
    <li>✏ Rename or 🗑 Delete files with a click</li>
    <li>🔍 Search folders</li>
    <li>🔐 Username/Password security</li>
    <li>🌐 Internet access via ngrok</li>
    <li>📱 100% mobile-friendly</li>
  </ul>
</div>

<div class="section">
  <h2>📢 Works Best On:</h2>
  <p>👉 <strong>Android device</strong> using <a href="https://f-droid.org/packages/com.termux/" target="_blank">Termux</a>.</p>
</div>

<hr>

<div class="section">
  <h2>🛠️ Step-by-Step Setup (For Beginners)</h2>

  <h3>1. Install Termux</h3>
  <p>Download Termux from F-Droid:</p>
  <a href="https://f-droid.org/packages/com.termux/" target="_blank">📲 Download Termux</a>

  <h3>2. Setup Storage Permissions</h3>
  <pre>termux-setup-storage</pre>
  <p>Then <strong>allow permission</strong> when asked.</p>

  <h3>3. Install Python, Git, tmux</h3>
  <pre>pkg update
pkg install python git tmux -y</pre>

  <h3>4. Clone the Project</h3>
  <pre>git clone https://github.com/your-username/personal-cloud-drive.git
cd personal-cloud-drive</pre>

  <h3>5. Run the Server</h3>
  <pre>python3 server.py</pre>

  <p>Now visit <code>http://localhost:8000</code> in your phone's browser.</p>
</div>

<div class="section">
  <h2>🔐 Login Credentials</h2>
  <ul>
    <li>Username: <code>username</code></li>
    <li>Password: <code>password</code></li>
  </ul>
  <p><strong>Tip:</strong> You can change these in <code>server.py</code></p>
</div>

<div class="section">
  <h2>🌐 Access from PC / Another Device</h2>
  <ol>
    <li>Run in Termux: <code>ip a</code></li>
    <li>Look for IP like: <code>192.168.x.x</code></li>
    <li>On your PC browser, go to: <code>http://192.168.x.x:8000</code></li>
  </ol>
</div>

<div class="section">
  <h2>🌍 Make It Online with Ngrok</h2>

  <h3>1. Download ngrok</h3>
  <pre>
pkg install wget unzip -y
wget https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-arm.zip
unzip ngrok-stable-linux-arm.zip
chmod +x ngrok
  </pre>

  <h3>2. Set your ngrok auth token</h3>
  <p>Copy from https://dashboard.ngrok.com/get-started/setup</p>
  <pre>./ngrok config add-authtoken YOUR_TOKEN_HERE</pre>

  <h3>3. Keep server running in background (tmux)</h3>
  <pre>
tmux new -s cloud
python3 server.py
# Then press Ctrl + B, then D to detach
  </pre>

  <h3>4. Start ngrok tunnel</h3>
  <pre>./ngrok http 8000</pre>

  <p>Now access your drive from anywhere using the URL like:</p>
  <code>https://abcd1234.ngrok.io</code>
</div>

<div class="section">
  <h2>⚙ Available Config Settings</h2>
  <ul>
    <li><code>UPLOAD_DIR</code> → Folder to store files (default: <code>/storage/emulated/0/Drive</code>)</li>
    <li><code>PORT</code> → Web server port (default: 8000)</li>
    <li><code>MAX_UPLOAD_SIZE</code> → Max upload file size (default: 100 MB)</li>
    <li><code>ALLOW_DELETE_NON_EMPTY_DIRS</code> → Set to true if you want to delete full folders</li>
  </ul>
</div>

<div class="section">
  <h2>📝 How to Use</h2>
  <ul>
    <li>Click folders to open</li>
    <li>Upload files using the upload button</li>
    <li>Click “⋮” menu next to a file to Rename or Delete</li>
    <li>Use search box to filter files</li>
  </ul>
</div>

<div class="section">
  <h2>🛑 How to Stop the Server</h2>
  <p>If running:</p>
  <pre>Ctrl + C</pre>
  <p>If running in background (tmux):</p>
  <pre>
tmux attach -t cloud
# Then Ctrl + C to stop
  </pre>
</div>

<div class="section">
  <h2>📁 Where Are My Files Stored?</h2>
  <p>Files are stored in your Android internal storage:</p>
  <pre>/storage/emulated/0/Drive</pre>
  <p>You can use your File Manager app to browse or move files in/out.</p>
</div>

<div class="section">
  <h2>💡 Tips</h2>
  <ul>
    <li>Use <strong>tmux</strong> to keep server running while switching apps</li>
    <li>Use <strong>ngrok</strong> for remote/online access</li>
    <li>Use basic auth to protect files</li>
    <li>Runs 100% offline with Termux</li>
  </ul>
</div>

<div class="section">
  <h2>⚠️ Disclaimers & Security</h2>
  <div class="warning">
    <ul>
      <li>This is for personal use only</li>
      <li>Basic Auth is NOT safe without HTTPS</li>
      <li>Do not expose your ngrok link to strangers</li>
      <li>No encryption, no SSL, no user roles</li>
    </ul>
  </div>
</div>

<div class="section">
  <h2>🙋 Need Help?</h2>
  <p>Feel free to ask questions, fork the project, or improve it!</p>
  <p><strong>Happy hosting your own cloud 😄☁️</strong></p>
</div>

</body>
</html>
