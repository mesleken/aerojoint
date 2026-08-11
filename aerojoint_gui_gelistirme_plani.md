# AeroJoint — GUI Geliştirme Planı

## 0. Yaklaşım

Mevcut yapı (React + TS + Vite + Tailwind + Plotly) zaten doğru temel. Bu plan kodu değil, **görsel yönü ve bilgi mimarisini** değiştiriyor. Amaç: "web app" hissini atıp gerçek bir mühendislik yazılımı (ANSYS, HyperMesh, CATIA tarzı) hissi vermek — ama günümüz standartlarında temiz ve modern.

Kaçınılacak şey: jenerik "AI tasarımı" kalıpları — krem arka plan + serif başlık + turuncu vurgu; ya da siyah arka plan + tek neon vurgu; ya da gazete tarzı ince çizgili broadsheet. Bunun yerine **kokpit/enstrüman paneli** diline oturan, alana özgü bir kimlik öneriyorum: uçak enstrümanlarındaki yeşil/amber/kırmızı durum kodlaması, dijital okuma göstergeleri (altimetre tarzı rakamlar), hafif mühendislik-çizim gridi. Bu hem "havalı" hem de mühendisin gözüne tanıdık, hem de amaç işlevsel (MoS/hasar durumunu renkle anında okutuyor).

---

## 1. Görsel Kimlik Sistemi

**Renk paleti** (6 ana ton):

| Rol | Hex | Kullanım |
|---|---|---|
| Zemin (base) | `#0E141B` | Ana arka plan — mavi-gri tonlu koyu, saf siyah değil |
| Panel yüzeyi | `#161F29` | Kartlar, sidebar, modal zemini |
| Çizgi/grid | `#26313E` | Kenarlıklar, blueprint gridi, ayraçlar |
| Metin | `#E7EDF3` / `#8FA0B3` | Birincil / ikincil metin |
| Marka vurgusu | `#3E8FD1` | İnteraktif elemanlar, aktif sekme, linkler — "avionics blue" |
| Durum: Güvenli | `#3FB77F` | MoS > eşik, "OK" durumu |
| Durum: Uyarı | `#E0A83E` | Marjinal katman, dikkat gerektiren değer |
| Durum: Kritik | `#E0543E` | MoS < 1, kırılma başlangıcı katmanı |

Bu üçlü (yeşil/amber/kırmızı) zaten uygulamanın kendi mantığında var (⚠️ kritik katman uyarısı) — onu dekorasyon değil, **sistemin ana görsel dili** haline getiriyoruz.

**Tipografi** (3 rol):

- **Başlık / UI etiketleri:** *Titillium Web* — geometrik, teknik, biraz "enstrüman paneli" karakterli, Avrupa havacılık/akademik projelerinde de kullanılmış bir font ailesi. Jenerik değil, alana uygun.
- **Gövde metni:** *Inter* veya *IBM Plex Sans* — okunabilir, nötr, yormaz.
- **Sayısal veri / koordinatlar / açılar:** *IBM Plex Mono* veya *JetBrains Mono* — tüm sayısal girdiler (delik çapı, X/Y, ply açısı, tork, MoS değeri) sabit genişlikli fontla yazılır. Bu tek başına uygulamayı "mühendislik aracı" gibi hissettiren en güçlü detaylardan biri; sayılar hizalanır, kullanıcı verinin ciddiye alındığını hisseder.

**Doku / zemin:** Ana viewport'un arkasında çok düşük opaklıkta (%3-5) ince bir mühendislik-kağıdı gridi (blueprint grid) — dekoratif değil, gerçek koordinat hissini destekleyen bir katman. Panel köşelerinde çok hafif "vida/rivet" noktası gibi mikro-detaylar (abartmadan, tek yerde — bkz. imza öğe).

---

## 2. İmza Öğe: "Güvenlik Marjı Göstergesi"

Sayfanın hatırlanacağı tek özgün eleman: MoS (Margin of Safety) değerini klasik uçak enstrümanı gibi **dairesel bir gösterge (gauge/dial)** ile gösteren bileşen.

- Yeşil/amber/kırmızı bölgeli yay, ibre MoS değerine göre döner.
- Kritik katman tespit edildiğinde ibre kırmızı bölgeye girer ve gösterge hafifçe "nabız" animasyonuyla dikkat çeker (abartısız, tek seferlik).
- Bu gösterge hem genel sonuç panelinde büyük halde, hem her katman satırında küçük mini-versiyon olarak tekrar eder — tutarlı bir motif oluşturur.
- ContourPlot'un yanına yerleştirilir; kullanıcı grafiğe bakmadan da "durumu" anında okur.

Bu, mevcut ⚠️ ikonunun doğal ve çok daha profesyonel bir evrimi.

---

## 3. Bilgi Mimarisi / Layout

Mevcut yapı muhtemelen dikey/form ağırlıklı. Gerçek mühendislik yazılımlarının (SolidWorks, ANSYS Workbench) alışıldık 4 bölgeli düzenine geçilmesi öneriliyor:

```
┌─────────────────────────────────────────────────┐
│  Üst Bar: Proje adı · Analiz Et · Rapor Al       │
├───────────┬───────────────────────┬─────────────┤
│           │                       │             │
│  SOL:     │      ORTA:            │   SAĞ:      │
│  Yapı     │      Viewport         │   Özellik   │
│  Ağacı    │      (ContourPlot +   │   Paneli    │
│  (Geo /   │      Güvenlik Marjı   │   (seçili   │
│  Laminate │      Göstergesi)      │   katman/   │
│  katman   │                       │   malzeme   │
│  listesi) │                       │   detayı)   │
│           │                       │             │
├───────────┴───────────────────────┴─────────────┤
│  Alt Bar: Durum / son analiz zamanı / hata logu  │
└─────────────────────────────────────────────────┘
```

- **Sol panel:** GeometryEditor + LaminateBuilder tek bir "yapı ağacı" hissiyle birleşir (katmanlar liste halinde, tıklayınca sağ panelde detay açılır). Bu, kullanıcının şu an muhtemelen ayrı ayrı gezdiği formları tek bakışta özetler.
- **Orta panel:** Her zaman görünür, en büyük alan — mevcut haliyle muhtemelen sayfa aşağı kaydırılınca görülüyordur; bunun "her zaman ekranda" olması en büyük UX kazanımlarından biri olur.
- **Sağ panel:** MaterialManager artık modal yerine buraya bağlı bir kontekst paneli olabilir (seçili katmana tıklanınca malzeme özellikleri burada açılır) — modal'lar akışı kesiyor, kontekst paneli akışı korur. Özel malzeme tanımlama için "yeni malzeme ekle" hâlâ modal kalabilir (bu nadiren yapılan bir işlem).
- **Alt bar:** Şu an kaybolan/örtük olabilecek sistem durumu (son analiz zamanı, hata/uyarı logu) her zaman görünür hâle gelir — profesyonel yazılımların "status bar" alışkanlığı.

---

## 4. Bileşen Bazlı Öneriler

**GeometryEditor**
- Girdi kutuları yanına küçük **canlı mini-önizleme** (deliğin plakadaki konumunu gösteren basit 2D şematik) eklenmesi — sayı değişince şematik anında güncellenir. Mühendis, girdiği X/Y'nin doğru olduğunu grafiğe gitmeden görür.
- Sayısal alanlar mono font + birim etiketleri sabit (örn. "mm", "Nm") input'un içinde soluk gri olarak.

**LaminateBuilder**
- Katman dizilimi yatay bir "stack" görseli olarak render edilsin — her ply, açısına göre eğik çizgili küçük bir dikdörtgen, kalınlığına göre yükseklik. Sürükle-bırak ile sıralama.
- 0°/45°/-45°/90° gibi standart açılar için tek tıkla hızlı ekleme butonları.

**MaterialManager**
- Karşılaştırma tablosu görünümü: kullanıcı birden fazla malzemeyi yan yana (Elastisite, Poisson, Kopma Mukavemeti) karşılaştırabilsin — malzeme seçimi kararını kolaylaştırır.

**ContourPlot**
- Mevcut akıllı zoom (uiRevisionKey) korunuyor — iyi bir detay.
- Renk skalası legend'ı her zaman görünür ve okunaklı olsun; kritik katman otomatik olarak "odaklan" butonuyla işaretlensin (tıklayınca kamera o bölgeye gider).
- Görselin üstünde ince, kaybolan bir "yükleniyor/hesaplanıyor" durumu — analiz saniyeler sürse de bir geçiş animasyonu güven verir (bkz. Bölüm 5).

---

## 5. Mikro-Etkileşim ve Hareket

- **Sayfa/analiz akışı:** "Analiz Et" tıklanınca buton kısa bir yükleniyor durumuna geçer, sonuçlar geldiğinde grafikler ve gösterge yumuşak bir fade/scale ile güncellenir (~150-200ms) — ani zıplama olmasın.
- **Kritik katman uyarısı:** Güvenlik marjı göstergesi kırmızıya girdiğinde *tek seferlik* hafif nabız animasyonu (sürekli yanıp sönme değil — yorucu olur ve "yormasın" isteğinizle çelişir).
- **Hover:** Katman listesinde satır üstüne gelince o katmanın ContourPlot'taki karşılığı hafifçe vurgulansın (çapraz-vurgulama, iki panel arası bağ kurar).
- Genel kural: **hareket az ve anlamlı** olsun. Her yere animasyon eklemek "AI yapımı" hissi verir; siz zaten yormasın istiyorsunuz — bu ilke doğrudan buna hizmet ediyor.

---

## 6. Erişilebilirlik ve Performans

- Koyu tema kontrastları WCAG AA seviyesinde tutulmalı (metin/arka plan oranı ≥ 4.5:1) — özellikle mono font ile yazılan küçük sayısal verilerde.
- Klavye ile gezinme: form alanları arası Tab sırası mantıklı, seçili öğe için görünür focus halkası (marka mavisi ile).
- `prefers-reduced-motion` desteklensin — nabız/fade animasyonları bu ayarda kapansın.
- Plotly grafiklerinin render performansı için büyük veri setlerinde (çok katmanlı laminate) sanal listeleme (virtualization) düşünülebilir.

---

## 7. Teknik Uygulama Notları

- Tailwind config'e yukarıdaki renk paleti `theme.extend.colors` altında token olarak tanımlanmalı (örn. `bg-panel`, `text-critical`, `border-grid`) — hardcoded hex yerine tutarlı kullanım sağlar.
- Font aileleri `@fontsource/titillium-web`, `@fontsource/inter`, `@fontsource/ibm-plex-mono` gibi paketlerle yerel olarak yüklenmeli (harici CDN bağımlılığı azaltılır, offline/kurumsal ağlarda da çalışır — mühendislik yazılımları için önemli).
- Güvenlik Marjı Göstergesi kendi başına yeniden kullanılabilir bir React bileşeni (`<SafetyGauge value={mos} size="lg|sm" />`) olarak yazılmalı; hem genel panelde hem katman satırlarında aynı bileşen kullanılmalı.
- Mevcut `uiRevisionKey` mantığı korunmalı, layout değişikliği ona dokunmamalı.

---

## 8. Aşamalı Yol Haritası

**Faz 1 — Temel (1-2 hafta):**
Renk paleti + tipografi token'larının Tailwind config'e işlenmesi, genel zemin/panel stillerinin uygulanması. Mevcut layout korunur, sadece "cilt değişimi." Bu tek başına büyük bir algı farkı yaratır ve erken geri bildirim almanızı sağlar.

**Faz 2 — Layout (2-3 hafta):**
3 panelli + status bar yapısına geçiş. GeometryEditor/LaminateBuilder'ın sol panelde birleştirilmesi, MaterialManager'ın kontekst paneline taşınması.

**Faz 3 — İmza öğe ve mikro-etkileşim (1-2 hafta):**
Güvenlik Marjı Göstergesi bileşeninin geliştirilmesi ve entegrasyonu, hover çapraz-vurgulama, geçiş animasyonları.

**Faz 4 — Bileşen detayları (2 hafta):**
GeometryEditor mini-önizleme, LaminateBuilder görsel stack, MaterialManager karşılaştırma tablosu.

**Faz 5 — Cila (1 hafta):**
Erişilebilirlik denetimi, responsive/dar ekran testleri, performans kontrolü, son ince ayarlar.

Toplam kabaca 7-10 haftalık bir çalışma; Faz 1 ve 3 en yüksek görsel etkiyi en az efor ile verir, isterseniz önce onlara odaklanılabilir.

---

## 9. Kaçınılması Gerekenler

- Her butona/karta gölge + gradient + hover-scale eklemek — "şablon SaaS" hissi verir, mühendislik aracı ciddiyetini zedeler.
- Aşırı renk çeşitliliği — palet 6 tonla sınırlı kalmalı, her yeni renk bir anlam taşımalı (durum kodlaması dışında dekoratif renk eklenmemeli).
- Sürekli/döngüsel animasyonlar (yanıp sönen ikonlar, dönen loading spinner'lar her yerde) — "yormasın" hedefiyle doğrudan çelişir.
- Modal'ların çoğalması — mümkün olduğunca kontekst paneli tercih edilmeli, modal akışı kesiyor.
