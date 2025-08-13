from database import Base, engine
from models import User, Category
Base.metadata.create_all(bind=engine)
print("Database and tables created.")