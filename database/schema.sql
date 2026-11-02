-- PROCUREMENTIQ AI Database Schema
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    company_name TEXT DEFAULT 'Global Logistics & Mfg Corp',
    role TEXT DEFAULT 'Procurement Lead',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS procurement_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_code TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    item_name TEXT NOT NULL,
    category TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    budget REAL NOT NULL,
    currency TEXT DEFAULT 'USD',
    required_delivery_date TEXT NOT NULL,
    delivery_location TEXT NOT NULL,
    min_warranty_months INTEGER DEFAULT 12,
    payment_terms_pref TEXT DEFAULT 'Net 30',
    additional_requirements TEXT,
    status TEXT DEFAULT 'Draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT NOT NULL,
    code TEXT,
    country TEXT DEFAULT 'USA',
    category TEXT,
    rating REAL DEFAULT 4.5,
    tier TEXT DEFAULT 'Tier 1',
    compliance_status TEXT DEFAULT 'Verified',
    on_time_delivery_rate REAL DEFAULT 95.0,
    defect_rate REAL DEFAULT 1.2,
    financial_stability TEXT DEFAULT 'Stable',
    years_in_business INTEGER DEFAULT 10,
    contact_email TEXT,
    contact_phone TEXT,
    notes TEXT,
    is_demo BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS quotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    supplier_id INTEGER,
    supplier_name TEXT NOT NULL,
    quotation_number TEXT,
    item_description TEXT,
    unit_price REAL NOT NULL,
    quantity INTEGER NOT NULL,
    currency TEXT DEFAULT 'USD',
    discount_amount REAL DEFAULT 0.0,
    tax_rate REAL DEFAULT 0.0,
    tax_amount REAL DEFAULT 0.0,
    shipping_cost REAL DEFAULT 0.0,
    installation_cost REAL DEFAULT 0.0,
    other_charges REAL DEFAULT 0.0,
    total_cost REAL NOT NULL,
    warranty_months INTEGER DEFAULT 12,
    delivery_days INTEGER DEFAULT 30,
    promised_delivery_date TEXT,
    payment_terms TEXT DEFAULT 'Net 30',
    quote_validity_date TEXT,
    filename TEXT,
    file_path TEXT,
    extraction_confidence REAL DEFAULT 92.0,
    extraction_notes TEXT,
    is_confirmed BOOLEAN DEFAULT 1,
    missing_fields TEXT DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES procurement_requests(id) ON DELETE CASCADE,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS quotation_line_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quotation_id INTEGER NOT NULL,
    item_desc TEXT,
    qty INTEGER,
    unit_price REAL,
    total_price REAL,
    FOREIGN KEY (quotation_id) REFERENCES quotations(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS supplier_research (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    supplier_id INTEGER,
    supplier_name TEXT NOT NULL,
    profile_summary TEXT,
    certifications TEXT,
    market_reputation TEXT,
    financial_health TEXT,
    source_references TEXT,
    data_freshness TEXT,
    information_gaps TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES procurement_requests(id) ON DELETE CASCADE,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS risk_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    quotation_id INTEGER NOT NULL,
    supplier_name TEXT NOT NULL,
    overall_risk_score REAL NOT NULL,
    risk_category TEXT NOT NULL,
    delivery_risk TEXT,
    compliance_risk TEXT,
    dependency_risk TEXT,
    documentation_risk TEXT,
    commercial_terms_risk TEXT,
    supporting_evidence TEXT,
    missing_evidence TEXT,
    recommended_mitigation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES procurement_requests(id) ON DELETE CASCADE,
    FOREIGN KEY (quotation_id) REFERENCES quotations(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS cost_comparisons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    quotation_id INTEGER NOT NULL,
    supplier_name TEXT NOT NULL,
    unit_price REAL NOT NULL,
    quantity INTEGER NOT NULL,
    subtotal REAL NOT NULL,
    discount_amount REAL DEFAULT 0.0,
    net_subtotal REAL NOT NULL,
    tax_amount REAL DEFAULT 0.0,
    shipping_cost REAL DEFAULT 0.0,
    installation_cost REAL DEFAULT 0.0,
    other_charges REAL DEFAULT 0.0,
    estimated_total_cost REAL NOT NULL,
    currency TEXT DEFAULT 'USD',
    cost_score REAL DEFAULT 0.0,
    formulas_used TEXT,
    missing_cost_warnings TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES procurement_requests(id) ON DELETE CASCADE,
    FOREIGN KEY (quotation_id) REFERENCES quotations(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    quotation_id INTEGER NOT NULL,
    supplier_name TEXT NOT NULL,
    rank INTEGER NOT NULL,
    is_recommended BOOLEAN DEFAULT 0,
    overall_score REAL NOT NULL,
    cost_score REAL NOT NULL,
    delivery_score REAL NOT NULL,
    risk_score REAL NOT NULL,
    warranty_score REAL NOT NULL,
    weight_breakdown TEXT,
    satisfies_mandatory BOOLEAN DEFAULT 1,
    disqualification_reasons TEXT,
    key_advantages TEXT,
    main_disadvantages TEXT,
    explanation TEXT,
    negotiation_tips TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES procurement_requests(id) ON DELETE CASCADE,
    FOREIGN KEY (quotation_id) REFERENCES quotations(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS agent_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    status TEXT DEFAULT 'Pending',
    execution_mode TEXT DEFAULT 'DEMO_FALLBACK',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    total_duration_seconds REAL DEFAULT 0.0,
    error_message TEXT,
    FOREIGN KEY (request_id) REFERENCES procurement_requests(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS agent_outputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    request_id INTEGER NOT NULL,
    agent_number INTEGER NOT NULL,
    agent_name TEXT NOT NULL,
    purpose TEXT NOT NULL,
    status TEXT DEFAULT 'Completed',
    input_summary TEXT,
    output_summary TEXT,
    full_output_json TEXT,
    execution_duration_seconds REAL DEFAULT 0.0,
    warnings TEXT,
    evidence_references TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (run_id) REFERENCES agent_runs(id) ON DELETE CASCADE,
    FOREIGN KEY (request_id) REFERENCES procurement_requests(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS decision_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    recommended_supplier TEXT NOT NULL,
    selected_supplier TEXT NOT NULL,
    was_overridden BOOLEAN DEFAULT 0,
    override_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES procurement_requests(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    weight_cost REAL DEFAULT 0.40,
    weight_delivery REAL DEFAULT 0.25,
    weight_risk REAL DEFAULT 0.20,
    weight_warranty REAL DEFAULT 0.15,
    default_currency TEXT DEFAULT 'USD',
    demo_mode BOOLEAN DEFAULT 1,
    llm_provider TEXT DEFAULT 'gemini',
    gemini_api_key TEXT,
    ngrok_api_key TEXT,
    groq_api_key TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
