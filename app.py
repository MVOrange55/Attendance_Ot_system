<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Attendance Management System</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root { --primary: #e67e22; --dark: #2c3e50; --light: #f4f7f6; }
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Poppins', sans-serif; }
        body { background: var(--light); display: flex; }

        /* --- 1. Attractive Navigation (Sidebar) --- */
        .sidebar { width: 280px; height: 100vh; background: var(--dark); color: white; position: fixed; padding: 20px; box-shadow: 4px 0 10px rgba(0,0,0,0.1); }
        .sidebar h2 { color: var(--primary); font-size: 24px; margin-bottom: 30px; border-bottom: 1px solid #34495e; padding-bottom: 10px; }
        .nav-links { list-style: none; }
        .nav-links li { padding: 12px 15px; margin-bottom: 5px; border-radius: 8px; cursor: pointer; transition: 0.3s; font-size: 14px; color: #bdc3c7; display: flex; align-items: center; gap: 10px; }
        .nav-links li:hover { background: var(--primary); color: white; }
        .nav-links li.active { background: var(--primary); color: white; font-weight: 500; }

        /* --- 2. Main Content --- */
        .main-content { margin-left: 280px; width: 100%; padding: 40px; }
        .header { margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center; }

        /* --- 3. Clean Login Section (No Placeholders) --- */
        .login-card { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 5px 20px rgba(0,0,0,0.05); max-width: 400px; margin-bottom: 40px; }
        .input-group { position: relative; margin-bottom: 25px; }
        .input-group input { width: 100%; padding: 12px; border: 2px solid #eee; border-radius: 8px; outline: none; font-size: 16px; background: transparent; }
        .input-group label { position: absolute; left: 15px; top: 50%; transform: translateY(-50%); color: #999; pointer-events: none; transition: 0.3s; background: #fff; padding: 0 5px; }
        /* Floating Label Logic */
        .input-group input:focus ~ label, .input-group input:valid ~ label { top: 0; font-size: 12px; color: var(--primary); font-weight: 600; }
        .input-group input:focus { border-color: var(--primary); }
        .btn-login { width: 100%; padding: 12px; background: var(--primary); color: white; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; transition: 0.3s; }

        /* --- 4. Report Display Table --- */
        .report-view { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 5px 20px rgba(0,0,0,0.05); }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 15px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #fafafa; color: #666; text-transform: uppercase; font-size: 12px; letter-spacing: 1px; }
    </style>
</head>
<body>

    <div class="sidebar">
        <h2><i class="fas fa-calendar-check"></i> Navigation</h2>
        <ul class="nav-links">
            <li class="active">1. Attendance Muster</li>
            <li>2. Overtime Report</li>
            <li>3. Exception Summary</li>
            <li>4. Exception Detailed</li>
            <li>5. Miss Punch Tracker</li>
            <li>6. Half Day Report</li>
            <li>7. Absenteeism Report</li>
            <li>8. Attendance Summary</li>
            <li>9. Correction Module</li>
        </ul>
    </div>

    <div class="main-content">
        <div class="header">
            <h1>Report Dashboard</h1>
            <div class="user"><i class="fas fa-user-circle"></i> Admin</div>
        </div>

        <div class="login-card">
            <h3 style="margin-bottom:20px;">System Login</h3>
            <div class="input-group">
                <input type="text" required>
                <label>Username</label>
            </div>
            <div class="input-group">
                <input type="password" required>
                <label>Password</label>
            </div>
            <button class="btn-login">View Report</button>
        </div>

        <div class="report-view">
            <h3>Active Report Data</h3>
            <table>
                <thead>
                    <tr>
                        <th>Employee ID</th>
                        <th>Name</th>
                        <th>Report Type</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>EMP_101</td>
                        <td>Rahul Singh</td>
                        <td>Attendance Muster</td>
                        <td style="color: green; font-weight: 600;">Present</td>
                    </tr>
                    <tr>
                        <td>EMP_102</td>
                        <td>Sonia Verma</td>
                        <td>Miss Punch</td>
                        <td style="color: red; font-weight: 600;">Correction Required</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

</body>
</html>
