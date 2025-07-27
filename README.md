📊 Locus – Business Intelligence Dashboard for Modern Entrepreneurs
Locus is a powerful all-in-one business analytics platform designed to help entrepreneurs, startups, and small businesses make data-driven decisions with ease. Whether you're tracking finances, measuring KPIs, optimizing ROI, or forecasting growth, Locus gives you a beautifully integrated experience to manage and visualize your business in real time.

🚀 Features
Here’s what Locus brings to your business toolkit:

🔢 Core Modules
📥 Data Entry
Centralized input panel for all business data across modules.

🏆 Achievements
Tracks milestone completions and gamifies business progress.

💳 Billing
Record revenue & expenses, track profitability, and generate simple ledgers.

❤️ Business Health
Evaluates your business performance using 8 KPIs:

Revenue Growth

Gross Profit Margin

Forecasting Accuracy

Customer Retention

Marketing ROI

Customer Acquisition Cost

Team Efficiency

User Growth

📄 Business Report Generator
Aggregates data from all modules into a comprehensive PDF report.

✅ Checklist
Add tasks, track progress, and manage team execution with ease.

💱 Currency Converter
Convert billing & projections across international currencies in real time.

🔥 Daily Streak
Tracks daily user engagement and encourages consistent usage.

🗓️ Event Planner
Schedule, track, and manage key business events & deadlines.

📈 Forecasting
Predict future growth, revenue, and other metrics with simple input logic.

💡 Suggestions
Offers automated improvement suggestions based on your business data.

🧠 Optimization
Budget allocator + ROI calculator to help allocate resources efficiently.

📊 Visualization
Graphical representations of business data with bar, pie, and trend charts.

🧑‍💼 User & Utility
🙋‍♂️ Profile Page
Manage personal and business info, contact, industry tags, and more.

🎯 Business Personality Quiz
4-question quiz to discover your entrepreneurial style (e.g., "Data-Driven", "Scrappy Builder").

🧮 Tax Estimator
Estimate income tax/GST liabilities based on earnings and expenses.

🛠️ Tech Stack
HTML5, CSS3, JavaScript (Vanilla/Bootstrap/Tailwind)

Optional backend (python)

LocalStorage / MySql

🎯 Who Is It For?
Locus is built for:

Startup founders

Early-stage businesses

Business analysts

Growth hackers

Students & Hackathon teams

📎 Setup Instructions
Clone the repository:
https://github.com/omchitlangia/locus.git

Open the app in the terminal and run the file (py main.py)
this will give you a link for localhosting for you to run the application

SQL WORKBENCH CODE(put the following code in sql workbench so that the app can stroe and retrive its data)
-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Create user table
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password VARCHAR(128) NOT NULL,
    email_verified BOOLEAN DEFAULT 0,
    profile_pic VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    business_name VARCHAR(100),
    business_type VARCHAR(50),
    industry VARCHAR(50),
    location VARCHAR(100),
    health_score FLOAT,
    persona VARCHAR(50)
);

-- Create daily_streak table
CREATE TABLE daily_streak (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    current_streak INTEGER DEFAULT 0,
    last_active_date DATE,
    FOREIGN KEY (user_id) REFERENCES user (id)
);

-- Create sku table
CREATE TABLE sku (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    cost_price FLOAT NOT NULL,
    selling_price FLOAT NOT NULL,
    quantity INTEGER DEFAULT 0,
    category VARCHAR(50),
    expiry_date DATE,
    user_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user (id)
);

-- Create revenue_predictions table
CREATE TABLE revenue_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    prediction_date DATETIME NOT NULL,
    period_start DATETIME NOT NULL,
    period_end DATETIME NOT NULL,
    predicted_amount FLOAT NOT NULL,
    actual_amount FLOAT,
    r_squared FLOAT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user (id)
);

-- Create revenue table
CREATE TABLE revenue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount FLOAT NOT NULL,
    remarks VARCHAR(200),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    bill_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (bill_id) REFERENCES bill (id)
);

-- Create fixed_cost table
CREATE TABLE fixed_cost (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount FLOAT NOT NULL,
    remarks VARCHAR(200),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user (id)
);

-- Create variable_cost table
CREATE TABLE variable_cost (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount FLOAT NOT NULL,
    remarks VARCHAR(200),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    bill_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (bill_id) REFERENCES bill (id)
);

-- Create event table
CREATE TABLE event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    event_type VARCHAR(50) NOT NULL,
    category VARCHAR(50),
    start_date DATETIME NOT NULL,
    end_date DATETIME NOT NULL,
    is_recurring BOOLEAN DEFAULT 0,
    recurrence_pattern VARCHAR(50),
    marketing_cost FLOAT DEFAULT 0,
    logistics_cost FLOAT DEFAULT 0,
    hiring_cost FLOAT DEFAULT 0,
    other_cost FLOAT DEFAULT 0,
    expected_revenue_boost FLOAT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user (id)
);

-- Create bill table
CREATE TABLE bill (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bill_number VARCHAR(20) UNIQUE NOT NULL,
    customer_name VARCHAR(100),
    customer_phone VARCHAR(20),
    date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    subtotal NUMERIC(10, 2) NOT NULL,
    tax_amount NUMERIC(10, 2) NOT NULL DEFAULT 0,
    discount NUMERIC(10, 2) NOT NULL DEFAULT 0,
    grand_total NUMERIC(10, 2) NOT NULL,
    payment_method VARCHAR(50) DEFAULT 'Cash',
    payment_status VARCHAR(20) DEFAULT 'paid',
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user (id)
);

-- Create billing_item table
CREATE TABLE billing_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bill_id INTEGER NOT NULL,
    sku_id INTEGER NOT NULL,
    sku_code VARCHAR(20) NOT NULL,
    sku_name VARCHAR(100) NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL,
    total_price NUMERIC(10, 2) NOT NULL,
    expiry_date DATE,
    FOREIGN KEY (bill_id) REFERENCES bill (id),
    FOREIGN KEY (sku_id) REFERENCES sku (id)
);

-- Create achievements table
CREATE TABLE achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon_class VARCHAR(50) DEFAULT 'fas fa-trophy',
    required_action VARCHAR(50),
    required_count INTEGER DEFAULT 1
);

-- Create user_achievements table
CREATE TABLE user_achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    achievement_id INTEGER NOT NULL,
    progress INTEGER DEFAULT 0,
    unlocked_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (achievement_id) REFERENCES achievements (id)
);

-- Create startup_checklist table
CREATE TABLE startup_checklist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    item_key VARCHAR(50),
    completed BOOLEAN DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES user (id)
);





Made with 💼 and ☕ by LOCUS
Feel free to fork, contribute, or raise issues!
