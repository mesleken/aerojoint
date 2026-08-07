# 🛩️ AeroJoint — Kompozit Bağlantı (Lug & Bolted Joint) Analiz ve Sertifikasyon Yazılımı

MIL-HDBK-17 / CMH-17 standartlarında, ANSYS ACP hassasiyetinde 2-5 saniyede anlık Sonlu Elemanlar Analizi (FEA), gerilme yığılması hesabı ve katman bazlı Hashin & Tsai-Wu kırılma denetimi yapan mühendislik yazılımı.

---

## 🚀 Öne Çıkan Özellikler

1. **Havacılık Hasar Kriterleri (FAA/EASA)**:
   - **Hashin (1980)** (Birincil): Elyaf Çekme, Elyaf Basma, Matris Çekme, Matris Basma modları.
   - **Tsai-Wu** (İkincil): Eliptik etkileşim zarfı ön taraması.
   - **Güvenlik Marjı (MoS)** hesabı.

2. **Hızlı Lineerize Contact Modeli**:
   - Kosinüs Dağılımlı Yataklama Basınç Modeli ($p_0 \cos\theta$) ile saatler süren non-lineer kontağı milisaniyelere düşürür.

3. **Otomatik Mesh Engine (Gmsh)**:
   - Delik çevresinde 4-6 katman radyal **Boundary Layer (Sıklaştırma)** ve Quad-dominant Q4 eleman ağı.

4. **Doğrudan Çözücü (Direct Sparse Solver)**:
   - `scipy.sparse.linalg.spsolve` (SuperLU) ile yüksek çözünürlüklü simetrik pozitif tanımlı rijitlik matrisi çözümü.

5. **Kurumsal PDF Sertifikasyon Raporu**:
   - WeasyPrint + Jinja2 HTML/CSS ile 3 sayfalık MIL-HDBK-17 sertifikasyon raporu üretimi.

---

## 🛠️ Hızlı Başlatma (Docker ile)

```bash
# Projeyi klonlayın ve kök dizine geçin
docker-compose up --build
```
* **Frontend UI**: http://localhost:3000
* **Backend API (Swagger Docs)**: http://localhost:8000/docs

---

## 💻 Yerel Geliştirme (Local Development)

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```
