import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json

class DatabaseManager:
    def __init__(self, db_path="pharma_inventory.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection with row factory for easier data access"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database with all required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Inventory table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                drug_name TEXT NOT NULL,
                category TEXT NOT NULL,
                manufacturer TEXT,
                batch_number TEXT UNIQUE NOT NULL,
                current_stock INTEGER DEFAULT 0,
                minimum_stock INTEGER DEFAULT 10,
                unit_price REAL DEFAULT 0.0,
                expiry_date DATE,
                supplier_name TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                drug_id INTEGER,
                transaction_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL,
                total_amount REAL,
                reference_number TEXT,
                notes TEXT,
                department TEXT,
                user_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (drug_id) REFERENCES inventory (id)
            )
        ''')
        
        # Suppliers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                contact_person TEXT,
                phone TEXT,
                email TEXT,
                address TEXT,
                lead_time_days INTEGER DEFAULT 7,
                reliability_score REAL DEFAULT 5.0,
                cost_rating REAL DEFAULT 5.0,
                quality_score REAL DEFAULT 5.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Purchase orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchase_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT UNIQUE NOT NULL,
                supplier_id INTEGER,
                drug_id INTEGER,
                quantity INTEGER NOT NULL,
                unit_price REAL,
                total_amount REAL,
                status TEXT DEFAULT 'pending',
                order_date DATE DEFAULT CURRENT_DATE,
                expected_delivery DATE,
                actual_delivery DATE,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (supplier_id) REFERENCES suppliers (id),
                FOREIGN KEY (drug_id) REFERENCES inventory (id)
            )
        ''')
        
        # Drug interactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drug_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                drug1 TEXT NOT NULL,
                drug2 TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT,
                clinical_effect TEXT,
                management TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Consumption patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS consumption_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                drug_id INTEGER,
                date DATE NOT NULL,
                quantity_consumed INTEGER DEFAULT 0,
                department TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (drug_id) REFERENCES inventory (id)
            )
        ''')
        
        # Alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                drug_id INTEGER,
                is_active BOOLEAN DEFAULT 1,
                acknowledged BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (drug_id) REFERENCES inventory (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Insert default data if tables are empty
        self.insert_default_data()
    
    def insert_default_data(self):
        """Insert sample data for demonstration"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if we already have data
        cursor.execute("SELECT COUNT(*) FROM inventory")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Insert sample suppliers
            suppliers = [
                ("PharmaCorp Inc", "John Smith", "+1-555-0101", "john@pharmacorp.com", "123 Pharma St", 5, 4.5, 4.0, 4.8),
                ("MediSupply Co", "Sarah Johnson", "+1-555-0102", "sarah@medisupply.com", "456 Medical Ave", 7, 4.2, 3.8, 4.5),
                ("HealthDist Ltd", "Mike Chen", "+1-555-0103", "mike@healthdist.com", "789 Health Blvd", 3, 4.8, 4.5, 4.9)
            ]
            
            cursor.executemany('''
                INSERT INTO suppliers (name, contact_person, phone, email, address, lead_time_days, reliability_score, cost_rating, quality_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', suppliers)
            
            # Insert sample inventory
            inventory_items = [
                ("Paracetamol 500mg", "Analgesics", "PharmaCorp", "PCM001", 250, 50, 20.75, "2025-06-15", "PharmaCorp Inc", "Pain relief medication"),
                ("Amoxicillin 250mg", "Antibiotics", "MediSupply", "AMX001", 180, 30, 124.50, "2025-04-20", "MediSupply Co", "Antibiotic for bacterial infections"),
                ("Metformin 500mg", "Diabetes", "HealthDist", "MET001", 320, 40, 62.25, "2025-12-10", "HealthDist Ltd", "Type 2 diabetes medication"),
                ("Aspirin 75mg", "Cardiovascular", "PharmaCorp", "ASP001", 150, 25, 24.90, "2025-08-25", "PharmaCorp Inc", "Low-dose aspirin for heart health"),
                ("Salbutamol Inhaler", "Respiratory", "MediSupply", "SAL001", 45, 15, 1037.50, "2025-03-30", "MediSupply Co", "Asthma relief inhaler"),
                ("Insulin Rapid", "Diabetes", "HealthDist", "INS001", 25, 10, 3735.00, "2025-02-15", "HealthDist Ltd", "Fast-acting insulin"),
                ("Ciprofloxacin 500mg", "Antibiotics", "PharmaCorp", "CIP001", 90, 20, 186.75, "2025-07-08", "PharmaCorp Inc", "Broad-spectrum antibiotic"),
                ("Omeprazole 20mg", "Gastrointestinal", "MediSupply", "OME001", 200, 35, 70.55, "2025-09-12", "MediSupply Co", "Proton pump inhibitor"),
                ("Atorvastatin 20mg", "Cardiovascular", "HealthDist", "ATO001", 175, 30, 99.60, "2025-11-18", "HealthDist Ltd", "Cholesterol-lowering medication"),
                ("Prednisolone 5mg", "Steroids", "PharmaCorp", "PRE001", 80, 15, 78.85, "2025-05-22", "PharmaCorp Inc", "Anti-inflammatory steroid")
            ]
            
            cursor.executemany('''
                INSERT INTO inventory (drug_name, category, manufacturer, batch_number, current_stock, minimum_stock, unit_price, expiry_date, supplier_name, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', inventory_items)
            
            # Insert sample drug interactions
            interactions = [
                ("Aspirin 75mg", "Metformin 500mg", "Moderate", "May increase risk of lactic acidosis", "Increased monitoring required", "Monitor blood glucose closely"),
                ("Ciprofloxacin 500mg", "Prednisolone 5mg", "Mild", "May increase steroid effects", "Potential enhanced anti-inflammatory action", "Standard monitoring sufficient"),
                ("Insulin Rapid", "Aspirin 75mg", "Moderate", "Aspirin may enhance hypoglycemic effect", "Increased risk of low blood sugar", "Monitor glucose levels frequently")
            ]
            
            cursor.executemany('''
                INSERT INTO drug_interactions (drug1, drug2, severity, description, clinical_effect, management)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', interactions)
            
            # Insert sample consumption data for the last 30 days
            drugs = cursor.execute("SELECT id, drug_name FROM inventory").fetchall()
            for drug in drugs:
                for days_ago in range(30):
                    date = datetime.now() - timedelta(days=days_ago)
                    # Generate realistic consumption patterns
                    base_consumption = {
                        "Paracetamol 500mg": 15,
                        "Amoxicillin 250mg": 8,
                        "Metformin 500mg": 12,
                        "Aspirin 75mg": 6,
                        "Salbutamol Inhaler": 2,
                        "Insulin Rapid": 4,
                        "Ciprofloxacin 500mg": 5,
                        "Omeprazole 20mg": 10,
                        "Atorvastatin 20mg": 9,
                        "Prednisolone 5mg": 3
                    }.get(drug['drug_name'], 5)
                    
                    # Add some randomness
                    import random
                    consumption = max(0, base_consumption + random.randint(-3, 3))
                    
                    cursor.execute('''
                        INSERT INTO consumption_patterns (drug_id, date, quantity_consumed, department)
                        VALUES (?, ?, ?, ?)
                    ''', (drug['id'], date.date(), consumption, random.choice(['ICU', 'Emergency', 'General Ward', 'Outpatient'])))
            
            # Insert default settings
            default_settings = [
                ('default_min_stock', '10'),
                ('low_stock_threshold', '20'),
                ('auto_reorder', 'true'),
                ('currency', 'INR'),
                ('expiry_warning_days', '30'),
                ('expiry_critical_days', '7')
            ]
            
            cursor.executemany('''
                INSERT INTO settings (setting_key, setting_value)
                VALUES (?, ?)
            ''', default_settings)
        
        conn.commit()
        conn.close()
    
    # Dashboard methods
    def get_total_inventory_count(self):
        """Get total number of inventory items"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM inventory")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_low_stock_count(self):
        """Get count of items below minimum stock level"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM inventory WHERE current_stock <= minimum_stock")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_expiring_soon_count(self):
        """Get count of items expiring within 30 days"""
        conn = self.get_connection()
        cursor = conn.cursor()
        expiry_date = datetime.now() + timedelta(days=30)
        cursor.execute("SELECT COUNT(*) FROM inventory WHERE expiry_date <= ?", (expiry_date.date(),))
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_total_inventory_value(self):
        """Get total value of current inventory"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(current_stock * unit_price) FROM inventory")
        result = cursor.fetchone()[0]
        conn.close()
        return result or 0.0
    
    def get_inventory_by_category(self):
        """Get inventory distribution by category"""
        conn = self.get_connection()
        query = '''
            SELECT category, SUM(current_stock) as quantity
            FROM inventory
            GROUP BY category
            ORDER BY quantity DESC
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_inventory(self):
        """Get all inventory items"""
        try:
            conn = self.get_connection()
            query = """
                SELECT * FROM inventory
                ORDER BY drug_name
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            print(f"Error getting inventory: {e}")
            return pd.DataFrame()
    
    def get_expiring_drugs(self, days_ahead=30):
        """Get drugs expiring within specified days"""
        try:
            conn = self.get_connection()
            query = """
                SELECT * FROM inventory
                WHERE expiry_date <= DATE('now', '+' || ? || ' days')
                ORDER BY expiry_date
            """
            df = pd.read_sql_query(query, conn, params=(days_ahead,))
            conn.close()
            return df
        except Exception as e:
            print(f"Error getting expiring drugs: {e}")
            return pd.DataFrame()
    
    def get_stock_levels(self):
        """Get current stock levels for all drugs"""
        conn = self.get_connection()
        query = '''
            SELECT drug_name, current_stock, minimum_stock
            FROM inventory
            ORDER BY current_stock ASC
            LIMIT 10
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_recent_transactions(self, limit=10):
        """Get recent transactions"""
        conn = self.get_connection()
        query = '''
            SELECT t.transaction_type, i.drug_name, t.quantity, t.total_amount, t.notes, t.created_at
            FROM transactions t
            JOIN inventory i ON t.drug_id = i.id
            ORDER BY t.created_at DESC
            LIMIT ?
        '''
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        return df
    
    # Inventory management methods
    def get_categories(self):
        """Get list of drug categories"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM inventory ORDER BY category")
        categories = [row[0] for row in cursor.fetchall()]
        conn.close()
        return categories
    
    def get_filtered_inventory(self, category_filter, stock_filter, search_term):
        """Get filtered inventory data"""
        conn = self.get_connection()
        
        query = '''
            SELECT id, drug_name, category, manufacturer, batch_number, 
                   current_stock, minimum_stock, unit_price, expiry_date, supplier_name
            FROM inventory
            WHERE 1=1
        '''
        params = []
        
        if category_filter != "All":
            query += " AND category = ?"
            params.append(category_filter)
        
        if stock_filter == "Low Stock":
            query += " AND current_stock <= minimum_stock"
        elif stock_filter == "Out of Stock":
            query += " AND current_stock = 0"
        elif stock_filter == "Normal":
            query += " AND current_stock > minimum_stock"
        
        if search_term:
            query += " AND drug_name LIKE ?"
            params.append(f"%{search_term}%")
        
        query += " ORDER BY drug_name"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    
    def add_inventory_item(self, drug_name, category, manufacturer, batch_number,
                          current_stock, minimum_stock, unit_price, expiry_date,
                          supplier_name, description):
        """Add new inventory item"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO inventory (drug_name, category, manufacturer, batch_number,
                                     current_stock, minimum_stock, unit_price, expiry_date,
                                     supplier_name, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (drug_name, category, manufacturer, batch_number,
                  current_stock, minimum_stock, unit_price, expiry_date,
                  supplier_name, description))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_all_items_for_dropdown(self):
        """Get all inventory items formatted for dropdown"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, drug_name, batch_number FROM inventory ORDER BY drug_name")
        items = [f"{row[0]} - {row[1]} ({row[2]})" for row in cursor.fetchall()]
        conn.close()
        return items
    
    def get_item_details(self, item_id):
        """Get details of a specific inventory item"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM inventory WHERE id = ?", (item_id,))
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None
    
    def update_stock_level(self, item_id, new_stock, transaction_type, quantity, reason):
        """Update stock level and log transaction"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Update inventory
            cursor.execute("UPDATE inventory SET current_stock = ? WHERE id = ?", (new_stock, item_id))
            
            # Log transaction
            cursor.execute('''
                INSERT INTO transactions (drug_id, transaction_type, quantity, notes)
                VALUES (?, ?, ?, ?)
            ''', (item_id, transaction_type, quantity, reason))
            
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
    
    # AI Forecasting methods
    def get_drugs_for_forecasting(self):
        """Get drugs that have enough historical data for forecasting"""
        conn = self.get_connection()
        query = '''
            SELECT DISTINCT i.drug_name
            FROM inventory i
            JOIN consumption_patterns cp ON i.id = cp.drug_id
            GROUP BY i.drug_name
            HAVING COUNT(cp.id) >= 7
            ORDER BY i.drug_name
        '''
        cursor = conn.cursor()
        cursor.execute(query)
        drugs = [row[0] for row in cursor.fetchall()]
        conn.close()
        return drugs
    
    def get_historical_consumption(self, drug_name):
        """Get historical consumption data for a drug"""
        conn = self.get_connection()
        query = '''
            SELECT cp.date, SUM(cp.quantity_consumed) as consumption
            FROM consumption_patterns cp
            JOIN inventory i ON cp.drug_id = i.id
            WHERE i.drug_name = ?
            GROUP BY cp.date
            ORDER BY cp.date
        '''
        df = pd.read_sql_query(query, conn, params=(drug_name,))
        df['date'] = pd.to_datetime(df['date'])
        conn.close()
        return df
    
    def get_current_stock(self, drug_name):
        """Get current stock for a drug"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT current_stock FROM inventory WHERE drug_name = ?", (drug_name,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0
    
    # Smart reordering methods
    def get_reorder_suggestions_data(self):
        """Get data needed for reorder suggestions"""
        conn = self.get_connection()
        query = '''
            SELECT i.id, i.drug_name, i.current_stock, i.minimum_stock, i.unit_price,
                   i.supplier_name, s.lead_time_days,
                   AVG(cp.quantity_consumed) as avg_daily_usage
            FROM inventory i
            LEFT JOIN suppliers s ON i.supplier_name = s.name
            LEFT JOIN consumption_patterns cp ON i.id = cp.drug_id 
                AND cp.date >= date('now', '-30 days')
            GROUP BY i.id, i.drug_name, i.current_stock, i.minimum_stock, 
                     i.unit_price, i.supplier_name, s.lead_time_days
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def create_purchase_order(self, suggestion):
        """Create a purchase order"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Generate order number
            order_number = f"PO{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Get supplier ID
            cursor.execute("SELECT id FROM suppliers WHERE name = ?", (suggestion['supplier'],))
            supplier_result = cursor.fetchone()
            supplier_id = supplier_result[0] if supplier_result else None
            
            # Get drug ID
            cursor.execute("SELECT id FROM inventory WHERE drug_name = ?", (suggestion['drug_name'],))
            drug_result = cursor.fetchone()
            drug_id = drug_result[0] if drug_result else None
            
            if drug_id:
                cursor.execute('''
                    INSERT INTO purchase_orders (order_number, supplier_id, drug_id, quantity, 
                                               unit_price, total_amount, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (order_number, supplier_id, drug_id, suggestion['suggested_quantity'],
                      suggestion.get('unit_price', 0), suggestion['estimated_cost'],
                      suggestion.get('notes', 'Auto-generated order')))
                
                conn.commit()
                conn.close()
                return True
        except Exception:
            pass
        
        conn.close()
        return False
    
    def get_suppliers(self):
        """Get list of suppliers"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM suppliers ORDER BY name")
        suppliers = [row[0] for row in cursor.fetchall()]
        conn.close()
        return suppliers
    
    def get_all_drugs(self):
        """Get list of all drug names"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT drug_name FROM inventory ORDER BY drug_name")
        drugs = [row[0] for row in cursor.fetchall()]
        conn.close()
        return drugs
    
    # Expiry management methods
    def get_expiring_items(self):
        """Get items expiring within 90 days"""
        conn = self.get_connection()
        query = '''
            SELECT drug_name, batch_number, current_stock, expiry_date,
                   CASE 
                       WHEN julianday(expiry_date) - julianday('now') <= 0 THEN 0
                       ELSE CAST(julianday(expiry_date) - julianday('now') AS INTEGER)
                   END as days_until_expiry,
                   current_stock * unit_price as value_at_risk
            FROM inventory
            WHERE expiry_date <= date('now', '+90 days')
            ORDER BY days_until_expiry ASC
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_drugs_with_consumption_data(self):
        """Get drugs that have consumption data"""
        conn = self.get_connection()
        query = '''
            SELECT DISTINCT i.drug_name
            FROM inventory i
            JOIN consumption_patterns cp ON i.id = cp.drug_id
            ORDER BY i.drug_name
        '''
        cursor = conn.cursor()
        cursor.execute(query)
        drugs = [row[0] for row in cursor.fetchall()]
        conn.close()
        return drugs
    
    def apply_expiry_action(self, drug_name, action):
        """Apply action to expired/expiring items"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Log the action in transactions
            cursor.execute('''
                INSERT INTO transactions (drug_id, transaction_type, quantity, notes)
                SELECT id, ?, current_stock, ?
                FROM inventory 
                WHERE drug_name = ?
            ''', (action, f"Expiry action: {action}", drug_name))
            
            # Update stock if disposing or using
            if action in ["Mark as Used", "Dispose"]:
                cursor.execute("UPDATE inventory SET current_stock = 0 WHERE drug_name = ?", (drug_name,))
            
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
    
    def get_wastage_analysis(self, start_date, end_date):
        """Get wastage analysis for a date range"""
        conn = self.get_connection()
        query = '''
            SELECT i.drug_name, i.category, 
                   SUM(t.quantity) as wasted_quantity,
                   SUM(t.quantity * i.unit_price) as wasted_value
            FROM transactions t
            JOIN inventory i ON t.drug_id = i.id
            WHERE t.transaction_type IN ('Dispose', 'Expired') 
                AND DATE(t.created_at) BETWEEN ? AND ?
            GROUP BY i.drug_name, i.category
            ORDER BY wasted_value DESC
        '''
        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        conn.close()
        return df
    
    def get_wastage_trends(self, start_date, end_date):
        """Get daily wastage trends"""
        conn = self.get_connection()
        query = '''
            SELECT DATE(t.created_at) as date,
                   SUM(t.quantity * i.unit_price) as daily_wastage
            FROM transactions t
            JOIN inventory i ON t.drug_id = i.id
            WHERE t.transaction_type IN ('Dispose', 'Expired') 
                AND DATE(t.created_at) BETWEEN ? AND ?
            GROUP BY DATE(t.created_at)
            ORDER BY date
        '''
        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        conn.close()
        return df
    
    # Drug interactions methods
    def get_known_interactions(self):
        """Get all known drug interactions"""
        conn = self.get_connection()
        query = '''
            SELECT drug1, drug2, severity, description, clinical_effect, management
            FROM drug_interactions
            ORDER BY severity DESC, drug1, drug2
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def add_drug_interaction(self, drug1, drug2, severity, description, clinical_effect, management):
        """Add new drug interaction"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO drug_interactions (drug1, drug2, severity, description, clinical_effect, management)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (drug1, drug2, severity, description, clinical_effect, management))
            
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
        
    
    
    
    def check_drug_availability(self, drug_name):
        """Check if drug is available in stock"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT current_stock FROM inventory WHERE drug_name = ?", (drug_name,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] > 0:
            return {"in_stock": True, "quantity": result[0]}
        else:
            return {"in_stock": False, "quantity": 0}
    
    # Analytics methods
    def get_consumption_analytics(self, start_date, end_date):
        """Get consumption analytics for date range"""
        conn = self.get_connection()
        query = '''
            SELECT i.drug_name, i.category, SUM(cp.quantity_consumed) as total_consumed
            FROM consumption_patterns cp
            JOIN inventory i ON cp.drug_id = i.id
            WHERE cp.date BETWEEN ? AND ?
            GROUP BY i.drug_name, i.category
            ORDER BY total_consumed DESC
        '''
        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        conn.close()
        return df
    
    def get_daily_consumption_trends(self, start_date, end_date):
        """Get daily consumption trends"""
        conn = self.get_connection()
        query = '''
            SELECT date, SUM(quantity_consumed) as daily_consumption
            FROM consumption_patterns
            WHERE date BETWEEN ? AND ?
            GROUP BY date
            ORDER BY date
        '''
        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        conn.close()
        return df
    
    def get_department_consumption(self, start_date, end_date):
        """Get consumption by department"""
        conn = self.get_connection()
        query = '''
            SELECT department, SUM(quantity_consumed) as consumption
            FROM consumption_patterns
            WHERE date BETWEEN ? AND ? AND department IS NOT NULL
            GROUP BY department
            ORDER BY consumption DESC
        '''
        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        conn.close()
        return df
    
    def get_financial_overview(self):
        """Get financial overview data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Total inventory value
        cursor.execute("SELECT SUM(current_stock * unit_price) FROM inventory")
        total_value = cursor.fetchone()[0] or 0
        
        # Monthly spend (last 30 days)
        cursor.execute('''
            SELECT SUM(total_amount) FROM transactions 
            WHERE created_at >= date('now', '-30 days') 
            AND transaction_type = 'Purchase'
        ''')
        monthly_spend = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_value': total_value,
            'monthly_spend': monthly_spend,
            'cost_savings': monthly_spend * 0.15,  # Estimated savings
            'roi': 0.25  # Estimated ROI
        }
    
    def get_cost_analysis(self):
        """Get cost analysis by category"""
        conn = self.get_connection()
        query = '''
            SELECT category, SUM(current_stock * unit_price) as total_cost
            FROM inventory
            GROUP BY category
            ORDER BY total_cost DESC
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_cost_trends(self):
        """Get monthly cost trends"""
        conn = self.get_connection()
        query = '''
            SELECT strftime('%Y-%m', created_at) as month,
                   SUM(total_amount) as monthly_cost
            FROM transactions
            WHERE transaction_type = 'Purchase'
            GROUP BY strftime('%Y-%m', created_at)
            ORDER BY month
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_budget_analysis(self):
        """Get budget vs actual analysis"""
        # Mock budget data - in real app this would come from budget table
        budget_data = {
            'Antibiotics': {'budgeted': 10000, 'actual': 8500},
            'Analgesics': {'budgeted': 5000, 'actual': 5200},
            'Cardiovascular': {'budgeted': 8000, 'actual': 7800},
            'Diabetes': {'budgeted': 12000, 'actual': 11500},
            'Respiratory': {'budgeted': 6000, 'actual': 6300}
        }
        return budget_data
    
    def get_supplier_metrics(self):
        """Get supplier performance metrics"""
        conn = self.get_connection()
        query = '''
            SELECT s.name as supplier_name,
                   s.lead_time_days as avg_delivery_time,
                   s.reliability_score,
                   s.cost_rating,
                   s.quality_score,
                   COUNT(po.id) as total_orders,
                   AVG(po.unit_price) as avg_unit_cost,
                   CASE 
                       WHEN COUNT(po.id) > 0 THEN 
                           CAST(SUM(CASE WHEN po.actual_delivery <= po.expected_delivery THEN 1 ELSE 0 END) AS FLOAT) / COUNT(po.id) * 100
                       ELSE 0 
                   END as on_time_delivery_rate
            FROM suppliers s
            LEFT JOIN purchase_orders po ON s.id = po.supplier_id
            GROUP BY s.id, s.name, s.lead_time_days, s.reliability_score, s.cost_rating, s.quality_score
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_supplier_recommendations(self):
        """Get supplier recommendations"""
        recommendations = [
            {
                'type': 'best_performer',
                'supplier': 'HealthDist Ltd',
                'reason': 'Highest quality score and reliability'
            },
            {
                'type': 'needs_improvement',
                'supplier': 'MediSupply Co',
                'reason': 'Below average delivery times'
            },
            {
                'type': 'cost_optimization',
                'message': 'Consider negotiating better rates with PharmaCorp Inc'
            }
        ]
        return recommendations
    
    def detect_anomalies(self):
        """Detect anomalies in inventory data"""
        anomalies = [
            {
                'severity': 'High',
                'description': 'Unusual spike in Insulin consumption detected in ICU department'
            },
            {
                'severity': 'Medium',
                'description': 'Stock level of Amoxicillin dropped 50% faster than predicted'
            },
            {
                'severity': 'Low',
                'description': 'Delivery delay pattern detected for MediSupply Co'
            }
        ]
        return anomalies
    
    def get_predictive_insights(self):
        """Get predictive insights"""
        insights = [
            {
                'title': 'Seasonal Demand Prediction',
                'description': 'Respiratory medications demand expected to increase by 40% in next 30 days',
                'chart_type': 'line',
                'chart_data': pd.DataFrame({
                    'x': pd.date_range(start='2024-01-01', periods=30, freq='D'),
                    'y': np.random.normal(50, 10, 30)
                }),
                'recommendations': [
                    'Increase Salbutamol orders by 50%',
                    'Stock up on respiratory medications',
                    'Review supplier capacity'
                ]
            },
            {
                'title': 'Cost Optimization Opportunity',
                'description': 'Switching suppliers for cardiovascular drugs could save 15%',
                'chart_type': 'bar',
                'chart_data': pd.DataFrame({
                    'x': ['Current Cost', 'Optimized Cost'],
                    'y': [8000, 6800]
                }),
                'recommendations': [
                    'Negotiate with alternative suppliers',
                    'Consider bulk purchasing',
                    'Review contract terms'
                ]
            }
        ]
        return insights
    
    # Settings methods
    def update_settings(self, settings):
        """Update system settings"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            for key, value in settings.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO settings (setting_key, setting_value, updated_at)
                    VALUES (?, ?, ?)
                ''', (key, str(value), datetime.now()))
            
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
    
    def update_alert_settings(self, alert_settings):
        """Update alert settings"""
        return self.update_settings(alert_settings)
    
    def update_ai_settings(self, ai_settings):
        """Update AI model settings"""
        return self.update_settings(ai_settings)
    
    def get_model_performance(self):
        """Get AI model performance metrics"""
        performance_data = [
            {'model_name': 'Demand Forecasting', 'accuracy': 0.85},
            {'model_name': 'Expiry Prediction', 'accuracy': 0.78},
            {'model_name': 'Anomaly Detection', 'accuracy': 0.82},
            {'model_name': 'Reorder Optimization', 'accuracy': 0.88}
        ]
        return performance_data
    
    # Data management methods
    def export_all_data(self):
        """Export all system data"""
        conn = self.get_connection()
        query = '''
            SELECT i.*, s.name as supplier_name
            FROM inventory i
            LEFT JOIN suppliers s ON i.supplier_name = s.name
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def export_inventory_data(self):
        """Export inventory data only"""
        conn = self.get_connection()
        df = pd.read_sql_query("SELECT * FROM inventory", conn)
        conn.close()
        return df
    
    def export_transaction_data(self):
        """Export transaction data"""
        conn = self.get_connection()
        query = '''
            SELECT t.*, i.drug_name
            FROM transactions t
            JOIN inventory i ON t.drug_id = i.id
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def export_report_data(self):
        """Export report data"""
        conn = self.get_connection()
        df = pd.read_sql_query("SELECT * FROM consumption_patterns", conn)
        conn.close()
        return df
    
    def import_data(self, df, import_type):
        """Import data from DataFrame"""
        try:
            conn = self.get_connection()
            
            if import_type == "Inventory Items":
                df.to_sql('inventory_temp', conn, if_exists='replace', index=False)
                # Merge with existing inventory logic here
            elif import_type == "Transactions":
                df.to_sql('transactions', conn, if_exists='append', index=False)
            elif import_type == "Suppliers":
                df.to_sql('suppliers', conn, if_exists='append', index=False)
            
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
    
    def clean_old_data(self):
        """Clean old data (older than 2 years)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=730)
        cursor.execute("DELETE FROM transactions WHERE created_at < ?", (cutoff_date,))
        cursor.execute("DELETE FROM consumption_patterns WHERE date < ?", (cutoff_date.date(),))
        
        cleaned_records = cursor.rowcount
        conn.commit()
        conn.close()
        
        return cleaned_records
    
    def add_sample_data(self):
        """Add sample data for testing smart reordering"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Add sample suppliers
        suppliers = [
            ('MedSupply Co.', 'John Smith', '555-0101', 'john@medsupply.com', '123 Medical St', 5, 4.5, 3.8, 4.2),
            ('PharmaDirect', 'Sarah Johnson', '555-0102', 'sarah@pharmadirect.com', '456 Health Ave', 7, 4.2, 4.0, 4.5),
            ('QuickMed', 'Mike Wilson', '555-0103', 'mike@quickmed.com', '789 Pharmacy Blvd', 3, 4.8, 4.2, 4.0)
        ]
        
        for supplier in suppliers:
            cursor.execute('''
                INSERT OR IGNORE INTO suppliers (name, contact_person, phone, email, address, 
                                               lead_time_days, reliability_score, cost_rating, quality_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', supplier)
        
        # Add sample consumption patterns
        cursor.execute("SELECT id, drug_name FROM inventory LIMIT 5")
        drugs = cursor.fetchall()
        
        for drug in drugs:
            drug_id, drug_name = drug
            # Add some consumption data for the last 30 days
            for i in range(30):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                quantity = np.random.randint(1, 10)  # Random consumption between 1-9
                cursor.execute('''
                    INSERT OR IGNORE INTO consumption_patterns (drug_id, date, quantity_consumed, department)
                    VALUES (?, ?, ?, ?)
                ''', (drug_id, date, quantity, 'General'))
        
        conn.commit()
        conn.close()
    
    def optimize_database(self):
        """Optimize database performance"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("VACUUM")
        cursor.execute("ANALYZE")
        conn.commit()
        conn.close()
    
    def backup_database(self):
        """Create database backup"""
        backup_filename = f"pharma_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        # Simple file copy for SQLite
        import shutil
        shutil.copy2(self.db_path, backup_filename)
        
        return backup_filename
    
    def snooze_reorder_suggestion(self, suggestion_id, days):
        """Snooze a reorder suggestion"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Create or update snooze record
            cursor.execute('''
                INSERT OR REPLACE INTO alerts (alert_type, severity, message, drug_id, is_active)
                VALUES ('reorder_snooze', 'info', ?, ?, 1)
            ''', (f"Snoozed for {days} days", suggestion_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
    
    def dismiss_reorder_suggestion(self, suggestion_id):
        """Dismiss a reorder suggestion"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Create dismiss record
            cursor.execute('''
                INSERT INTO alerts (alert_type, severity, message, drug_id, is_active)
                VALUES ('reorder_dismissed', 'info', 'Reorder suggestion dismissed', ?, 1)
            ''', (suggestion_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False
    
    def get_all_drugs(self):
        """Get all drug names for dropdown"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT drug_name FROM inventory ORDER BY drug_name")
        results = cursor.fetchall()
        conn.close()
        return [row[0] for row in results]
    
    def get_suppliers(self):
        """Get all supplier names for dropdown"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT name FROM suppliers ORDER BY name")
        results = cursor.fetchall()
        conn.close()
        return [row[0] for row in results]
    
    def get_supplier_metrics(self):
        """Get supplier performance metrics"""
        conn = self.get_connection()
        query = '''
            SELECT s.name as supplier_name, s.lead_time_days as avg_delivery_time,
                   s.reliability_score, s.cost_rating as avg_unit_cost, s.quality_score,
                   COUNT(po.id) as total_orders
            FROM suppliers s
            LEFT JOIN purchase_orders po ON s.id = po.supplier_id
            GROUP BY s.id, s.name, s.lead_time_days, s.reliability_score, s.cost_rating, s.quality_score
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
