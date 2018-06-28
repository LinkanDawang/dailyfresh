from django.conf.urls import url
from cart import views

urlpatterns = [
    url(r'^add$', views.AddCartView.as_view(), name='add'),  # 添加商品到购物车
]
