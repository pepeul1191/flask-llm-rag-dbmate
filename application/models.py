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

  def to_json(self):
    return {
      'id': self.id,
      'name': self.name,
      'image': self.image,
      'projects_count': len(self.projects) if self.projects else 0
    }

class Project(Base):
  __tablename__ = 'projects'

  id = Column(Integer, primary_key=True)
  title = Column(String(30), nullable=False)
  description = Column(String(180), nullable=False)
  connection_string = Column(String(100), nullable=False)
  engine_id = Column(Integer, ForeignKey("engines.id"), nullable=False)

  engine = relationship("Engine", back_populates="projects")
  versions = relationship("Version", back_populates="project", cascade="all, delete-orphan")

  def to_json(self, include_versions=False, include_engine=False):
    result = {
      'id': self.id,
      'title': self.title,
      'description': self.description,
      'connection_string': self.connection_string,
      'engine_id': self.engine_id,
      'versions_count': len(self.versions) if self.versions else 0
    }
    
    if include_engine and self.engine:
      result['engine'] = self.engine.to_json()
    
    if include_versions and self.versions:
      result['versions'] = [version.to_json() for version in self.versions]
    
    return result

class Version(Base):
  __tablename__ = 'versions'

  id = Column(Integer, primary_key=True)
  name = Column(String(50), nullable=False)
  model = Column(Text, nullable=False)
  created_at = Column(DateTime, default=datetime.utcnow)
  updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
  project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

  project = relationship("Project", back_populates="versions")

  def to_json(self, include_project=False):
    result = {
      'id': self.id,
      'name': self.name,
      'model': self.model,
      'created_at': self.created_at.isoformat() if self.created_at else None,
      'updated_at': self.updated_at.isoformat() if self.updated_at else None,
      'project_id': self.project_id
    }
    
    if include_project and self.project:
      result['project'] = self.project.to_json()
    
    return result
