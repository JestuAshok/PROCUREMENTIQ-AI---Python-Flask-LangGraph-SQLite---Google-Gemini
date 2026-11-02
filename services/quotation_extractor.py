"""
Document Extraction Service for PROCUREMENTIQ AI
Extracts structured procurement and quotation data from PDF, XLSX, and CSV documents
using PyMuPDF (fitz), openpyxl, and csv/regex heuristics.
"""

import os
import re
import csv
from datetime import datetime
from pathlib import Path
import openpyxl

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDIF = True
except ImportError:
    HAS_PYMUPDIF = False

def extract_quotation_data(file_path, original_filename=""):
    """
    Parses an uploaded quotation document (PDF, XLSX, CSV).
    Returns a normalized dictionary with extraction confidence and missing fields.
    """
    path = Path(file_path)
    ext = path.suffix.lower().strip('.')
    
    if ext == 'pdf':
        return _extract_from_pdf(file_path, original_filename or path.name)
    elif ext in ('xlsx', 'xls'):
        return _extract_from_xlsx(file_path, original_filename or path.name)
    elif ext == 'csv':
        return _extract_from_csv(file_path, original_filename or path.name)
    else:
        return {
            "error": f"Unsupported file extension: .{ext}",
            "supplier_name": "Not provided",
            "extraction_confidence": 0.0,
            "missing_fields": ["All fields"]
        }

def _extract_from_pdf(file_path, filename):
    text = ""
    if HAS_PYMUPDIF:
        try:
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
        except Exception as e:
            text = f"Error reading PDF: {e}"
            
    return _parse_raw_quotation_text(text, filename)

def _extract_from_xlsx(file_path, filename):
    text_lines = []
    data_grid = []
    try:
        wb = openpyxl.load_workbook(file_path, data_only=True)
        sheet = wb.active
        for row in sheet.iter_rows(values_only=True):
            row_vals = [str(v).strip() for v in row if v is not None]
            if row_vals:
                text_lines.append(" | ".join(row_vals))
                data_grid.append(row_vals)
        wb.close()
    except Exception as e:
        text_lines.append(f"Error parsing XLSX: {e}")
        
    full_text = "\n".join(text_lines)
    res = _parse_raw_quotation_text(full_text, filename)
    return res

def _extract_from_csv(file_path, filename):
    text_lines = []
    try:
        with open(file_path, mode='r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            for row in reader:
                cleaned = [c.strip() for c in row if c.strip()]
                if cleaned:
                    text_lines.append(" | ".join(cleaned))
    except Exception as e:
        text_lines.append(f"Error reading CSV: {e}")
        
    full_text = "\n".join(text_lines)
    return _parse_raw_quotation_text(full_text, filename)

def _parse_raw_quotation_text(text, filename):
    """
    Applies pattern recognition and heuristics to extract quotation fields.
    """
    data = {
        "supplier_name": "Not provided",
        "quotation_number": "Not provided",
        "item_description": "Industrial Equipment",
        "unit_price": 0.0,
        "quantity": 1,
        "currency": "USD",
        "discount_amount": 0.0,
        "tax_rate": 0.0,
        "tax_amount": 0.0,
        "shipping_cost": 0.0,
        "installation_cost": 0.0,
        "other_charges": 0.0,
        "total_cost": 0.0,
        "warranty_months": 12,
        "delivery_days": 30,
        "promised_delivery_date": "",
        "payment_terms": "Net 30",
        "quote_validity_date": "",
        "filename": filename,
        "extraction_confidence": 75.0,
        "missing_fields": []
    }
    
    # 1. Supplier Name detection
    supplier_patterns = [
        r'(?:Supplier|Vendor|Company|From):\s*([A-Za-z0-9\s&.,\-]+?)(?:\n|\||$)',
        r'([A-Za-z0-9\s&.,\-]+?(?:Corporation|Corp|Solutions|Dynamics|Systems|Electrics|Power|Logistics|Industries|Ltd|Inc))',
    ]
    for pattern in supplier_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            if len(candidate) > 3 and "quotation" not in candidate.lower() and "invoice" not in candidate.lower():
                data["supplier_name"] = candidate[:50]
                break
                
    if data["supplier_name"] == "Not provided":
        # Heuristic from filename
        fname_clean = Path(filename).stem.replace('_', ' ').replace('-', ' ').title()
        if "Quote" in fname_clean:
            fname_clean = fname_clean.replace("Quote", "").strip()
        if fname_clean:
            data["supplier_name"] = fname_clean

    # 2. Quotation Number
    quote_no_match = re.search(r'(?:Quote\s*(?:No|Number|#)|Quotation\s*(?:No|Number|#)|Ref(?:erence)?):\s*([A-Za-z0-9\-_]+)', text, re.IGNORECASE)
    if quote_no_match:
        data["quotation_number"] = quote_no_match.group(1).strip()
    else:
        # Fallback generate identifier
        data["quotation_number"] = f"QUO-{abs(hash(filename)) % 100000:05d}"

    # 3. Currency detection
    if "€" in text or "EUR" in text:
        data["currency"] = "EUR"
    elif "£" in text or "GBP" in text:
        data["currency"] = "GBP"
    elif "₹" in text or "INR" in text:
        data["currency"] = "INR"
    else:
        data["currency"] = "USD"

    def _find_amount(keywords):
        for kw in keywords:
            # 1. Same line match: Keyword: $1,234.56 or Keyword | 63000.0
            m1 = re.search(rf'{kw}[^\n$€£₹0-9]*[$€£₹]?\s*([0-9][0-9,]*(?:\.[0-9]+)?)', text, re.IGNORECASE)
            if m1:
                try:
                    return float(m1.group(1).replace(',', ''))
                except ValueError:
                    pass
            # 2. Next lines match: Keyword\n ... $1,234.56
            m2 = re.search(rf'{kw}[^\n]*\n(?:[^\n]*\n)?.*?[$€£₹]\s*([0-9][0-9,]*(?:\.[0-9]+)?)', text, re.IGNORECASE)
            if m2:
                try:
                    return float(m2.group(1).replace(',', ''))
                except ValueError:
                    pass
        return None

    # 4. Quantity detection
    qty_match = re.search(r'(?:Quantity|Qty)[:\s|]+(\d+)', text, re.IGNORECASE)
    if qty_match:
        data["quantity"] = int(qty_match.group(1))
    else:
        # Check table pattern: newline number newline currency (e.g. \n5\n$16,000)
        table_qty = re.search(r'\n\s*(\d{1,4})\s*\n\s*[$€£₹]', text)
        if table_qty:
            data["quantity"] = int(table_qty.group(1))

    # 5. Unit Price detection
    up = _find_amount(['Unit\\s*Price', 'Rate', 'Price\\s*per\\s*unit'])
    if up is not None:
        data["unit_price"] = up
    else:
        # Fallback to first dollar amount in table row
        first_amt = re.search(r'\n\s*\d+\s*\n\s*[$€£₹]\s*([0-9][0-9,]*(?:\.[0-9]+)?)', text)
        if first_amt:
            data["unit_price"] = float(first_amt.group(1).replace(',', ''))

    # 6. Discount detection
    disc = _find_amount(['Discount', 'Volume\\s*Promotional\\s*Discount', 'Rebate'])
    if disc is not None:
        data["discount_amount"] = disc

    # 7. Tax detection
    tax_amt = _find_amount(['Applicable.*Tax', 'Sales\\s*Tax', 'Tax', 'VAT', 'GST'])
    if tax_amt is not None:
        data["tax_amount"] = tax_amt
    rate_m = re.search(r'(?:Tax|VAT|GST)\s*\(([0-9.]+)%\)', text, re.IGNORECASE)
    if rate_m:
        data["tax_rate"] = float(rate_m.group(1))

    # 8. Shipping Cost
    ship = _find_amount(['Shipping', 'Freight', 'Heavy\\s*Freight', 'Delivery\\s*Fee', 'Logistics'])
    if ship is not None:
        data["shipping_cost"] = ship

    # 9. Installation Cost
    inst = _find_amount(['Installation', 'Testing', 'Commissioning', 'Setup'])
    if inst is not None:
        data["installation_cost"] = inst

    # 10. Total Cost detection
    tot = _find_amount(['Grand\\s*Total', 'Total\\s*Cost', 'Total\\s*Amount', 'Total\\s*Price', 'Net\\s*Payable'])
    if tot is not None:
        data["total_cost"] = tot

    # 11. Warranty
    warr_match = re.search(r'(\d+)\s*(?:months?|yrs?|years?)', text, re.IGNORECASE)
    if warr_match:
        val = int(warr_match.group(1))
        if "yr" in warr_match.group(0).lower():
            val *= 12
        data["warranty_months"] = val

    # 12. Delivery Timeline / Days
    deliv_match = re.search(r'(\d+)\s*(?:business\s*days?|days?|weeks?)', text, re.IGNORECASE)
    if deliv_match:
        days = int(deliv_match.group(1))
        if "week" in deliv_match.group(0).lower():
            days *= 7
        data["delivery_days"] = days

    # 13. Payment Terms
    terms_match = re.search(r'(?:Payment\s*Terms?|Terms?)[:\s]+([A-Za-z0-9\s%]+?(?:Net\s*\d+|Advance|COD|Due\s*on\s*receipt))', text, re.IGNORECASE)
    if terms_match:
        data["payment_terms"] = terms_match.group(1).strip()

    # 14. Quote Validity
    val_match = re.search(r'(?:Valid\s*(?:Until|Through|To)|Validity)[:\s]+([0-9\-\/A-Za-z\s]+?)(?:\n|$)', text, re.IGNORECASE)
    if val_match:
        data["quote_validity_date"] = val_match.group(1).strip()

    # Recalculate / reconcile total if unit price and qty are available but total is 0
    if data["total_cost"] == 0.0 and data["unit_price"] > 0:
        sub = data["unit_price"] * data["quantity"] - data["discount_amount"]
        data["total_cost"] = round(sub + data["tax_amount"] + data["shipping_cost"] + data["installation_cost"] + data["other_charges"], 2)
    elif data["unit_price"] == 0.0 and data["total_cost"] > 0 and data["quantity"] > 0:
        data["unit_price"] = round(data["total_cost"] / data["quantity"], 2)

    # Track missing fields explicitly
    missing = []
    if data["supplier_name"] == "Not provided":
        missing.append("Supplier name")
    if data["unit_price"] == 0.0:
        missing.append("Unit price")
    if data["shipping_cost"] == 0.0:
        missing.append("Shipping cost")
    if data["installation_cost"] == 0.0:
        missing.append("Installation charges")
    if not data["quote_validity_date"]:
        missing.append("Quote validity date")
    data["missing_fields"] = missing

    # Compute extraction confidence score
    score = 100.0 - (len(missing) * 8.0)
    data["extraction_confidence"] = round(max(35.0, min(99.0, score)), 1)

    return data
