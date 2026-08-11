# AeroJoint Hesap Motoru — Kod İncelemesi ve İyileştirme Planı

## Genel Değerlendirme

Önce iyi haber: bu, amatör bir kod değil. CLT'nin ABD matrisi türetimi, Q̄ dönüşüm formülleri, Q4 izoparametrik formülasyon, Gauss-nokta-ekstrapolasyon matrisi, ve özellikle **Hashin/Tsai-Wu kriterlerinin termal+mekanik yükü tek bir λ (rezerv faktörü) ikinci derece denklemiyle birlikte çözen yaklaşımı** — bunların hepsi standart mühendislik literatürüyle (Jones, Hashin 1980, Tsai-Wu) örtüşüyor ve doğru uygulanmış. Bu son nokta (λ-bazlı rezerv faktörü çözümü) özellikle iyi düşünülmüş; çoğu ticari olmayan araçta bu kadar titiz yapılmaz.

Ama gerçek bir stres mühendisinin imza atacağı bir araç olması için **bir kritik, birkaç orta öncelikli** teknik sorun var. Öncelik sırasıyla gidiyorum.

---

## 🔴 KRİTİK — Öncelik 1: Kırılma hesabı, ortalanmış (smoothed) gerilmeler üzerinden yapılıyor

**Nerede:** `fem_solver.py`, `FEMSolver.solve()` → `_extrapolate_to_nodes()` → `_compute_ply_stresses()`

**Sorun:** Kendi matematik kılavuzunuz (Bölüm 4) şunu söylüyor:
> "Nodal Averaging (Ortalama): Görselleştirme amaçlı kontur grafikleri için... Kırılma hesabı için ise en kritik Gauss/Nodal değerler doğrudan kullanılır."

Ama koda bakınca durum bu değil. `solve()` metodunda:
```python
nodal_stresses = self._extrapolate_to_nodes(mesh, element_stresses)  # ORTALANMIŞ
ply_stresses = self._compute_ply_stresses(nodal_stresses)             # ORTALANMIŞ veri ile hesaplanıyor
```
`_extrapolate_to_nodes()` fonksiyonu, her düğümdeki gerilmeyi **komşu elemanların ortalamasını alarak** (`nodal_sum / nodal_count`) hesaplıyor — bu tam olarak "görselleştirme için pürüzsüzleştirme" işlemi. Ama bu ortalanmış değer, doğrudan `_compute_ply_stresses()`'e (yani katman gerilmelerine, yani Hashin/Tsai-Wu'ya, yani MoS'a) besleniyor. Ayrı, ortalanmamış bir "kırılma hesabı için ham değer" yolu **yok**.

**Neden ciddi:** Gerilme yığılmasının en şiddetli olduğu yer tam olarak delik kenarı — yani MoS'un en kritik olduğu, tam da bu ortalamanın en çok "yumuşattığı" bölge. Komşu elemanlarla ortalama almak, delik kenarındaki gerçek pik gerilmeyi **olduğundan düşük gösterir** (non-conservative). Yani şu anki mimaride, raporlanan MoS değerleri muhtemelen gerçekte olması gerekenden **daha iyimser** — dokümantasyonunuzun kendi belirttiği metodolojiye göre bile bu bir hata.

**Çözüm:**
1. `_compute_element_stresses()` zaten her elemanın Gauss noktası gerilmelerini (ortalanmamış) hesaplıyor — bu veri zaten elinizde (`FEMResult.element_stresses`).
2. Katman/kırılma hesabını (`_compute_ply_stresses` → Hashin/Tsai-Wu), düğüm-ortalamalı `nodal_stresses` yerine **her elemanın kendi (ortalanmamış) Gauss/köşe gerilmesinden** yapın. Pratikte: her eleman için, o elemana ait 4 düğümün *o elemana özgü* (ortalama alınmamış) ekstrapole edilmiş köşe gerilmesini kullanın — yani `_extrapolate_to_nodes`'daki `node_stresses_elem` ara değerini (ortalamadan ÖNCEKİ hâli) saklayın ve kırılma hesabı bunun üzerinden, `nodal_sum/nodal_count` sonrası hâli ise SADECE ContourPlot görselleştirmesi için kullanın.
3. Sonuç: iki ayrı gerilme alanı olacak — `stresses_for_visualization` (ortalanmış, pürüzsüz) ve `stresses_for_failure` (ortalanmamış, eleman-bazlı, konservatif). Rapor ve MoS hesabı ikincisini kullanmalı.

Bu, bence şu an yapılacak en önemli tek değişiklik — çünkü diğer her şey doğru olsa bile, girdi verisi (gerilme) yanlış kaynaktan geliyorsa çıktı (MoS/PASS-FAIL) güvenilmez olur.

---

## 🔴 KRİTİK — Öncelik 2: Termal hasar bayrağı (`thermal_fail`) hesaplanıyor ama hiçbir yere aktarılmıyor

**Nerede:** `failure.py`, `hashin_criteria()` ve `tsai_wu_criterion()` bir `thermal_fail` alanı hesaplayıp döndürüyor (`C_ft > 1.0` vb. — yani "sadece termal artık gerilme bile, hiç mekanik yük binmeden, katmanı zaten kırıyor mu" kontrolü). Ama `evaluate_ply()` bu değeri okuyup `FailureResult`'a hiç yazmıyor — `FailureResult` dataclass'ında `thermal_fail` diye bir alan bile yok.

**Neden ciddi:** Bu, tam olarak bir sertifikasyon aracının kaçırmaması gereken bir durum — "bu katman, hiç dış yük binmeden, sadece kür/soğuma sonrası kalıcı termal gerilmeyle zaten hasarlı" bilgisi sessizce hesaplanıp çöpe atılıyor.

**Çözüm:** `FailureResult`'a `thermal_fail: bool` alanı ekleyin, `evaluate_ply()` içinde `hashin['thermal_fail'] or tsai_wu['thermal_fail']` olarak doldurun, arayüzde bu true olduğunda ayrı, özel bir uyarı rozeti gösterin ("⚠ Termal Artık Gerilme Kritik" gibi) — normal PASS/FAIL/MARGINAL rozetinden ayrı, çünkü kök nedeni farklı (yük değil, malzeme/kür süreci).

**Bununla bağlantılı bir gözlem:** `fem_solver.py`'de hiçbir yerde `delta_T` kullanılmıyor — yani `CLTEngine.compute_thermal_loads()` ve malzemedeki `alpha1/alpha2` (CTE) alanları şu an **hiç çağrılmıyor**, gerçek analiz akışına bağlı değil. Bu, aslında önceki konuşmamızdaki "çevresel koşul/hot-wet" planıyla doğrudan ilişkili: termal-mekanik birleşik hesap altyapısı zaten yazılmış durumda, sadece FEM çözücüsüne bağlanmamış. Yani bu, sıfırdan yazılacak bir özellik değil, **var olan ama bağlı olmayan bir motoru devreye sokma** işi — bu iyi haber, efor tahmininde bunu göz önünde bulundurun.

*(Not: Termal artık gerilme modellemesi ile "hot/wet allowable düşüşü" farklı iki mekanizma — biri kür sonrası kalıcı gerilme, diğeri sıcaklık/nemin malzeme mukavemetini düşürmesi. İkisi de "çevresel etki" şemsiyesi altında ama ayrı ayrı ele alınmalı; ikisi de şu an motorda eksik/bağlı değil.)*

---

## 🟠 ORTA ÖNCELİK — Öncelik 3: Clearance (boşluk) modeli doğrulanmamış, kendi içinde tutarsız

**Nerede:** `bearing.py`, `apply_bearing_loads()` içindeki `theta_c` hesaplama bloğu.

**Sorun:** Kodun kendi yorum satırları bile birbiriyle tutarsız. Yorum diyor ki: *"c=0.1mm → 120° (π/3)"* ve *"Maksimum daralma 90° (π/4) ile sınırlandırılır."* Ama gerçek formülü çalıştırırsanız:
- c=0.1mm'de: `reduction_factor = min(0.5, 0.1/0.2) = 0.5`, `theta_c = (π/2)×(1 - 0.5×0.5) = (π/2)×0.75 = 67.5°` — yorumdaki iddia edilen 60°(π/3) değil.
- Üstelik `reduction_factor` en fazla 0.5'te sınırlandığı için, `theta_c` hiçbir zaman yorumun iddia ettiği 45°'ye (π/4) inemiyor; ulaşabileceği en düşük değer 67.5°.

**Neden önemli:** Bu formül docstring'de zaten *"Basit ampirik yaklaşım"* olarak işaretlenmiş — yani siz de bunun geçici/kesin olmayan bir yaklaşım olduğunun farkındasınız. Ama şu anki hâliyle hem kendi hedeflediği davranışı (yorumdaki sayılar) tutturamıyor hem de literatürde yayınlanmış, doğrulanmış bir clearance-temas açısı modeline dayanmıyor.

**Çözüm:**
1. Kısa vadede: yorum satırlarını gerçek formülün ürettiği değerlerle uyumlu hâle getirin (ya formülü düzeltin ya da yorumu) — en azından iç tutarlılık sağlanmış olur.
2. Orta vadede: bu ampirik yaklaşımı, yayınlanmış bir referansa dayandırın. Havacılıkta pim/cıvata boşluğu-temas açısı ilişkisi için literatürde kabul görmüş modeller var (örn. Hertzian temas mekaniği tabanlı yaklaşımlar, ya da NASA/ESDU veri sayfalarındaki ampirik eğriler). Hangi referansı kullandığınızı raporda belirtebilmeniz, "Metodoloji Şeffaflığı" planımızın (madde 1) doğal bir parçası.
3. Bu modelin sonuçlara duyarlılığını (sensitivity) bir doğrulama/test çalışmasıyla gösterin — clearance=0 durumunda sonuçların bilinen kapalı-form çözümle (pure half-cosine, θc=90°) örtüştüğünü zaten garanti ediyorsunuz (formül c=0'da doğru davranıyor), ama c>0 için elinizde referans karşılaştırma yok.

---

## 🟠 ORTA ÖNCELİK — Öncelik 4: Mesh/eleman doğruluğu — Q4 lineer eleman, delik çevresinde ne kadar yeterli?

**Sorun:** `Q4Element`, standart 4-düğümlü lineer izoparametrik eleman — doğru uygulanmış ama bu eleman tipi, **gerilme yığılması bölgelerinde** (tam da delik kenarında, yani probleminizin en kritik yerinde) yakınsaması yavaş bilinen bir formülasyon. Ekran görüntülerinizde gördüğüm "792 Eleman / 848 Düğüm" gibi bir mesh yoğunluğu, bir delik etrafındaki pik gerilmeyi (Kirsch tipi 1/r² azalımı) yeterli doğrulukla yakalamak için muhtemelen **yetersiz** — klasik hole-in-plate problemlerinde bile literatür genelde delik çevresinde çok daha sık, radyal olarak kademelendirilmiş bir mesh önerir.

**Çözüm seçenekleri (öncelik sırasına göre değil, birbirini dışlamayan seçenekler):**
1. **En düşük efor:** Delik çevresi mesh yoğunluğunu (zaten "Mesh Yoğunluğu Delik" parametreniz var) çok daha agresif varsayılan değerlerle başlatın, ve bir **yakınsama kontrolü** ekleyin — aynı problemi 2-3 farklı mesh yoğunluğunda otomatik çözüp pik gerilmenin %'lik değişimini karşılaştıran, kullanıcıya "mesh yeterince sık mı" diye otomatik geri bildirim veren bir iç mekanizma (tam bir adaptif mesh refinement değil, basit bir "duyarlılık kontrolü").
2. **Orta efor, yüksek getiri:** Q4 yerine **Q8 (8 düğümlü, kuadratik) eleman** kullanmaya geçin. Aynı düğüm sayısında çok daha iyi gerilme doğruluğu verir, özellikle eğrisel sınırlarda (delik kenarı tam olarak böyle bir yer) kuadratik kenar enterpolasyonu geometriyi de daha doğru temsil eder. Bu, `Q4Element`'e paralel bir `Q8Element` sınıfı yazmayı gerektirir (şekil fonksiyonları, 3×3 Gauss, farklı boyutlu B matrisi) — mevcut mimariye (ayrı bir eleman sınıfı, solver'da tip parametresi) temiz bir şekilde eklenebilir.
3. Hangi seçeneği seçerseniz seçin, **doğrulama planımızla (önceki konuşmamızdaki madde 5) doğrudan bağlantılı**: bilinen bir analitik çözüm (örn. sonsuz plakada delik, SCF=3) ile mesh yakınsama davranışınızı karşılaştırıp raporlayın.

---

## 🟡 DÜŞÜK-ORTA ÖNCELİK — Öncelik 5: Bearing-Bypass yük kombinasyonu eksik görünüyor

**Sorun:** Mevcut modelde her delik için bir "Yük P (N)" ve bir açı giriliyor (bearing/yataklama yükü), artı plakanın bir kenarı sabitleniyor. Gerçek kompozit bağlantı tasarımında, bir deliğin taşıdığı yük genelde iki bileşene ayrılır:
- **Bearing yükü** (delikten pime/cıvataya doğrudan aktarılan) — sizde var.
- **Bypass yükü** (deliğin yanından "geçen", net kesitte kalan gerilmeye katkı yapan uzak-alan yükü) — bu, ayrı bir uzak-alan (remote) çekme/basma yükü olarak tanımlanabilir ve gerçek bağlantı tasarımlarında MoS'u bearing yükü kadar belirleyici olabilir (özellikle çok-cıvatalı bağlantılarda).

Şu anki arayüz/API'de (paylaştığınız kodlarda) ayrı bir "uzak alan/bypass yük" girişi göremedim — sadece delik-bazlı P ve sınır koşulu var.

**Çözüm:** Geometri paneline bir **"Bypass Yükü (N/mm ya da toplam N)"** girişi ekleyin — bu, sabitlenmemiş kenardan uygulanan ek bir dağıtık/toplu kuvvet olarak FEM'e (mevcut `create_force_vector` mantığına ek bir yük vektörü bileşeni olarak) eklenebilir. Bu eklendiğinde, sonuç raporunda bir **bearing/bypass oranı** (β = P_bearing / (P_bearing + P_bypass)) gösterilmesi, gerçek mühendislik pratiğinde çok değerli bir bilgi olur — bu oran, kritik hasar modunun bearing mi yoksa net-tension mu olacağını belirleyen ana parametredir.

---

## 🟡 DÜŞÜK ÖNCELİK — Öncelik 6: Sessiz varsayımlar (S23, Tsai-Wu F12) raporda görünmüyor

**Sorun:**
- `failure.py`'de `S23 = material.S23 if material.S23 is not None else Yc / 2.0` — kullanıcı S23 (enine kayma mukavemeti) girmezse sessizce `Yc/2` varsayılıyor. Bu, literatürde kabul gören bir varsayım ama S23, matris-basma hasar modunda etkili bir parametre; bu varsayımın kullanıldığı her analizde raporlanmalı.
- `tsai_wu_criterion()`'da `F12 = -0.5*sqrt(F11*F22)` — deneysel biaksiyel veri olmadan kullanılan standart bir normalize edilmiş varsayım, ama yine sessiz.

**Çözüm:** Bu tarz her "veri yoksa varsayılan kullan" durumunu, sonuç/PDF raporunda açıkça listeleyen bir **"Varsayımlar" bölümü** ekleyin ("S23 verisi girilmediği için Yc/2 varsayılmıştır" gibi). Bu, tam olarak önceki konuşmamızdaki "Metodoloji Şeffaflığı" planının somut bir uygulama parçası.

---

## 🟢 MİMARİ/PERFORMANS NOTLARI (bug değil ama teknik borç)

1. **Kod tekrarı:** `clt.py` içindeki `CLTEngine.compute_ply_stresses()` (tam ABD, eğilme dahil) ile `fem_solver.py` içindeki `FEMSolver._compute_ply_stresses()` (sadece membran, C_eff üzerinden) iki ayrı, örtüşen implementasyon. Biri kullanılmıyor gibi görünüyor (FEM yolu kendi metodunu kullanıyor) — ölü kod mu, yoksa başka bir yerde (örn. tekil-nokta el-hesabı doğrulama modu) mi kullanılıyor belirsiz. Netleştirin; kullanılmıyorsa kaldırın, kullanılıyorsa iki implementasyonun sonuçlarının tutarlı olduğunu bir testle garanti edin (aksi hâlde ileride biri güncellenir, diğeri güncellenmez, sessizce birbirinden sapar).
2. **Sparse matris montaj performansı:** `assemble_global_stiffness()`, Python `list.append()` ile COO triplet biriktiriyor — küçük/orta modellerde sorun değil ama Faz 2'de konuştuğumuz "toplu/çoklu delik analizi" veya ileride "parametrik tarama" özelliği geldiğinde, bu fonksiyon binlerce kez çağrılacağından, numpy ön-tahsisli (pre-allocated) array'lerle vektörize edilmiş bir montaj performans açısından fark yaratır.
3. **`K[np.ix_(free_dofs, free_dofs)]`** — CSR sparse matriste fancy indexing pahalı bir işlemdir; büyük modellerde `K.tocsc()[free_dofs][:, free_dofs]` ya da montaj sırasında sabit DOF'ları hiç eklemeyecek şekilde (elimination-by-construction) bir yaklaşım daha verimli olur.

---

## Uygulama Planı — Öncelik Sırasına Göre

| # | Konu | Tip | Efor | Neden bu sıra |
|---|---|---|---|---|
| 1 | Kırılma hesabını ortalanmamış gerilmeye taşı | **Doğruluk düzeltmesi** | Orta (1-2 hafta) | Şu anki MoS değerlerinin güvenilirliğini doğrudan etkiliyor — her şeyden önce bu |
| 2 | `thermal_fail` bayrağını `FailureResult`'a bağla | Eksik özellik | Düşük (birkaç gün) | Küçük efor, gizli bir hasar modunu ortaya çıkarıyor |
| 4 | Mesh yakınsama kontrolü / Q8 element değerlendirmesi | Doğruluk + doğrulama | Yüksek (Q8: 3-4 hafta / yakınsama kontrolü: 1 hafta) | 1 numaralı düzeltmeyle birlikte ele alınmalı — ikisi de "gerçek pik gerilme ne kadar doğru" sorusuna cevap veriyor |
| 3 | Clearance modelini düzelt/referansla | Tutarlılık + doğrulama | Düşük-Orta (1 hafta) | Küçük ama görünürlüğü yüksek bir tutarsızlık |
| 5 | Bypass yükü desteği | Yeni özellik | Orta-Yüksek (2-3 hafta) | Gerçek tasarım pratiğine yakınlaştırıyor ama mevcut sonuçların doğruluğunu etkilemiyor, bu yüzden 1-4'ten sonra |
| 6 | Varsayımlar bölümü (rapor) | Şeffaflık | Düşük (birkaç gün) | Önceki "Metodoloji Şeffaflığı" planıyla birlikte yürütülebilir |
| — | Mimari/performans temizliği (kod tekrarı, sparse montaj) | Teknik borç | Orta (paralel yürütülebilir) | Aciliyeti yok ama Faz 2 (toplu analiz) öncesi yapılmalı |

**Genel öneri:** 1 ve 2 numaralı maddeleri **aynı sprint'te** ele alın — ikisi de "hesabın kendi belgelediği metodolojiyle tutarlı olması" başlığı altında toplanabilir ve göreceli olarak düşük efor/yüksek güven getirisi sağlar. 4 numaralı madde (mesh/eleman doğruluğu), daha önce konuştuğumuz Doğrulama Sayfası planıyla birleştirilip tek bir "doğrulama sprintine" dönüştürülebilir: hem mesh yakınsamasını hem de genel çözücü doğruluğunu aynı çalışmada kanıtlarsınız.
