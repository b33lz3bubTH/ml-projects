import os

class AppDataScrapper:
    def __init__(self):
        '''
            browser details
        '''
        self.name = "AppDataScrapper"

    def gather_info(self, xdepth=1):
        current_path = os.getcwd()
        process_list = os.popen("{}/utils/get_processes.sh".format(current_path)).read()
        process_list = process_list.split("\n")
        data = []
        for process in process_list:
            if process: data.append(process)

        return data
    def run(self):
        return self.gather_info()


