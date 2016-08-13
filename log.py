# generates a log file

class Log:
    def __init__(self, filename, overwrite = False, silent = False):
        self.filename = filename
        self.silent = silent
        if (overwrite):
            f = open(self.filename, 'w')
            f.close()
        

    def set_message(self, message):
        self.message = message

    def get_silent(self):
        return self.silent
    
    def record(self, message):
        if (not self.silent):
            print(message)

        fileoption = 'a'
        f = open(self.filename, fileoption)
        f.write(message + "\n")
        f.close()
