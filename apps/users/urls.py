#!/usr/bin/python
# -*- coding:utf-8 -*-

from django.conf.urls import url
from apps.users import views


urlpatterns = [
    url(r'^register$', views.RegisterView.as_view(), name='register'),  # 注册视图
    url(r'^login$', views.LoginView.as_view(), name='login'),  # 登入视图
    url(r'^logout$', views.LogoutView.as_view(), name='logout'),  # 登入视图
    url(r'^activate/(?P<token>.+)$', views.ActivateView.as_view(), name='activate'),  # 激活用户视图
    url(r'^address$', views.AddressView.as_view(), name='address'),  # 个人中心收货地址
    url(r'^userinfo', views.UserinfoView.as_view(), name='info'),  # 个人中心收货地址
]



