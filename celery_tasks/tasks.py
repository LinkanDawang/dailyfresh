import os
# os.environ["DJANGO_SETTINGS_MODULE"] = 'dailyfresh.settings'
# import django
# django.setup()
from celery import Celery
from django.conf import settings
from django.core.mail import send_mail
from django.template import loader
from goods.models import GoodsCategory, IndexGoodsBanner, IndexPromotionBanner, IndexCategoryGoodsBanner

# 实例化celery对象   第一个参数为生成任务的文件路径  第二个参数为broker
app = Celery('clelry_tasks.tasks', broker='redis://192.168.3.168:6379/3')


# @app.task
def send_active_mail(recipient_list, user_name, token):
    """发送激活邮件"""
    html_body = '<h1>尊敬的用户 %s, 感谢您注册天天生鲜！</h1>' \
                '<br/><p>请点击此链接激活您的帐号<a href="http://127.0.0.1:8000/users/activate/%s">' \
                'http://127.0.0.1:8000/users/activate/%s</a></p>' % (user_name, token, token)

    # 参数1：邮件标题
    # 参数2：邮件内容 必须是纯文本内容
    # 参数3：传送者
    # 参数4：接收者
    send_mail('生鲜商城账号激活', '', settings.EMAIL_FROM, recipient_list, html_message=html_body)


# @app.task
def generate_index():
    # 查询需要的数据 商品分类 幻灯片 活动
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

    # 把查询到的数据填充到模板李生成一个静态文件
    content = loader.render_to_string('static_index.html', context)

    # 把content保存成一个静态文件
    file_path = os.path.join(settings.STATICFILES_DIRS[0], 'static_index.html')

    with open(file_path, 'w') as f:
        f.write(content)



