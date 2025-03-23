from fastapi import Depends, FastAPI, Request, Form, HTTPException, APIRouter
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from bson import ObjectId

from main import User, get_current_user

app = FastAPI()
shop = APIRouter()

# MongoDB client setup
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.ImranAutos

# Jinja2 templates setup
templates = Jinja2Templates(directory="templates")
# ye function login page render karnay ke liya hy
@shop.get("/sale")
async def read_sale(request: Request,user: User = Depends(get_current_user)):
    return templates.TemplateResponse("sale.html", {"request": request})

@shop.post("/add_product", response_class=RedirectResponse)
async def add_product(productname: str = Form(...), productdescription: str = Form(...), price: int = Form(...)):
    product_details = {"productname": productname, "productdescription": productdescription, "price": price}
    await db.ProductData.insert_one(product_details)
    return RedirectResponse(url="/view_products", status_code=303)


@shop.get("/view_products")
async def view_products(request: Request,user: User = Depends(get_current_user)):
    product_cursor = db.ProductData.find()
    products = await product_cursor.to_list(length=None)
    return templates.TemplateResponse("view.html", {"request": request, "products": products})
@shop.get("/view_products1")
async def view_products(request: Request,user: User = Depends(get_current_user)):
    product_cursor = db.ProductData.find()
    products = await product_cursor.to_list(length=None)
    return templates.TemplateResponse("view1.html", {"request": request, "products": products})

@shop.post("/delete_product/{product_id}", response_class=RedirectResponse)
async def delete_product(product_id: str):
    await db.ProductData.delete_one({"_id": ObjectId(product_id)})
    return RedirectResponse(url="/view_products", status_code=303)

@shop.get("/update_product/{product_id}")
async def update_product_form(product_id: str, request: Request):
    product = await db.ProductData.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return templates.TemplateResponse("update_product.html", {"request": request, "product": product})

@shop.post("/update_product/{product_id}", response_class=RedirectResponse)
async def update_product(product_id: str, productname: str = Form(...), productdescription: str = Form(...), price: int = Form(...)):
    updated_product = {"productname": productname, "productdescription": productdescription, "price": price}
    await db.ProductData.update_one({"_id": ObjectId(product_id)}, {"$set": updated_product})
    return RedirectResponse(url="/view_products", status_code=303)
