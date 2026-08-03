
# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.metrics import dp
import sqlite3
from pathlib import Path
from datetime import datetime
from decimal import Decimal

URUNLER = {
    "19L Damacana": 210.00,
    "1L Pet": 125.00,
    "1.5L Pet": 125.00,
    "5L Pet": 125.00,
    "0.50L Pet": 250.00,
    "0.33L Pet": 250.00,
    "Sade Soda 6'lı": 90.00,
    "Meyveli Soda 6'lı": 95.00,
    "Bardak Su": 235.00,
    "Pompa": 250.00,
    "Boş Damacana": 120.00,
    "Sade soda 24'lü": 355.00,
}

DB_PATH = "su_takip.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS musteriler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            isim TEXT NOT NULL,
            telefon TEXT NOT NULL UNIQUE,
            adres TEXT DEFAULT '',
            emanet_damacana INTEGER NOT NULL DEFAULT 0,
            notlar TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS siparisler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            musteri_id INTEGER NOT NULL,
            tarih TEXT NOT NULL,
            toplam REAL NOT NULL,
            odeme_turu TEXT NOT NULL DEFAULT 'Pesin',
            FOREIGN KEY (musteri_id) REFERENCES musteriler(id)
        );
        CREATE TABLE IF NOT EXISTS siparis_kalemleri (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            siparis_id INTEGER NOT NULL,
            urun TEXT NOT NULL,
            adet INTEGER NOT NULL,
            birim_fiyat REAL NOT NULL,
            toplam REAL NOT NULL,
            FOREIGN KEY (siparis_id) REFERENCES siparisler(id)
        );
        """)

class AnaEkran(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=dp(10), spacing=dp(8), **kwargs)
        init_db()
        self.sepet = []
        self.secili_musteri = None
        
        self.add_widget(Label(text='AYTAÇ ÖNER - SU TAKIP PRO v5', size_hint_y=None, height=dp(40), font_size='18sp', bold=True))
        
        # Musteri arama
        arama_box = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(5))
        self.telefon_input = TextInput(hint_text='Telefon ile ara / yeni müşteri tel', multiline=False, size_hint_x=0.6)
        arama_box.add_widget(self.telefon_input)
        arama_box.add_widget(Button(text='ARA', on_press=self.musteri_ara, size_hint_x=0.2))
        arama_box.add_widget(Button(text='KAYDET', on_press=self.musteri_kaydet, size_hint_x=0.2))
        self.add_widget(arama_box)
        
        self.isim_input = TextInput(hint_text='Müşteri Adı Soyadı', size_hint_y=None, height=dp(40), multiline=False)
        self.add_widget(self.isim_input)
        self.adres_input = TextInput(hint_text='Adres (Mahalle/Sokak)', size_hint_y=None, height=dp(40), multiline=False)
        self.add_widget(self.adres_input)
        
        self.bilgi_label = Label(text='Müşteri seçili değil', size_hint_y=None, height=dp(30))
        self.add_widget(self.bilgi_label)
        
        # Urun ekleme
        urun_box = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(5))
        self.urun_spinner = Spinner(text='19L Damacana', values=list(URUNLER.keys()), size_hint_x=0.6)
        self.adet_input = TextInput(text='1', input_filter='int', size_hint_x=0.2, multiline=False)
        urun_box.add_widget(self.urun_spinner)
        urun_box.add_widget(self.adet_input)
        urun_box.add_widget(Button(text='SEPETE EKLE', on_press=self.sepete_ekle, size_hint_x=0.4))
        self.add_widget(urun_box)
        
        self.sepet_label = Label(text='Sepet: Boş', size_hint_y=None, height=dp(30))
        self.add_widget(self.sepet_label)
        
        # Odeme ve Kaydet
        odeme_box = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(5))
        self.odeme_spinner = Spinner(text='Pesin', values=['Pesin','Kredi Karti','Veresiye','Online Odeme'], size_hint_x=0.4)
        odeme_box.add_widget(self.odeme_spinner)
        odeme_box.add_widget(Button(text='SIPARISI KAYDET', on_press=self.siparis_kaydet))
        self.add_widget(odeme_box)
        
        # Alt butonlar
        alt_box = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
        alt_box.add_widget(Button(text='SIPARISLER\n(Sil içinde)', on_press=self.siparisleri_goster))
        alt_box.add_widget(Button(text='EMANET LISTESI\n(Ver/Al içinde)', on_press=self.emanet_listesi))
        alt_box.add_widget(Button(text='WHATSAPP', on_press=self.whatsapp_ac))
        self.add_widget(alt_box)

    def musteri_ara(self, *a):
        tel = self.telefon_input.text.strip()
        if not tel:
            return
        with get_conn() as c:
            row = c.execute("SELECT * FROM musteriler WHERE telefon=?", (tel,)).fetchone()
            if row:
                self.secili_musteri = dict(row)
                self.isim_input.text = row['isim']
                self.adres_input.text = row['adres']
                self.bilgi_label.text = f"{row['isim']} | Emanet: {row['emanet_damacana']} | {row['telefon']}"
            else:
                self.bilgi_label.text = "Müşteri bulunamadı, isim girip KAYDET ile oluştur"

    def musteri_kaydet(self, *a):
        tel = self.telefon_input.text.strip()
        isim = self.isim_input.text.strip()
        adres = self.adres_input.text.strip()
        if not tel or not isim:
            self.bilgi_label.text = "Telefon ve isim gerekli!"
            return
        with get_conn() as c:
            try:
                c.execute("INSERT INTO musteriler (isim, telefon, adres) VALUES (?,?,?)", (isim, tel, adres))
                self.bilgi_label.text = "Müşteri kaydedildi"
            except sqlite3.IntegrityError:
                c.execute("UPDATE musteriler SET isim=?, adres=? WHERE telefon=?", (isim, adres, tel))
                self.bilgi_label.text = "Müşteri güncellendi"
        self.musteri_ara()

    def sepete_ekle(self, *a):
        try:
            adet = int(self.adet_input.text or 1)
        except:
            adet = 1
        urun = self.urun_spinner.text
        fiyat = URUNLER.get(urun, 0)
        self.sepet.append({"urun": urun, "adet": adet, "fiyat": fiyat, "toplam": fiyat*adet})
        self.sepet_guncelle()

    def sepet_guncelle(self):
        if not self.sepet:
            self.sepet_label.text = "Sepet: Boş"
            return
        toplam = sum(x['toplam'] for x in self.sepet)
        txt = " | ".join([f"{x['urun']} x{x['adet']}" for x in self.sepet])
        self.sepet_label.text = f"{txt} = {toplam:.2f} TL"

    def siparis_kaydet(self, *a):
        if not self.secili_musteri:
            self.bilgi_label.text = "Önce müşteri seç!"
            return
        if not self.sepet:
            self.bilgi_label.text = "Sepet boş!"
            return
        toplam = sum(x['toplam'] for x in self.sepet)
        tarih = datetime.now().strftime("%d.%m.%Y %H:%M")
        odeme = self.odeme_spinner.text
        with get_conn() as c:
            cur = c.execute("INSERT INTO siparisler (musteri_id, tarih, toplam, odeme_turu) VALUES (?,?,?,?)",
                            (self.secili_musteri['id'], tarih, toplam, odeme))
            sip_id = cur.lastrowid
            for k in self.sepet:
                c.execute("INSERT INTO siparis_kalemleri (siparis_id, urun, adet, birim_fiyat, toplam) VALUES (?,?,?,?,?)",
                          (sip_id, k['urun'], k['adet'], k['fiyat'], k['toplam']))
                if "Damacana" in k['urun']:
                    c.execute("UPDATE musteriler SET emanet_damacana = emanet_damacana + ? WHERE id=?", (k['adet'], self.secili_musteri['id']))
        self.sepet = []
        self.sepet_guncelle()
        self.bilgi_label.text = f"Sipariş kaydedildi: {toplam:.2f} TL"
        self.musteri_ara()

    def siparisleri_goster(self, *a):
        content = BoxLayout(orientation='vertical', spacing=dp(5), padding=dp(10))
        scroll = ScrollView()
        grid = GridLayout(cols=1, spacing=dp(5), size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))
        
        with get_conn() as c:
            rows = c.execute("SELECT s.id, m.isim, m.telefon, s.tarih, s.toplam, s.odeme_turu FROM siparisler s JOIN musteriler m ON m.id=s.musteri_id ORDER BY s.id DESC LIMIT 100").fetchall()
            for r in rows:
                row_box = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
                row_box.add_widget(Label(text=f"{r['id']} - {r['isim']} - {r['toplam']} TL - {r['tarih']}", font_size='11sp'))
                btn_sil = Button(text='SIL', size_hint_x=0.25, background_color=(1,0.3,0.3,1))
                def make_sil(sid=r['id']):
                    def sil_func(*_):
                        with get_conn() as cc:
                            cc.execute("DELETE FROM siparis_kalemleri WHERE siparis_id=?", (sid,))
                            cc.execute("DELETE FROM siparisler WHERE id=?", (sid,))
                        popup.dismiss()
                        self.bilgi_label.text = f"Sipariş {sid} silindi"
                    return sil_func
                btn_sil.bind(on_press=make_sil())
                row_box.add_widget(btn_sil)
                grid.add_widget(row_box)
        
        scroll.add_widget(grid)
        content.add_widget(scroll)
        close_btn = Button(text='KAPAT', size_hint_y=None, height=dp(45))
        content.add_widget(close_btn)
        popup = Popup(title='Son 100 Sipariş - Sil butonu içinde', content=content, size_hint=(0.95,0.9))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

    def emanet_listesi(self, *a):
        content = BoxLayout(orientation='vertical', spacing=dp(5), padding=dp(10))
        scroll = ScrollView()
        grid = GridLayout(cols=1, spacing=dp(5), size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))
        
        def refresh():
            grid.clear_widgets()
            with get_conn() as c:
                rows = c.execute("SELECT * FROM musteriler WHERE emanet_damacana>0 ORDER BY emanet_damacana DESC").fetchall()
                for r in rows:
                    row_box = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
                    row_box.add_widget(Label(text=f"{r['isim']} ({r['telefon']}) - {r['emanet_damacana']} adet", font_size='11sp'))
                    btn_ver = Button(text='VER +', size_hint_x=0.2)
                    btn_al = Button(text='AL -', size_hint_x=0.2, background_color=(0.3,0.8,0.3,1))
                    def make_ver(mid=r['id']):
                        def f(*_):
                            with get_conn() as cc:
                                cc.execute("UPDATE musteriler SET emanet_damacana=emanet_damacana+1 WHERE id=?", (mid,))
                            refresh()
                        return f
                    def make_al(mid=r['id']):
                        def f(*_):
                            with get_conn() as cc:
                                cc.execute("UPDATE musteriler SET emanet_damacana=MAX(emanet_damacana-1,0) WHERE id=?", (mid,))
                            refresh()
                        return f
                    btn_ver.bind(on_press=make_ver())
                    btn_al.bind(on_press=make_al())
                    row_box.add_widget(btn_ver)
                    row_box.add_widget(btn_al)
                    grid.add_widget(row_box)
            if not grid.children:
                grid.add_widget(Label(text='Emaneti olan müşteri yok'))
        
        refresh()
        scroll.add_widget(grid)
        content.add_widget(scroll)
        close_btn = Button(text='KAPAT', size_hint_y=None, height=dp(45))
        content.add_widget(close_btn)
        popup = Popup(title='Emanet Listesi - Ver/Al butonları içinde', content=content, size_hint=(0.95,0.9))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

    def whatsapp_ac(self, *a):
        from kivy.utils import platform
        tel = self.telefon_input.text.strip()
        if not tel:
            self.bilgi_label.text = "WhatsApp için telefon gir"
            return
        # temizle
        num = ''.join([c for c in tel if c.isdigit()])
        if num.startswith('0'):
            num = '90' + num[1:]
        if not num.startswith('90'):
            num = '90' + num
        try:
            if platform == 'android':
                from jnius import autoclass
                Intent = autoclass('android.content.Intent')
                Uri = autoclass('android.net.Uri')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                intent = Intent()
                intent.setAction(Intent.ACTION_VIEW)
                intent.setData(Uri.parse(f"https://wa.me/{num}"))
                currentActivity = PythonActivity.mActivity
                currentActivity.startActivity(intent)
            else:
                import webbrowser
                webbrowser.open(f"https://wa.me/{num}")
            self.bilgi_label.text = f"WhatsApp açılıyor: {num}"
        except Exception as e:
            self.bilgi_label.text = f"WhatsApp hata: {e}"

class SuTakipApp(App):
    def build(self):
        return AnaEkran()

if __name__ == '__main__':
    SuTakipApp().run()
