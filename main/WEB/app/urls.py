from django.conf.urls import url

from . import views

urlpatterns = [
	url('upload/', views.UploadFile.as_view()),
	url('cancel/', views.get_cancel, name='get_cancel'),
	url('work/', views.work, name='work'),
	url('set_channel/', views.set_channel, name='set_channel'),
	url('download_file/', views.download_file, name='download_file'),
	url('', views.get_index, name='get_index'),
]
