# --- [ฟังก์ชันสำหรับคลิกหน้าถัดไป - ฉบับง่าย] ---
import re
import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def go_to_next_page(driver, wait):
    """
    ฟังก์ชันคลิกหน้าถัดไป - ไม่ต้องใช้ xpath ตาราง
    """
    print("\n--- กำลังตรวจสอบ Pagination ---")
    
    try:
        # 1. ตรวจสอบจากข้อความ "แสดงข้อมูล 1 - 10 จาก ... รายการ"
        try:
            pagination_text_element = driver.find_element(By.XPATH, "//div[contains(text(), 'แสดงข้อมูล')]")
            pagination_text = pagination_text_element.text
            print(f"พบข้อความ Pagination: {pagination_text}")
            
            # ดึงตัวเลขออกมา เช่น "แสดงข้อมูล 1 - 10 จาก 13 รายการ"
            numbers = re.findall(r'\d+', pagination_text)
            
            if len(numbers) >= 3:
                current_end = int(numbers[1])    # เลขหลัง "-" (เช่น 10)
                total_items = int(numbers[2])    # เลขรวม (เช่น 13)
                
                print(f"แสดงถึงรายการที่: {current_end}, รวมทั้งหมด: {total_items}")
                
                # ถ้าแสดงยังไม่ครบ แสดงว่ามีหน้าถัดไป
                if current_end < total_items:
                    print("-> มีหน้าถัดไป, กำลังคลิกปุ่ม Next")
                    
                    # 2. หาปุ่ม Next และคลิก
                    # ลองหลายวิธีในการหาปุ่ม Next
                    next_button = None
                    
                    # วิธีที่ 1: หาจาก text ">"
                    try:
                        next_button = driver.find_element(By.XPATH, "//button[contains(text(), '>')]")
                        print("พบปุ่ม Next จาก text '>'")
                    except:
                        pass
                    
                    # วิธีที่ 2: หาจาก CSS selector
                    if not next_button:
                        try:
                            next_button = driver.find_element(By.CSS_SELECTOR, "button[class*='btn']:last-child")
                            print("พบปุ่ม Next จาก CSS selector")
                        except:
                            pass
                    
                    # วิธีที่ 3: หาจาก pagination container
                    if not next_button:
                        try:
                            # หาจาก div ที่มีข้อความ "แสดงข้อมูล" แล้วหา button ถัดไป
                            pagination_container = pagination_text_element.find_element(By.XPATH, "../..")
                            buttons = pagination_container.find_elements(By.TAG_NAME, "button")
                            if buttons:
                                next_button = buttons[-1]  # ปุ่มสุดท้าย
                                print("พบปุ่ม Next จาก pagination container")
                        except:
                            pass
                    
                    # วิธีที่ 4: หาจากทั้งหน้า
                    if not next_button:
                        try:
                            buttons = driver.find_elements(By.TAG_NAME, "button")
                            for btn in buttons:
                                if ">" in btn.text or "next" in btn.text.lower():
                                    next_button = btn
                                    print("พบปุ่ม Next จากการค้นหาทั้งหน้า")
                                    break
                        except:
                            pass
                    
                    # 3. คลิกปุ่ม Next
                    if next_button:
                        try:
                            # ตรวจสอบว่าปุ่มคลิกได้หรือไม่
                            if next_button.is_enabled():
                                # เลื่อนไปยังปุ่ม
                                driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                                time.sleep(0.5)
                                
                                # คลิกด้วย ActionChains
                                ActionChains(driver).move_to_element(next_button).click().perform()
                                
                                # รอให้หน้าโหลด
                                time.sleep(2)
                                
                                print("-> คลิกปุ่ม Next สำเร็จ!")
                                return True
                            else:
                                print("-> ปุ่ม Next ไม่สามารถคลิกได้ (disabled)")
                                return False
                        except Exception as e:
                            print(f"!!! เกิดข้อผิดพลาดขณะคลิกปุ่ม Next: {e}")
                            return False
                    else:
                        print("!!! ไม่พบปุ่ม Next")
                        return False
                else:
                    print("-> เป็นหน้าสุดท้ายแล้ว")
                    return False
            else:
                print("!!! ไม่สามารถแยกตัวเลขจากข้อความ pagination ได้")
                return False
                
        except NoSuchElementException:
            print("!!! ไม่พบข้อความ pagination")
            return False
            
    except Exception as e:
        print(f"!!! เกิดข้อผิดพลาดร้ายแรง: {e}")
        return False

# --- วิธีใช้งาน (ง่ายขึ้น) ---
def process_all_pages(driver, wait):
    """
    ฟังก์ชันประมวลผลข้อมูลทุกหน้า
    """
    page_number = 1
    
    while True:
        print(f"\n=== กำลังประมวลผลหน้าที่ {page_number} ===")
        
        # ประมวลผลข้อมูลในหน้าปัจจุบัน
        # ... (ใส่โค้ดอ่านข้อมูลของคุณที่นี่) ...
        
        # พยายามไปหน้าถัดไป
        if go_to_next_page(driver, wait):
            page_number += 1
            print(f"ไปหน้าถัดไป (หน้า {page_number}) สำเร็จ")
        else:
            print("ไม่มีหน้าถัดไป หรือเป็นหน้าสุดท้ายแล้ว")
            break
    
    print(f"\n=== ประมวลผลเสร็จสิ้น รวม {page_number} หน้า ===")

# --- ตัวอย่างการใช้งาน ---
if __name__ == "__main__":
    # ตัวอย่างการใช้งาน
    print("--- เริ่มประมวลผลข้อมูลทุกหน้า ---")
    
    # วิธีใช้แบบง่าย
    process_all_pages(driver, wait)
    
    # หรือใช้แบบทีละหน้า
    # if go_to_next_page(driver, wait):
    #     print("มีหน้าถัดไป")
    # else:
    #     print("ไม่มีหน้าถัดไป")