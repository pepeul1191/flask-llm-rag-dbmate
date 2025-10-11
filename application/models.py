#!/usr/bin/env python
# -*- coding: utf-8 -*-

# application/models.py

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

# --- MODELOS ---

class Engine(Base):
  __tablename__ = 'engines'

  id = Column(Integer, primary_key=True)
  name = Column(String(20), nullable=False)
  image = Column(String(30), nullable=False)

  projects = relationship("Project", back_populates="engine")

class Project(Base):
  __tablename__ = 'projects'

  id = Column(Integer, primary_key=True)
  title = Column(String(30), nullable=False)
  description = Column(String(180), nullable=False)
  connection_string = Column(String(100), nullable=False)
  engine_id = Column(Integer, ForeignKey("engines.id"), nullable=False)

  engine = relationship("Engine", back_populates="projects")
  versions = relationship("Version", back_populates="project", cascade="all, delete-orphan")

class Version(Base):
  __tablename__ = 'versions'

  id = Column(Integer, primary_key=True)
  name = Column(String(50), nullable=False)
  model = Column(Text, nullable=False)
  created_at = Column(DateTime, default=datetime.utcnow)
  updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
  project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

  project = relationship("Project", back_populates="versions")
