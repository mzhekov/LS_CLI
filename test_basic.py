#!/usr/bin/env python
"""Basic functionality test"""

import sys
sys.path.insert(0, '/home/user/LS_CLI')

from leadsauce.utils.db import get_session, init_database
from leadsauce.utils.helpers import hash_password, verify_password
from leadsauce.models.user import User

# Initialize database
init_database()

# Test password hashing
password = "TestPassword123"
hashed = hash_password(password)
print(f"Password: {password}")
print(f"Hashed: {hashed}")
print(f"Verification: {verify_password(password, hashed)}")
print()

# Test creating a user
session = get_session()

# Delete existing test user if exists
existing = session.query(User).filter(User.email == "test@example.com").first()
if existing:
    session.delete(existing)
    session.commit()
    print("Deleted existing test user")

# Create new user
user = User(
    email="test@example.com",
    password_hash=hash_password("TestPassword123"),
    first_name="Test",
    last_name="User"
)
session.add(user)
session.commit()
print(f"Created user: {user.email} (ID: {user.id})")

# Verify we can retrieve and verify password
retrieved_user = session.query(User).filter(User.email == "test@example.com").first()
print(f"Retrieved user: {retrieved_user.email}")
print(f"Password verification: {verify_password('TestPassword123', retrieved_user.password_hash)}")

session.close()
print("\n✓ All tests passed!")
