# AeroJoint — Genel Proje Değerlendirmesi ve Gelişim Planı
*(Matematiksel modelleme hariç — arayüz, iş akışı mantığı ve kullanılabilirlik odaklı)*

## 0. Önce netleştirilmesi gereken şey: "İddia edilen" vs "Gerçek" durum

Bu planın her maddesini uygularken referans noktanız **kod ve ekran görüntüleri** olmalı, "Proje Kılavuzu" belgesindeki iddialar değil. Önerim: iç kullanım için ayrı bir **"Gerçek Durum Kaydı" (Ground Truth)** belgesi tutun — hangi özellik gerçekten kodda var, hangisi planlanıyor, hangisi sadece fikir aşamasında. Bu, hem ekip içi iletişimi hem de ileride bir denetim/sertifikasyon sürecinde "ne zaman, ne eklendi" sorusuna cevap vermeyi kolaylaştırır. Aşağıdaki plan bu ayrımı koruyarak yazıldı.

---

## 1. Genel Proje Değerlendirmesi

**Güçlü yönler:**
- Kompozit bağlantı analizi gerçek, dar ve değerli bir niş — "her şeyi yapan FEA aracı" değil, spesifik bir mühendislik problemine odaklanmış. Bu iyi bir ürün stratejisi.
- Sertifikasyon diline uygun çıktı formatı (MoS, Hashin/Tsai-Wu, PASS/FAIL) — hedef kullanıcının (stres mühendisi) diliyle konuşuyor.
- Görsel kimlik artık gerçekten profesyonel duruyor (önceki konuşmalarımızda detaylıca işledik).

**Zayıf/riskli yönler:**
- İddia edilen özellik seti ile gerçek kod arasındaki fark (Bölüm 0) — bu, teknik değil ama ürün/güven riski.
- Doğrulama/validasyon eksikliği (matematik incelememizde detaylandırdık) — burada tekrar etmiyorum ama bu planın "kullanım" boyutunu da etkiliyor: kullanıcı bir sonuca ne kadar güvenebileceğini bilmiyor.
- Tek-kullanıcı, tek-oturumluk bir araç gibi tasarlanmış görünüyor — kurumsal bir mühendislik ekibinin ihtiyaç duyacağı iş akışı unsurları (proje kaydetme, versiyon, onay süreci) henüz konuşulmadı. Bu planın asıl odağı burası.

---

## 2. Mantıksal / İş Akışı Sorunları

Bu bölüm, arayüzün "güzel görünmesi"nden bağımsız olarak, **bir mühendislik ekibinin gerçekte nasıl çalıştığıyla** ilgili eksikler.

### 2.1 Proje/Oturum Yönetimi Eksik

**Sorun:** Şu ana kadar gördüğümüz her ekran görüntüsü, tek bir "canlı" analiz durumunu gösteriyor. Kullanıcı sayfayı kapatırsa/yenilerse girdiği 16 katman, delik koordinatları, malzeme seçimleri kayboluyor mu? Bir mühendis aynı anda 5 farklı bağlantıyı (farklı bracket'ler) analiz ediyorsa, bunları nasıl ayrı ayrı saklayıp geri çağıracak?

**Çözüm:**
- **"Proje" kavramı** eklenmeli: kullanıcı bir analiz konfigürasyonunu (geometri + laminate + malzeme + yük) isimlendirip kaydedebilmeli ("Kanat-Gövde-Braket-A Rev2" gibi).
- Kayıtlı projeler listesi (son değiştirilme tarihi, kim tarafından, hangi durumda — PASS/FAIL) ile bir "Projelerim" ana ekranı.
- **Otomatik taslak kaydetme (autosave):** kullanıcı form doldururken tarayıcı çökse/kapansa bile son durum kurtarılabilmeli — mühendislik yazılımlarında bu, kullanıcı güvenini kazanan temel bir detay.

### 2.2 Değişiklik/Versiyon Geçmişi ve İzlenebilirlik

**Sorun:** Sertifikasyon amaçlı bir araçta "bu PASS sonucu tam olarak hangi girdilerle, hangi yazılım versiyonuyla, ne zaman üretildi" sorusuna cevap verebilmek zorunludur (traceability). Şu anki akışta bu bilgi kalıcı görünmüyor.

**Çözüm:**
- Her analiz çalıştırıldığında, o anki **tüm girdi seti + yazılım/motor versiyon numarası + zaman damgası + kullanıcı** ile birlikte **değişmez (immutable)** bir kayıt oluşturulmalı.
- PDF raporun içine bu meta veri (versiyon, tarih, kullanıcı) otomatik basılmalı — zaten muhtemelen basılıyordur ama arayüzde de bu geçmişe erişim (bir "Analiz Geçmişi" sekmesi, o projenin daha önce hangi versiyonlarla çalıştırıldığını gösteren bir liste) olmalı.
- Bir mühendis "geçen ay çalıştırdığım analizle şimdiki neden farklı sonuç veriyor" diye sorduğunda, cevap arayüzden bulunabilmeli, Slack/e-posta arşivinden değil.

### 2.3 Doğrulama/Girdi Sırası Mantığı

**Sorun:** Şu anki form akışında (katman ekle → geometri gir → delik ekle → analiz çalıştır), kullanıcı eksik/tutarsız bir konfigürasyonla (örn. hiç katman eklemeden, ya da delik plaka sınırları dışında bir X/Y ile) "Analiz Et"e basarsa ne oluyor? Ekran görüntülerinde bir hata durumu görmedik.

**Çözüm:**
- **Aşamalı doğrulama (progressive validation):** her adımda (katman eklerken, delik koordinatı girerken) anlık, alan-bazlı doğrulama — örn. delik X koordinatı plaka genişliğinden büyükse input kutusu kırmızı kenarlıkla anında uyarsın, "Analiz Et" butonuna kadar beklemeden.
- **"Analiz Et" öncesi özet kontrol listesi:** buton tıklanmadan hemen önce (ya da tıklandığında ilk adım olarak), eksik/şüpheli girdileri toplayan bir kontrol — "0 katman tanımlı", "Delik #2 plaka sınırları dışında", "Sınır koşulu seçilmedi" gibi. Analiz, bu kontroller geçmeden çalıştırılmamalı.
- Bu, hem kullanıcı deneyimini hem de -daha önce motor incelemesinde bahsettiğimiz- e/D, s/D gibi geometrik kısıt kontrollerini doğal olarak barındıracağı yer.

### 2.4 Malzeme Kütüphanesi Yönetişimi

**Sorun:** "Malzeme Kütüphanesi" butonu var ama bu kütüphaneyi kim yönetiyor? Bir mühendis yanlışlıkla (ya da bilerek ama hatalı) bir malzemenin Xt/Xc değerini değiştirirse, bu değişiklik o an açık olan tüm analizleri, hatta geçmiş kayıtlı analizleri de mi etkiliyor?

**Çözüm:**
- Malzeme kayıtları da **versiyonlanmalı** — bir analiz, "T300/5208 v3" gibi belirli bir malzeme versiyonuna kilitlenmeli; kütüphanede sonradan yapılan bir değişiklik, geçmiş analiz sonuçlarını sessizce değiştirmemeli.
- Malzeme kütüphanesine yazma yetkisi, standart kullanıcıdan ayrı bir rol (örn. "Malzeme Sorumlusu") ile sınırlandırılabilir — kurumsal kullanımda veri bütünlüğü için önemli.

### 2.5 Hata Durumları ve Backend Başarısızlıkları

**Sorun:** Daha önce konuştuğumuz asenkron mimaride (3D içe aktarma, toplu analiz), iş parçacıkları (job) başarısız olabilir — CAD kernel çökebilir, solver yakınsamayabilir. Bu belgede ya da ekran görüntülerinde bir "hata" durumunun nasıl göründüğünü hiç görmedik.

**Çözüm:** Her asenkron işlem için üç durumun (başarı, devam ediyor, **başarısız + neden**) arayüzde net, eyleme geçirilebilir şekilde gösterilmesi — "Analiz başarısız: mesh oluşturulamadı, delik #3 çok küçük" gibi teknik ama anlaşılır mesajlar, sessiz döngü veya belirsiz "Bir hata oluştu" mesajları değil.

---

## 3. Kullanılabilirlik (Usability) Planı

### 3.1 İlk Kullanım Deneyimi (Onboarding)

**Sorun:** Yeni bir mühendis ilk kez açtığında karşısına boş bir form mu çıkıyor, yoksa örnek/şablon bir proje mi? Aracın karmaşıklığı (16 katman, PDM, Hashin/Tsai-Wu, mesh yoğunluğu gibi çok sayıda teknik parametre) düşünülünce, sıfırdan boş form gözü korkutucu olabilir.

**Çözüm:**
- İlk açılışta **örnek bir proje** (önceden doldurulmuş, tipik bir T300/5208 bağlantısı) yüklü gelsin — kullanıcı "değiştirerek öğrensin", boş kutulardan başlamasın.
- Karmaşık/az bilinen parametrelerin yanına (örn. "Mesh Yoğunluğu", "PDM") kısa, teknik ama öz açıklama tooltip'leri — zaten bazı alanların altında küçük açıklamalar var, bunu tüm ileri düzey parametrelere tutarlı şekilde yayın.

### 3.2 Verimlilik Özellikleri (Deneyimli Kullanıcı İçin)

**Sorun:** Mühendisler günde onlarca analiz çalıştırabilir — tekrarlayan işlemler için hız kritik.

**Çözüm:**
- **Klavye kısayolları:** "Analizi Çalıştır" için Ctrl+Enter, yeni katman eklemek için bir kısayol, vb. — güç kullanıcıları fareyle her butona tıklamak zorunda bırakmayın.
- **Kopyala/çoğalt:** mevcut bir projeyi "Farklı Kaydet" ile kopyalayıp küçük bir parametre değişikliğiyle yeni bir varyant oluşturma (örn. aynı laminate, farklı delik konumu) — sıfırdan girmek yerine.
- **Geri al/ileri al (undo/redo):** form üzerinde yapılan değişiklikler için standart Ctrl+Z desteği — özellikle 16 katmanlık bir diziliminin ortasında yanlışlıkla bir satır silindiğinde hayat kurtarır.

### 3.3 Karşılaştırma ve Karar Desteği

**Sorun:** Bir mühendis genelde "A tasarımı mı B tasarımı mı daha iyi" sorusunu sorar (örn. delik çapı 6mm mi 8mm mi olmalı). Şu anki akış, bunu ancak iki ayrı analiz çalıştırıp sonuçları elle karşılaştırarak yapmaya izin veriyor.

**Çözüm:** İki (veya daha fazla) kayıtlı proje/analiz sonucunu **yan yana karşılaştıran** bir görünüm — MoS, kritik katman, ağırlık gibi metriklerin bir karşılaştırma tablosunda gösterilmesi. Bu, daha önce konuştuğumuz "parametrik tarama" özelliğinin daha basit, manuel bir ön-versiyonu olarak da düşünülebilir; ikisi aynı UI bileşenini (karşılaştırma tablosu) paylaşabilir.

### 3.4 Rapor ve Paylaşım Akışı

**Sorun:** "PDF Rapor" butonu var ama bu rapor kiminle, nasıl paylaşılıyor? Bir kalite/sertifikasyon sorumlusunun bu raporu inceleyip onaylaması gerekiyorsa, bu onay süreci araç içinde mi yoksa dışında (e-posta ile) mı yürüyor?

**Çözüm (ileri düzey, isteğe bağlı):** Basit bir **"İnceleme Durumu"** alanı — bir analiz sonucu "Taslak / İncelemede / Onaylandı" durumlarından birinde olabilir, onaylayan kişinin adı ve tarihi kayıt altına alınır. Bu, tam bir onay iş akışı motoru kurmadan da, mevcut PDF-e-posta pratiğine hafif bir iz sürülebilirlik katmanı ekler.

### 3.5 Boş/Yükleniyor Durumları (Empty & Loading States)

**Sorun:** Analiz çalışmadan önce sonuç paneli ne gösteriyor — boş mu, yer tutucu mu? Bu, "profesyonel araç" hissinin gözden kaçan ama etkili bir parçası.

**Çözüm:** Analiz henüz çalıştırılmamışken sonuç paneli, boş bir kutu yerine **"Henüz analiz çalıştırılmadı — parametreleri girip Analiz Et'e basın"** gibi yönlendirici bir boş-durum illüstrasyonu/mesajı göstersin. Bu küçük bir detay ama ilk izlenimde araç "bozuk" hissi vermemesi için önemli.

---

## 4. Öncelik Sıralı Özet

| # | Konu | Kategori | Efor | Öncelik | Not |
|---|---|---|---|---|---|
| 1 | Doküman/gerçeklik uyumsuzluğunu gidermek | Bütünlük/Risk | Düşük (yazı işi) | **En yüksek** | Teknik değil ama en acil — yanlış iddialarla dışarı çıkmayın |
| 2 | Proje kaydetme + autosave | İş akışı | Orta | Yüksek | Şu an "tek oturumluk araç" hissi veriyor, kurumsal kullanım için temel |
| 3 | Analiz öncesi doğrulama + hata durumları | İş akışı | Orta | Yüksek | Kullanıcı güveni ve zaman kaybı önleme açısından kritik |
| 4 | Versiyon/izlenebilirlik kaydı | İş akışı | Orta-Yüksek | Yüksek (sertifikasyon bağlamında) | Motor incelemesindeki "Metodoloji Şeffaflığı" ile birleştirilebilir |
| 5 | Malzeme kütüphanesi versiyonlama/yetkilendirme | İş akışı | Orta | Orta | Veri bütünlüğü riski, ama acil değilse ötelenebilir |
| 6 | Onboarding (örnek proje + tooltip'ler) | Kullanılabilirlik | Düşük | Orta | Düşük efor, yeni kullanıcı deneyimini belirgin iyileştirir |
| 7 | Undo/redo, kopyala/çoğalt, kısayollar | Kullanılabilirlik | Orta | Orta | Güç kullanıcı verimliliği |
| 8 | Karşılaştırma görünümü | Kullanılabilirlik | Orta-Yüksek | Düşük-Orta | Parametrik tarama özelliğiyle birleştirilebilir |
| 9 | Rapor onay/inceleme durumu | İş akışı | Düşük-Orta | Düşük | İsteğe bağlı, kurum sürecine göre değişir |
| 10 | Boş/yükleniyor durumları | Kullanılabilirlik | Düşük | Düşük ama hızlı kazanım | Küçük efor, algıyı iyileştirir |

**Genel öneri:** 2, 3 ve 4 numaralı maddeler (proje kaydetme, doğrulama, izlenebilirlik) aslında birbirine bağlı bir "temel altyapı" grubu — üçü birlikte ele alınırsa, aracı "demo/prototip" hissinden "kurumsal araç" hissine taşıyan asıl eşik burası olur. Görsel kimlik ve 3D içe aktarma gibi önceki planlarımız bu temel olmadan da değerli, ama bu temel olmadan araç gerçek bir mühendislik ekibinde günlük kullanıma geçemez.
