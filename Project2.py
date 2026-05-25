# =====================================================================
        # 📋 โมดูลการจัดสรรตารางงานให้รถ 2 คัน (Fleet Assignment & Dispatching)
        # =====================================================================
        st.markdown("### 📋 ตารางการปฏิบัติงานแยกตามยานพาหนะ (Fleet Dispatch Schedule)")
        
        # สร้างคลังรถขยะ (สมมติว่าดึงค่ามาจาก max_vehicles ที่ผู้ใช้กรอกใน Sidebar)
        # ในกรณีของนักศึกษาคือ 2 คัน
        fleet_schedule = {f"🚛 รถขยะคันที่ {i+1}": [] for i in range(max_vehicles)}
        
        # แจกจ่ายงานให้รถแต่ละคันสลับกันไป (Round-Robin Assignment)
        for i, r in enumerate(routes):
            vehicle_idx = i % max_vehicles # หาว่ารอบวิ่งนี้ตกเป็นของรถคันไหน
            vehicle_name = f"🚛 รถขยะคันที่ {vehicle_idx + 1}"
            
            # เก็บข้อมูลรอบวิ่งของรถคันนั้นๆ
            trip_info = {
                "trip_sequence": (i // max_vehicles) + 1, # รอบที่เท่าไหร่ของรถคันนี้
                "route": r,
                "vol": route_vols[i]
            }
            fleet_schedule[vehicle_name].append(trip_info)
        
        # แสดงผลบน Streamlit โดยแบ่งเป็นหน้าต่าง (Expander) ของรถแต่ละคัน
        for vehicle_name, trips in fleet_schedule.items():
            # สรุปปริมาตรและจำนวนรอบของรถแต่ละคัน
            total_vehicle_vol = sum([t['vol'] for t in trips])
            
            with st.expander(f"{vehicle_name} (รับผิดชอบทั้งหมด {len(trips)} เที่ยววิ่ง | ขยะรวม {total_vehicle_vol:.2f} ลบ.ม.)", expanded=True):
                if len(trips) == 0:
                    st.write("✅ ไม่มีภารกิจในรอบนี้ (รถว่าง)")
                else:
                    for t in trips:
                        st.info(f"**เที่ยววิ่งที่ {t['trip_sequence']}** (ปริมาตรขยะ: {t['vol']:.2f} / {max_capacity} ลบ.ม.): \n\n บ่อขยะ Depot ➡️ {' ➡️ '.join(t['route'])} ➡️ บ่อขยะ Depot")
