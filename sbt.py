import sublime, os, functools
from functools import partial as bind

def sbt_binary():
  return sublime.load_settings("Ensime.sublime-settings").get("sbt_binary", "sbt")
