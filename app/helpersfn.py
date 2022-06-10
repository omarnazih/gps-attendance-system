import datetime

def getDay():
   now = datetime.datetime.now()
   return now.strftime("%A")  

def getTimeHM():
   now = datetime.datetime.now()
   return f"{now.hour}:{now.minute}"

def ifEmpty(var, val):
  if var == '':
    return val
  return var

def nvl(var):
  if var == '':
    return 'null'
  return var

