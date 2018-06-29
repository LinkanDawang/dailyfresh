import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import View
from django_redis import get_redis_connection
from goods.models import GoodsSKU


class AddCartView(View):
    """添加商品到购物车功能"""

    def post(self, request):
        # 获取添加到购物车的商品和数量
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 校验数据
        if not all([sku_id, count]):
            return JsonResponse({'code': 1, 'msg': '购物车参数不全'})

        # 判断商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'code': 2, 'msg': '不存在该商品'})

        # 判断商品数量是否正确
        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'code': 3, 'msg': e})

        # 判断库存是否足够
        if count > sku.stock:
            return JsonResponse({'code': 4, 'msg': '库存不足'})

        user = request.user
        # 用户登入的情况下
        if user.is_authenticated():
            # 使用哈希格式来存储数据user_id:{'sku_id1':count1, 'sku_id:count2}
            redis_conn = get_redis_connection('default')
            # 存到redis的购物车数量=之前的数量+现在添加数量
            origin_count = redis_conn.hget('cart_%s' % user.id, sku_id)
            if origin_count is not None:
                count += int(origin_count)
            # 把数据保存到redis
            redis_conn.hset('cart_%s' % user.id, sku_id, count)
        # 用户没有登入的情况下,把数据保存到浏览器
        else:
            cart_json = request.COOKIES.get('cart')
            if cart_json is not None:
                cart_dict = json.loads(cart_json)
            else:
                cart_dict = {}

            # 如果已经存在该商品，累加数量
            if sku_id in cart_dict:
                origin_count = cart_dict.get(sku_id)
                count += origin_count

            cart_dict[sku_id] = count

        # 查询购物车数量,登入从redis中获取，未登入从cookie获取
        cart_num = 0
        if user.is_authenticated():
            user = request.user
            redis_conn = get_redis_connection('default')
            cart_dict = redis_conn.hgetall('cart_%s' % user.id)

        for value in cart_dict.values():
            cart_num += int(value)

        response = JsonResponse({'code': 0, 'msg': '添加成功', 'cart_num': cart_num})

        if not user.is_authenticated():
            cart_json = json.dumps(cart_dict)
            response.set_cookie('cart', cart_json)

        return response


class CartInfoView(View):
    """购物车页面"""

    def get(self, request):
        # 用户登入，从redis中获取数据， 用户未登入，从浏览器cookie获取数据
        user = request.user

        if user.is_authenticated():
            redis_conn = get_redis_connection('default')
            # 获取所有的数据
            cart_dict = redis_conn.hget('cart_%s' % user.id)
        else:
            cart_json = request.COOKIES.get('cart')
            if cart_json is not None:
                cart_dict = json.loads(cart_json)
            else:
                cart_dict = {}

        total_count = 0  # 用于计算全部商品的数量
        total_amount = 0  # 用于计算全部商品的总价
        skus = []

        # 遍历所有的商品
        for sku_id, count in cart_dict.items():
            try:
                sku = GoodsSKU.objects.get(id=sku_id)
            except GoodsSKU.DoesNotExist:
                continue

            count = int(count)
            amount = count * sku.price
            sku.count = count
            sku.amount = amount
            total_amount += amount
            total_count += count
            skus.append(sku)

        context = {
            'skus': skus,
            'total_count': total_count,
            'total_amount': total_amount
        }

        return render(request, 'cart.html', context)

