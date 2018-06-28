import re
import itsdangerous
from django import db
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import View
from users.models import User, Address
from django.conf import settings
from celery_tasks.tasks import send_active_mail
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from utils.views import LoginRequiredMixin


class RegisterView(View):
    """用户注册视图"""
    def get(self, request):
        """get方法返回页面"""
        return render(request, 'register.html')

    def post(self, request):
        """post方法处理注册逻辑"""
        # 获取用户输入的信息：用户名，密码,邮箱,是否记住用户名
        user_name = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 校验参数完整性
        if not all([user_name, password, email]):
            return redirect(reverse('users:register'))
        # 判断邮箱是否格式正确
        if not re.match('^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式错误'})
        # 用户是否勾选协议
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意用户协议'})

        # 验证通过，在数据库里创建用户
        try:
            user = User.objects.create_user(username=user_name, password=password, email=email)
        except db.IntegrityError:
            return render(request, 'register.html', {'errmsg': '用户名已经被注册'})
        # 创建的用户默认是激活的，需要手动改成未激活状态
        user.is_active = False
        user.save()

        # 生产用户token，包含用户的id，该过程为签名
        token = user.generate_active_token()  # 用于用户激活

        # 向用户邮箱发送激活邮件
        recipient_list = [user.email]

        # 发送邮件是耗时操作，调用异步方法发送激活邮件
        send_active_mail.si(recipient_list, user.username, token).delay()

        # 响应浏览器
        return redirect(reverse('users:login'))


class ActivateView(View):
    """用户激活的视图"""
    def get(self, request, token):
        # 解析token，获取用户id
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            # 解析出来的数据类型为{"confirm": self.id}
            result = serializer.loads(token)
        except itsdangerous.SignatureExpired:
            return HttpResponse('激活超时')

        user_id = result['confirm']

        # 从数据库从查找用户
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return HttpResponse('用户不存在')

        if user.is_active:
            return HttpResponse('用户已被激活')

        # 激活用户
        user.is_active = True
        user.save()

        return redirect(reverse('goods:index'))


class LoginView(View):
    """用户登入"""
    def get(self, request):
        """返回登入页面"""
        return render(request, 'login.html')

    def post(self, request):
        """处理用户登入的逻辑"""
        # 获取用户名和密码
        user_name = request.POST.get('username')
        password = request.POST.get('pwd')
        remembered = request.POST.get('remembered')

        # 校验参数的完整性
        if not all([user_name, password]):
            return redirect(reverse('users:login'))

        # 使用django自带的用户认证方法
        user = authenticate(username=user_name, password=password)

        if user is None:
            return render(request, 'login.html', {'errmsg': '用户名或密码错误'})

        # 判断用户是否已经激活
        if user.is_active is False:
            return render(request, 'login.html', {'errmsg': '用户未激活'})

        # 通过验证，登入用户
        login(request, user)

        # 用户是否勾选记住用户名
        if remembered is None:  # 不记住用户名
            request.session.set_expiry(0)  # 关闭浏览器时清空用户信息
        else:  # 记住用户名
            request.session.set_expiry(None)

        return redirect(reverse('goods:index'))


class LogoutView(View):
    """登出"""
    def get(self, request):
        # 注销登入，清除用户的cookie和Session
        logout(request)

        return redirect(reverse('goods:index'))


class AddressView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user

        try:
            address = user.address_set.latest('create_time')
        except Address.DoesNotExist:
            address = None

        context = {
            'address': address
        }

        return render(request, 'user_center_site.html', context)


class UserinfoView(LoginRequiredMixin, View):
    def get(self, request):

        return render(request, 'user_center_info.html')

