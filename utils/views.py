from functools import wraps

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.utils.decorators import classonlymethod


# 用来验证是否登录的类 需要就继承
class LoginRequiredMixin(object):
    # 用于验证是否登入的工具类
    @classonlymethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)

        return login_required(view)


# 定义一个装饰器,装饰视图函数,判断是否登入,如果没有登入返回json数据
def Login_Required_Json(view_func):
    @wraps(view_func)  # 恢复view_fun的名字和文档
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated():
            return view_func(request, *args, **kwargs)
        else:
            return JsonResponse({'code': 1, 'msg': '用户未登录'})
    return wrapper


# 用于验证是否需要登入的类 需要就继承
class LoginRequiredJsonMixin(object):
    @classonlymethod
    def as_view(cls, **initkwargs):
        # 调用父类as_view
        view = super().as_view(**initkwargs)
        return Login_Required_Json(view)


# 用于添加事务的类
class TransactionAtomicMixin(object):
    @classonlymethod
    def as_view(cls, **initkwargs):
        # 调用父类的as_view
        view = super().as_view(**initkwargs)
        return transaction.atomic(view)

