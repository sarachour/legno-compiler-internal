
def keys_in_dict(keys,dict_):
  for key in keys:
    if not key in dict_:
      return False
  return True
