from flask import render_template, request, jsonify, send_file, current_app, url_for, flash, redirect
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from sqlalchemy import and_, or_
import pdfkit
from jinja2 import Environment, FileSystemLoader
import os
import tempfile
import logging
from . import billing_bp
from app.models import SKU, Bill, BillingItem, db, Revenue, VariableCost
from sqlalchemy.exc import SQLAlchemyError

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@billing_bp.route('/billing')
@login_required
def billing_page():
    """Render the billing page with available SKUs"""
    skus = SKU.query.filter(
        and_(
            SKU.quantity > 0,
            or_(
                SKU.expiry_date == None,
                SKU.expiry_date > date.today()
            )
        )
    ).all()
    return render_template('billing/billing.html', skus=skus)

@billing_bp.route('/billing/api/skus')
@login_required
def get_skus():
    """API endpoint to get available SKUs"""
    skus = SKU.query.filter(
        and_(
            SKU.quantity > 0,
            or_(
                SKU.expiry_date == None,
                SKU.expiry_date > date.today()
            )
        )
    ).all()
    
    return jsonify([{
        'id': sku.id,
        'sku_code': sku.code,
        'name': sku.name,
        'selling_price': float(sku.selling_price),
        'quantity': sku.quantity,
        'expiry_date': sku.expiry_date.isoformat() if sku.expiry_date else None
    } for sku in skus])

@billing_bp.route('/billing/process_bill', methods=['POST'])
@login_required
def process_bill():
    data = request.get_json()
    current_app.logger.info(f"Received bill data: {data}")  # Log incoming data
    
    try:
        # Start transaction
        db.session.begin_nested()  # Use nested transaction for better control
        
        # Validate items
        for item in data.get('items', []):
            sku = SKU.query.get(item['sku_id'])
            if not sku:
                current_app.logger.error(f"SKU not found: {item['sku_id']}")
                raise ValueError(f"SKU {item['sku_id']} not found")
            
            if sku.quantity < item['quantity']:
                current_app.logger.error(f"Insufficient stock for {sku.name}")
                raise ValueError(f"Insufficient stock for {sku.name}")
        
        # Calculate totals
        subtotal = sum(item['quantity'] * item['unit_price'] for item in data['items'])
        tax_amount = subtotal * 0.18
        discount = float(data.get('discount', 0))
        grand_total = subtotal + tax_amount - discount

        # Create bill
        bill = Bill(
            bill_number=f"INV-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            customer_name=data.get('customer_name', 'Walk-in Customer'),
            customer_phone=data.get('customer_phone', ''),
            subtotal=subtotal,
            tax_amount=tax_amount,
            discount=discount,
            grand_total=grand_total,
            payment_method=data.get('payment_method', 'Cash'),
            date=datetime.utcnow(),
            user_id=current_user.id
        )
        db.session.add(bill)
        db.session.flush()
        current_app.logger.info(f"Created bill: {bill.bill_number}")

        # Process items
        total_cost = 0
        for item in data['items']:
            sku = SKU.query.get(item['sku_id'])
            
            # Create billing item
            billing_item = BillingItem(
                bill_id=bill.id,
                sku_id=sku.id,
                sku_code=sku.code,
                sku_name=sku.name,
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                total_price=item['quantity'] * item['unit_price'],
                expiry_date=sku.expiry_date
            )
            db.session.add(billing_item)
            
            # Update inventory
            sku.quantity -= item['quantity']
            db.session.add(sku)
            
            total_cost += sku.cost_price * item['quantity']
            current_app.logger.debug(f"Processed item: {sku.code} x{item['quantity']}")

        # Record financials
        revenue_entry = Revenue(
            user_id=current_user.id,
            amount=grand_total,
            remarks=f"Bill #{bill.bill_number}",
            timestamp=datetime.utcnow(),
            bill_id=bill.id
        )
        db.session.add(revenue_entry)

        if total_cost > 0:
            cost_entry = VariableCost(
                user_id=current_user.id,
                amount=total_cost,
                remarks=f"COGS for Bill #{bill.bill_number}",
                timestamp=datetime.utcnow(),
                bill_id=bill.id
            )
            db.session.add(cost_entry)

        db.session.commit()
        current_app.logger.info(f"Successfully processed bill {bill.bill_number}")

        return jsonify({
            'success': True,
            'bill_id': bill.id,
            'bill_number': bill.bill_number,
            'pdf_url': url_for('billing.download_bill', bill_id=bill.id),
            'view_url': url_for('billing.view_bill', bill_id=bill.id, _external=True) + '?autoprint=true'
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error processing bill: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f"Error: {str(e)}"  # Return actual error to client
        }), 500

@billing_bp.route('/billing/view/<int:bill_id>')
@login_required
def view_bill(bill_id):
    bill = Bill.query.get_or_404(bill_id)
    return render_template('billing/bill_view.html',
        bill=bill,
        company={
            'name': 'LOCUS Retail Store',
            'address': 'Street - 007, GitHub Nagar, Panama City',
            'gstin': 'github123',
            'phone': 'omchitlangia.github.io'
        }
    )

@billing_bp.route('/billing/download/<int:bill_id>')
@login_required
def download_bill(bill_id):
    """Download the generated PDF bill"""
    bill = Bill.query.get_or_404(bill_id)
    pdf_path = os.path.join(
        current_app.root_path,
        'static',
        'bills',
        f'bill_{bill.bill_number}.pdf'
    )
    
    if not os.path.exists(pdf_path):
        try:
            pdf_path = generate_pdf(bill)
        except Exception as e:
            current_app.logger.error(f"PDF regeneration failed: {str(e)}")
            flash('Invoice not available', 'error')
            return redirect(url_for('billing.billing_page'))
    
    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f'Invoice_{bill.bill_number}.pdf',
        mimetype='application/pdf'
    )

def generate_pdf(bill):
    """Generate PDF invoice with Windows-specific fixes"""
    try:
        bills_dir = os.path.join(current_app.root_path, 'static', 'bills')
        os.makedirs(bills_dir, exist_ok=True)
        
        wkhtml_path = current_app.config.get(
            'WKHTMLTOPDF_PATH',
            r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
        )
        
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w') as html_file:
            html_path = html_file.name
            html_file.write(render_template('/billing/bill_template.html',
                bill=bill,
                company={
                    'name': current_app.config.get('COMPANY_NAME', 'LOCUS Retail'),
                    'address': current_app.config.get('COMPANY_ADDRESS', '123 Business Street'),
                    'gstin': current_app.config.get('COMPANY_GSTIN', 'GSTIN123456789'),
                    'phone': current_app.config.get('COMPANY_PHONE', '+1 234 567 8900'),
                    'email': current_app.config.get('COMPANY_EMAIL', 'info@locusretail.com')
                },
                current_user=current_user,
                timedelta=timedelta
            ))

        pdf_path = os.path.join(bills_dir, f'bill_{bill.bill_number}.pdf')
        
        import subprocess
        subprocess.run(
            [
                wkhtml_path,
                '--quiet',
                '--enable-local-file-access',
                html_path,
                pdf_path
            ],
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        os.unlink(html_path)
        if not os.path.exists(pdf_path):
            raise RuntimeError("PDF was not created")
        if os.path.getsize(pdf_path) == 0:
            os.unlink(pdf_path)
            raise RuntimeError("Generated PDF is empty")

        return pdf_path

    except subprocess.CalledProcessError as e:
        error_msg = f"PDF conversion failed: {e.stderr.decode('utf-8')}" if e.stderr else "PDF conversion failed"
        current_app.logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        current_app.logger.error(f"PDF generation error: {str(e)}")
        if 'html_path' in locals() and os.path.exists(html_path):
            os.unlink(html_path)
        if 'pdf_path' in locals() and os.path.exists(pdf_path):
            os.unlink(pdf_path)
        raise RuntimeError(f"PDF generation failed: {str(e)}")