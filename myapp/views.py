from django.shortcuts import get_object_or_404, render,redirect
from.models import Product,CartItem,Order
import razorpay
from django.conf import settings
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.mail import send_mail

# Create your views here.
def product_list(request):
    products=Product.objects.all()
    return render(request,'product_list.html',{'products':products})

def product_detail(request, product_id):
    product=get_object_or_404(Product, id=product_id)
    return render(request, 'product_detail.html', {'product':product})

def add_to_cart(request,product_id):
    product=get_object_or_404(Product, id=product_id)
    cart_item,created=CartItem.objects.get_or_create(user=request.user, product=product)

    if not created:
        cart_item.quantity +=1
        cart_item.save()
    return redirect('cart_view')


def cart_view(request):
    cart_items=CartItem.objects.filter(user=request.user)
    Total_price=sum(item.get_total_price() for item in cart_items)
    return render(request,'cart.html',{'cart_items':cart_items,'total_price':Total_price})

def remove_from_cart(request,cart_itemid):
    cart_item=get_object_or_404(CartItem,id=cart_itemid, user=request.user)
    cart_item.delete()
    return redirect('cart_view')

def checkout(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total_price = sum(item.get_total_price() for item in cart_items)
    total_price_paise = int(total_price * 100)

    if request.method == 'POST':
        name    = request.POST.get('name')
        phone   = request.POST.get('phone')
        email   = request.POST.get('email')
        address = request.POST.get('address')

        if not name or not phone or not email or not address:
            return redirect('checkout')
        
        request.session['name'] =name
        request.session['phone'] =phone
        request.session['email'] =email
        request.session['address'] =address

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        payment = client.order.create({
            'amount': total_price_paise,
            'currency': 'INR',
            'payment_capture': 1
        })

        # If you want to create an order in your database before payment, uncomment and use:
        # order = Order.objects.create(
        #     user=request.user,
        #     total_price=total_price,
        #     name=name,
        #     phone=phone,
        #     address=address,
        #     email=email
        # )
        # order.items.set(cart_items)
        # order.save()

        return render(request, 'confirm_payment.html', {
            'cart_items': cart_items,
            'total_price': total_price,
            'order_id': payment['id'],
            'razorpay_key': settings.RAZORPAY_KEY_ID,
            'address': address,
            'name': name,
            'phone': phone,
            'email': email,
        })

    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price
    })


def order_success(request):
    return render(request, 'order_success.html')


@csrf_exempt
def verify_payment(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_order_id   = data.get('razorpay_order_id')

        name= request.session.get('name')
        phone= request.session.get('phone')
        email= request.session.get('email')
        address= request.session.get('address')

        if razorpay_payment_id and razorpay_order_id:
            cart_items   = CartItem.objects.filter(user=request.user)
            total_price  = sum(item.get_total_price() for item in cart_items)

            order = Order.objects.create(
                user=request.user,
                total_price=total_price,
                name=name,
                phone=phone,
                address=address,
                email=email,
                status='pending')

            order.items.set(cart_items)
            order.save()

            # Clear user's cart
            cart_items.delete()

            subjects="oredr confirmation message....!!!!"
            message=f"hii {name},\n\n order your has placed succesfully...! thankyou.\n\n Order ID:{order.id}\n Total Amount:{total_price}\n Addrees:{address}\n"
            send_mail(subject,message,settings)

            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'failed'})

