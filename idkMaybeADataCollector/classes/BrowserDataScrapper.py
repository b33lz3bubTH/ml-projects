import os

class BrowserDataScrapper:
    def __init__(self, browser_name="brave"):
        '''
            browser details
        '''
        browser_info = {
            'brave': {
                'SESSION_FOLDER': '/home/sourav/.config/BraveSoftware/Brave-Browser/Default/Sessions'
                }
        }
        self.name = "BrowserDataScrapper"
        self.browser_details = browser_info[browser_name]

    def gather_info(self, xdepth=1):
        data = []
        session_files = os.listdir(self.browser_details['SESSION_FOLDER'])
        for session_file in session_files:
            session_data = os.popen("strings {} | grep http | tail -n 30".format(
                self.browser_details['SESSION_FOLDER'] + "/{}".format(session_file)
                )
            ).read()
            data.append(session_data)
        # processing  needed
        processed_data = []
        for string_data in data:
            splitted_data = string_data.split("\n")
            for split_string in splitted_data:
                if split_string: processed_data.append(split_string)

        return processed_data

    def run(self):
        return self.gather_info()

