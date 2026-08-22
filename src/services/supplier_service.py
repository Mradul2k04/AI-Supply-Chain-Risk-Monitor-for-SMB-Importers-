import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from src.services.database import DBSupplier
from src.schemas.supplier import Supplier

logger = logging.getLogger(__name__)

def get_supplier_by_id(db: Session, supplier_id: str) -> Optional[Supplier]:
    db_supp = db.query(DBSupplier).filter(DBSupplier.supplier_id == supplier_id).first()
    if not db_supp:
        return None
    return Supplier(
        supplier_id=db_supp.supplier_id,
        name=db_supp.name,
        country=db_supp.country,
        city_or_region=db_supp.city_or_region,
        latitude=db_supp.latitude,
        longitude=db_supp.longitude,
        product_categories=db_supp.product_categories,
        primary_port=db_supp.primary_port,
        dependency_percent=db_supp.dependency_percent,
        lead_time_days=db_supp.lead_time_days,
        approved_alternate_supplier_ids=db_supp.approved_alternate_supplier_ids
    )

def list_suppliers(db: Session) -> List[Supplier]:
    db_supps = db.query(DBSupplier).all()
    return [
        Supplier(
            supplier_id=s.supplier_id,
            name=s.name,
            country=s.country,
            city_or_region=s.city_or_region,
            latitude=s.latitude,
            longitude=s.longitude,
            product_categories=s.product_categories,
            primary_port=s.primary_port,
            dependency_percent=s.dependency_percent,
            lead_time_days=s.lead_time_days,
            approved_alternate_supplier_ids=s.approved_alternate_supplier_ids
        ) for s in db_supps
    ]

def upsert_supplier(db: Session, supplier: Supplier) -> Supplier:
    logger.info(f"Upserting supplier: {supplier.supplier_id} - {supplier.name}")
    db_supp = db.query(DBSupplier).filter(DBSupplier.supplier_id == supplier.supplier_id).first()
    
    if db_supp:
        # Update existing
        db_supp.name = supplier.name
        db_supp.country = supplier.country
        db_supp.city_or_region = supplier.city_or_region
        db_supp.latitude = supplier.latitude
        db_supp.longitude = supplier.longitude
        db_supp.product_categories = supplier.product_categories
        db_supp.primary_port = supplier.primary_port
        db_supp.dependency_percent = supplier.dependency_percent
        db_supp.lead_time_days = supplier.lead_time_days
        db_supp.approved_alternate_supplier_ids = supplier.approved_alternate_supplier_ids
    else:
        # Create new
        db_supp = DBSupplier(
            supplier_id=supplier.supplier_id,
            name=supplier.name,
            country=supplier.country,
            city_or_region=supplier.city_or_region,
            latitude=supplier.latitude,
            longitude=supplier.longitude,
            product_categories=supplier.product_categories,
            primary_port=supplier.primary_port,
            dependency_percent=supplier.dependency_percent,
            lead_time_days=supplier.lead_time_days,
            approved_alternate_supplier_ids=supplier.approved_alternate_supplier_ids
        )
        db.add(db_supp)
        
    db.commit()
    return supplier

def delete_supplier(db: Session, supplier_id: str) -> bool:
    db_supp = db.query(DBSupplier).filter(DBSupplier.supplier_id == supplier_id).first()
    if db_supp:
        db.delete(db_supp)
        db.commit()
        logger.info(f"Deleted supplier ID: {supplier_id}")
        return True
    return False

def clear_all_suppliers(db: Session) -> int:
    deleted = db.query(DBSupplier).delete()
    db.commit()
    logger.info(f"Cleared all {deleted} suppliers from database.")
    return deleted

