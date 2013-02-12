import sublime
import threading, uuid
from uuid import uuid4
import dotensime, dotsession
from paths import *

envLock = threading.RLock()
ensime_envs = {}

def for_window(window):
  if window:
    if window.id() in ensime_envs:
      return ensime_envs[window.id()]
    envLock.acquire()
    try:
      if not (window.id() in ensime_envs):
        # protection against reentrant EnsimeEnvironment calls
        ensime_envs[window.id()] = None
        ensime_envs[window.id()] = EnsimeEnvironment(window)
      return ensime_envs[window.id()]
    finally:
      envLock.release()
  return None

class EnsimeEnvironment(object):
  def __init__(self, window):
    self.w = window
    self.recalc() # might only see empty window.folders(), so initialized values will be bogus
    sublime.set_timeout(self.__deferred_init__, 500)

  def __deferred_init__(self):
    self.recalc()
    from ensime import Daemon
    v = self.w.active_view()
    if v != None: Daemon(v).on_activated() # recolorize

  @property
  def project_root(self):
    return decode_path(self._project_root)

  @property
  def project_config(self):
    config = self._project_config
    if self.settings.get("os_independent_paths_in_dot_ensime"):
      if type(config) == list:
        i = 0
        while i < len(config):
          key = config[i]
          literal_keys = [":root-dir", ":target"]
          list_keys = [":compile-deps", ":compile-jars", ":runtime-deps", ":runtime-jars", ":test-deps", ":sources", ":reference-source-roots"]
          if str(key) in literal_keys:
            config[i + 1] = decode_path(config[i + 1])
          elif str(key) in list_keys:
            config[i + 1] = map(lambda path: decode_path(path), config[i + 1])
          else:
            pass
          i += 2
    return config

  @property
  def session_file(self):
    return (self.project_root + os.sep + ".ensime_session") if self.project_root else None

  def recalc(self):
    # plugin-wide stuff (immutable)
    self.settings = sublime.load_settings("Ensime.sublime-settings")
    server_dir = self.settings.get("ensime_server_path", "Ensime" + os.sep + "server")
    self.server_path = (server_dir
                        if os.path.isabs(server_dir)
                        else os.path.join(sublime.packages_path(), server_dir))
    self.ensime_executable = (self.server_path + os.sep +
                              ("bin\\server.bat" if os.name == 'nt'
                               else "bin/server"))
    self.ensime_args = self.settings.get("ensime_server_args")
    self.plugin_root = os.path.normpath(os.path.join(self.server_path, ".."))
    self.log_root = os.path.normpath(os.path.join(self.plugin_root, "logs"))

    # instance-specific stuff (immutable)
    (root, conf, _) = dotensime.load(self.w)
    self._project_root = root
    self._project_config = conf
    self.valid = self.project_config != None

    # system stuff (mutable)
    self.session_id = uuid4()
    self.running = False
    self.controller = None # injected by EnsimeStartup to ensure smooth reloading
    self.compiler_ready = False

    # TODO: find a better place for this beast
    class NoteStorage(object):
      def __init__(self):
        self.data = []
        self.normalized_cache = {}
        self.per_file_cache = {}
      def append(self, data):
        self.data += data
        for datum in data:
          if not datum.file_name in self.normalized_cache:
            self.normalized_cache[datum.file_name] = normalize_path(datum.file_name)
          file_name = self.normalized_cache[datum.file_name]
          if not file_name in self.per_file_cache:
            self.per_file_cache[file_name] = []
          self.per_file_cache[file_name].append(datum)
      def filter(self, pred):
        dropouts = set(map(lambda n: self.normalized_cache[n.file_name], filter(lambda n: not pred(n), self.data)))
        # doesn't take into account pathological cases when a "*.scala" file
        # is actually a symlink to something without a ".scala" extension
        for file_name in self.per_file_cache.keys():
          if file_name in dropouts:
            del self.per_file_cache[file_name]
        self.data = filter(pred, self.data)
      def clear(self):
        self.filter(lambda f: False)
      def for_file(self, file_name):
        if not file_name in self.normalized_cache:
          self.normalized_cache[file_name] = normalize_path(file_name)
        file_name = self.normalized_cache[file_name]
        if not file_name in self.per_file_cache:
          self.per_file_cache[file_name] = []
        return self.per_file_cache[file_name]

    # core stuff (mutable)
    self._notes = NoteStorage()
    self.notee = None
    # Tracks the most recent completion prefix that has been shown to yield empty
    # completion results. Use this so we don't repeatedly hit ensime for results
    # that don't exist.
    self.completion_ignore_prefix = None

    # debugger stuff (mutable)
    # didn't prefix it with "debugger_", because there are no name clashes yet
    self.profile_being_launched = None
    self.profile = None # launch config used in current debug session
    self.breakpoints = []
    self.focus = None
    self.backtrace = None
    self.stackframe = None
    self.watchstate = None
    self._output = ""

    # load the session (if exists)
    self.load_session()

  # the guys below are made to be properties
  # because we do want to encapsulate them in objects
  # however doing that will prevent smooth development
  # if we put an object instance into a field, then it won't be reloaded by Sublime
  # when the corresponding source file is changed

  # this leads to a funny model, when env contains all shared state
  # and objects outside env are just bunches of pure functions that carry state around
  # state weaving is made implicit by the EnsimeCommon base class, but it's still there

  @property
  def rpc(self):
    from rpc import Rpc
    return Rpc(self)

  @property
  def notes(self):
    from ensime import Notes
    return Notes(self)

  @property
  def debugger(self):
    from ensime import Debugger
    return Debugger(self)

  @property
  def output(self):
    from ensime import Output
    return Output(self)

  @property
  def stack(self):
    from ensime import Stack
    return Stack(self)

  @property
  def watches(self):
    from ensime import Watches
    return Watches(self)

  # externalizable part of mutable state

  def load_session(self):
    session = dotsession.load(self)
    if session: self.breakpoints = session.breakpoints
    return session

  def save_session(self):
    session = dotsession.load(self) or dotsession.Session(breakpoints = [], launches = [], current_launch = None)
    session.breakpoints = self.breakpoints
    dotsession.save(self, session)
