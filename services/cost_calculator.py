"""
Cost Calculator Service for PROCUREMENTIQ AI
Implements exact, transparent procurement total cost calculations
strictly separating arithmetic from natural language text.
"""

def calculate_quotation_cost(unit_price, quantity, discount_amount=0.0,
                             tax_rate=0.0, tax_amount=None, shipping_cost=0.0,
                             installation_cost=0.0, other_charges=0.0,
                             currency="USD"):
    """
    Computes landed procurement cost:
    - Subtotal = Unit Price * Quantity
    - Net Subtotal = Subtotal - Applicable Discount
    - Estimated Total Cost = Net Subtotal + Applicable Taxes + Shipping + Installation + Other Included Charges
    """
    unit_price = float(unit_price or 0.0)
    quantity = int(quantity or 1)
    discount_amount = float(discount_amount or 0.0)
    shipping_cost = float(shipping_cost or 0.0)
    installation_cost = float(installation_cost or 0.0)
    other_charges = float(other_charges or 0.0)
    
    # Subtotal calculation
    subtotal = round(unit_price * quantity, 2)
    
    # Net Subtotal (cannot be negative)
    net_subtotal = max(0.0, round(subtotal - discount_amount, 2))
    
    # Taxes: either explicit tax_amount or percentage applied on net subtotal
    if tax_amount is not None and float(tax_amount) > 0:
        calc_tax = round(float(tax_amount), 2)
    elif tax_rate and float(tax_rate) > 0:
        calc_tax = round(net_subtotal * (float(tax_rate) / 100.0), 2)
    else:
        calc_tax = 0.0
        
    estimated_total_cost = round(net_subtotal + calc_tax + shipping_cost + installation_cost + other_charges, 2)
    
    formulas_used = (
        f"Subtotal = {quantity} x {currency} {unit_price:,.2f} = {currency} {subtotal:,.2f}; "
        f"Net Subtotal = {currency} {subtotal:,.2f} - {currency} {discount_amount:,.2f} (Discount) = {currency} {net_subtotal:,.2f}; "
        f"Estimated Total = {currency} {net_subtotal:,.2f} + {currency} {calc_tax:,.2f} (Tax) + "
        f"{currency} {shipping_cost:,.2f} (Freight) + {currency} {installation_cost:,.2f} (Install) + "
        f"{currency} {other_charges:,.2f} (Other) = {currency} {estimated_total_cost:,.2f}"
    )
    
    missing_warnings = []
    if shipping_cost == 0.0:
        missing_warnings.append("Shipping cost documented as $0.00 / included or not provided.")
    if installation_cost == 0.0:
        missing_warnings.append("Installation charges documented as $0.00 / not required.")
    if calc_tax == 0.0:
        missing_warnings.append("Applicable taxes documented as $0.00 or pending regional tax exemption.")
        
    return {
        "unit_price": unit_price,
        "quantity": quantity,
        "subtotal": subtotal,
        "discount_amount": discount_amount,
        "net_subtotal": net_subtotal,
        "tax_rate": float(tax_rate or 0.0),
        "tax_amount": calc_tax,
        "shipping_cost": shipping_cost,
        "installation_cost": installation_cost,
        "other_charges": other_charges,
        "estimated_total_cost": estimated_total_cost,
        "currency": currency,
        "formulas_used": formulas_used,
        "missing_cost_warnings": " | ".join(missing_warnings) if missing_warnings else "None. All required cost lines verified."
    }
