import sys

for line in sys.stdin:
    line = line.replace('\\', '\\\\')
    line = line.replace('"', '\\"')
    sys.stdout.write('"'+line[:-1]+'\\n"\n')

