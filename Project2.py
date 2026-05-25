import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
import math
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import urllib.request
import os
import matplotlib.font_manager as fm

# =====================================================================
# 🛠️ 1. การตั้งค่าทรัพยากรและฟอนต์ภาษาไทย (Font Configuration)
# =====================================================================
@st.cache_resource
def setup_thai_font():
    font_url = "https://github.com/Phonbopit/sarabun-webfont/raw/master/fonts/thsarabunnew-webfont.ttf"
    font_path = "thsarabunnew-webfont.ttf"
    if not os.path.exists(font_path):
        urllib.request.urlretrieve(font_url, font_path)
    fm.fontManager.addfont(font_path)
    plt.rcParams['font.family'] = 'TH Sarabun New'
    plt.rcParams['axes.unicode_minus'] = False

setup_thai_font()

# =====================================================================
# ⚙️ 2. ฐานข้อมูลตั้งต้น (Default Field Survey Data)
# =====================================================================
DEFAULT_DATA = [
    ("Depot โรงจัดการขยะ", 14.862939, 102.027903, 0),
    ("ภูมิทัศน์(ใหม่)", 14.86903, 102.02135, 0.3),
    ("สวนพฤกษศาสตร์", 14.86991, 102.022113, 0.3),
    ("อุทยานผีเสื้อ", 14.871074, 102.022713, 0.3),
    ("ซินโครตรอน", 14.872731, 102.023232, 0),
    ("อาคารสุรพัฒน์ 2", 14.8754, 102.02286, 0.2),
    ("อาคารสุรพัฒน์ 3", 14.874078, 102.022316, 0.4),
    ("เรือนไทย", 14.875346, 102.021912, 0.3),
    ("อาคารสุรพัฒน์ 1 จุดที่ 1", 14.87584, 102.02302, 0.2),
    ("อาคารสุรพัฒน์ 1 จุดที่ 2", 14.87572, 102.02284, 0.2),
    ("เซเว่น-อีเลฟเว่น เทคโนธานี จุดที่ 1", 14.876072, 102.022745, 0.7),
    ("เซเว่น-อีเลฟเว่น เทคโนธานี จุดที่ 2", 14.876125, 102.022341, 0.4),
    ("ร้านคอกาแฟ ข้าง 7-11 เทคโนธานี", 14.876938, 102.022377, 0.1),
    ("อาคารสุรสัมนาคาร", 14.876533, 102.024665, 0),
    ("โรงอาหารครัวท่านท้าว", 14.877234, 102.02026, 0.2),
    ("อาคารวิจัยมันสำปะหลัง", 14.874527, 102.020047, 0.2),
    ("หอดูดาว", 14.87414, 102.027598, 0.2),
    ("กาญจนาภิเษก", 14.873602, 102.026147, 0.5),
    ("กัญชา (สวนเกษตรอินทรีย์)", 14.871656, 102.026088, 0.4),
    ("สุรนิทัศน์", 14.871756, 102.024782, 0.2),
    ("อุทยานวิทยาศาสตร์", 14.87176, 102.01974, 0.3),
    ("อาคารงานภูมิทัศน์(เก่า)", 14.87273, 102.01824, 0.1),
    ("อาคารทดลอง-รถไฟ", 14.87422, 102.01791, 0.1),
    ("เครื่องมือฯ9", 14.87516, 102.01613, 0.1),
    ("ร้านกาแฟเด็กชายนมสด อาคารเครื่องมือ 9", 14.87412, 102.01637, 0.1),
    ("เครื่องมือฯ11", 14.87561, 102.01656, 0.1),
    ("เครื่องมือฯ12", 14.873347, 102.01454, 0),
    ("ร้านกาแฟ Polar Polar อาคารเครื่องมือ 12", 14.87458, 102.01527, 0.1),
    ("เครื่องมือฯ 16 (ฝั่งตรงข้าม อาคารเครื่องมือ 12)", 14.87456, 102.01447, 0.2),
    ("เครื่องมือฯ10", 14.876915, 102.015231, 0.5),
    ("เครื่องมือฯ6 และเทคโนวัสดุ", 14.875158, 102.017524, 0.5),
    ("เครื่องมือฯ7 จุดที่ 1", 14.874528, 102.021982, 0.4),
    ("เครื่องมือฯ7 จุดที่ 2", 14.875195, 102.020605, 0.2),
    ("เครื่องมือฯ5", 14.876734, 102.016839, 0.4),
    ("เครื่องมือฯ3", 14.8768643, 102.01825, 0.4),
    ("เครื่องมือฯ2", 14.876625, 102.01834, 0.4),
    ("ร้านกาแฟ Bus Stop หน้าอาคารเครื่องมือ 2", 14.87701, 102.01743, 0.1),
    ("เครื่องมือฯ4", 14.877436, 102.016732, 0.4),
    ("เครื่องมือฯ1", 14.877715, 102.017417, 0.5),
    ("อาคารวิชาการ1", 14.878152, 102.018926, 0.1),
    ("อาคารวิจัย", 14.878043, 102.019042, 0.5),
    ("อาคารวิชาการ2 จุดที่ 1", 14.87943, 102.02011, 0.5),
    ("อาคารวิชาการ2 จุดที่ 2", 14.87946, 102.0196, 0.1),
    ("ร้านกาแฟ See-U Café อาคารวิชาการ 2", 14.87945, 102.02009, 0.1),
    ("โรงอาหารเด่นทองกวาว", 14.879128, 102.020349, 0.1),
    ("อาคารบริหาร", 14.88013, 102.02042, 0.4),
    ("ศาลารอรถ-อาคารบริหาร", 14.88131, 102.02124, 0.2),
    ("อาคารส่วนอาคารสถานที่", 14.87975, 102.02205, 0.2),
    ("อาคารบริการสถานที่และกิจกรรม", 14.87978, 102.02124, 0.1),
    ("อาคารรักษาความปลอดภัย จุดที่ 1", 14.883761, 102.02421, 0.3),
    ("อาคารรักษาความปลอดภัย จุดที่ 2", 14.883344, 102.024802, 0.3),
    ("อาคารรักษาความปลอดภัย จุดที่ 3", 14.88327, 102.024581, 0.2),
    ("ร้านกาแฟ Amazon มทส.ประตู 1", 14.88361, 102.025, 0.1),
    ("ส่วนกิจการนักศึกษา 2", 14.88656, 102.01711, 0.3),
    ("สนามเปตอง", 14.8852, 102.01685, 0.5),
    ("สนามกีฬาสุรเริงไชย จุดที่ 1", 14.886019, 102.01908, 0.2),
    ("สนามกีฬาสุรเริงไชย จุดที่ 2", 14.886347, 102.018367, 0.2),
    ("ร้านกาแฟดอยช้าง อาคารสุรเริงไชย", 14.88631, 102.0184, 0.1),
    ("กีฬาภิรมย์ สนามแบตมินตัน จุดที่ 1", 14.886362, 102.015663, 0.4),
    ("กีฬาภิรมย์ สนามแบตมินตัน จุดที่ 2", 14.886342, 102.01558, 0.3),
    ("สุรพลากรีฑาสถาน", 14.887047, 102.017691, 0.4),
    ("สนามเทนนิส", 14.890428, 102.013754, 0.2),
    ("สุรนิเวศ7/อาคารบริการ", 14.89713, 102.011243, 0.2),
    ("สุรนิเวศ8", 14.89674, 102.010574, 0.1),
    ("สุรนิเวศ9/อาคารบริการ", 14.896464, 102.009932, 0.2),
    ("สุรนิเวศ10", 14.8965557, 102.00972, 0.2),
    ("สุรนิเวศ12/อาคารบริการ", 14.897603, 102.010749, 0.3),
    ("สุรนิเวศ11", 14.89797, 102.011122, 0.3),
    ("ป้อมยามประตู4", 14.901028, 102.009991, 0.3),
    ("โรงกรองน้ำประปา", 14.900384, 102.009308, 0.3),
    ("อาคารหน่วยสิ่งแวดล้อม", 14.90274, 102.009668, 0.2),
    ("ห้องประชุมรัชดาพัฒน์ (ของหน่วยสิ่งแวดล้อม)", 14.899768, 102.009965, 0.2),
    ("สุรนิเวศ13 EF", 14.899166, 102.012239, 0.1),
    ("สุรนิเวศ13 AB", 14.897875, 102.012431, 0.1),
    ("โรงอาหารกาสะลองคำ", 14.896759, 102.012427, 0.5),
    ("ศาลารอรถศาลาลอย", 14.896777, 102.012657, 0.3),
    ("เซเว่น-อีเลฟเว่น โรงอาหารกาสะลองคำ จุดที่ 1", 14.89652, 102.01277, 0.1),
    ("เซเว่น-อีเลฟเว่น โรงอาหารกาสะลองคำ จุดที่ 2", 14.89657, 102.01272, 0.2),
    ("ร้านกาแฟ K Coff ศาลาลอย", 14.89626, 102.01295, 0.3),
    ("อ่างสุระ จุดที่ 1", 14.87749, 102.01247, 0.1),
    ("อ่างสุระ จุดที่ 2", 14.87685, 102.00889, 0.3),
    ("อ่างสุระ จุดที่ 3", 14.88074, 102.01095, 0.4),
    ("สัตว์ทดลอง", 14.875691, 102.008908, 0.3),
    ("ศูนย์วิจัยเทคโนโลยีตัวอ่อน", 14.877418, 102.007463, 0.3),
    ("งานพืชไร่และเมล็ดพันธุ์", 14.87745, 102.00743, 0.2),
    ("โรงเชือดโควากิว (คอกขยะ)", 14.87567, 102.00739, 0),
    ("สถานีไฟฟ้าย่อย", 14.874195, 102.009501, 0.2),
    ("โรงประลองวัสดุขั้นสูง(หลังอาคารเครื่องมือ 16)", 14.87414, 102.01426, 0.2),
    ("บริษัทก่อสร้างพัฒนาวัสดุขั้นสูง(หลังอาคารเครื่องมือ 16)", 14.87188, 102.01456, 0.3),
    ("บ้านพักซอยสุขวิถี 1 (ใช้ถังแบบมีล้อ)", 14.88649, 102.00676, 4.3)
]

# =====================================================================
# 📡 3. การเชื่อมต่อโครงข่ายทางภูมิศาสตร์ (OSRM API Integration)
# =====================================================================
@st.cache_data(show_spinner=False)
def get_distance_matrix(locations):
    """ฟังก์ชันสร้าง Distance Matrix จากระยะทางขับขี่จริงบนถนน"""
    N = len(locations)
    distance_matrix = np.zeros((N, N))
    CHUNK_SIZE = 50
    # OSRM รับพิกัดแบบ (Longitude, Latitude)
    coords = [(item[2], item[1]) for item in locations]
    
    for i in range(0, N, CHUNK_SIZE):
        for j in range(0, N, CHUNK_SIZE):
            src_chunk = coords[i:i+CHUNK_SIZE]
            dst_chunk = coords[j:j+CHUNK_SIZE]
            combined_coords = src_chunk + dst_chunk
            coords_string = ";".join([f"{lon},{lat}" for lon, lat in combined_coords])
            
            num_src = len(src_chunk)
            num_dst = len(dst_chunk)
            sources_str = ";".join([str(x) for x in range(num_src)])
            destinations_str = ";".join([str(x) for x in range(num_src, num_src + num_dst)])
            
            url = f"http://router.project-osrm.org/table/v1/driving/{coords_string}?sources={sources_str}&destinations={destinations_str}&annotations=distance"
            try:
                response = requests.get(url)
                data = response.json()
                if data.get("code") == "Ok":
                    distance_matrix[i:i+num_src, j:j+num_dst] = np.array(data["distances"])
            except Exception as e:
                st.error(f"OSRM API Error (Matrix): {e}")
            time.sleep(0.5) # ป้องกันการส่ง Request ถี่เกินไป
            
    return pd.DataFrame(distance_matrix) / 1000.0  # แปลง เมตร เป็น กิโลเมตร

def get_osrm_route_geometry(route_seq, coords, depot):
    """ดึงพิกัดจุดเลี้ยว (Shapepoints) ตามแนวถนนจริงจาก OSRM Route API"""
    full_route = [depot] + route_seq + [depot]
    route_coords = [coords[n] for n in full_route]
    
    coords_string = ";".join([f"{lon},{lat}" for lon, lat in route_coords])
    url = f"http://router.project-osrm.org/route/v1/driving/{coords_string}?overview=full&geometries=geojson"
    
    try:
        response = requests.get(url)
        data = response.json()
        if data.get("code") == "Ok":
            return data["routes"][0]["geometry"]["coordinates"]
    except Exception as e:
        st.warning(f"⚠️ ไม่สามารถดึงเส้นทางตามแนวถนนจริงได้: {e}")
        
    return route_coords

# =====================================================================
# 🧠 4. อัลกอริทึมการจัดเส้นทาง (Optimization Engines)
# =====================================================================
def run_savings_algorithm(df_dist, demands, nodes, max_capacity):
    """Clarke-Wright Savings Algorithm (Capacitated)"""
    depot = nodes[0]
    customers = nodes[1:]
    
    savings = []
    for i in customers:
        for j in customers:
            if i != j:
                s_ij = df_dist.loc[i, depot] + df_dist.loc[depot, j] - df_dist.loc[i, j]
                if s_ij > 0:
                    savings.append((s_ij, i, j))
    savings.sort(key=lambda x: x[0], reverse=True)

    routes = [[c] for c in customers]
    route_vols = [demands[c] for c in customers]

    def get_route_idx(node):
        for idx, r in enumerate(routes):
            if node in r: return idx
        return -1

    for s_ij, i, j in savings:
        idx_i = get_route_idx(i)
        idx_j = get_route_idx(j)
        if idx_i != idx_j and idx_i != -1 and idx_j != -1:
            if routes[idx_i][-1] == i and routes[idx_j][0] == j:
                if route_vols[idx_i] + route_vols[idx_j] <= max_capacity:
                    routes[idx_i].extend(routes[idx_j])
                    route_vols[idx_i] += route_vols[idx_j]
                    routes.pop(idx_j)
                    route_vols.pop(idx_j)
                    
    return routes, route_vols

def run_sweep_algorithm(locations, demands, nodes, max_capacity):
    """Sweep Algorithm (Angular Clustering)"""
    depot = nodes[0]
    depot_lat, depot_lon = locations[0][1], locations[0][2]
    
    customer_angles = []
    for i, item in enumerate(locations[1:]):
        node_name = item[0]
        lat, lon = item[1], item[2]
        angle = math.degrees(math.atan2(lat - depot_lat, lon - depot_lon))
        if angle < 0: angle += 360
        customer_angles.append({"node": node_name, "angle": angle, "vol": demands[node_name]})
        
    customer_angles.sort(key=lambda x: x['angle'])
    
    routes = []
    route_vols = []
    current_route = []
    current_vol = 0.0
    
    for c in customer_angles:
        if current_vol + c['vol'] <= max_capacity:
            current_route.append(c['node'])
            current_vol += c['vol']
        else:
            routes.append(current_route)
            route_vols.append(current_vol)
            current_route = [c['node']]
            current_vol = c['vol']
            
    if current_route:
        routes.append(current_route)
        route_vols.append(current_vol)
        
    return routes, route_vols

# =====================================================================
# 🎨 5. โมดูลแสดงผลแผนที่ (Data Visualization Module)
# =====================================================================
def plot_routes(routes, locations, nodes, title, grand_total_distance):
    depot = nodes[0]
    coords = {item[0]: (item[2], item[1]) for item in locations} # (Lon, Lat)
    
    fig, ax = plt.subplots(figsize=(12, 8))
    cmap = cm.get_cmap('tab20', max(20, len(routes)))

    for trip_idx, route_seq in enumerate(routes):
        route_color = cmap(trip_idx % 20)

        # เรนเดอร์เส้นทางตามแนวถนนกายภาพจริง
        road_coords = get_osrm_route_geometry(route_seq, coords, depot)
        x_vals = [pt[0] for pt in road_coords]
        y_vals = [pt[1] for pt in road_coords]
        
        ax.plot(x_vals, y_vals, color=route_color, linewidth=2.5, alpha=0.8, label=f'Trip {trip_idx+1}')

        # สุ่มใส่ลูกศรเพื่อบอกทิศทาง (ไม่ให้รกเกินไป)
        for k in range(0, len(x_vals) - 1, 15):
            ax.annotate('', xy=(x_vals[k+1], y_vals[k+1]), xytext=(x_vals[k], y_vals[k]),
                         arrowprops=dict(arrowstyle="->", color=route_color, lw=1.5, alpha=0.7))
        
        time.sleep(0.2)

    # พล็อตจุดทิ้งขยะและจุด Depot
    all_x = [coords[n][0] for n in nodes[1:]]
    all_y = [coords[n][1] for n in nodes[1:]]
    ax.scatter(all_x, all_y, color='dimgray', zorder=5, s=25)
    ax.scatter(coords[depot][0], coords[depot][1], color='red', marker='*', s=350, zorder=10, label='Depot')

    # ใส่ป้ายกำกับจุด (Labeling)
    for node, (x, y) in coords.items():
        if node == depot:
            ax.text(x, y + 0.0004, 'DEPOT (บ่อขยะ)', fontsize=10, fontweight='bold', color='red', ha='center')
        else:
            short_name = str(node).replace(' จุดที่ ', '-')
            ax.text(x + 0.0001, y + 0.0001, short_name, fontsize=8, color='black', alpha=0.8)

    ax.set_title(f'{title}\n[ระบบแสดงผลอิงตามโครงข่ายถนนจริงบนระบบ GIS]', fontsize=16, fontweight='bold')
    ax.set_xlabel('Longitude (พิกัด X)', fontsize=12)
    ax.set_ylabel('Latitude (พิกัด Y)', fontsize=12)
    ax.grid(True, linestyle=':', alpha=0.5)
    ax.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), fontsize=10, title="ลำดับรอบวิ่ง (Trip No.)")
    
    return fig

# =====================================================================
# 🖥️ 6. หน้าจอผู้ใช้งาน (Streamlit UI - Dynamic Input Version)
# =====================================================================
st.set_page_config(page_title="Smart Waste Collection CVRP", layout="wide")
st.title("🚛 Smart Waste Collection Routing System")
st.markdown("ระบบวิเคราะห์และแสดงผลลัพธ์การจัดเส้นทางแบบปรับเปลี่ยนตัวแปรได้ (Dynamic VRP DSS) พร้อมโครงข่ายถนนจริง")

# --- แถบเครื่องมือด้านข้าง ---
with st.sidebar:
    st.header("⚙️ 1. ปรับแต่งตัวแปรยานพาหนะ")
    max_vehicles = st.number_input("จำนวนรถขยะที่มีในระบบ (คัน)", min_value=1, value=5, step=1)
    max_capacity = st.number_input("ความจุสูงสุดของรถ (ลบ.ม. / คัน)", min_value=1.0, value=4.5, step=0.5)
    
    st.header("⚙️ 2. เลือกอัลกอริทึม")
    algorithm_choice = st.selectbox("เทคนิคการจัดเส้นทาง", ("Clarke-Wright Savings", "Sweep Algorithm"))
    
    st.header("📂 3. นำเข้าข้อมูลภาคสนาม (Optional)")
    uploaded_file = st.file_uploader("อัปโหลดไฟล์ Excel/CSV (พิกัดและ Demand)", type=["xlsx", "csv"])
    st.info("💡 หากไม่อัปโหลด ระบบจะใช้ฐานข้อมูลจำลองของ มทส.")

# --- ส่วนจัดการข้อมูลและแสดงผล ---
st.subheader("📝 ตารางจัดการข้อมูลพิกัดและปริมาณขยะ (Data Editor)")
st.markdown("นักศึกษาสามารถ **เพิ่มแถวใหม่ (Add Row)** เพื่อใส่พิกัดใหม่ หรือ **แก้ไขตัวเลข Demand** ในตารางด้านล่างได้โดยตรง")

if uploaded_file is not None:
    if uploaded_file.name.endswith('.csv'):
        df_input = pd.read_csv(uploaded_file)
    else:
        df_input = pd.read_excel(uploaded_file)
else:
    df_input = pd.DataFrame(DEFAULT_DATA, columns=["Node_Name", "Latitude", "Longitude", "Demand"])

# แสดงตารางให้ผู้ใช้โต้ตอบและแก้ไขข้อมูลได้
edited_df = st.data_editor(df_input, num_rows="dynamic", use_container_width=True)

# ปุ่มดำเนินการ
start_btn = st.button("🚀 ยืนยันข้อมูลและเริ่มการประมวลผล (Start Optimization)", type="primary")

if start_btn:
    data_to_use = edited_df.values.tolist()
    nodes = edited_df["Node_Name"].tolist()
    demands = dict(zip(edited_df["Node_Name"], edited_df["Demand"]))
    
    # Validation: ตรวจสอบไม่ให้ Demand จุดใดจุดหนึ่งเกินความจุรถ
    max_single_demand = max(demands.values())
    if max_single_demand > max_capacity:
        st.error(f"❌ พบข้อผิดพลาดทางโลจิสติกส์: มีจุดเก็บขยะบางจุด (Demand = {max_single_demand}) ที่มีปริมาณเกินความจุของรถ ({max_capacity})")
        st.stop()

    osrm_input_format = [(row[0], row[1], row[2], row[3]) for row in data_to_use]

    with st.spinner("📡 ขั้นตอนที่ 1/3: กำลังคำนวณระยะทางขับขี่จริงระหว่างคู่จุดจอดจาก OSRM API..."):
        df_dist = get_distance_matrix(osrm_input_format)
        df_dist.columns = nodes
        df_dist.index = nodes

    with st.spinner(f"⚙️ ขั้นตอนที่ 2/3: กำลังประมวลผลการจัดกลุ่มเส้นทางด้วย {algorithm_choice}..."):
        if algorithm_choice == "Clarke-Wright Savings":
            routes, route_vols = run_savings_algorithm(df_dist, demands, nodes, max_capacity)
        elif algorithm_choice == "Sweep Algorithm":
            routes, route_vols = run_sweep_algorithm(osrm_input_format, demands, nodes, max_capacity)
            
        total_trips_needed = len(routes)
        if total_trips_needed > max_vehicles:
            st.warning(f"⚠️ ข้อสังเกตเชิงปฏิบัติการ: ระบบต้องใช้รอบวิ่งทั้งหมด {total_trips_needed} รอบ ซึ่งเกินจำนวนยานพาหนะที่มี ({max_vehicles} คัน)")
            
        # คำนวณสมรรถนะการปฏิบัติงาน (KPIs)
        grand_total_distance = 0.0
        grand_total_volume = sum(route_vols)
        
        for r in routes:
            full_route = [nodes[0]] + r + [nodes[0]]
            dist = 0
            for k in range(len(full_route)-1):
                dist += df_dist.loc[full_route[k], full_route[k+1]]
            grand_total_distance += dist
            
        emission_factor = 0.3 # สัมประสิทธิ์การปล่อยก๊าซ CO2 สำหรับรถบรรทุกขยะขนาดกลาง
        carbon_emitted = grand_total_distance * emission_factor
        
        st.success("✅ ออปติไมซ์คำตอบและออกแบบเส้นทางเสร็จสมบูรณ์!")
        
        # แสดงแดชบอร์ด
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("รอบวิ่งที่ต้องใช้ (Trips)", f"{total_trips_needed} เที่ยว")
        col2.metric("ระยะทางขับขี่จริงรวม", f"{grand_total_distance:.2f} กม.")
        col3.metric("ปริมาตรขยะที่เก็บขน", f"{grand_total_volume:.2f} ลบ.ม.")
        col4.metric("คาร์บอนฟุตพริ้นท์ (CO₂)", f"{carbon_emitted:.2f} กก.")
        
        # เรนเดอร์กราฟิก
        with st.spinner("🗺️ ขั้นตอนที่ 3/3: กำลังเรนเดอร์ลายเส้นตามพิกัดถนนจริงบนระบบสารสนเทศภูมิศาสตร์..."):
            fig = plot_routes(routes, osrm_input_format, nodes, f"แผนภาพจำลองเส้นทางจริง ({algorithm_choice})", grand_total_distance)
            st.pyplot(fig)
        
        # ตารางปฏิบัติงาน (Dispatch Schedule)
        st.markdown("### 📋 ตารางลำดับการปฏิบัติงานรายเที่ยวรถ (Dispatch Schedule)")
        for i, r in enumerate(routes):
            st.info(f"🚚 **เที่ยววิ่งที่ {i+1}** (ปริมาตรสะสม: {route_vols[i]:.2f} / {max_capacity} ลบ.ม.): \n\n บ่อขยะ Depot ➡️ {' ➡️ '.join(r)} ➡️ บ่อขยะ Depot")
