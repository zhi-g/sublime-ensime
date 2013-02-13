import sublime, os, sys, traceback, json, re
from paths import *

def location(env):
  return env.session_file

def exists(env):
  return not not location(env)

class Breakpoint(object):
  def __init__(self, file_name, line):
    self.file_name = file_name or ""
    self.line = line or 0

  def is_meaningful(self):
    return self.file_name != "" or self.line != 0

  def is_valid(self):
    return not not self.file_name and self.line != None

class Launch(object):
  def __init__(self, name, main_class, args, remote_address):
    self.name = name or ""
    self.main_class = main_class or ""
    self.args = args or ""
    self.remote_address = remote_address or ""

  def is_meaningful(self):
    return self.name != "" or self.main_class != "" or self.args != "" or self.remote_address != ""

  def is_valid(self):
    mainclass_ok = not not self.main_class
    remoteaddress_ok = not not self.remote_address and self._match_remote_address()
    return mainclass_ok or remoteaddress_ok and (mainclass_ok != remoteaddress_ok)

  @property
  def command_line(self):
    cmdline = self.main_class
    if self.args:
      cmdline += (" " + self.args)
    return cmdline

  def _match_remote_address(self):
    return re.match("^(?P<host>.*?):(?P<port>.*)$", self.remote_address)

  @property
  def remote_host(self):
    return self._match_remote_address().group("host")

  @property
  def remote_port(self):
    return self._match_remote_address().group("port")

class Session(object):
  def __init__(self, env, breakpoints, launches, launch_key):
    self.env = env
    self.breakpoints = breakpoints or []
    self.launches = launches or {}
    self.launch_key = launch_key or ""

  @property
  def launch_name(self):
    if self.launch_key: name = "launch configuration \"" + self.launch_key + "\""
    else: name =  "launch configuration"
    return name + " for your Ensime project"

  @property
  def launch(self):
    return self.launches.get(self.launch_key, None)

def load(env):
  file_name = location(env)
  if file_name:
    try:
      session = None
      if os.path.exists(file_name):
        with open(file_name, "r") as f:
          contents = f.read()
          session = json.loads(contents)
      session = session or {}
      breakpoints = map(lambda b: Breakpoint(decode_path(b.get("file_name")), b.get("line")), session.get("breakpoints", []))
      breakpoints = filter(lambda b: b.is_meaningful(), breakpoints)
      launches_list = map(lambda c: Launch(c.get("name"), c.get("main_class"), c.get("args"), c.get("remote_address")), session.get("launch_configs", []))
      launches = {}
      # todo. this might lose user data
      for c in launches_list: launches[c.name] = c
      launch_key = session.get("current_launch_config") or ""
      return Session(env, breakpoints, launches, launch_key)
    except:
      print "Ensime: " + str(file_name) + " has failed to load"
      exc_type, exc_value, exc_tb = sys.exc_info()
      detailed_info = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
      print detailed_info
      return None
  else:
    return None

def save(env, data):
  file_name = location(env)
  if file_name:
    session = {}
    session["breakpoints"] = map(lambda b: {"file_name": encode_path(b.file_name), "line": b.line}, data.breakpoints)
    session["launch_configs"] = map(lambda c: {"name": c.name, "main_class": c.main_class, "args": c.args, "remote_address": c.remote_address}, data.launches.values())
    session["current_launch_config"] = data.launch_key
    if not session["launch_configs"]:
      # create a dummy launch config, so that the user has easier time filling in the config
      session["launch_configs"] = [{"name": "", "main_class": "", "args": "", "remote_address": ""}]
    contents = json.dumps(session, sort_keys=True, indent=2)
    with open(file_name, "w") as f:
      f.write(contents)

def edit(env):
  env.w.open_file(location(env))

def load_launch(env):
  if not os.path.exists(env.session_file) or not os.path.getsize(env.session_file):
    message = "Launch configuration does not exist. "
    message += "Sublime will now create a configuration file for you. Do you wish to proceed?"
    if sublime.ok_cancel_dialog(message):
      env.save_session() # to pre-populate the config, so that the user has easier time filling it in
      env.w.run_command("ensime_show_session")
    return None

  session = env.load_session()
  if not session:
    message = "Launch configuration for the Ensime project could not be loaded. "
    message += "Maybe the config is not accessible, but most likely it's simply not a valid JSON. "
    message += "\n\n"
    message += "Sublime will now open the configuration file for you to fix. "
    message += "If you don't know how to fix the config, delete it and Sublime will recreate it from scratch. "
    message += "Do you wish to proceed?"
    if sublime.ok_cancel_dialog(message):
      env.w.run_command("ensime_show_session")
    return None

  launch = session.launch
  if not launch:
    message = "Your current " + session.launch_name + " is not present. "
    message += "\n\n"
    message += "This error happened because the \"current_launch_config\" field of the config "
    if session.launch_key: config_status = "set to \"" + session.launch_key + "\""
    else: config_status = "set to an empty string"
    message += "(which is currently " + config_status + ") "
    message += "doesn't correspond to any entries in the \"launch_configs\" field of the launch configuration."
    message += "\n\n"
    message += "Sublime will now open the configuration file for you to fix. Do you wish to proceed?"
    if sublime.ok_cancel_dialog(message):
      env.w.run_command("ensime_show_session")
    return None

  if not launch.is_valid():
    message = "Your current " + session.launch_name + " is incorrect. "
    message += "\n\n"
    if session.launch_key: launch_description = "the entry named \"" + session.launch_key + "\""
    else: launch_description = "the default unnamed entry"
    message += "This error happened because " + launch_description + " in the \"launch_configs\" field of the launch configuration "
    message += "has neither the \"main_class\", nor the \"remote_address\" attribute set."
    message += "\n\n"
    message += "Sublime will now open the configuration file for you to fix. Do you wish to proceed?"
    if sublime.ok_cancel_dialog(message):
      env.w.run_command("ensime_show_session")
    return None

  return launch
