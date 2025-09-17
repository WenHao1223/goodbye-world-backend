from io import StringIO

# Shared log output
log_output = StringIO()

def log_print(msg):
    print(msg)
    log_output.write(msg + "\n")