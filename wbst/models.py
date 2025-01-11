from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

class Ucus(models.Model):
    ucus_id = models.AutoField(primary_key=True)
    kalıs = models.CharField(max_length=100)
    varıs = models.CharField(max_length=100)
    kalkis_saati = models.DateTimeField()
    fiyat = models.DecimalField(max_digits=10, decimal_places=2)
    toplam_sure = models.DurationField()
    ucak_tipi = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.kalıs} → {self.varıs}"


class Musteri(models.Model):
    musteri_id = models.AutoField(primary_key=True)
    isim = models.CharField(max_length=100)
    soyisim = models.CharField(max_length=100)
    telefon = models.CharField(max_length=15)
    email = models.EmailField()  # unique=True kaldırıldı
    dogum_tarihi = models.DateField()
    cinsiyet = models.BooleanField(choices=[(True, 'Erkek'), (False, 'Kadın')])

    def __str__(self):
        return f"{self.isim} {self.soyisim}"


class Bilet(models.Model):
    bilet_id =  (models.AutoField(primary_key=True))
    bilet_no = models.CharField(max_length=100, unique=True)
    fiyat = models.DecimalField(max_digits=10, decimal_places=2)
    ucus = models.ForeignKey(Ucus, on_delete=models.CASCADE, related_name='biletler')
    koltuk = models.CharField(max_length=5)
    tarih = models.TimeField()
    musteri = models.ForeignKey(Musteri, on_delete=models.CASCADE, null=True, blank=True, related_name='biletler')

    # Yeni: Durum alanı
    DURUM_SECENEKLERI = [
        ('Beklemede', 'Beklemede'),
        ('Ödendi', 'Ödendi'),
        ('İptal', 'İptal'),
        ('Tamamlandi', 'Tamamlandı'), 
    ]

    durum = models.CharField(
        max_length=20,
        choices=DURUM_SECENEKLERI,
        default='Beklemede'
    )

    def clean(self):
        # Aynı uçuşta aynı koltuk zaten dolu mu?
        if Bilet.objects.filter(ucus=self.ucus, koltuk=self.koltuk).exists():
            raise ValidationError(f"{self.koltuk} numaralı koltuk zaten dolu!")

    def __str__(self):
        return f"Bilet No: {self.bilet_no} - Koltuk: {self.koltuk} - Durum: {self.durum}"


class Odeme(models.Model):
    odeme_id = models.AutoField(primary_key=True)
    bilet = models.OneToOneField(Bilet, on_delete=models.CASCADE, related_name='odeme')
    kart_sahibi = models.CharField(max_length=100)
    kart_numarasi = models.CharField(max_length=16)
    son_kullanma_tarihi = models.CharField(max_length=5)  # "12/25"
    cvc = models.CharField(max_length=4)
    odeme_tutari = models.DecimalField(max_digits=10, decimal_places=2)
    odeme_tarihi = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Ödeme #{self.odeme_id} - Bilet {self.bilet.bilet_no}"
