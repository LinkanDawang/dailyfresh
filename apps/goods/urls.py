#!/usr/bin/python
# -*- coding:utf-8 -*-

from django.conf.urls import url
from apps.goods import views


urlpatterns = [
    url(r'^index$', views.IndexView.as_view(), name='index'),  # 主页的视图
]

