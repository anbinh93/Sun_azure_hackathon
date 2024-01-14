import shutil
import zipfile
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
import os
import sys
sys.path.append(os.getcwd())


manifest_json = """
{
    "version": "1.0.0",
    "manifest_version": 2,
    "name": "Chrome Proxy",
    "permissions": [
        "proxy",
        "tabs",
        "unlimitedStorage",
        "storage",
        "<all_urls>",
        "webRequest",
        "webRequestBlocking"
    ],
    "background": {
        "scripts": ["background.js"]
    },
    "minimum_chrome_version":"22.0.0"
}
"""


def get_background_js(host, port, user, password):
    background_js = """
    var config = {
            mode: "fixed_servers",
            rules: {
            singleProxy: {
                scheme: "http",
                host: "%s",
                port: parseInt(%s)
            },
            bypassList: ["localhost"]
            }
        };

    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

    function callbackFn(details) {
        return {
            authCredentials: {
                username: "%s",
                password: "%s"
            }
        };
    }

    chrome.webRequest.onAuthRequired.addListener(
                callbackFn,
                {urls: ["<all_urls>"]},
                ['blocking']
    );
    """ % (host, port, user, password)

    return background_js


class ChromeDriver():
    def __init__(self, headless: bool = False, **kwargs) -> None:
        '''
            Keyword arguments:
            - headless: bool
            - download_path: str
            - authenticate_proxy: dict

            ```python
            {
                'host': Any,
                'port': Any,
                'user': Any,
                'password': Any
            }
            ```
        '''
        # Get the keyword arguments
        self.headless = headless
        self.disable_js = kwargs.get('disable_js', False)
        self.disable_images = kwargs.get('disable_images', False)

        self.download_path = kwargs.get('download_path', None)
        self.authenticate_proxy = kwargs.get('authenticate_proxy', None)

        # Initiate the driver
        if not os.path.exists('chromedriver.exe'):
            driver_path = ChromeDriverManager().install()
            shutil.copy(driver_path, 'chromedriver.exe')

        webdriver_service = Service('chromedriver.exe')

        chrome_options = Options()
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')

        if self.headless:
            chrome_options.add_argument("--headless")

        if self.disable_js:
            chrome_options.add_experimental_option("prefs", {'profile.managed_default_content_settings.javascript': 2})

        if self.disable_images:
            chrome_options.add_experimental_option("prefs", {'profile.managed_default_content_settings.images': 2})

        if self.download_path is not None:
            prefs = {"download.default_directory": self.download_path}
            chrome_options.add_experimental_option("prefs", prefs)

        if self.authenticate_proxy is not None:
            host = self.authenticate_proxy['host']
            port = self.authenticate_proxy['port']
            username = self.authenticate_proxy['username']
            password = self.authenticate_proxy['password']

            pluginfile_name = 'proxy_auth_plugin.zip'
            pluginfile_path = os.path.join(os.getcwd(), 'src', 'utils', pluginfile_name)

            with zipfile.ZipFile(pluginfile_path, 'w') as zp:
                zp.writestr("manifest.json", manifest_json)
                zp.writestr("background.js", get_background_js(
                    host, port, username, password))
            chrome_options.add_extension(pluginfile_path)

        # Get the driver
        self.driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)

        # Set the timeout
        self.driver.set_page_load_timeout(60)
