import json

from django.shortcuts import render
from django_redis import get_redis_connection
from django.core.cache import cache
from django.views.generic import View

from goods.models import GoodsCategory, IndexGoodsBanner, IndexPromotionBanner, IndexCategoryGoodsBanner


class BaseCart(View):
    """获取购物车商品的数量"""
    def get_cart_num(self, request):
        user = request.user
        cart_num = 0

        # 用户登入，从redis中获取数据
        if user.is_authenticated():
            redis_conn = get_redis_connection('default')
            # 获取购物车所有的商品信息[skuid1:1, skuid2:10, skuid3:15]
            cart = redis_conn.hgetall('cart_%s' % user.id)
        # 用户未登入，从浏览器cookies中获取数据
        else:
            cart_json = request.COOKIES.get('cart')
            if cart_json is not None:
                cart = json.loads(cart_json)
            else:
                cart = {}

        for value in cart.values():
            cart_num += value
        return cart_num


class IndexView(BaseCart):
    """商品主页"""
    def get(self, request):
        # 主页数据先从缓存从查找
        context = cache.get('index_cache_data')

        # 没有缓存，从mysql中获取数据
        if context is None:
            print('没有主页数据的缓存')
            # 查询数据 商品分类 幻灯片 活动
            categorys = GoodsCategory.objects.all()  # 商品类别
            banners = IndexGoodsBanner.objects.all()  # 首页轮播图
            promotion_banners = IndexPromotionBanner.objects.all()  # 活动图片

            # 遍历所有的商品类别
            for category in categorys:
                # 获取不带图片的类别
                title_banners = IndexCategoryGoodsBanner.objects.filter(category=category, display_type=0).order_by('index')
                category.title_banners = title_banners

                # 获取带图片的数据
                image_banners = IndexCategoryGoodsBanner.objects.filter(category=category, display_type=1).order_by('index')
                category.image_banners = image_banners

            context = {
                'categorys': categorys,
                'banners': banners,
                'promotion_banners': promotion_banners
            }

            # 把主页需要的数据缓存起来
            cache.set('index_cache_data', context, 3600)
        else:
            print('使用缓存数据填充主页')

        # 获取购物车数量
        cart_num = self.get_cart_num(request)
        context['cart_num'] = cart_num

        return render(request, 'index.html', context)

