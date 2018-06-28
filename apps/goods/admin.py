from django.contrib import admin
from django.core.cache import cache
from celery_tasks.tasks import generate_index
from celery_tasks.itsme import static_index
from goods.models import GoodsCategory, Goods, GoodsSKU, IndexGoodsBanner, IndexCategoryGoodsBanner, \
    IndexPromotionBanner


class BaseAdmin(admin.ModelAdmin):
    # 后台admin页面修改数据时会走下面的方法
    # 修改数据后需要从新生成静态主页，并且删除缓存李的数据
    def save_model(self, request, obj, form, change):
        obj.save()
        # generate_index.sl().delay()
        static_index.si().delay()
        cache.delete('index_cache_data')
        print('在后台修改了数据')

    def delete_model(self, request, obj):
        obj.save()
        # generate_index.si().delay()
        static_index.si().delay()
        cache.delete('index_cache_data')
        print('在后台删除了数据')


class GoodsCategoryAdmin(BaseAdmin):
    pass


class GoodsAdmin(BaseAdmin):
    pass


class GoodsSKUAdmin(BaseAdmin):
    pass


class IndexGoodsBannerAdmin(BaseAdmin):
    pass


class IndexCategoryGoodsBannerAdmin(BaseAdmin):
    pass


class IndexPromotionBannerAdmin(BaseAdmin):
    pass


admin.site.register(GoodsCategory, GoodsCategoryAdmin)
admin.site.register(Goods, GoodsAdmin)
admin.site.register(GoodsSKU, GoodsSKUAdmin)
admin.site.register(IndexGoodsBanner, IndexGoodsBannerAdmin)
admin.site.register(IndexCategoryGoodsBanner, IndexCategoryGoodsBannerAdmin)
admin.site.register(IndexPromotionBanner, IndexPromotionBannerAdmin)

