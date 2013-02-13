import sublime, os, functools
from functools import partial as bind

def sbt_binary():
  return sublime.load_settings("Ensime.sublime-settings").get("sbt_binary", "sbt")

def sbt_flags():
  return sublime.load_settings("Ensime.sublime-settings").get("sbt_flags", ["-Dsbt.log.noformat=true"])

def sbt_command(*args):
  return [sbt_binary()] + sbt_flags() + list(args) if sbt_binary() else None