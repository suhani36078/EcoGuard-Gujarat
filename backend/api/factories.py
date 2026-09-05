"""API route: /api/factories"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.database import Factory, get_db
from models.schemas import FactoryOut

router = APIRouter()


@router.get("", response_model=List[FactoryOut])
def list_factories(db: Session = Depends(get_db)):
    return db.query(Factory).all()


@router.get("/{factory_id}", response_model=FactoryOut)
def get_factory(factory_id: str, db: Session = Depends(get_db)):
    factory = db.query(Factory).filter(Factory.id == factory_id).first()
    if not factory:
        raise HTTPException(status_code=404, detail="Factory not found")
    return factory
