"""API route: /api/citizen-reports — Citizen pollution reporting"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from models.database import CitizenReport, get_db

router = APIRouter()


class ReportCreate(BaseModel):
    category: str
    location: str
    district: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None
    severity: Optional[str] = "MODERATE"
    image_url: Optional[str] = None


class ReportOut(BaseModel):
    id: int
    category: str
    location: str
    district: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    image_url: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    submitted_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution_note: Optional[str] = None
    upvotes: Optional[int] = None

    class Config:
        from_attributes = True


class StatusUpdate(BaseModel):
    status: str
    assigned_to: Optional[str] = None
    resolution_note: Optional[str] = None


@router.post("", response_model=ReportOut, status_code=201)
def create_report(report: ReportCreate, db: Session = Depends(get_db)):
    db_report = CitizenReport(
        category=report.category,
        location=report.location,
        district=report.district,
        latitude=report.latitude,
        longitude=report.longitude,
        description=report.description,
        severity=report.severity or "MODERATE",
        image_url=report.image_url,
        status="submitted",
        submitted_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report


@router.get("", response_model=List[ReportOut])
def get_reports(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(CitizenReport)
    if status:
        q = q.filter(CitizenReport.status == status)
    if category:
        q = q.filter(CitizenReport.category == category)
    if district:
        q = q.filter(CitizenReport.district.ilike(f"%{district}%"))
    return q.order_by(CitizenReport.submitted_at.desc()).offset(skip).limit(limit).all()


@router.get("/summary")
def reports_summary(db: Session = Depends(get_db)):
    reports = db.query(CitizenReport).all()
    by_status: dict = {}
    by_category: dict = {}
    by_severity: dict = {}
    for r in reports:
        by_status[r.status] = by_status.get(r.status, 0) + 1
        by_category[r.category] = by_category.get(r.category, 0) + 1
        by_severity[r.severity] = by_severity.get(r.severity, 0) + 1
    return {
        "total": len(reports),
        "by_status": by_status,
        "by_category": by_category,
        "by_severity": by_severity,
    }


@router.get("/{report_id}", response_model=ReportOut)
def get_report(report_id: int, db: Session = Depends(get_db)):
    r = db.query(CitizenReport).filter(CitizenReport.id == report_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Report not found")
    return r


@router.patch("/{report_id}/status", response_model=ReportOut)
def update_report_status(report_id: int, update: StatusUpdate, db: Session = Depends(get_db)):
    r = db.query(CitizenReport).filter(CitizenReport.id == report_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Report not found")
    r.status = update.status
    r.updated_at = datetime.utcnow()
    if update.assigned_to:
        r.assigned_to = update.assigned_to
    if update.resolution_note:
        r.resolution_note = update.resolution_note
    if update.status == "resolved":
        r.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(r)
    return r


@router.post("/{report_id}/upvote")
def upvote_report(report_id: int, db: Session = Depends(get_db)):
    r = db.query(CitizenReport).filter(CitizenReport.id == report_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Report not found")
    r.upvotes = (r.upvotes or 0) + 1
    db.commit()
    return {"upvotes": r.upvotes}
