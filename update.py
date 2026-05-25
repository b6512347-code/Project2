# =====================================================================
# 🖥️ Streamlit Web Interface Configuration (Dynamic Data Entry)
# =====================================================================
st.set_page_config(page_title="Smart Waste Collection CVRP", layout="wide")
st.title("🚛 Smart Waste Collection Routing System (Dynamic Inputs)")
st.markdown("ระบบวิเคราะห์และแสดงผลลัพธ์การจัดเส้นทาง โดยรองรับการเพิ่มจุดเก็บขยะและปรับเปลี่ยนข้อมูลได้อย่างอิสระ")

# --- แถบด้านข้าง: ตั้งค่าตัวแปรยานพาหนะและอัลกอริทึม ---
with st.sidebar:
    st.header("⚙️ 1. ปรับแต่งตัวแปรยานพาหนะ")
    # รองรับการเพิ่มเงื่อนไขจำนวนรถที่มี (เพื่อเช็คว่าผลลัพธ์ใช้รถเกินที่มีหรือไม่)
    max_vehicles = st.number_input("จำนวนรถขยะที่มีในระบบ (คัน)", min_value=1, value=5, step=1)
    max_capacity = st.number_input("ความจุสูงสุดของรถ (ลบ.ม. / คัน)", min_value=1.0, value=4.5, step=0.5)
    
    st.header("⚙️ 2. เลือกอัลกอริทึม")
    algorithm_choice = st.selectbox("อัลกอริทึมคำนวณ", ("Clarke-Wright Savings", "Sweep Algorithm"))
    
    st.header("📂 3. นำเข้าข้อมูล (Optional)")
    uploaded_file = st.file_uploader("อัปโหลดไฟล์ Excel/CSV (พิกัดและ Demand)", type=["xlsx", "csv"])

# --- พื้นที่หลัก: จัดการข้อมูลพิกัดและ Demand ---
st.subheader("📝 ตารางจัดการข้อมูลพิกัดและปริมาณขยะ (Data Editor)")
st.markdown("นักศึกษาสามารถ **พิมพ์เพิ่มแถวใหม่ (Add Row)** เพื่อเพิ่มพิกัด หรือ **แก้ไขตัวเลข Demand** ในตารางด้านล่างนี้ได้โดยตรงก่อนกดคำนวณครับ")

# จัดการข้อมูลนำเข้า (หากไม่อัปโหลดไฟล์ ให้ใช้ Default Data แปลงเป็น DataFrame)
if uploaded_file is not None:
    if uploaded_file.name.endswith('.csv'):
        df_input = pd.read_csv(uploaded_file)
    else:
        df_input = pd.read_excel(uploaded_file)
else:
    df_input = pd.DataFrame(DEFAULT_DATA, columns=["Node_Name", "Latitude", "Longitude", "Demand"])

# ฟีเจอร์เด็ด: ให้ผู้ใช้แก้ไขตารางบนหน้าเว็บได้เลย (เพิ่ม/ลดพิกัด ปรับ Demand)
edited_df = st.data_editor(df_input, num_rows="dynamic", use_container_width=True)

# ปุ่มกดคำนวณ
start_btn = st.button("🚀 ยืนยันข้อมูลและเริ่มการประมวลผล (Start Optimization)", type="primary")

if start_btn:
    # ดึงข้อมูลจากตารางที่ผู้ใช้แก้ไขแล้วมาแปลงกลับเป็น List และ Dictionary
    data_to_use = edited_df.values.tolist()
    nodes = edited_df["Node_Name"].tolist()
    demands = dict(zip(edited_df["Node_Name"], edited_df["Demand"]))
    
    # ⚠️ ตรวจสอบเบื้องต้น: Demand จุดใดจุดหนึ่ง ต้องไม่เกินความจุรถ
    max_single_demand = max(demands.values())
    if max_single_demand > max_capacity:
        st.error(f"❌ พบข้อผิดพลาด: มีจุดเก็บขยะบางจุด (Demand = {max_single_demand}) ที่มีปริมาณเกินความจุของรถ ({max_capacity}) กรุณาปรับแก้ข้อมูล!")
        st.stop()

    with st.spinner("📡 ขั้นตอนที่ 1/3: กำลังคำนวณระยะทางขับขี่จริงระหว่างคู่จุดจอดจาก OSRM API..."):
        # ส่งค่าที่มีการเรียงลำดับใหม่ [ชื่อ, Lat, Lon, Demand] เข้าฟังก์ชัน
        osrm_input_format = [(row[0], row[1], row[2], row[3]) for row in data_to_use]
        df_dist = get_distance_matrix(osrm_input_format)
        df_dist.columns = nodes
        df_dist.index = nodes

    with st.spinner(f"⚙️ ขั้นตอนที่ 2/3: กำลังประมวลผลการจัดกลุ่มเส้นทางด้วย {algorithm_choice}..."):
        if algorithm_choice == "Clarke-Wright Savings":
            routes, route_vols = run_savings_algorithm(df_dist, demands, nodes, max_capacity)
        elif algorithm_choice == "Sweep Algorithm":
            routes, route_vols = run_sweep_algorithm(osrm_input_format, demands, nodes, max_capacity)
            
        # ตรวจสอบเงื่อนไขจำนวนรถ
        total_trips_needed = len(routes)
        if total_trips_needed > max_vehicles:
            st.warning(f"⚠️ คำเตือน: ระบบจัดเส้นทางได้ {total_trips_needed} รอบ/คัน ซึ่งเกินกว่าจำนวนรถที่คุณระบุไว้ ({max_vehicles} คัน) อาจต้องพิจารณาเพิ่มรอบวิ่งหรือเพิ่มรถครับ")
            
        # คำนวณรอยเท้าระยะทางและคาร์บอน
        grand_total_distance = 0.0
        grand_total_volume = sum(route_vols)
        
        for r in routes:
            full_route = [nodes[0]] + r + [nodes[0]]
            dist = 0
            for k in range(len(full_route)-1):
                dist += df_dist.loc[full_route[k], full_route[k+1]]
            grand_total_distance += dist
            
        emission_factor = 0.3 
        carbon_emitted = grand_total_distance * emission_factor
        
        # แสดงผลแดชบอร์ด
        st.success("✅ ออปติไมซ์คำตอบและออกแบบเส้นทางเสร็จสมบูรณ์!")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("จำนวนรถ/รอบที่ต้องใช้", f"{total_trips_needed} เที่ยว")
        col2.metric("ระยะทางขับขี่จริงรวม", f"{grand_total_distance:.2f} กม.")
        col3.metric("ปริมาตรขยะที่เก็บขน", f"{grand_total_volume:.2f} ลบ.ม.")
        col4.metric("คาร์บอนฟุตพริ้นท์", f"{carbon_emitted:.2f} กก. CO₂")
        
        # แสดงผลลัพธ์ภาพกราฟิก
        with st.spinner("🗺️ ขั้นตอนที่ 3/3: กำลังเรนเดอร์ลายเส้นเลี้ยวตามพิกัดถนนจริงบนแผนที่..."):
            fig = plot_routes(routes, osrm_input_format, nodes, f"แผนภาพจำลองเส้นทางจริง ({algorithm_choice})", grand_total_distance)
            st.pyplot(fig)
        
        # ตารางสรุปแผนงาน
        st.markdown("### 📋 ตารางลำดับการปฏิบัติงานรายเที่ยวรถ")
        for i, r in enumerate(routes):
            st.info(f"🚚 **เที่ยววิ่งที่ {i+1}** (ปริมาตรขยะสะสม: {route_vols[i]:.2f} / {max_capacity} ลบ.ม.): \n\n บ่อขยะ Depot ➡️ {' ➡️ '.join(r)} ➡️ บ่อขยะ Depot")
