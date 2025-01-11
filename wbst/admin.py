from django.contrib import admin
from .models import Bilet, Musteri, Ucus

class UcusAdmin(admin.ModelAdmin):
    list_display = ('ucus_id', 'kalıs', 'varıs', 'kalkis_saati' , 'fiyat', 'toplam_sure', 'ucak_tipi')

class MusteriAdmin(admin.ModelAdmin):
    list_display = ('isim', 'soyisim', 'telefon', 'email', 'dogum_tarihi', 'cinsiyet')

class BiletAdmin(admin.ModelAdmin):
        list_display = ('bilet_no', 'ucus', 'koltuk', 'durum')
        list_filter = ('durum', 'ucus')


admin.site.register(Ucus, UcusAdmin)
admin.site.register(Bilet)
admin.site.register(Musteri, MusteriAdmin)
