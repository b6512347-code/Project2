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
# 🛠️ ตั้งค่าฟอนต์ภาษาไทยสำหรับ Matplotlib
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
# ⚙️ ข้อมูลนำเข้า (Default Data)
# =====================================================================
DEFAULT_DATA = [
    ("Depot โรงจัดการขยะ", 14.862939, 102.027903, 0),
    ("ภูมิทัศน์(ใหม่)", 14.86903, 102.02135, 0.3),
    ("สวนพฤกษศาสตร์", 14.86991, 102.022113, 0.3),
    ("อุทยานผีเสื้อ", 14.871074, 102.022713, 0.3),
    ("ซินโครตรอน", 14.872731, 102.023232, 0.1),
    ("อาคารสุรพัฒน์ 2", 14.8754, 102.02286, 0.2),
    ("เซเว่น-อีเลฟเว่น เทคโนธานี", 14.876072, 102.022745, 0.7),
    ("หอดูดาว", 14.87414, 102.027598, 0.2),
    ("กาญจนาภิเษก", 14.873602, 102.026147, 0.5),
    ("อุทยานวิทยาศาสตร์", 14.87176, 102.01974, 0.3),
    ("เครื่องมือฯ9", 14.87516, 102.01613, 0.1),
    ("เครื่องมือฯ10", 14.876915, 102.015231, 0.5),
    ("เครื่องมือฯ6", 14.875158, 102.017524, 0.5),
    ("อาคารบริหาร", 14.88013, 102.02042, 0.4),
    ("สุรนิเวศ7", 14.89713, 102.011243, 0.2),
    ("โรงอาหารกาสะลองคำ", 14.896759, 102.012427, 0.5)
] # อาจารย์ย่อข้อมูลลงเล็กน้อยเพื่อให้รันบน Streamlit ได้เร็วขึ้นสำหรับการทดสอบ

# =====================================================================
# 📡 ฟังก์ชันดึงข้อมูล OSRM (ใช้ Cache เพื่อไม่ให้โหลดใหม่ทุกครั้ง)
# =====================================================================
@st.cache_data
def get_distance_matrix(locations):
    N = len(locations)
    distance_matrix = np.zeros((N, N))
    CHUNK_SIZE = 50
    
    # OSRM ต้องการ (Lon, Lat)
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
                st.error(f"OSRM API Error: {e}")
            time.sleep(0.5)
            
    return pd.DataFrame(distance_matrix) / 1000.0  # เมตร -> กิโลเมตร

# =====================================================================
# 🧠 Algorithms
# =====================================================================
def run_savings_algorithm(df_dist, demands, nodes, max_capacity):
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
    depot = nodes[0]
    depot_lat, depot_lon = locations[0][1], locations[0][2]
    
    # คำนวณมุม (Angle) ของแต่ละจุดเทียบกับ Depot
    customer_angles = []
    for i, item in enumerate(locations[1:]): # ข้าม Depot
        node_name = item[0]
        lat, lon = item[1], item[2]
        angle = math.degrees(math.atan2(lat - depot_lat, lon - depot_lon))
        if angle < 0: angle += 360
        customer_angles.append({"node": node_name, "angle": angle, "vol": demands[node_name]})
        
    # เรียงลำดับตามมุม (Sweep)
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
# 🎨 ฟังก์ชันวาดกราฟ (Visualization)
# =====================================================================
def plot_routes(routes, locations, nodes, title, grand_total_distance):
    depot = nodes[0]
    coords = {item[0]: (item[2], item[1]) for item in locations} # (Lon, Lat)
    
    fig, ax = plt.subplots(figsize=(12, 8))
    cmap = cm.get_cmap('tab20', len(routes))

    for trip_idx, route_seq in enumerate(routes):
        full_route = [depot] + route_seq + [depot]
        route_color = cmap(trip_idx % 20)

        x_vals = [coords[n][0] for n in full_route]
        y_vals = [coords[n][1] for n in full_route]
        
        ax.plot(x_vals, y_vals, marker='o', color=route_color, linewidth=2.5, markersize=5, alpha=0.8, label=f'Trip {trip_idx+1}')

        for k in range(len(x_vals)-1):
            ax.annotate('', xy=(x_vals[k+1], y_vals[k+1]), xytext=(x_vals[k], y_vals[k]),
                         arrowprops=dict(arrowstyle="->", color=route_color, lw=1.5, alpha=0.7))

    all_x = [coords[n][0] for n in nodes[1:]]
    all_y = [coords[n][1] for n in nodes[1:]]
    ax.scatter(all_x, all_y, color='dimgray', zorder=5, s=20)
    ax.scatter(coords[depot][0], coords[depot][1], color='red', marker='*', s=300, zorder=10, label='Depot')

    ax.set_title(f'{title}\nGrand Total Distance: {grand_total_distance:.2f} km', fontsize=16, fontweight='bold')
    ax.set_xlabel('Longitude (X)', fontsize=12)
    ax.set_ylabel('Latitude (Y)', fontsize=12)
    ax.grid(True, linestyle=':', alpha=0.5)
    ax.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), fontsize=10, title="Route Details")
    
    return fig

# =====================================================================
# 🖥️ Streamlit UI
# =====================================================================
st.set_page_config(page_title="Smart Waste Collection CVRP", layout="wide")
st.title("🚛 Smart Waste Collection Routing System")
st.markdown("ระบบวิเคราะห์และปรับปรุงเส้นทางเดินรถเก็บขยะ (CVRP) เพื่อลดต้นทุนและคาร์บอนฟุตพริ้นท์")

with st.sidebar:
    st.header("⚙️ System Configuration")
    max_capacity = st.number_input("ความจุสูงสุดของรถ (ลบ.ม.)", min_value=1.0, value=4.5, step=0.5)
    algorithm_choice = st.selectbox("เลือก Algorithm", ("Clarke-Wright Savings", "Sweep Algorithm"))
    use_default = st.checkbox("ใช้ข้อมูลทดสอบ (Default Data)", value=True)
    start_btn = st.button("🚀 Start Optimization")

if start_btn:
    if use_default:
        data_to_use = DEFAULT_DATA
    else:
        st.warning("⚠️ โหมดอัปโหลดไฟล์กำลังอยู่ในการพัฒนา กรุณาใช้ข้อมูลทดสอบไปก่อนครับ")
        st.stop()
        
    nodes = [item[0] for item in data_to_use]
    demands = {item[0]: item[3] for item in data_to_use}
    
    with st.spinner("📡 กำลังดึงข้อมูลระยะทางจริงจาก OSRM API..."):
        df_dist = get_distance_matrix(data_to_use)
        df_dist.columns = nodes
        df_dist.index = nodes

    with st.spinner(f"⚙️ กำลังประมวลผลด้วย {algorithm_choice}..."):
        if algorithm_choice == "Clarke-Wright Savings":
            routes, route_vols = run_savings_algorithm(df_dist, demands, nodes, max_capacity)
        elif algorithm_choice == "Sweep Algorithm":
            routes, route_vols = run_sweep_algorithm(data_to_use, demands, nodes, max_capacity)
            
        # คำนวณระยะทางรวมและ Carbon Footprint
        grand_total_distance = 0.0
        grand_total_volume = sum(route_vols)
        
        for r in routes:
            full_route = [nodes[0]] + r + [nodes[0]]
            dist = 0
            for k in range(len(full_route)-1):
                dist += df_dist.loc[full_route[k], full_route[k+1]]
            grand_total_distance += dist
            
        emission_factor = 0.3 # สมมติ 0.3 kgCO2/km
        carbon_emitted = grand_total_distance * emission_factor
        
        # แสดงผล
        st.success("✅ จัดเส้นทางสำเร็จ!")
        col1, col2, col3 = st.columns(3)
        col1.metric("ระยะทางรวม (Total Distance)", f"{grand_total_distance:.2f} km")
        col2.metric("ปริมาณขยะรวม (Total Volume)", f"{grand_total_volume:.2f} m³")
        col3.metric("คาร์บอนที่ปล่อย (Est. CO₂)", f"{carbon_emitted:.2f} kg", "- ลดลงจากแผนเดิม", delta_color="inverse")
        
        # แสดงแผนที่
        fig = plot_routes(routes, data_to_use, nodes, f"Optimized Routes ({algorithm_choice})", grand_total_distance)
        st.pyplot(fig)
        
        # สรุปเส้นทาง
        st.markdown("### 📋 สรุปเส้นทางเดินรถ")
        for i, r in enumerate(routes):
            st.write(f"**Trip {i+1}** (ปริมาตร {route_vols[i]:.2f} m³): Depot -> {' -> '.join(r)} -> Depot")
