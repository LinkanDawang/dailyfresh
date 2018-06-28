import json

from django.core.paginator import Paginator, EmptyPage
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django_redis import get_redis_connection
from django.core.cache import cache
from django.views.generic import View

from goods.models import GoodsCategory, IndexGoodsBanner, IndexPromotionBanner, IndexCategoryGoodsBanner, GoodsSKU


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
                title_banners = IndexCategoryGoodsBanner.objects.filter(category=category, display_type=0).order_by(
                    'index')
                category.title_banners = title_banners

                # 获取带图片的数据
                image_banners = IndexCategoryGoodsBanner.objects.filter(category=category, display_type=1).order_by(
                    'index')
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


class DetailView(BaseCart):
    """商品详情页的视图函数"""

    # 需要的数据
    # 1.商品的类别
    # 2.当前商品的sku
    # 3.当前商品的spu（当前类别其他商品的sku）
    # 4.新品推荐商品
    # 5.商品的评论信息
    # 6.购物车的商品信息

    def get(self, request, sku_id):
        # 先从缓存中获取数据
        context = cache.get("detail_%s" % sku_id)

        if context is None:
            try:
                # 获取当前商品的sku
                sku = GoodsSKU.objects.get(id=sku_id)
            except GoodsSKU.DoesNotExist:
                return redirect(reverse('goods:index'))

            # 获取所有的商品类别
            categorys = GoodsCategory.objects.all()

            # 从订单中获取评论信息，评论存在多个订单中
            sku_orders = sku.ordergoods_set.all().order_by('-create_time')[0:30]
            if sku_orders:
                for sku_order in sku_orders:
                    sku_order.ctime = sku_order.create_time.strftime('%Y-%m-%d %H:%M:%S')
                    sku_order.username = sku_order.order.user.username
            else:
                sku_orders = []

            # 获取新品推荐的商品
            new_skus = GoodsSKU.objects.filter(category=sku.category).order_by('-create_time')[0:2]

            # 获取其他规格的商品
            other_skus = sku.goods.goodssku_set.exclude(id=sku_id)

            context = {
                "categorys": categorys,
                "sku": sku,
                "orders": sku_orders,
                "new_skus": new_skus,
                "other_skus": other_skus
            }

            # 设置缓存
            cache.set("detail_%s" % sku_id, context, 3600)

        # 获取购物车的商品数量
        cart_num = self.get_cart_num(request)

        context['cart_num'] = cart_num

        # 用户登入
        if request.user.is_authenticated():
            # 获取用户对象
            user = request.user
            # 从redis中获取购物车的信息
            redis_conn = get_redis_connection('default')

            # 把之前相同的商品记删除
            redis_conn.lrem('history_%s' % user.id, 0, sku_id)
            # 把当前商品添加到历史记录
            redis_conn.lpush('history_%s' % user.id, sku_id)
            # 最多只保存5条商品记录，ltrim截取前5个，删除其余的记录
            redis_conn.ltrim('history_%s' % user.id, 0, 4)

        return render(request, 'detail.html', context)


class ListView(BaseCart):

    def get(self, request, category_id, page_num):
        # 1.商品的排序方式 默认defaul 价格price 人气hot
        # 2.当前的类别
        # 3.所有的类别
        # 4.新品推荐
        # 5.当前类别里的所有商品
        # 6.购物车数据
        # 分页的页码列表

        # 获取商品的排序方式
        sort = request.GET.get('sort')

        # 获取当前的类别
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return redirect(reverse('goods:index'))

        # 获取所有的商品类别
        categorys = GoodsCategory.objects.all()

        # 新品推荐
        new_skus = GoodsSKU.objects.filter(category=category).order_by('-create_time')[0:2]

        # 当前类别里的所有商品
        if sort == 'prcice':
            skus = GoodsSKU.objects.filter(category=category).order_by('price')
        elif sort == 'got':
            skus = GoodsSKU.objects.filter(category=category).order_by('-sales')
        else:
            skus = GoodsSKU.objects.filter(category=category)

        # 对当前类别下的所有商品进行分类
        paginator = Paginator(skus, 1)
        pagenum = int(page_num)

        # 获取当前页的数据
        try:
            skus_page = paginator.page(pagenum)
        except EmptyPage:
            pagenum = 1
            skus_page = paginator.page(pagenum)

        # 分页按钮显示数字的逻辑
        if paginator.num_pages <= 5:
            page_list = paginator.page_range
        elif pagenum <= 3:
            page_list = range(1, 6)
        elif paginator.num_pages - pagenum <= 2:
            page_list = range(paginator.num_pages - 4, paginator.num_pages + 1)
        else:
            page_list = range(pagenum - 2, pagenum + 3)

        context = {
            'sort': sort,
            'category': category,
            'categorys': categorys,
            'new_skus': new_skus,
            'page_list': page_list,
            'skus_page': skus_page
        }

        # 获取购物车数量
        cart_num = self.get_cart_num(request)

        context['cart_num'] = cart_num

        return render(request, 'list.html', context)

