import os
import sys
from django.conf import settings
from django.conf.urls import url
from django.http import HttpResponse,HttpResponseBadRequest
from django.core.wsgi import get_wsgi_application
import hashlib
from django import forms
from io import BytesIO
from PIL import Image,ImageDraw
from django.core.cache import cache
from django.shortcuts import render,reverse
from django.views.decorators.http import etag


'''
设置
'''

'''
使用环境变量来配置（下面的代码也要跟着改）
例如使用时 export/set DEBUG=off
'''
DEBUG = os.environ.get("DEBUG","on")=="on"
ALLOWED_HOSTS=os.environ.get("ALLOWED_HOSTS","localhost").split(',')

# SECRET_KEY = os.environ.get("SECRET_KEY",os.urandom(32))
SECRET_KEY = os.environ.get("SECRET_KEY",'$7n2r7vsp3gkd0qbbzgd!ei(^*02l55jl78^+u6oi41)*lw2p=')
 # 以本文件为项目模板，每次创建新项目会创建一个随机秘钥，这样保证secret_key在项目层面是固定的，项目间是随机的

BASE_DIR = os.path.dirname(__file__)
 
settings.configure(
    DEBUG=True,
    SECRET_KEY='thisisthescretkey',
    ROOT_URLCONF=__name__,
    ALLOWED_HOSTS=[],
    MIDDLEWARE_CLASSES=[
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ],
    INSTALLED_APPS=[
        "django.contrib.staticfiles",
    ],
    TEMPLATES = [
        {
            "BACKEND":"django.template.backends.django.DjangoTemplates",
            "DIRS": [os.path.join(BASE_DIR,'templates'),],
        }
    ],
    STATICFILES_DIRS=[
        os.path.join(BASE_DIR,'static'),
    ],
    STATIC_URL = '/static/',
)




'''
views
'''
class ImageForm(forms.Form):
    height = forms.IntegerField(min_value=1,max_value=2000)
    width = forms.IntegerField(min_value=1,max_value=2000)

    def generate(self,image_format = "PNG"):
        height = self.cleaned_data['height']
        width = self.cleaned_data['width']

        ## 生成缓存key
        key = "{}.{}.{}".format(width,height,image_format)
        content = cache.get(key)

        if content is None:
            image = Image.new('RGB',(width,height))
            draw = ImageDraw.Draw(image)
            text = '{} x {}'.format(width,height)
            tw,th = draw.textsize(text)
            if tw<width and th<height:
                t_top = (height-th)//2
                t_left = (width-tw)//2
                draw.text((t_left,t_top),text,fill=(255,255,255))
            content = BytesIO()
            image.save(content,image_format)
            content.seek(0)
            cache.set(key,content,60*60) #保留60*60 s
        return content


# cache是服务器端缓存 下面来使用 etag客户端缓存
def generate_etag(request,width,height):
    content = "Placeholder:{0} x {1}".format(width,height)
    return hashlib.sha1(content.encode("utf-8")).hexdigest()

@etag(generate_etag)
def placeholder(request,width,height):
    form = ImageForm({'height':height,"width":width})
    if form.is_valid():
       image = form.generate()
       return  HttpResponse(image,content_type="image/png")
    else:
        return HttpResponseBadRequest("Invalid Image Request!")



def index(request):
    example = reverse('placeholder',kwargs={'width':50,"height":50})
    context = {
        "example":request.build_absolute_uri(example)
    }
    return render(request,'home.html',context)



'''
url patterns
'''
urlpatterns = [
    url(r'^image/(?P<width>[0-9]+)x(?P<height>[0-9]+)/$',placeholder,name="placeholder"),#?P语法捕获命名参数
    url(r'^$', index, name="index"),
]




'''
manage project
'''

application =  get_wsgi_application() ##创建 wsgi应用, 这样就能被 WSGI规范的web服务器


if __name__ == '__main__':
   
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


