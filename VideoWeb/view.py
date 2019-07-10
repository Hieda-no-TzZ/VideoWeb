from django.http import HttpResponse
from django.shortcuts import render, redirect
import boto
import boto.s3.connection
from . import video2frames
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import os

access_key = ''
secret_key = ''

class Video:

    def __init__(self, name, desc, url, size, modify):
        self.name = name
        self.desc = desc
        self.url = url
        self.size = size
        self.modify = modify
        self.poster = 'img/'+desc + '@' + name+'.jpg'

conn = boto.connect_s3(
        aws_access_key_id = access_key,
        aws_secret_access_key = secret_key,
        host = '<host-address>',
        port = 7480,
        is_secure=False,               # uncomment if you are not using ssl
        calling_format = boto.s3.connection.OrdinaryCallingFormat(),
        )

def index(request):
    video_list = getVideoList()
    return render(request, 'index.html', {'video_list':video_list})

def upload(request):
    return render(request, 'upload.html')

def manage(request):
    video_list = getVideoList()
    return render(request, 'manage.html', {'video_list':video_list})

def delete(request):
    name = request.GET['name']
    bucket = conn.get_bucket('video_bucket')
    key = bucket.get_key(name)
    key.delete()
    video_list = getVideoList()
    return render(request, 'manage.html', {'video_list':video_list})

def video(request):
    url = request.GET['url']
    return redirect(url)

def show(request):
    url = request.GET['url']
    context = {}
    context['url'] = url
    return render(request, 'show.html', context)

def handle(request):
    desc = request.POST.get('desc', None)
    video = request.FILES.get('inputfile', None)
    video_name = desc + '@' + video.name
    path = default_storage.save('static/' + video_name, ContentFile(video.read()))
    tmp_file = os.path.join(settings.MEDIA_ROOT, path)
    video.seek(0)
    bucket = conn.get_bucket('video_bucket')
    key = bucket.new_key(video_name)
    key.set_contents_from_file(video, policy='public-read')
    # 截图
    video2frames.video2frames('static/' + video_name, 'static/img', output_prefix=video_name, extract_time_points=(10,))
    os.remove('static/' + video_name)
    return render(request, 'upload.html')

def getVideoList():
    bucket = conn.get_bucket('video_bucket')
    video_list = []
    for key in bucket.list():
        name = key.name
        size = int(int(key.size) / 1000000)
        url = key.generate_url(0, query_auth=False)
        modified = key.last_modified
        video = Video(name.split('@')[1], name.split('@')[0], url, size, modified)
        video_list.append(video)
    return video_list