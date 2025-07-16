from django.contrib import admin
from .models import Product,CartItem,Order

# Register your models here.
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display=('name','price','stock','created_at')
    search_fields=('name',)
    list_filter=('created_at',)

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display=('user','product','quantity','added_at')
    list_filter=('added_at',)
    search_fields=('user__username','product__name')

@admin.register(Order)
class OredrAdmin(admin.ModelAdmin):
    list_display=('id','user','total_price','status','ordered_at')
    list_filter=('status','ordered_at',)
    search_fields=('user__username',)
    filter_horizontal=('items',)