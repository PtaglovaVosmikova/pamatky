from kivy_garden.mapview import MapView, MapMarkerPopup,MapSource
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.list import OneLineListItem
import requests
from kivy.clock import Clock
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
import webbrowser

from kivymd.uix.snackbar import Snackbar
import math
#from plyer import gps
from plyer import compass
from threading import Thread
import requests
import traceback
import sys
from kivy.utils import platform
print("=== PYTHON START ===")

# ==================================================
# HARD ERROR LOG
# ==================================================

def excepthook(exctype, value, tb):
    print("".join(traceback.format_exception(exctype, value, tb)))

sys.excepthook = excepthook

KV = """


<RootLayout@BoxLayout>:
    orientation: "vertical"
    arrow_angle: 0


RootLayout:

    MapView:
        id: map
        lat: 49.875250
        lon: 13.303320
        zoom: 16
        map_source: app.osm

    MDBoxLayout:
        size_hint_y: None
        height: "80dp"
        padding: "12dp"
        radius: [20, 20, 0, 0]

        MDIcon:
            id: arrow
            icon: "navigation"
            font_size: "48sp"
            halign: "center"
            valign: "middle"

            canvas.before:
                PushMatrix
                Rotate:
                    angle: root.arrow_angle
                    origin: self.center
            canvas.after:
                PopMatrix


"""

#API_URL = "http://127.0.0.1:8000/nearby"
API_URL = "http://127.0.0.1:8000/nearby?lat=49.875250&lon=13.303320&radius=5000"
#API_URL = "http://192.168.1.117:8000/nearby?lat=49.875250&lon=13.303320&radius=5000"

# Testovací souřadnice
#USER_LAT = 49.875250
#USER_LON = 13.303320
#RADIUS = 500

def azimut(lat1, lon1, lat2, lon2):
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)
    dlon = math.radians(lon2 - lon1)

    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (
    math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    )

    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360   



class PamatkyApp(MDApp):
    
    def build(self):
        print("=== BUILD START ===")
        # ===============================
        # MAP SOURCE (OpenStreetMap)
        # ===============================
        self.osm = MapSource(
            name="osm",
            url="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            cache_key="osm",
            tile_size=256,
            image_ext="png",
            attribution="© OpenStreetMap contributors"
        )
        self.zobrazene = set()
        self.pamatky = []
        self.user_heading = 0
        self.active_pamatka = None


        self.root = Builder.load_string(KV)
        print("=== KV LOADED ===")
        self.map = self.root.ids.map
        print("=== MAP FOUND ===", self.map)
        
        #kompas
        if platform == "android":
            try:
                compass.enable()
                Clock.schedule_interval(self.update_heading, 0.5)
            except Exception as e:
                print("Kompas nedostupný:", e)

        

        #data
        Clock.schedule_once(self.load_pamatky, 1)
        Clock.schedule_interval(self.check_nearby, 5)
        print("=== BUILD END ===")
        return self.root
    

    # ==================================================
    # KOMPAS
    # ==================================================
    # 
    def open_url(self, url):
        if platform == "android":
            from jnius import autoclass
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')
            intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            PythonActivity.mActivity.startActivity(intent)    

    def update_heading(self, dt):
        try:
            orientation = compass.orientation
            if orientation:
                self.user_heading = orientation[0] # azimut
            if self.active_pamatka:
                bearing = azimut(
                    49.875250,
                    13.303320,
                    float(self.active_pamatka["lat"]),
                    float(self.active_pamatka["lon"])
                )    
                self.update_arrow(bearing)
                 
        except Exception as e:
            print("Kompas chyba:", e)
    # ==================================================
    # NAČTENÍ PAMÁTEK – THREAD
    # ==================================================
    def load_pamatky(self, dt):
        def task():
            try:
                print("Volám API:", API_URL)
                r = requests.get(API_URL, timeout=5)
                data = r.json()

                if not isinstance(data, list):
                    print("API nevrátilo list:", data)
                    return

                Clock.schedule_once(lambda dt: self.add_markers(data))
            
            except Exception as e:
                print("API chyba:", e)

        Thread(target=task, daemon=True).start()

    # ==================================================
    # MARKERY
    # ==================================================
    def add_markers(self, data):
        self.pamatky = data

        for p in data:
            try:
                lat = float(p.get("lat"))
                lon = float(p.get("lon"))
            except Exception:
                print("Špatné souřadnice:", p)
                continue
            marker = MapMarkerPopup(lat=lat, lon=lon)
            marker.bind(on_press=lambda m, p=p: self.open_detail(p))
            self.map.add_widget(marker)

    # ==================================================
    # BLÍZKOST
    # ==================================================
    #automatická kontrola blízkých památek
    def check_nearby(self, dt):
        if not self.pamatky:
            return

        for p in self.pamatky:
            try:
                pid = p.get("id")
                dist = p.get("vzdalenost_m")

                if pid is None or dist is None:
                    continue

                if pid in self.zobrazene:
                    continue

                if dist < 30:
                    self.zobrazene.add(pid)

                    bearing = azimut(
                    49.875250,
                    13.303320,
                    float(p["lat"]),
                    float(p["lon"])
                    )

                    smer = self.smer_text(bearing, self.user_heading)
                    self.notify_pamatka(p, smer)

            except Exception as e:
                print("check_nearby chyba:", e)


    # ==================================================
    # UI
    # ==================================================

    def notify_pamatka(self, pamatka, smer):
        snackbar = Snackbar(
            duration=3
        )

        label = MDLabel(
            text=f"Památka: {pamatka['nazev']} ({round(pamatka['vzdalenost_m'])} m,{smer})",
            valign="middle",
            halign="left"
        )

        snackbar.add_widget(label)

        snackbar.bind(
            on_release=lambda *args: self.open_detail(pamatka)
        )

        snackbar.open()

    def update_arrow(self, bearing):
        if self.user_heading is None:
            return

        rotation = (bearing - self.user_heading + 360) % 360
        self.root.arrow_angle = -rotation
        
    
    def smer_text(self, bearing, heading):
        diff = (bearing - heading + 360) % 360

        if diff < 30 or diff > 330:
            return "před vámi"
        elif 30 <= diff < 120:
            return "vpravo"
        elif 120 <= diff < 240:
            return "za vámi"
        else:
            return "vlevo"
 
    


    # ==================================================
    # DETAIL
    # ==================================================


    def open_detail(self, pamatka):
        self.active_pamatka = pamatka
        bearing = azimut(
            49.875250,
            13.303320,
            float(pamatka["lat"]),
            float(pamatka["lon"])
        )
        self.update_arrow(bearing)
        smer = self.smer_text(bearing, self.user_heading)


        dialog = MDDialog(
            title=pamatka["nazev"],
            text=f"Vzdálenost: {round(pamatka['vzdalenost_m'], 1)} m\nSměr: {smer}",
            buttons=[
                MDFlatButton(
                    text="VÍC INFO",
                    on_release=lambda x: self.open_more_info(pamatka)
                ),
                MDFlatButton(
                    text="ZAVŘÍT",
                    on_release=lambda x: dialog.dismiss()
                ),
            ]
        )
        dialog.open()

    def open_more_info(self, pamatka):
       url = f"https://cs.wikipedia.org/wiki/{pamatka['nazev'].replace(' ', '_')}"
       self.open_url(url)

    
    



if __name__ == "__main__":
    PamatkyApp().run()
