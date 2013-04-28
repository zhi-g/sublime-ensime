import sublime, os, functools
from functools import partial as bind

def _sbt_binary(window):
  return sublime.load_settings("Ensime.sublime-settings").get("sbt_binary", "sbt")

def _sbt_binary_exists(window):
  def check_file(fullpath):
    try:
      os.stat(fullpath)
      return True
    except os.error:
      pass
  if check_file(_sbt_binary(window)): return True
  for pathdir in os.environ["PATH"].split(os.pathsep):
    fname = os.path.join(pathdir, _sbt_binary(window))
    if check_file(fname): return True

def _sbt_flags(window):
  return sublime.load_settings("Ensime.sublime-settings").get("sbt_flags", ["-Dsbt.log.noformat=true"])

def sbt_command(window, *args):
  if _sbt_binary(window) and _sbt_binary_exists(window):
    return [_sbt_binary(window)] + _sbt_flags(window) + list(args)
  else:
    message =  "Configured path for the SBT binary, namely: " + _sbt_binary(window) + ", does not exist "
    message += "and cannot be resolved from your Sublime's PATH, namely: " + os.environ["PATH"] + "."
    message += "\n\n"
    message += "Consider updating the \"sbt_binary\" entry in Ensime configuration via Preferences > Package Settings > Ensime "
    message += "or adjusting your PATH. (Note that on Mac OS, Sublime doesn't read .bashrc or .bash_profile on startup, so "
    message += "it might be easier to provide an absolute path to the SBT binary rather than to try adjusting Sublime's PATH)."
    sublime.set_timeout(bind(sublime.error_message, message), 0)
    return None
