import streamlit as st
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import pandas as pd

# Check if pytesseract is available
try:
    import pytesseract
    # Set the Tesseract executable path explicitly
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

# Check if OpenAI is available for intelligent parsing
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class ReceiptScanner:
    def __init__(self):
        self.openai_client = None
        if OPENAI_AVAILABLE and os.environ.get("OPENAI_API_KEY"):
            self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results using PIL only"""
        try:
            # Convert to grayscale
            gray_image = image.convert('L')
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(gray_image)
            enhanced = enhancer.enhance(1.5)
            
            # Enhance sharpness
            sharpness_enhancer = ImageEnhance.Sharpness(enhanced)
            sharpened = sharpness_enhancer.enhance(2.0)
            
            # Apply a slight blur to reduce noise, then sharpen
            blurred = sharpened.filter(ImageFilter.MedianFilter(size=3))
            
            return blurred
            
        except Exception as e:
            st.warning(f"Image preprocessing failed: {str(e)}, using original image")
            return image.convert('L')
    
    def extract_text_from_image(self, image: Image.Image) -> str:
        """Extract text from image using OCR"""
        if not TESSERACT_AVAILABLE:
            st.error("Tesseract OCR is not available. Please install pytesseract package.")
            return ""
            
        try:
            # Preprocess image
            processed_image = self.preprocess_image(image)
            
            # Configure tesseract for better results
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,/-:()$ '
            
            # Extract text
            text = pytesseract.image_to_string(processed_image, config=custom_config)
            
            return text.strip()
        except Exception as e:
            st.error(f"Error extracting text: {str(e)}")
            return ""
    
    def parse_receipt_with_ai(self, receipt_text: str) -> Optional[Dict]:
        """Parse receipt text using OpenAI to extract structured data"""
        if not self.openai_client:
            return self.parse_receipt_manually(receipt_text)
        
        try:
            prompt = f"""
            Parse the following pharmaceutical receipt and extract structured data. 
            Extract drug information including names, quantities, prices, batch numbers, expiry dates, and supplier information.
            
            Receipt text:
            {receipt_text}
            
            Please respond with a JSON object in this exact format:
            {{
                "supplier_name": "supplier name if found",
                "receipt_date": "date in YYYY-MM-DD format if found",
                "receipt_number": "receipt/invoice number if found",
                "items": [
                    {{
                        "drug_name": "drug name",
                        "quantity": number,
                        "unit_price": number,
                        "total_price": number,
                        "batch_number": "batch number if found",
                        "expiry_date": "expiry date in YYYY-MM-DD format if found",
                        "manufacturer": "manufacturer if found",
                        "category": "best guess category (Antibiotics, Analgesics, etc.)"
                    }}
                ],
                "total_amount": number,
                "confidence": number between 0-1
            }}
            
            If you cannot find certain information, use null for strings and 0 for numbers.
            """
            
            # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
            # do not change this unless explicitly requested by the user
            response = self.openai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": "You are a pharmaceutical receipt parser. Extract structured data accurately from receipt text."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            parsed_data = json.loads(response.choices[0].message.content)
            return parsed_data
            
        except Exception as e:
            st.warning(f"AI parsing failed: {str(e)}. Falling back to manual parsing.")
            return self.parse_receipt_manually(receipt_text)
    
    def parse_receipt_manually(self, receipt_text: str) -> Dict:
        """Manual parsing of receipt text using regex patterns"""
        lines = receipt_text.split('\n')
        
        parsed_data = {
            "supplier_name": self.extract_supplier_name(lines),
            "receipt_date": self.extract_date(receipt_text),
            "receipt_number": self.extract_receipt_number(receipt_text),
            "items": self.extract_items(lines),
            "total_amount": self.extract_total_amount(receipt_text),
            "confidence": 0.6  # Lower confidence for manual parsing
        }
        
        return parsed_data
    
    def extract_supplier_name(self, lines: List[str]) -> Optional[str]:
        """Extract supplier name from receipt lines"""
        # Look for common supplier patterns in first few lines
        for line in lines[:5]:
            line = line.strip()
            if len(line) > 5 and any(keyword in line.lower() for keyword in 
                                   ['pharmacy', 'pharmaceutical', 'medical', 'health', 'pharma']):
                return line
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """Extract date from receipt text"""
        # Common date patterns
        date_patterns = [
            r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b',
            r'\b(\d{2,4}[-/]\d{1,2}[-/]\d{1,2})\b',
            r'\b(\d{1,2}\s+\w+\s+\d{2,4})\b'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    date_str = matches[0]
                    # Try to parse and standardize date
                    for fmt in ['%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d', '%d-%m-%Y']:
                        try:
                            parsed_date = datetime.strptime(date_str, fmt)
                            return parsed_date.strftime('%Y-%m-%d')
                        except ValueError:
                            continue
                except:
                    continue
        return None
    
    def extract_receipt_number(self, text: str) -> Optional[str]:
        """Extract receipt/invoice number"""
        patterns = [
            r'(?:receipt|invoice|bill)?\s*#?\s*([A-Z0-9\-]+)',
            r'(?:no|number)\.?\s*:?\s*([A-Z0-9\-]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        return None
    
    def extract_items(self, lines: List[str]) -> List[Dict]:
        """Extract drug items from receipt lines"""
        items = []
        
        # Look for lines that might contain drug information
        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:
                continue
            
            # Skip header lines
            if any(keyword in line.lower() for keyword in 
                   ['receipt', 'invoice', 'total', 'subtotal', 'tax', 'thank you']):
                continue
            
            # Try to extract item information using patterns
            item = self.parse_item_line(line)
            if item:
                items.append(item)
        
        return items
    
    def parse_item_line(self, line: str) -> Optional[Dict]:
        """Parse individual item line"""
        # Common patterns for pharmaceutical items
        # Pattern: drug_name quantity price
        patterns = [
            r'([A-Za-z][A-Za-z\s]+[A-Za-z])\s+(\d+)\s+[\$]?(\d+\.?\d*)',
            r'([A-Za-z][A-Za-z\s]+[A-Za-z])\s+(\d+)\s+.*?(\d+\.?\d*)$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                drug_name = match.group(1).strip()
                quantity = int(match.group(2))
                price = float(match.group(3))
                
                # Skip if drug name is too short or generic
                if len(drug_name) < 3:
                    continue
                
                return {
                    "drug_name": self.clean_drug_name(drug_name),
                    "quantity": quantity,
                    "unit_price": price / quantity if quantity > 0 else price,
                    "total_price": price,
                    "batch_number": self.extract_batch_from_line(line),
                    "expiry_date": self.extract_expiry_from_line(line),
                    "manufacturer": None,
                    "category": self.guess_category(drug_name)
                }
        
        return None
    
    def clean_drug_name(self, name: str) -> str:
        """Clean and standardize drug name"""
        # Remove extra spaces and capitalize properly
        name = ' '.join(name.split())
        return name.title()
    
    def extract_batch_from_line(self, line: str) -> Optional[str]:
        """Extract batch number from line"""
        batch_patterns = [
            r'(?:batch|lot|b#|l#)\s*:?\s*([A-Z0-9]+)',
            r'\b([A-Z]{2,3}\d{3,6})\b'
        ]
        
        for pattern in batch_patterns:
            matches = re.findall(pattern, line, re.IGNORECASE)
            if matches:
                return matches[0]
        return None
    
    def extract_expiry_from_line(self, line: str) -> Optional[str]:
        """Extract expiry date from line"""
        expiry_patterns = [
            r'(?:exp|expiry|expires?)\s*:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'(?:exp|expiry|expires?)\s*:?\s*(\d{2,4}[-/]\d{1,2}[-/]\d{1,2})'
        ]
        
        for pattern in expiry_patterns:
            matches = re.findall(pattern, line, re.IGNORECASE)
            if matches:
                try:
                    date_str = matches[0]
                    for fmt in ['%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d']:
                        try:
                            parsed_date = datetime.strptime(date_str, fmt)
                            return parsed_date.strftime('%Y-%m-%d')
                        except ValueError:
                            continue
                except:
                    continue
        return None
    
    def guess_category(self, drug_name: str) -> str:
        """Guess drug category based on name"""
        name_lower = drug_name.lower()
        
        category_keywords = {
            'Antibiotics': ['amoxicillin', 'ciprofloxacin', 'azithromycin', 'penicillin', 'cephalexin'],
            'Analgesics': ['paracetamol', 'acetaminophen', 'ibuprofen', 'aspirin', 'diclofenac', 'tramadol'],
            'Cardiovascular': ['atenolol', 'lisinopril', 'amlodipine', 'metoprolol', 'atorvastatin'],
            'Diabetes': ['metformin', 'insulin', 'glipizide', 'glyburide', 'glimepiride'],
            'Respiratory': ['salbutamol', 'ventolin', 'prednisolone', 'budesonide', 'montelukast']
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in name_lower for keyword in keywords):
                return category
        
        return 'Other'
    
    def extract_total_amount(self, text: str) -> float:
        """Extract total amount from receipt"""
        total_patterns = [
            r'(?:total|grand\s+total)\s*:?\s*\$?(\d+\.?\d*)',
            r'(?:amount|sum)\s*:?\s*\$?(\d+\.?\d*)'
        ]
        
        for pattern in total_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    return float(matches[-1])  # Take the last match (usually the final total)
                except ValueError:
                    continue
        
        return 0.0
    
    def validate_parsed_data(self, data: Dict) -> Dict:
        """Validate and clean parsed data"""
        if not data.get('items'):
            return data
        
        validated_items = []
        for item in data['items']:
            # Validate required fields
            if not item.get('drug_name') or item.get('quantity', 0) <= 0:
                continue
            
            # Set defaults for missing fields
            if not item.get('unit_price'):
                item['unit_price'] = item.get('total_price', 0) / max(item.get('quantity', 1), 1)
            
            if not item.get('category'):
                item['category'] = 'Other'
            
            # Generate batch number if missing
            if not item.get('batch_number'):
                item['batch_number'] = f"RCP{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Set default expiry date if missing (1 year from now)
            if not item.get('expiry_date'):
                future_date = datetime.now() + timedelta(days=365)
                item['expiry_date'] = future_date.strftime('%Y-%m-%d')
            
            validated_items.append(item)
        
        data['items'] = validated_items
        return data
    
    def save_to_database(self, db, parsed_data: Dict) -> tuple:
        """Save parsed receipt data to database"""
        if not parsed_data.get('items'):
            return False, "No items found in receipt"
        
        success_count = 0
        error_count = 0
        errors = []
        
        for item in parsed_data['items']:
            try:
                success = db.add_inventory_item(
                    drug_name=item['drug_name'],
                    category=item.get('category', 'Other'),
                    manufacturer=item.get('manufacturer', parsed_data.get('supplier_name', '')),
                    batch_number=item['batch_number'],
                    current_stock=item['quantity'],
                    minimum_stock=max(10, item['quantity'] // 4),  # Set min stock as 25% of current
                    unit_price=item['unit_price'],
                    expiry_date=item['expiry_date'],
                    supplier_name=parsed_data.get('supplier_name', 'Receipt Import'),
                    description=f"Imported from receipt on {datetime.now().strftime('%Y-%m-%d')}"
                )
                
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    errors.append(f"Failed to add {item['drug_name']} - batch number may already exist")
                    
            except Exception as e:
                error_count += 1
                errors.append(f"Error adding {item['drug_name']}: {str(e)}")
        
        return success_count, error_count, errors

def render_receipt_scanner_page(db):
    """Render the receipt scanner page"""
    st.title("📷 Receipt Scanner")
    st.write("Upload pharmaceutical receipts to automatically extract and import inventory data.")
    
    scanner = ReceiptScanner()
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload Receipt Image", 
        type=['png', 'jpg', 'jpeg', 'tiff', 'bmp'],
        help="Upload a clear image of your pharmaceutical receipt"
    )
    
    if uploaded_file is not None:
        # Display uploaded image
        image = Image.open(uploaded_file)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📸 Uploaded Receipt")
            st.image(image, caption="Receipt Image", width=400)
        
        with col2:
            st.subheader("⚙️ Processing Options")
            
            # Processing options
            use_ai_parsing = st.checkbox(
                "Use AI Parsing", 
                value=scanner.openai_client is not None,
                help="Use AI for better text extraction and parsing",
                disabled=scanner.openai_client is None
            )
            
            if scanner.openai_client is None and use_ai_parsing:
                st.warning("OpenAI API key not found. Using manual parsing.")
            
            # Process button
            if st.button("🔍 Scan Receipt"):
                with st.spinner("Extracting text from receipt..."):
                    # Extract text using OCR
                    extracted_text = scanner.extract_text_from_image(image)
                
                if extracted_text:
                    st.subheader("📝 Extracted Text")
                    with st.expander("View Raw OCR Text"):
                        st.text_area("OCR Output", extracted_text, height=200, disabled=True)
                    
                    with st.spinner("Parsing receipt data..."):
                        # Parse the extracted text
                        if use_ai_parsing and scanner.openai_client:
                            parsed_data = scanner.parse_receipt_with_ai(extracted_text)
                        else:
                            parsed_data = scanner.parse_receipt_manually(extracted_text)
                    
                    if parsed_data:
                        # Validate data
                        parsed_data = scanner.validate_parsed_data(parsed_data)
                        
                        st.subheader("📊 Parsed Receipt Data")
                        
                        # Display receipt summary
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Supplier", parsed_data.get('supplier_name', 'Unknown'))
                        with col2:
                            st.metric("Date", parsed_data.get('receipt_date', 'Unknown'))
                        with col3:
                            st.metric("Total Amount", f"₹{parsed_data.get('total_amount', 0):.2f}")
                        
                        # Display items
                        if parsed_data.get('items'):
                            st.subheader("🧾 Extracted Items")
                            
                            # Create DataFrame for better display
                            items_df = pd.DataFrame(parsed_data['items'])
                            st.dataframe(items_df, use_container_width=True)
                            
                            # Confidence indicator
                            confidence = parsed_data.get('confidence', 0.5)
                            if confidence >= 0.8:
                                st.success(f"High confidence: {confidence:.1%}")
                            elif confidence >= 0.6:
                                st.warning(f"Medium confidence: {confidence:.1%}")
                            else:
                                st.error(f"Low confidence: {confidence:.1%}")
                            
                            # Save to database
                            st.subheader("💾 Import to Database")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("📥 Import All Items"):
                                    with st.spinner("Importing items to database..."):
                                        success_count, error_count, errors = scanner.save_to_database(db, parsed_data)
                                    
                                    if success_count > 0:
                                        st.success(f"Successfully imported {success_count} items!")
                                    
                                    if error_count > 0:
                                        st.warning(f"{error_count} items failed to import:")
                                        for error in errors:
                                            st.write(f"• {error}")
                            
                            with col2:
                                # Allow manual editing before import
                                if st.button("✏️ Edit Before Import"):
                                    st.info("Manual editing feature coming soon!")
                        
                        else:
                            st.warning("No items could be extracted from the receipt. Try with a clearer image.")
                    
                    else:
                        st.error("Failed to parse receipt data. Please try with a clearer image.")
                
                else:
                    st.error("Could not extract text from image. Please ensure the image is clear and readable.")
    
    # Tips for better scanning
    with st.expander("💡 Tips for Better Scanning Results"):
        st.write("""
        **For best results:**
        - Ensure good lighting when taking photos
        - Keep the receipt flat and straight
        - Make sure all text is clearly visible
        - Avoid shadows and glare
        - Use high resolution images
        - Include the entire receipt in the frame
        
        **Supported receipt formats:**
        - Standard pharmacy receipts
        - Pharmaceutical supplier invoices
        - Medical supply purchase orders
        - Drug procurement receipts
        """)
    
    # Recent scans
    st.subheader("📋 Recent Imports")
    recent_imports = db.get_recent_transactions(limit=10)
    if not recent_imports.empty:
        # Filter for receipt imports
        receipt_imports = recent_imports[
            recent_imports['notes'].str.contains('receipt', case=False, na=False) |
            recent_imports['notes'].str.contains('import', case=False, na=False)
        ]
        
        if not receipt_imports.empty:
            st.dataframe(receipt_imports, use_container_width=True)
        else:
            st.info("No recent receipt imports found.")
    else:
        st.info("No recent transactions found.")