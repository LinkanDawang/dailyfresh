# from django.core.urlresolvers import reverse
from django.urls import reverse
from django.shortcuts import render, redirect
import json
import os
from django.views.generic import View
from django_redis import get_redis_connection

from users.models import Address


class PlaceOrderView(View):
    """提交订单的视图"""
    # 商品数据可以是购物车页面过来的也可以是商品详情页过来的
    def post(self, request):
        user = request.user

        # 获取一个或多个商品sku_id
        sku_ids = request.POST.getlist('sku_ids')
        count = request.POST.get('count')

        # 校验数据
        if sku_ids is None:
            return redirect(reverse('cart:info'))

        # 获取用户最新的收货地址
        try:
            address = Address.objects.filter(user=user).latest('create_time')
        except Address.DoesNotExist:
            address = None

        skus = []
        total_count = 0  # 所有商品的总数
        total_amount = 0  # 所有商品的总价
        trans_cost = 10  # 运费

        redis_conn = get_redis_connection('default')
        cart_dict = redis_conn.hgetall('cart_%s' % user.id)

        if count is None:
            pass


