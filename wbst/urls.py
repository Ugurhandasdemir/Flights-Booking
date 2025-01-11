
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register'),

    path('', views.home, name='home'),
    path('get-kalkis-noktalari/', views.get_kalkis_noktalari, name='get_kalkis_noktalari'),
    path('get-varis-noktalari/', views.get_varis_noktalari, name='get_varis_noktalari'),
    path('ucus_bilgileri/', views.ucus_bilgileri, name='ucus_bilgileri'),
    path('bilet-al/<int:ucus_id>/', views.bilet_al, name='bilet_al'),

    path('musteri-bilgisi-kaydet/<int:ucus_id>/', views.musteri_bilgisi_kaydet, name='musteri_bilgisi_kaydet'),
    path('koltuk-sec/<int:ucus_id>/', views.koltuk_sec, name='koltuk_sec'),

    path('odeme/<int:bilet_id>/', views.odeme, name='odeme'),
    path('odeme/ozet/<int:bilet_id>/', views.odenmis_bilet_ozet, name='odemis_bilet_ozet'),
    path('bilet-sorgulama/', views.bilet_sorgulama, name='bilet_sorgulama'),
    path('bilet-iptal/<int:bilet_id>/', views.bilet_iptal, name='bilet_iptal'),
]
