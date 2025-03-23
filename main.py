
from fastapi import FastAPI, Request, Form, HTTPException, Depends, Response, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from fastapi_login import LoginManager

# added
import os
from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

app = FastAPI()

# Get absolute path of the static directory
BASE_DIR = os.path.dirname(os.path.abspath(_file_))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Debug: Print the absolute path
print(f"Static Directory Path: {STATIC_DIR}")

# Ensure the static directory exists
if not os.path.exists(STATIC_DIR):
    print("Static directory is missing. Creating it now...")
    os.makedirs(STATIC_DIR)

# Mount the static folder
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
#Till here 

# MongoDB client setup
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.ImranAutos

# Jinja2 templates setup
templates = Jinja2Templates(directory="templates")

# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

SECRET = "welcome"
manager = LoginManager(SECRET, token_url='/signin', use_cookie=True)
manager.cookie_name = "auth_token"
USERNAME = "imran@gmail.com"
PASSWORD = "imran123"

class User(BaseModel):
    username: str

# Session dictionary to store session data
sessions = {}

@manager.user_loader()
async def load_user(username: str):
    if username == USERNAME:
        return User(username=username)
    return None

@app.middleware("http")
async def add_no_store_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    return response

# Dependency to check if user is authenticated
async def get_current_user(request: Request):
    auth_token = request.cookies.get(manager.cookie_name)
    if auth_token not in sessions:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return User(username=sessions[auth_token]["username"])
    

@app.route("/signin", methods=["GET", "POST"])
async def signin(request: Request, adminEmail: str = Form(None), adminPassword: str = Form(None)):
    if request.method == "POST":
        form_data = await request.form()
        adminEmail = form_data.get('adminEmail')
        adminPassword = form_data.get('adminPassword')
        if adminEmail == USERNAME and adminPassword == PASSWORD:
            user = User(username=adminEmail)
            access_token = manager.create_access_token(data={"sub": adminEmail})
            response = RedirectResponse(url="/MainHome", status_code=302)
            manager.set_cookie(response, access_token)
            sessions[access_token] = {"username": adminEmail}
            return response
        else:
            message = "Invalid credentials"
            return templates.TemplateResponse("login.html", {"request": request, "message": message})
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def signup_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})
@app.get("/", response_class=HTMLResponse)
async def signup_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/register", response_class=JSONResponse)
async def signup(username: str = Form(...), password: str = Form(...)):
    existing_user = await db.users.find_one({"username": username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    await db.users.insert_one({"username": username, "password": password})
    return JSONResponse(content={"message": "User registered successfully", "message_type": "success"})


@app.get("/user_login", response_class=HTMLResponse)
async def user_login(request: Request):
    return templates.TemplateResponse("userlogin.html", {"request": request})

@app.post("/user_login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    # Check if username exists in the database
    user = await db.users.find_one({"username": username})
    if user:
        # If username exists, check if the password matches
        if user["password"] == password:
            access_token = manager.create_access_token(data={"sub": username})
            response = RedirectResponse(url="/services", status_code=302)
            manager.set_cookie(response, access_token)
            return response
        else:
            return templates.TemplateResponse("userlogin.html", {"request": request, "message": "Incorrect password"})
    else:
        return templates.TemplateResponse("userlogin.html", {"request": request, "message": "Username not found"})

@app.get("/MainHome")
async def read_main_home(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("MainHome.html", {"request": request, "user": user})

@app.get("/middle")
async def read_middle(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("middle.html", {"request": request, "user": user})

@app.get("/services")
async def read_services(request: Request):
    return templates.TemplateResponse("services.html", {"request": request})
@app.get("/services2")
async def read_services(request: Request):
    return templates.TemplateResponse("services2.html", {"request": request})

@app.get("/contact")
async def read_contact(request: Request):
    return templates.TemplateResponse("contactus.html", {"request": request})

@app.get("/logout")
async def logout(request: Request, response: Response):
    auth_token = request.cookies.get(manager.cookie_name)
    if auth_token in sessions:
        del sessions[auth_token]
    response.delete_cookie(manager.cookie_name)
    return RedirectResponse(url="/signin", status_code=303)

# Include the shop router (assuming shop router is defined in shop.py)
from shop import shop
app.include_router(shop)
