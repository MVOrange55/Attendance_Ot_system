<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Professional Admin Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
        :root {
            --primary-color: #4834d4;
            --bg-color: #f4f7fe;
            --sidebar-color: #ffffff;
            --text-color: #333;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Poppins', sans-serif;
        }

        body {
            background-color: var(--bg-color);
            display: flex;
        }

        /* --- Sidebar Navigation --- */
        .sidebar {
            width: 260px;
            height: 100vh;
            background: var(--sidebar-color);
            position: fixed;
            padding: 30px 20px;
            box-shadow: 4px 0 10px rgba(0,0,0,0.05);
        }

        .logo {
            font-size: 22px;
            font-weight: 700;
            color: var(--primary-color);
            margin-bottom: 40px;
            text-align: center;
        }

        .nav-links {
            list-style: none;
        }

        .nav-links li {
            margin-bottom: 10px;
        }

        .nav-links a {
            text-decoration: none;
            color: #7d8da1;
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 12px 15px;
            border-radius: 10px;
            transition: 0.3s;
        }

        .nav-links a:hover, .nav-links a.active {
            background: var(--primary-color);
            color: #fff;
        }

        /* --- Main Content Area --- */
        .main-content {
            margin-left: 260px;
            width: calc(100% - 260px);
            padding: 40px;
        }

        header {
            display: flex
