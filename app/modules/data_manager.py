import json
import io
import base64
import zipfile
from datetime import datetime
from app.database import db
from sqlalchemy.orm import class_mapper
from flask import current_app

# Import all models to ensure they are registered
from app.models import (
    User, Role, BusinessConfig, Service, Estimator, Appointment, 
    ContactFormSubmission, Page, PageRender, AuditLog, Post, Media, 
    Channel, Message, LeaveRequest, EncryptedDocument, Task, Newsletter, 
    PageView, UnsubscribedEmail, Product, Order, OrderItem
)

MODELS = [
    User, Role, BusinessConfig, Service, Estimator, Appointment, 
    ContactFormSubmission, Page, PageRender, AuditLog, Post, Media, 
    Channel, Message, LeaveRequest, EncryptedDocument, Task, Newsletter, 
    PageView, UnsubscribedEmail, Product, Order, OrderItem
]

def model_to_dict(obj):
    """
    Convert a SQLAlchemy model instance to a dictionary.
    Handles datetime and bytes.
    """
    data = {}
    for column in class_mapper(obj.__class__).columns:
        value = getattr(obj, column.name)
        if isinstance(value, datetime):
            data[column.name] = value.isoformat()
        elif isinstance(value, bytes):
            data[column.name] = base64.b64encode(value).decode('utf-8')
        else:
            data[column.name] = value
    return data

def dict_to_model(model_class, data):
    """
    Convert a dictionary back to a model instance.
    Handles datetime and bytes decoding.
    Bypasses __init__ to avoid side effects (hashing) or argument mismatches.
    """
    # Create an empty instance using SQLAlchemy's internal mechanism
    # This ensures the object is properly instrumented but skips __init__
    mapper = class_mapper(model_class)
    obj = mapper.class_manager.new_instance()
    
    for column in mapper.columns:
        if column.name in data:
            val = data[column.name]
            if val is None:
                setattr(obj, column.name, None)
                continue
            
            # Check type of column
            col_type = column.type
            try:
                if str(col_type) == 'DATETIME' and isinstance(val, str):
                    val = datetime.fromisoformat(val)
                elif str(col_type) in ('LARGEBINARY', 'BLOB') and isinstance(val, str):
                    val = base64.b64decode(val)
            except Exception as e:
                # Log warning but continue
                current_app.logger.warning(f"Failed to convert {column.name} for {model_class.__name__}: {e}")
            
            setattr(obj, column.name, val)
                
    return obj

def create_backup_zip():
    """
    Generates a ZIP file containing JSON dumps of all models.
    Returns a BytesIO object of the ZIP file.
    """
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for model in MODELS:
            table_name = model.__tablename__ if hasattr(model, '__tablename__') else model.__name__.lower()
            records = model.query.all()
            data = [model_to_dict(record) for record in records]
            json_data = json.dumps(data, indent=2)
            zf.writestr(f"{table_name}.json", json_data)
    
    memory_file.seek(0)
    return memory_file

def restore_from_zip(zip_file_obj):
    """
    Restores data from a ZIP file object.
    WARNING: This logic assumes a clean state or handling collisions.
    For this generic implementation, we will skip existing PKs (upsert is hard generic).
    
    Actually, for a true restore of a "backup", we might want to wipe first?
    Risk: Wiping is dangerous.
    Strategy: Upsert (merge).
    """
    try:
        with zipfile.ZipFile(zip_file_obj, 'r') as zf:
            # We should probably process in dependency order if we were reconstructing relationships...
            # But plain merge might work if we turn off constraints or do it carefully.
            # Simplified approach: Iterate models, find corresponding json, load.
            
            # Iterate models in dependency order
            for model in MODELS:
                table_name = model.__tablename__ if hasattr(model, '__tablename__') else model.__name__.lower()
                filename = f"{table_name}.json"
                
                if filename not in zf.namelist():
                    continue
                
                current_app.logger.info(f"Restoring {table_name} from {filename}...")
                json_data = zf.read(filename)
                records = json.loads(json_data)
                
                if not records:
                    continue
                    
                # Process records to convert types (datetime/bytes)
                # bulk_insert_mappings expects dicts, so we use a simplified converter
                processed_records = []
                mapper = class_mapper(model)
                for record in records:
                    processed = {}
                    for col_name, val in record.items():
                        if val is None:
                            processed[col_name] = None
                            continue
                        
                        # Find column
                        if col_name in mapper.columns:
                            col_type = mapper.columns[col_name].type
                            try:
                                if str(col_type) == 'DATETIME' and isinstance(val, str):
                                    val = datetime.fromisoformat(val)
                                elif str(col_type) in ('LARGEBINARY', 'BLOB') and isinstance(val, str):
                                    val = base64.b64decode(val)
                            except:
                                pass
                        
                        processed[col_name] = val
                    processed_records.append(processed)

                # Use bulk_insert_mappings for speed and bypassing __init__
                # Note: This might fail on duplicate PKs. Logic assumes empty or non-conflicting.
                # If we want "upsert", it's harder with bulk. 
                # For now, let's try strict bulk insert and catch IntegrityError if needed.
                # In a restore scenario, we might want to skip existing?
                # bulk_insert_mappings doesn't support 'skip'.
                
                # Check for existing to avoid integrity error?
                # For restoration of "Download All", usually we assume clean target or we use merge.
                # But merge failed us.
                # Let's try bulk_insert_mappings. If it fails, we might need a fallback.
                
                # Optimization: Filter out records that already exist?
                # Fetch all IDs?
                # Only if records are few.
                
                # Let's try naive bulk insert.
                try:
                    db.session.bulk_insert_mappings(model, processed_records)
                    db.session.commit() # Commit per table to save progress?
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.warning(f"Bulk insert failed for {table_name}: {e}. Falling back to merge.")
                    # Fallback to slow merge
                    for record in processed_records:
                        pk = record.get('id')
                        existing = db.session.get(model, pk) if pk else None
                        if existing:
                            # Update attrs
                            for k, v in record.items():
                                setattr(existing, k, v)
                        else:
                            # Create new using new_instance
                            obj = mapper.class_manager.new_instance()
                            for k, v in record.items():
                                setattr(obj, k, v)
                            db.session.add(obj)
                    db.session.commit()
            
            current_app.logger.info("Restore completion confirmed.")
            return True, "Restore successful"
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return False, str(e)
