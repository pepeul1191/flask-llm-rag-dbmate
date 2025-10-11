#!/usr/bin/env python
# -*- coding: utf-8 -*-

# main/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite:///db/app.db", echo=True)
Session = sessionmaker(bind=engine)
session = Session()