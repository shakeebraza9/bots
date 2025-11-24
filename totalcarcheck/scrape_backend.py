import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os

# Make sure done folder exists
if not os.path.exists("done"):
    os.makedirs("done")


def login_totalcarcheck(email, password):
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get("https://totalcarcheck.co.uk/Account/Login")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "UserName")))

    driver.find_element(By.ID, "UserName").send_keys(email)
    driver.find_element(By.ID, "Password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "input.btn.btn-primary").click()

    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.ID, "userIdLink"))
    )
    print("✅ Logged in successfully!")
    return driver


def fetch_vehicle_info(reg, driver, max_retries=3, delay_between=2):
    for attempt in range(1, max_retries + 1):
        try:
            url = f"https://totalcarcheck.co.uk/FreeCheck?regno={reg.replace(' ', '+')}"
            driver.get(url)

            # Check if rate limit message appears
            try:
                rate_limit = driver.find_element(
                    By.XPATH, '//pre[contains(text(), "You have checked too many vehicles")]'
                )
                if rate_limit and rate_limit.is_displayed():
                    print("⚠️ Too many requests. Waiting 60 seconds before retrying...")
                    time.sleep(60)
                    continue  # retry after waiting
            except:
                pass  # no rate limit message, continue normally

            mot_element = WebDriverWait(driver, 12).until(
                EC.presence_of_element_located((By.XPATH, '//span[text()="MOT Status"]/following::span[1]'))
            )
            mot_status = mot_element.text.strip()

            tax_element = WebDriverWait(driver, 12).until(
                EC.presence_of_element_located((By.XPATH, '//span[text()="Road Tax Status"]/following::span[1]'))
            )
            tax_status = tax_element.text.strip()

            try:
                days_left = driver.find_element(By.XPATH, '//span[text()="Days Left"]/following::span[1]').text.strip()
            except:
                days_left = ""

            tax_expiry = tax_status.replace("Expires:", "").replace("Expired:", "").strip()

            try:
                cost_12 = driver.find_element(By.XPATH, '//span[text()="12 Months Cost"]/following::span[1]').text.strip()
            except:
                cost_12 = ""

            try:
                cost_6 = driver.find_element(By.XPATH, '//span[text()="6 Months Cost"]/following::span[1]').text.strip()
            except:
                cost_6 = ""

            try:
                co2_output = driver.find_element(By.XPATH, '//span[text()="CO₂ Output"]/following::span[1]').text.strip()
            except:
                co2_output = ""

            try:
                body_style = driver.find_element(By.XPATH, '//span[text()="Body Style"]/following::span[1]').text.strip()
            except:
                body_style = ""

            data = {}
            try:
                rows = driver.find_elements(By.XPATH, '//table[@class="table table-responsive table-freecheck"]//tr')
                for row in rows:
                    try:
                        label = row.find_element(By.XPATH, './/span[@class="cert-label"]').text.strip()
                        value = row.find_element(By.XPATH, './/span[contains(@class,"cert-data")]').text.strip()
                        data[label] = value
                    except:
                        continue
            except Exception as e:
                print(f"⚠️ Error while extracting table: {e}")

            return mot_status, tax_status, tax_expiry, days_left, cost_12, cost_6, co2_output, body_style, data

        except Exception as e:
            print(f"⚠️ Attempt {attempt} failed for {reg}: {e}")
            time.sleep(delay_between)

    return "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", {}
