from pickle import FALSE
from django.shortcuts import redirect, render
from django.http import HttpResponse
from flask import jsonify
from posApp.models import Category, Products, Sales, salesItems, Barcode
from django.db.models import Count, Sum
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
import json
import sys
from datetime import date, datetime, timedelta
import pandas as pd
import razorpay
from django.conf import settings
import random

# Login

def login_user(request):
    logout(request)
    resp = {"status": 'failed', 'msg': ''}
    username = ''
    password = ''
    if request.POST:
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                resp['status'] = 'success'
            else:
                resp['msg'] = "Incorrect username or password"
        else:
            resp['msg'] = "Incorrect username or password"
    return HttpResponse(json.dumps(resp), content_type='application/json')

# Logout


def logoutuser(request):
    logout(request)
    return redirect('/')

# Create your views here.


@login_required
def home(request):
    now = datetime.now()
    current_year = now.strftime("%Y")
    current_month = now.strftime("%m")
    current_day = now.strftime("%d")
    categories = len(Category.objects.all())
    products = len(Products.objects.all())
    transaction = len(Sales.objects.filter(
        date_added__year=current_year,
        date_added__month=current_month,
        date_added__day=current_day
    ))
    today_sales = Sales.objects.filter(
        date_added__year=current_year,
        date_added__month=current_month,
        date_added__day=current_day
    ).all()
    total_sales = sum(today_sales.values_list('grand_total', flat=True))

    alert = Products.objects.filter(stock__lt=30)


    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=29)
    sales_data = Sales.objects.filter(
        date_added__date__range=(start_date, end_date))

    dates = []
    sales = []
    current_date = start_date
    while current_date <= end_date:
        sales_total = sales_data.filter(date_added__date=current_date).aggregate(
            total=Sum('grand_total'))['total']
        dates.append(current_date.strftime('%Y-%m-%d'))
        sales.append(sales_total or 0)
        current_date += timedelta(days=1)

    productname = []
    inventory = []
    x,y = 0,0
    productdata = Products.objects.all()
    for i in productdata:
        productname.append(i.name)
        n = { "x": x, "y": i.stock}
        inventory.append(n)
        x+=1

    # report - Transactions
    print(inventory)
    # print(sales)

    context = {
        'page_title': 'Home',
        'categories': categories,
        'products': products,
        'transaction': transaction,
        'total_sales': total_sales,
        'alert': alert,
        'dates': dates,
        'sales' : sales,
        'productname': productname,
        'inventory' : inventory
    }
    return render(request, 'posApp/home.html', context)


def about(request):
    context = {
        'page_title': 'About',
    }
    return render(request, 'posApp/about.html', context)


# Categories
@login_required
def category(request):
    category_list = Category.objects.all()
    # category_list = {}
    context = {
        'page_title': 'Category List',
        'category': category_list,
    }
    return render(request, 'posApp/category.html', context)


@login_required
def manage_category(request):
    category = {}
    if request.method == 'GET':
        data = request.GET
        id = ''
        if 'id' in data:
            id = data['id']
        if id.isnumeric() and int(id) > 0:
            category = Category.objects.filter(id=id).first()

    context = {
        'category': category
    }
    return render(request, 'posApp/manage_category.html', context)


@login_required
def save_category(request):
    data = request.POST
    resp = {'status': 'failed'}
    try:
        if (data['id']).isnumeric() and int(data['id']) > 0:
            save_category = Category.objects.filter(id=data['id']).update(
                name=data['name'], status=data['status'])
        else:
            save_category = Category(
                name=data['name'], status=data['status'])
            save_category.save()
        resp['status'] = 'success'
        messages.success(request, 'Category Successfully saved.')
    except:
        resp['status'] = 'failed'
    return HttpResponse(json.dumps(resp), content_type="application/json")


@login_required
def delete_category(request):
    data = request.POST
    resp = {'status': ''}
    try:
        Category.objects.filter(id=data['id']).delete()
        resp['status'] = 'success'
        messages.success(request, 'Category Successfully deleted.')
    except:
        resp['status'] = 'failed'
    return HttpResponse(json.dumps(resp), content_type="application/json")


# Products

@login_required
def products(request):
    if request.method == 'POST':
        excel_file = request.FILES['excel_file']
        print(excel_file)
        data = pd.read_excel(excel_file)
        # Process data and save to Category and Product tables
        for _, row in data.iterrows():
            category_name = row['category']
            category, _ = Category.objects.get_or_create(name=category_name)

            # product_data = {
            #     'code': row['code'],
            #     'name': row['name'],
            #     'price': row['price'],
            #     'stock': row['stock'],
            #     'category': category
            # }
            try:
                product = Products.objects.get(name=row['name'])
            except Products.DoesNotExist:
                product = None
            if product:
                product.stock += row['stock']
                product.save()
            else:
                Products.objects.create(code=row['code'],
                                        category_id=category,
                                        name=row['name'],
                                        price=row['price'],
                                        stock=row['stock'])
    product_list = Products.objects.all()
    for products in product_list:
        if products.stock > 0:
            products.status = 1
            products.save()
    context = {
        'page_title': 'Product List',
        'products': product_list,
    }
    return render(request, 'posApp/products.html', context)


@login_required
def manage_products(request):
    product = {}
    categories = Category.objects.filter(status=1).all()
    if request.method == 'GET':
        data = request.GET
        id = ''
        if 'id' in data:
            id = data['id']
        if id.isnumeric() and int(id) > 0:
            product = Products.objects.filter(id=id).first()

    context = {
        'product': product,
        'categories': categories
    }
    return render(request, 'posApp/manage_product.html', context)


def test(request):
    categories = Category.objects.all()
    context = {
        'categories': categories
    }
    return render(request, 'posApp/test.html', context)


@login_required
def save_product(request):
    data = request.POST
    resp = {'status': 'failed'}
    id = ''
    if 'id' in data:
        id = data['id']
    if id.isnumeric() and int(id) > 0:
        check = Products.objects.exclude(id=id).filter(code=data['code']).all()
    else:
        check = Products.objects.filter(code=data['code']).all()
    if len(check) > 0:
        resp['msg'] = "Product Code Already Exists in the database"
    else:
        category = Category.objects.filter(id=data['category_id']).first()
        try:
            if (data['id']).isnumeric() and int(data['id']) > 0:
                save_product = Products.objects.filter(id=data['id']).update(
                    code=data['code'], category_id=category, name=data['name'], price=float(data['price']), status=data['status'], stock=data['stock'])
            else:
                save_product = Products(code=data['code'], category_id=category, name=data['name'],
                                        price=float(data['price']), status=data['status'], stock=data['stock'])
                save_product.save()
            resp['status'] = 'success'
            messages.success(request, 'Product Successfully saved.')
        except:
            resp['status'] = 'failed'
    return HttpResponse(json.dumps(resp), content_type="application/json")


# @login_required
# def save_bulk_product(request):
#     if request.method == 'POST':
#         excel_file = request.POST.get('excel_file')
#         print(excel_file)
#         data = pd.read_excel(excel_file)
#         # Process data and save to Category and Product tables
#         for _, row in data.iterrows():
#             category_name = row['category']
#             category, _ = Category.objects.get_or_create(category=category_name)

#             product_data = {
#                 'code': row['code'],
#                 'name': row['name'],
#                 'price': row['price'],
#                 'stock': row['stock'],
#                 'category': category
#             }
#             Products.objects.create(**product_data)

#     return render(request, 'posApp/products.html')


@login_required
def delete_product(request):
    data = request.POST
    resp = {'status': ''}
    try:
        Products.objects.filter(id=data['id']).delete()
        resp['status'] = 'success'
        messages.success(request, 'Product Successfully deleted.')
    except:
        resp['status'] = 'failed'
    return HttpResponse(json.dumps(resp), content_type="application/json")


@login_required
def pos(request):
    products = Products.objects.filter(status=1)
    product_json = []
    for product in products:
        if product.stock != 0:
            product_json.append(
                {'id': product.id, 'name': product.name, 'price': float(product.price), 'barcode': product.code})
    context = {
        'page_title': "Point of Sale",
        'products': products,
        'product_json': json.dumps(product_json)
    }

    # products = Products.objects.filter(status=1)
    # product_json = []
    # for product in products:
    #     if product.stock != 0:
    #         product_json.append(
    #             {'id': product.id, 'name': product.name, 'price': float(product.price)})
    # context = {
    #     'page_title': "Point of Sale",
    #     'products': products,
    #     'product_json': json.dumps(product_json)
    # }
    # print(json.dumps(product_json))
    # return HttpResponse('')total = int(grand_total) * 100

    # client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    # # payment = client.order.create(amount= int(total), currency='INR')
    # data = { "amount": total, "currency": "INR", "receipt": "order_rcptid_11" }
    # payment = client.order.create(data=data)
    # print(payment)

    return render(request, 'posApp/pos.html', context)


@login_required
def checkout_modal(request):
    grand_total = 0
    if 'grand_total' in request.GET:
        grand_total = request.GET['grand_total']
    
    context = {
        'grand_total': grand_total,
    }

    return render(request, 'posApp/checkout.html', context)


@login_required
def save_pos(request):
    resp = {'status': 'failed', 'msg': ''}
    data = request.POST
    print(data)
    pref = datetime.now().year + datetime.now().year
    i = 1
    while True:
        code = '{:0>5}'.format(i)
        i += int(1)
        check = Sales.objects.filter(code=str(pref) + str(code)).all()
        if len(check) <= 0:
            break
    code = str(pref) + str(code)

    try:
        sales = Sales(code=code, sub_total=data['sub_total'], tax=data['tax'], tax_amount=data['tax_amount'],
                      grand_total=data['grand_total'], tendered_amount=data['tendered_amount'], amount_change=data['amount_change']).save()
        sale_id = Sales.objects.last().pk
        i = 0
        for prod in data.getlist('product_id[]'):
            product_id = prod
            sale = Sales.objects.filter(id=sale_id).first()
            product = Products.objects.filter(code=product_id).first()
            qty = data.getlist('qty[]')[i]
            product.stock = product.stock - int(qty)
            product.save()
            if product.stock == 0:
                product.status = 0
                product.save()
            # if qty > product.stock:
            #     resp['msg'] = "Only" + product.stock + "available"
            price = data.getlist('price[]')[i]
            total = float(qty) * float(price)
            print({'sale_id': sale, 'product_id': product,
                  'qty': qty, 'price': price, 'total': total})
            salesItems(sale_id=sale, product_id=product,
                       qty=qty, price=price, total=total).save()
            i += int(1)
        resp['status'] = 'success'
        resp['sale_id'] = sale_id
        messages.success(request, "Sale Record has been saved.")
    except:
        resp['msg'] = "An error occured"
        print("Unexpected error:", sys.exc_info()[0])
    return HttpResponse(json.dumps(resp), content_type="application/json")


@login_required
def salesList(request):
    sales = Sales.objects.all()
    sale_data = []
    for sale in sales:
        data = {}
        for field in sale._meta.get_fields(include_parents=False):
            if field.related_model is None:
                data[field.name] = getattr(sale, field.name)
        data['items'] = salesItems.objects.filter(sale_id=sale).all()
        data['item_count'] = len(data['items'])
        if 'tax_amount' in data:
            data['tax_amount'] = format(float(data['tax_amount']), '.2f')
        # print(data)
        sale_data.append(data)
    # print(sale_data)
    context = {
        'page_title': 'Sales Transactions',
        'sale_data': sale_data,
    }
    # return HttpResponse('')
    return render(request, 'posApp/sales.html', context)


@login_required
def receipt(request):
    id = request.GET.get('id')
    sales = Sales.objects.filter(id=id).first()
    transaction = {}
    for field in Sales._meta.get_fields():
        if field.related_model is None:
            transaction[field.name] = getattr(sales, field.name)
    if 'tax_amount' in transaction:
        transaction['tax_amount'] = format(float(transaction['tax_amount']))
    ItemList = salesItems.objects.filter(sale_id=sales).all()
    context = {
        "transaction": transaction,
        "salesItems": ItemList
    }

    return render(request, 'posApp/receipt.html', context)
    # return HttpResponse('')


@login_required
def delete_sale(request):
    resp = {'status': 'failed', 'msg': ''}
    id = request.POST.get('id')
    try:
        delete = Sales.objects.filter(id=id).delete()
        resp['status'] = 'success'
        messages.success(request, 'Sale Record has been deleted.')
    except:
        resp['msg'] = "An error occured"
        print("Unexpected error:", sys.exc_info()[0])
    return HttpResponse(json.dumps(resp), content_type='application/json')


# @login_required
# def report(request):
#     # report - sales
#     end_date = datetime.now().date()
#     start_date = end_date - timedelta(days=6)
#     sales_data = Sales.objects.filter(
#         date_added__date__range=(start_date, end_date))

#     dates = []
#     sales = []
#     current_date = start_date
#     while current_date <= end_date:
#         sales_total = sales_data.filter(date_added__date=current_date).aggregate(
#             total=Sum('grand_total'))['total']
#         dates.append(current_date.strftime('%Y-%m-%d'))
#         sales.append(sales_total or 0)
#         current_date += timedelta(days=1)

    
#     # report - Transactions
#     print(dates)
#     print(sales)
#     context = {
#         'dates': dates,
#         'sales': sales
#     }
#     return render(request, 'posApp/report.html', context)

@login_required
def barcodeGenerator(request):
    if request.method == "POST":
        productname = request.POST.get('productname')
        categoryname = request.POST.get('category_id')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        status = request.POST.get('status')
        
        barcodeNumber = ""
        # check_digit = ""
        if Barcode.objects.filter(name=productname):
            messages.error(request, "Product already exist.")
        else:    
            barcodeNumber = "%0.12d" % random.randint(0,999999999999)
            Barcode.objects.create(name=productname, barcodeNo=barcodeNumber)
            odd_sum = sum(int(barcodeNumber[i]) for i in range(0, 12, 2))
            even_sum = sum(int(barcodeNumber[i]) for i in range(1, 12, 2))
            total = odd_sum + even_sum * 3
            check_digit = (10 - (total % 10)) % 10
        category_id = Category.objects.get(id=categoryname)
        Products.objects.create(code=str(barcodeNumber)+str(check_digit), name=productname, category_id=category_id, price=price, status=status, stock=stock).save()
        return redirect('barcode-generator')
    barcodes = Barcode.objects.all()
    product = Products.objects.all()
    categories = Category.objects.all()
    context = {"barcodes":barcodes, 'product':product, "categories":categories}
    return render(request, 'posApp/barcode_generator.html', context)

@login_required
def delete_barcode(request, barcodeNo):
    Barcode.objects.get(barcodeNo=barcodeNo).delete()
    messages.success(request, 'Product Successfully deleted.')
    return redirect('barcode-generator')