import platform
import browsers
import requests
import zipfile
import io
import shutil
import os
import stat


DRIVER_URL = "https://googlechromelabs.github.io/chrome-for-testing/latest-patch-versions-per-build-with-downloads.json"

def get_arch_for_driver():
    pname = platform.system().lower()
    arch = platform.machine().lower()
    if pname == "darwin":
        pname = "mac"
    
    arch_name = pname + "-" + arch
    
    return arch_name.replace("-x86_", "")

def get_instaled_browsers():
    installed_browsers = {}
    for b in browsers.browsers():
        installed_browsers[b["browser_type"]] = b["version"]
    return installed_browsers

def auto_install_driver(download_path):
    user_browsers = get_instaled_browsers()
    chromelike_browser = user_browsers.get("chrome", None)
    if not chromelike_browser:
        chromelike_browser = user_browsers.get("chromium", None)
    
    if not chromelike_browser:
        raise Exception("Chrome is the only supported browser at the time. Please install it first to continue with the app.")
    
    platform_data = get_arch_for_driver()
    
    print(chromelike_browser, platform_data)
    
    driver_req = requests.get(DRIVER_URL)
    
    if driver_req.status_code != 200:
        raise Exception("Error when requesting the browser available drivers.")
    
    available_drivers : dict = driver_req.json()["builds"]
    
    browser_version = ".".join(chromelike_browser.split(".")[:3])
    
    available_drivers = available_drivers.get(browser_version, None)
    
    if not available_drivers:
        raise Exception("The driver version for Chrome {} can't be found".format(browser_version))
    
    driver_urls = available_drivers["downloads"]["chromedriver"]
    
    drivers_dict = {}
    for d in driver_urls:
        drivers_dict[d["platform"]] = d["url"]
    
    selected_driver = drivers_dict[platform_data]
    
    drv = requests.get(selected_driver)
    
    if drv.status_code != 200:
        raise Exception("An error ocurred when downloading the Chrome driver.")
    
    zfile = zipfile.ZipFile(io.BytesIO(drv.content))
    driver_file = zfile.infolist()[-1]
    zfile.extract(driver_file.filename, download_path)
    
    shutil.move(os.path.join(download_path, driver_file.filename), download_path)
    os.rmdir(os.path.join(download_path, driver_file.filename.split("/")[0]))
    
    drv_path = os.path.join(download_path, driver_file.filename.split("/")[-1])
    
    if "win" not in platform_data:
        os.chmod(drv_path, stat.S_IEXEC)
    
    return drv_path