from app.main import app

for route in app.routes:
    print(f"Route: {route.path} {route.methods}")
