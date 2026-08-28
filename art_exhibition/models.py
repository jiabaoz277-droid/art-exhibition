"""数据模型（对应 PRD 数据模型：campaigns / applicants / works / check_reports）。"""
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    deadline = Column(DateTime, nullable=True)
    image_formats = Column(String, default="jpg,jpeg,png,webp")
    max_image_mb = Column(Float, default=10.0)
    link_token = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=utcnow)

    applicants = relationship("Applicant", back_populates="campaign", cascade="all, delete-orphan")


class Applicant(Base):
    __tablename__ = "applicants"
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, default="")
    email = Column(String, default="")
    wechat = Column(String, default="")
    resume_path = Column(String, default="")
    status = Column(String, default="submitted")  # submitted / checked
    created_at = Column(DateTime, default=utcnow)

    campaign = relationship("Campaign", back_populates="applicants")
    works = relationship("Work", back_populates="applicant", cascade="all, delete-orphan")
    report = relationship("CheckReport", back_populates="applicant", uselist=False, cascade="all, delete-orphan")


class Work(Base):
    __tablename__ = "works"
    id = Column(Integer, primary_key=True)
    applicant_id = Column(Integer, ForeignKey("applicants.id"), nullable=False, index=True)
    title = Column(String, default="")
    dimensions = Column(String, default="")
    medium = Column(String, default="")   # 画种
    school = Column(String, default="")   # 毕业院校
    price = Column(String, default="")
    image_path = Column(String, default="")

    applicant = relationship("Applicant", back_populates="works")


class CheckReport(Base):
    __tablename__ = "check_reports"
    id = Column(Integer, primary_key=True)
    applicant_id = Column(Integer, ForeignKey("applicants.id"), nullable=False, unique=True, index=True)
    missing = Column(Text, default="[]")         # JSON 数组
    format_issues = Column(Text, default="[]")   # JSON 数组
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=utcnow)

    applicant = relationship("Applicant", back_populates="report")
