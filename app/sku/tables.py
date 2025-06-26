from app import create_app, db
from .. import create_app, db
from .models import SKU
from app.sku.models import SKU

def initialize_sku_tables():
    """Initialize SKU-related database tables"""
    app = create_app()
    
    with app.app_context():
        try:
            db.create_all()
            print("✅ SKU tables created successfully!")
            return True
        except Exception as e:
            print(f"❌ Error creating SKU tables: {str(e)}")
            return False

if __name__ == '__main__':
    initialize_sku_tables()