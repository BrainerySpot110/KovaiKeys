from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    Request,
    Response,
    Cookie
)

from database import engine, Base
import models

Base.metadata.create_all(bind=engine)

from fastapi import Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import shutil
import os

from database import get_db
from models import User, Property

app = FastAPI()




ALL_ROLES = ["Owner", "Admin", "Broker", "Buyer", "Rent"]
CAN_MANAGE_PROPERTIES = ["Owner", "Admin", "Broker"]
CAN_VIEW_USERS = ["Admin"]


def require_roles(allowed_roles):
    """Dependency factory for API routes: raises 403 if the logged-in
    user's role (read from the 'role' cookie set at login) is not in
    allowed_roles. Anonymous (no cookie) is always rejected."""

    def checker(role: Optional[str] = Cookie(default=None)):
        if role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. This action requires one of these roles: {', '.join(allowed_roles)}"
            )
        return role

    return checker


UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOAD_FOLDER), name="uploads")

templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RegisterUser(BaseModel):
    name: str
    email: str
    password: str
    role: str


class LoginUser(BaseModel):
    email: str
    password: str
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


@app.get("/login-page")
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )


@app.get("/register-page")
def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html"
    )


@app.get("/add-property-page")
def add_property_page(request: Request, role: Optional[str] = Cookie(default=None)):
    # Only Owners, Admins and Brokers are allowed to list a property.
    # Buyers and Renters ("Rent") are shoppers, not listers.
    if role not in CAN_MANAGE_PROPERTIES:
        return templates.TemplateResponse(
            request=request,
            name="access_denied.html",
            context={
                "message": "Only Property Owners, Brokers, or Admins can add a property.",
                "current_role": role or "Guest"
            },
            status_code=403
        )
    return templates.TemplateResponse(
        request=request,
        name="add_property.html"
    )


@app.get("/property-page")
def property_page(request: Request, db: Session = Depends(get_db), role: Optional[str] = Cookie(default=None)):
    properties = db.query(Property).all()
    return templates.TemplateResponse(
        request=request,
        name="property.html",
        context={
            "properties": properties,
            "can_manage_properties": role in CAN_MANAGE_PROPERTIES
        }
    )


@app.post("/register")
def register(user: RegisterUser, db: Session = Depends(get_db)):

    existing = db.query(User).filter(User.email == user.email).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    new_user = User(
        name=user.name,
        email=user.email,
        password=user.password,
        role=user.role
    )

    db.add(new_user)
    db.commit()

    return {
        "message": "Registration Successful"
    }


@app.post("/login")
def login(user: LoginUser, response: Response, db: Session = Depends(get_db)):

    db_user = db.query(User).filter(
        User.email == user.email
    ).first()

    if db_user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid Email"
        )

    if db_user.password != user.password:
        raise HTTPException(
            status_code=401,
            detail="Wrong Password"
        )

    
    response.set_cookie(key="role", value=db_user.role, httponly=False, samesite="lax")
    response.set_cookie(key="user_name", value=db_user.name, httponly=False, samesite="lax")

    return {
        "message": "Login Successful",
        "name": db_user.name,
        "role": db_user.role
    }


@app.post("/logout")
def logout(response: Response):
    response.delete_cookie("role")
    response.delete_cookie("user_name")
    return {"message": "Logged out"}


@app.post("/properties")
async def add_property(

    title: str = Form(...),
    location: str = Form(...),
    price: str = Form(...),
    property_type: str = Form(...),
    bedrooms: int = Form(...),
    description: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    role: str = Depends(require_roles(CAN_MANAGE_PROPERTIES))

):

    filename = image.filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    new_property = Property(
    title=title,
    location=location,
    price=price,
    property_type=property_type,
    bedrooms=bedrooms,
    description=description,
    broker="+91 9043096587",   
    image=filename,
    status="Active"
)

    db.add(new_property)
    print("Saving property:", title)
    db.commit()
    print("Property saved successfully")
    return RedirectResponse(
    url="/property-page",
    status_code=303
)


@app.post("/properties/{property_id}/mark-sold")
def mark_property_sold(
    property_id: int,
    db: Session = Depends(get_db),
    role: str = Depends(require_roles(CAN_MANAGE_PROPERTIES))
):
   

    property = db.query(Property).filter(Property.id == property_id).first()

    if property is None:
        raise HTTPException(status_code=404, detail="Property not found")

    property.status = "Active" if property.status == "Sold" else "Sold"
    db.commit()

    return {
        "message": f"Marked as {property.status}",
        "status": property.status
    }


@app.delete("/properties/{property_id}")
def delete_property(
    property_id: int,
    db: Session = Depends(get_db),
    role: str = Depends(require_roles(CAN_MANAGE_PROPERTIES))
):


    property = db.query(Property).filter(Property.id == property_id).first()

    if property is None:
        raise HTTPException(status_code=404, detail="Property not found")

    image_path = os.path.join(UPLOAD_FOLDER, property.image)
    if os.path.exists(image_path):
        os.remove(image_path)

    db.delete(property)
    db.commit()

    return {"message": "Property deleted"}


@app.get("/api/properties")
def get_properties(db: Session = Depends(get_db)):
    return db.query(Property).all()


@app.get("/users")
def get_users(
    db: Session = Depends(get_db),
    role: str = Depends(require_roles(CAN_VIEW_USERS))
):
    return db.query(User).all()


@app.get("/me")
def get_current_user(role: Optional[str] = Cookie(default=None), user_name: Optional[str] = Cookie(default=None)):
    """Lets the frontend know who is logged in and what they're allowed to do."""
    return {
        "logged_in": role is not None,
        "name": user_name,
        "role": role,
        "can_manage_properties": role in CAN_MANAGE_PROPERTIES,
        "can_view_users": role in CAN_VIEW_USERS
    }


@app.get("/properties/{property_id}")
def get_property(
    property_id: int,
    db: Session = Depends(get_db)
):

    property = db.query(Property).filter(
        Property.id == property_id
    ).first()

    if property is None:
        raise HTTPException(
            status_code=404,
            detail="Property not found"
        )

    return property
@app.get("/property/{property_id}")
def property_details(
    property_id: int,
    request: Request,
    db: Session = Depends(get_db),
    role: Optional[str] = Cookie(default=None)
):

    property = db.query(Property).filter(
        Property.id == property_id
    ).first()

    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    return templates.TemplateResponse(
        request=request,
        name="property_detail.html",
        context={
            "property": property,
            "can_manage_properties": role in CAN_MANAGE_PROPERTIES
        }
    )
@app.get("/search")
def search_properties(
    request: Request,
    location: str = "",
    property_type: str = "",
    bedrooms: str = "",
    db: Session = Depends(get_db),
    role: Optional[str] = Cookie(default=None)
):

    query = db.query(Property)

    if location:
        query = query.filter(
            Property.location.ilike(f"%{location}%")
        )

    if property_type:
        query = query.filter(
            Property.property_type == property_type
        )

    if bedrooms:
        if bedrooms == "4":
            query = query.filter(Property.bedrooms >= 4)
        else:
            query = query.filter(
                Property.bedrooms == int(bedrooms)
            )

    properties = query.all()

    return templates.TemplateResponse(
        request=request,
        name="property.html",
        context={
            "properties": properties,
            "can_manage_properties": role in CAN_MANAGE_PROPERTIES
        }
    )