<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>9-Rule Validation Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Poppins', sans-serif; }
        body { background: #f0f2f5; display: flex; min-height: 100vh; }

        /* --- Stylish Sidebar --- */
        .sidebar { width: 260px; background: #1a1a2e; color: white; position: fixed; height: 100vh; padding: 25px; }
        .sidebar h2 { color: #00d2ff; font-size: 22px; margin-bottom: 35px; text-transform: uppercase; letter-spacing: 2px; }
        .nav-links { list-style: none; }
        .nav-links li { padding: 15px; margin-bottom: 8px; border-radius: 8px; cursor: pointer; transition: 0.3s; display: flex; align-items: center; gap: 12px; color: #adb5bd; }
        .nav-links li:hover, .nav-links li.active { background: #00d2ff; color: #1a1a2e; font-weight: 600; }

        /* --- Main Layout --- */
        .main-content { margin-left: 260px; width: 100%; padding: 40px; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; border-bottom: 2px solid #ddd; padding-bottom: 10px; }

        /* --- Modern Login Card (Blank Fields) --- */
        .card { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); max-width: 450px; margin-bottom: 30px; }
        .input-group { position: relative; margin-bottom: 20px; }
        .input-group input { width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 10px; outline: none; font-size: 15px; transition: 0.3s; }
        .input-group label { position: absolute; left: 15px; top: 50%; transform: translateY(-50%); color: #aaa; pointer-events: none; transition: 0.3s; background: #fff; padding: 0 5px; }
        .input-group input:focus ~ label, .input-group input:valid ~ label { top: 0; font-size: 12px; color: #00d2ff; font-weight: 600; }
        .input-group input:focus { border-color: #00d2ff; }
        .btn { width: 100%; padding: 12px; background: #00d2ff; color: #1a1a2e; border: none; border-radius: 10px; font-weight: 600; cursor: pointer; transition: 0.3s; }
        .btn:hover { background: #00b8e6; transform: translateY(-2px); }

        /* --- 9-Rule Report Table --- */
        .report-card { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 15px; text-align: left; border-bottom: 1px solid #eee; font-size: 14px; }
        th { background: #f8f9fa; color: #333; font-weight: 600; }
        .pass { color: #27ae60; font-weight: 600; }
        .fail { color: #e74c3c; font-weight: 600; }
        .badge { padding: 4px 10px; border-radius: 20px; font-size: 11px; text-transform: uppercase; }
    </style>
</head>
<body>

    <div class="sidebar">
        <h2><i class="fas fa-shield-alt"></i> SafeGuard</h2>
        <ul class="nav-links">
            <li class="active"><i class="fas fa-tachometer-alt"></i> Dashboard</li>
            <li><i class="fas fa-file-invoice"></i> All 9 Reports</li>
            <li><i class="fas fa-user-shield"></i> Security Check</li>
            <li><i class="fas fa-cog"></i> Settings</li>
        </ul>
    </div>

    <div class="main-content">
        <div class="header">
            <h1>System Security Console</h1>
            <span id="currentTime">April 4, 2026</span>
        </div>

        <div class="card">
            <h3 style="margin-bottom: 15px;">User Validation</h3>
            <div class="input-group">
                <input type="text" id="username" required>
                <label>Username</label>
            </div>
            <div class="input-group">
                <input type="password" id="password" required>
                <label>Password</label>
            </div>
            <button class="btn" onclick="runAll9Reports()">Run All 9 Reports</button>
        </div>

        <div class="report-card" id="reportArea" style="display:none;">
            <h3>Full Validation Report (9 Rules)</h3>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Security Rule Description</th>
                        <th>Status</th>
                        <th>Verdict</th>
                    </tr>
                </thead>
                <tbody id="resultBody"></tbody>
            </table>
        </div>
    </div>

    <script>
        function runAll9Reports() {
            const u = document.getElementById('username').value;
            const p = document.getElementById('password').value;
            const body = document.getElementById('resultBody');
            document.getElementById('reportArea').style.display = 'block';
            body.innerHTML = "";

            const rules = [
                { id: 1, name: "Empty Username Check", check: u !== "" },
                { id: 2, name: "Empty Password Check", check: p !== "" },
                { id: 3, name: "Min Password Length (8)", check: p.length >= 8 },
                { id: 4, name: "Max Password Length (20)", check: p.length <= 20 },
                { id: 5, name: "Username No Spaces", check: !u.includes(" ") },
                { id: 6, name: "Password Special Char", check: /[!@#$%^&*]/.test(p) },
                { id: 7, name: "Password Number Check", check: /\d/.test(p) },
                { id: 8, name: "Admin Restriction", check: u.toLowerCase() !== "admin" },
                { id: 9, name: "Username Length (Min 4)", check: u.length >= 4 }
            ];

            rules.forEach(r => {
                let statusClass = r.check ? "pass" : "fail";
                let statusText = r.check ? "PASSED" : "FAILED";
                let verdict = r.check ? "Secure" : "Action Required";
                
                body.innerHTML += `<tr>
                    <td>${r.id}</td>
                    <td>${r.name}</td>
                    <td class="${statusClass}">${statusText}</td>
                    <td><span class="badge" style="background:${r.check ? '#d4edda':'#f8d7da'}">${verdict}</span></td>
                </tr>`;
            });
        }
    </script>
</body>
</html>
