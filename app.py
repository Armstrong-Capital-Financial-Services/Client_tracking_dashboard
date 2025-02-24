import time
import os
import tempfile
import pandas as pd
import streamlit as st
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Set refresh interval in minutes
REFRESH_INTERVAL = 2  

# Initialize session state for refresh tracking
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

def create_driver():
    options = Options()
    options.add_argument("--headless")  
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    temp_dir = tempfile.gettempdir()

    options.add_experimental_option("prefs", {
        "download.default_directory": temp_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })

    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    ), temp_dir

def login_and_navigate(driver):
    try:
        driver.get("https://publisher.smallcase.com/login")
        st.write("Logging in...")

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//input[@type='email']")))
        email_input = driver.find_element(By.XPATH, "//input[@type='email']")
        email_input.send_keys('manju@armstrong-cap.com')

        password_input = driver.find_element(By.XPATH, "//input[@type='password']")
        password_input.send_keys('Manju9')

        submit = driver.find_element(By.XPATH, "//input[@type='submit']")
        submit.click()

        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input.login__login-text-pwd__11RBh"))
        )
        inputs = driver.find_elements(By.CSS_SELECTOR, "input.login__login-text-pwd__11RBh")

        inputs[0].send_keys("Vennela")
        time.sleep(3)
        inputs[1].send_keys("Bangalore")

        submit = driver.find_element(By.XPATH, "//input[@type='submit']")
        submit.click()

        # Handle modal
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "NamingMigrationModal__modal-cta__2JGF9"))
        )
        button.click()

        # Navigate to Users tab
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.LINK_TEXT, "Users")))
        other_tab = driver.find_element(By.LINK_TEXT, "Users")
        other_tab.click()
        st.write("Navigated to Users tab...")

        # Download button
        d_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "PrivateSmallcaseUsers__download-SVG__3VuSB"))
        )
        d_button.click()
        time.sleep(3)
        d_button.click()
        st.write("Download initiated...")

    except Exception as e:
        st.error(f"An error occurred: {e}")
        driver.quit()

def wait_for_download(temp_dir):
    time.sleep(2)  # Initial wait for download to start
    downloaded_file = None
    timeout = 15  
    start_time = time.time()

    while time.time() - start_time < timeout:
        files = os.listdir(temp_dir)
        csv_files = [f for f in files if f.endswith('.csv')]
        crdownload_files = [f for f in files if f.endswith('.crdownload')]

        if csv_files and not crdownload_files:
            downloaded_file = os.path.join(temp_dir, csv_files[0])
            break

        time.sleep(1)

    return downloaded_file

def main():
    st.title("📊 Smallcase Users Data Downloader")

    # Auto-refresh logic
    if time.time() - st.session_state.last_refresh > REFRESH_INTERVAL * 60:
        st.session_state.last_refresh = time.time()
        st.experimental_rerun()

    st.write("Click the button below to start the process.")

    if st.button("Start Download"):
        driver, temp_dir = create_driver()

        try:
            login_and_navigate(driver)
            downloaded_file = wait_for_download(temp_dir)

            if downloaded_file:
                st.success(f"✅ File downloaded successfully!")

                # Store downloaded file in session state
                st.session_state["downloaded_file"] = downloaded_file

                # Display options: View Data or Download Data
                option = st.radio("Choose an option:", ["View Data", "Download Data"])

                if option == "View Data":
                    df = pd.read_csv(downloaded_file)
                    st.dataframe(df)

                elif option == "Download Data":
                    with open(downloaded_file, "rb") as file:
                        st.download_button(
                            label="📥 Download CSV File",
                            data=file,
                            file_name="smallcase_users.csv",
                            mime="text/csv"
                        )

            else:
                st.error("⚠️ Download failed or timed out.")
        finally:
            driver.quit()

    # Display refresh timer
    st.write(f"🔄 Next refresh in {REFRESH_INTERVAL} minutes...")
    time.sleep(REFRESH_INTERVAL * 60)
    st.experimental_rerun()  

if __name__ == "__main__":
    main()
