from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
import uuid
from django.db import connection, transaction
from datetime import timedelta
from .models import Ucus, Musteri, Bilet, Odeme
from .forms import SignUpForm


def home(request):
    # Tüm uçuşları anasayfaya göster
    ucuslar = Ucus.objects.all()

    # Bilet sorgulama sonucu için bir değişken
    bilet_bilgisi = None

    return render(request, 'home.html', {
        'ucuslar': ucuslar,
        'bilet_bilgisi': bilet_bilgisi,  # Varsayılan None
    })


def bilet_sorgulama(request):

    bilet_bilgisi = None

    if request.method == 'POST':
        bilet_no = request.POST.get('bilet_no')
        try:
            #sayfadan alınan bilet no su ile veritabanı sorguluyor
            bilet_bilgisi = Bilet.objects.select_related('ucus', 'musteri').get(bilet_no=bilet_no)
        except Bilet.DoesNotExist:
            messages.error(request, "Böyle bir bilet bulunamadı ya da iptal edilmiş olabilir.")
    #uçuşla ilgili bilgileri çek
    ucuslar = Ucus.objects.all()
    return render(request, 'home.html', {
        'ucuslar': ucuslar,
        'bilet_bilgisi': bilet_bilgisi
    })


def bilet_iptal(request, bilet_id):
    with connection.cursor() as cursor:
        try:
            #bilet iptal edildimi edilmedi mi ?
            cursor.execute("""
                DECLARE @sonuc NVARCHAR(50);
                EXEC sp_BiletOdemeDurumuGuncelle 
                    @bilet_id = %s,
                    @islem_sonucu = @sonuc OUTPUT;
                SELECT @sonuc;
            """, [bilet_id])

            sp_sonuc = cursor.fetchone()
            if sp_sonuc:
                sp_sonuc = sp_sonuc[0]

            messages.info(request, sp_sonuc)

            if sp_sonuc and "başarıyla iptal edildi" in sp_sonuc.lower():
                #iptal edildi şeklinde güncelle
                Bilet.objects.filter(bilet_id=bilet_id).update(durum='İptal Edildi')
        except Exception as e:
            messages.error(request, f"İptal işleminde hata: {str(e)}")

    return redirect('home')


def login_user(request):
    if request.method == "POST":
        # Formdan gelen kullanıcı adı ve şifreyi al
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        # Eğer kullanıcı adı ve şifre doğru ise giriş yap ve anasayfaya yönlendir
        if user:
            login(request, user)
            messages.success(request, 'Giriş yapıldı')
            return redirect('home')
        # Eğer bilgiler yanlış ise kayıt ekranına yönlendir
        else:
            messages.error(request, 'Yanlış kullanıcı adı veya şifre ')
            return redirect('login')
    return render(request, 'login.html', {})


def logout_user(request):
    # Çıkış yap ve anasayfaya yönlendir.
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('home')


def register_user(request):
    # Kayıt olma
    form = SignUpForm()  # Boş bir form oluştur
    if request.method == "POST":
        form = SignUpForm(request.POST)
        # Tüm alanlar doğru doldurulmuş mu diye kontrol et
        if form.is_valid():
            user = form.save()  # Yeni kullanıcı
            login(request, user)  # Giriş Yap otomatik
            messages.success(request, "Başarıyla kayıt olundu")
            return redirect('home')
        else:
            messages.error(request, "Bir hata oluştu. Tekrar deneyiniz.")
    return render(request, 'register.html', {'form': form})


def get_kalkis_noktalari(request):
    # Kalkış noktalarını döndürür
    with connection.cursor() as cursor:
        cursor.execute("EXEC GetKalkisNoktalari")
        kalkis_noktalari = [row[0] for row in cursor.fetchall()]
    return JsonResponse({'kalkis_noktalari': kalkis_noktalari})


def get_varis_noktalari(request):
    # Varış noktalarını döndürür
    kalkis_noktasi = request.GET.get('from', None)
    if kalkis_noktasi:
        with connection.cursor() as cursor:
            cursor.execute("EXEC GetVarisNoktalari @Kalkis=%s", [kalkis_noktasi])
            varis_noktalari = [row[0] for row in cursor.fetchall()]
        return JsonResponse({'varis_noktalari': varis_noktalari})
    return JsonResponse({'varis_noktalari': []})


def ucus_bilgileri(request):
    if request.method == 'POST':
        # Gelen iniş ve kalkış bilgilerini al
        kalkis = request.POST.get('from')
        varis = request.POST.get('to')
        departure_date = request.POST.get('departure_date')

        # Veri tabanından uçuş bilgilerini çek
        with connection.cursor() as cursor:
            #HesaplaUcusSuresi fonk çağırılıyor
            cursor.execute(""" 
                SELECT ucus_id, kalıs, varıs, kalkis_saati, fiyat, ucak_tipi,
                       dbo.HesaplaUcusSuresi(kalkis_saati, DATEADD(HOUR, 3, kalkis_saati)) AS ucus_suresi
                FROM dbo.wbst_ucus
                WHERE kalıs = %s 
                  AND varıs = %s
                  AND CAST(kalkis_saati AS DATE) = %s
            """, [kalkis, varis, departure_date])

            ucuslar = [
                {
                    'ucus_id': row[0],
                    'kalıs': row[1],
                    'varıs': row[2],
                    'kalkis_saati': row[3],
                    'fiyat': row[4],
                    'ucak_tipi': row[5],
                    'ucus_suresi': row[6]
                }
                for row in cursor.fetchall()
            ]

        return render(request, 'ucus_bilgileri.html', {'ucuslar': ucuslar})

    return render(request, 'ucus_bilgileri.html', {'ucuslar': []})


def call_sp_create_musteri(isim, soyisim, telefon, email, dogum_tarihi, cinsiyet, bilet_no):
    try:
        with connection.cursor() as cursor:
            # Müşteri oluşturma sp'sini kullanarak müşteri oluşturuyor
            cursor.execute("""
                DECLARE @musteriID INT;
                EXEC spCreateMusteri 
                    @pIsim=%s, 
                    @pSoyisim=%s, 
                    @pTelefon=%s, 
                    @pEmail=%s, 
                    @pDogumTarihi=%s, 
                    @pCinsiyet=%s, 
                    @bilet_no=%s, 
                    @pmusteri_id=@musteriID OUTPUT;
                SELECT @musteriID;
            """, [isim, soyisim, telefon, email, dogum_tarihi, cinsiyet, bilet_no])

            musteri_id = cursor.fetchone()
            print({musteri_id})
            # Müşteri id oluştuysa dön
            if musteri_id and musteri_id[0]:
                return musteri_id[0]
            else:
                raise ValueError("SP müşteri ID döndürmedi")
    except Exception as e:
        print(f"SP başarısız {str(e)}")
        raise ValueError(f"SP hatası: {str(e)}")


def musteri_bilgisi_kaydet(request, ucus_id):
    # Uçuş bilgilerini getir, yoksa 404 hatası ver
    ucus = get_object_or_404(Ucus, pk=ucus_id)

    if request.method == 'POST':
        isim = request.POST.get('isim')
        soyisim = request.POST.get('soyisim')
        telefon = request.POST.get('telefon')
        email = request.POST.get('email')
        dogum_tarihi = request.POST.get('dogum_tarihi')
        cinsiyet = request.POST.get('cinsiyet')

        print(f"Formdan Gelen Veriler: İsim: {isim}, Soyisim: {soyisim}, Telefon: {telefon}, E-posta: {email}, Doğum: {dogum_tarihi}, Cinsiyet: {cinsiyet}")

        # Eksik veri var mı kontrol et
        if not (isim and soyisim and telefon and email and dogum_tarihi and cinsiyet):
            messages.error(request, "Lütfen tüm bilgileri eksiksiz doldurun!")
            return redirect('musteri_bilgisi_kaydet', ucus_id=ucus_id)

        cinsiyet_bool = True if cinsiyet == "True" else False  # True -> 1, False -> 0

        # Rasgele bilet no oluştur
        bilet_no = f"BLT-{uuid.uuid4().hex[:6].upper()}"
        request.session['bilet_no'] = bilet_no  # Bilet numarasını session'a kaydet

        try:
            # Create Musteri SP kullanarak musteri oluştur
            musteri_id = call_sp_create_musteri(isim, soyisim, telefon, email, dogum_tarihi, cinsiyet_bool, bilet_no)
            request.session['musteri_id'] = musteri_id

            messages.success(request, f"Müşteri kaydedildi Müşteri ID: {musteri_id}, Bilet No: {bilet_no}")
            # Koltuk sec sayfasına yönlendir
            return redirect('koltuk_sec', ucus_id=ucus_id)
        except Exception as e:
            messages.error(request, f"Müşteri kaydedilirken hata oluştu: {str(e)}")
            print(f" HATA: {str(e)}")

    return render(request, 'musteri_bilgileri.html', {'ucus': ucus})


@transaction.atomic
def koltuk_sec(request, ucus_id):
    # Uçuş bilgilerini getir
    ucus = get_object_or_404(Ucus, pk=ucus_id)

    # 1 den 10'a kadar koltuk belirt
    seat_rows = range(1, 11)
    seat_cols = ['A', 'B', 'C', 'D', 'E', 'F']

    # Dolu Koltukları veritabanından çek
    dolu_koltuklar = Bilet.objects.filter(ucus=ucus).values_list('koltuk', flat=True)
    dolu_koltuk_set = set(dolu_koltuklar)

    # Koltuk haritasını oluştur
    seat_map = []
    for row in seat_rows:
        row_list = []
        for col in seat_cols:
            seat_name = f"{row}{col}"
            row_list.append({
                'name': seat_name,
                'dolu': seat_name in dolu_koltuk_set
            })
        seat_map.append(row_list)

    # Boş koltuk sayısını BosKoltukSayisi fonksiyonu ile getir
    with connection.cursor() as cursor:
        cursor.execute("SELECT dbo.BosKoltukSayisi(%s)", [ucus_id])
        bos_koltuk_sayisi = cursor.fetchone()[0]

    if request.method == 'POST':
        email = request.POST.get('email')
        secilen_koltuk = request.POST.get('koltuk')

        if not email:
            messages.error(request, "E-posta bilgisi eksik. Lütfen e-posta adresinizi giriniz.")
            return redirect('koltuk_sec', ucus_id=ucus_id)

        if not secilen_koltuk:
            messages.error(request, "Koltuk seçilmedi!")
            return redirect('koltuk_sec', ucus_id=ucus_id)

        try:
            with connection.cursor() as cursor:
                # Fonksiyon kullanarak koltuk boş mu dolu mu kontrol et
                cursor.execute("SELECT dbo.koltuk_bos_mu(%s, %s)", [ucus_id, secilen_koltuk])
                is_available = cursor.fetchone()[0]  # 0 = Dolu, 1 = Boş

            if is_available == 0:
                messages.error(request, "Seçilen koltuk şu anda dolu.")
                return redirect('koltuk_sec', ucus_id=ucus_id)

            # Eğer koltuk boşsa bileti oluştur
            bilet_no = f"BLT-{uuid.uuid4().hex[:6].upper()}"
            musteri_id = request.session.get('musteri_id')

            bilet = Bilet(
                bilet_no=bilet_no,
                fiyat=ucus.fiyat,
                ucus=ucus,
                koltuk=secilen_koltuk,
                tarih=ucus.kalkis_saati.time(),
                musteri_id=musteri_id
            )
            bilet.full_clean()
            bilet.save()

            messages.success(request, f"{secilen_koltuk} koltuğu başarıyla seçildi. Bilet No: {bilet_no}")
            return redirect('odeme', bilet_id=bilet.bilet_id)

        except Exception as e:
            messages.error(request, f"Koltuk seçilemedi: {str(e)}")
            return redirect('koltuk_sec', ucus_id=ucus_id)

    context = {
        'ucus': ucus,
        'seat_map': seat_map,
        'bos_koltuk_sayisi': bos_koltuk_sayisi
    }
    return render(request, 'koltuk_sec.html', context)


def odeme(request, bilet_id):
    bilet = get_object_or_404(Bilet, pk=bilet_id)

    if request.method == 'POST':
        kart_sahibi = request.POST.get('kart_sahibi')
        kart_numarasi = request.POST.get('kart_numarasi')
        son_kullanma_tarihi = request.POST.get('son_kullanma_tarihi')
        cvc = request.POST.get('cvc')
        odeme_tutari = bilet.fiyat

        try:
            # CreateOdeme SP ile ödeme oluştur
            with connection.cursor() as cursor:
                cursor.execute(""" 
                    EXEC spCreateOdeme 
                        @pBiletID = %s, 
                        @pKartSahibi = %s, 
                        @pKartNumarasi = %s, 
                        @pSonKullanma = %s, 
                        @pCvc = %s, 
                        @pOdemeTutari = %s
                """, [bilet.bilet_id, kart_sahibi, kart_numarasi, son_kullanma_tarihi, cvc, odeme_tutari])

            messages.success(request, "Ödeme başarıyla tamamlandı.")
            return redirect('odemis_bilet_ozet', bilet_id=bilet.bilet_id)
        except Exception as e:
            messages.error(request, f"Ödeme sırasında hata: {str(e)}")
            return redirect('odeme', bilet_id=bilet.bilet_id)

    return render(request, 'odeme.html', {'bilet': bilet})


def bilet_al(request, ucus_id):
    ucus = get_object_or_404(Ucus, pk=ucus_id)
    return render(request, 'musteri_bilgileri.html', {'ucus': ucus})


def hesapla_ucus_suresi(kalkis_saati):

    # varsayılan uçuş süresini 2 saat
    varsayilan_ucus_suresi = timedelta(hours=2)
    varis_saati = kalkis_saati + varsayilan_ucus_suresi
    return varis_saati


def odenmis_bilet_ozet(request, bilet_id):
    # Bilet ve ilişkili uçuş bilgilerini al
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT bilet_id, bilet_no, koltuk, durum,
                   MusteriAdi, MusteriSoyadi, Kalkis, Varis, KalkisSaati,
                   OdemeTutari
            FROM dbo.vw_OdenmisBiletler
            WHERE bilet_id = %s
        """, [bilet_id])

        bilet_detaylari = cursor.fetchone()

    if bilet_detaylari:
        # Kalkış saatini al ve uçuş süresini hesapla
        kalkis_saati = bilet_detaylari[8]  # Kalkış Saati
        ucus_suresi = hesapla_ucus_suresi(kalkis_saati)

        context = {
            'bilet_detaylari': bilet_detaylari,
            'ucus_suresi': ucus_suresi
        }
    else:
        context = {
            'error': 'Bilet bilgileri bulunamadı.'
        }

    return render(request, 'ozet.html', context)


