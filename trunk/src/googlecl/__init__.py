# Copyright (C) 2010 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Contains configuration and read/write utility functions for GoogleCL."""
from __future__ import with_statement

__author__ = 'tom.h.miller@gmail.com (Tom Miller)'
import logging
import os
import re
import googlecl.config.parser

SUBDIR_NAME = 'googlecl'
DEFAULT_GOOGLECL_DIR = os.path.expanduser(os.path.join('~', '.googlecl'))
HISTORY_FILENAME = 'history'
TOKENS_FILENAME_FORMAT = 'access_tok_%s'
DEVKEY_FILENAME = 'yt_devkey'

FILE_EXT_PATTERN = re.compile('.*\.([a-zA-Z0-9]{2,}$)')
LOGGER_NAME = 'googlecl'
LOG = logging.getLogger(LOGGER_NAME)


def determine_terminal_encoding():
  import sys
  in_enc = ''
  out_enc = ''
  if sys.stdin.encoding:
    in_enc = sys.stdin.encoding
  if sys.stdout.encoding:
    out_enc = sys.stdout.encoding

  # Sometimes these are both defined, and hopefully they are both equal.
  # I'm not sure if they are guaranteed to be equal.
  if in_enc.lower() == out_enc.lower():
    # If they're not defined, return the python system-wide default encoding
    if not in_enc:
      return_enc = sys.getdefaultencoding()
    else:
      return_enc = in_enc
  # If they are not equal, at least one of them must be defined.
  else:
    # Both defined, but are not the same
    if in_enc and out_enc:
      LOG.warning('HEY! You have a different encoding for input and output')
      LOG.warning('Input: ' + in_enc)
      LOG.warning('Output: ' + in_enc)
    return_enc = out_enc or in_enc
  LOG.debug('determine_terminal_encoding(): ' + return_enc)
  return return_enc


TERMINAL_ENCODING = determine_terminal_encoding()


class SafeEncodeError(Exception):
  pass


class SafeDecodeError(Exception):
  pass


def build_titles_list(title, args):
  """Build a list of titles from the 'title' option and arguments.

  Args:
    title: NoneType or unicode Title given to options.title
    args: list Leftover arguments on the command line, presumably extra titles.

  Returns:
    List of strings or [None].

  """
  # If args is non-empty, assume the user is giving us titles to get
  if args:
    titles_list = args
    # If options.title is also given, add it to the list of titles
    if title:
      titles_list.insert(0,title)
  else:
    titles_list = [title]
  return titles_list


def get_data_path(filename,
                  default_directories=None,
                  create_missing_dir=False):
  """Get the full path to the history file.

  See googlecl.get_xdg_path()

  """
  return get_xdg_path(filename, 'DATA', default_directories,
                      create_missing_dir)


def get_extension_from_path(path):
  """Return the extension of a file."""
  match = FILE_EXT_PATTERN.match(path)
  if match:
    return match.group(1)
  else:
    return None


def get_xdg_path(filename, data_type, default_directories=None,
                 create_missing_dir=False):
  """Get the full path to a file using XDG file layout spec.

  Follows XDG Base Directory Specification.
  (http://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html).
  Tries default_directories and DEFAULT_GOOGLECL_DIR if no file is found
  via XDG spec.

  Keyword arguments:
    filename: Filename of the file.
    data_type: One of 'config' for config files or 'data' for data files.
    default_directories: List of directories to check if no file is found
        in directories specified by XDG spec and DEFAULT_GOOGLECL_DIR.
        Default None.
    create_missing_dir: Whether or not to create a missing config subdirectory
        in the default base directory. Default False.

  Returns:
    Path to config file, which may not exist. If create_missing_dir,
    the directory where the config file should be will be created if it
    does not exist.

  """
  data_type = data_type.upper()
  if data_type not in ('CONFIG', 'DATA'):
    raise Exception('Invalid value for data_type: ' + data_type)
  xdg_home_dir = os.environ.get('XDG_' + data_type + '_HOME')
  if not xdg_home_dir:
    home_dir = os.path.expanduser('~')
    if data_type == 'DATA':
      xdg_home_dir = os.path.join(home_dir, '.local', 'share')
    elif data_type == 'CONFIG':
      # No variable defined, using $HOME/.config
      xdg_home_dir = os.path.join(home_dir, '.config')
  xdg_home_dir = os.path.join(xdg_home_dir, SUBDIR_NAME)

  xdg_dir_list = os.environ.get('XDG_' + data_type + '_DIRS')
  if not xdg_dir_list:
    if data_type == 'DATA':
      xdg_dir_list = '/usr/local/share/:/usr/share/'
    elif data_type == 'CONFIG':
      xdg_dir_list = '/etc/xdg'
  xdg_dir_list = [os.path.join(d, SUBDIR_NAME)
                  for d in xdg_dir_list.split(':')]

  dir_list = [os.path.abspath('.'), xdg_home_dir] + xdg_dir_list +\
             [DEFAULT_GOOGLECL_DIR]
  if default_directories:
    dir_list += default_directories
  for directory in dir_list:
    config_path = os.path.join(directory, filename)
    if os.path.isfile(config_path):
      return config_path
  LOG.debug('Could not find ' + filename + ' in any of ' + str(dir_list))

  if os.name == 'posix':
    default_dir = xdg_home_dir
    mode = 0700
  else:
    default_dir = DEFAULT_GOOGLECL_DIR
    mode = 0777
  if not os.path.isdir(default_dir) and create_missing_dir:
    try:
      os.makedirs(default_dir, mode)
    except OSError, err:
      LOG.error(err)
      return ''
  return os.path.join(default_dir, filename)


def _move_failed_token_file(token_path):
  new_path = token_path + '.failed'
  LOG.debug('Moving ' + token_path + ' to ' + new_path)
  if os.path.isfile(new_path):
    LOG.debug(new_path + ' already exists. Deleting it.')
    try:
      os.remove(new_path)
    except EnvironmentError, err:
      LOG.debug('Cannot remove old failed token file: ' + str(err))
  try:
    os.rename(token_path, new_path)
  except EnvironmentError, err:
    LOG.debug('Cannot rename token file to ' + new_path + ': ' + str(err))


def read_access_token(service, user):
  """Try to read an authorization token from a file.

  Keyword arguments:
    service: Service the token is for. E.g. 'picasa', 'docs', 'blogger'.
    user: Username / email the token is associated with.

  Returns:
    The access token, if it exists. If there is no access token,
    return NoneType.

  """
  import pickle
  token_path = get_data_path(TOKENS_FILENAME_FORMAT % user)
  if os.path.exists(token_path):
    with open(token_path, 'rb') as token_file:
      try:
        token_dict = pickle.load(token_file)
      except ImportError:
        return None
    try:
      token = token_dict[service.lower()]
    except KeyError:
      return None
    else:
      return token
  else:
    return None


def read_devkey():
  """Return the cached YouTube developer's key."""
  key_path = get_data_path(DEVKEY_FILENAME)
  devkey = None
  if os.path.exists(key_path):
    with open(key_path, 'r') as key_file:
      devkey = key_file.read().strip()
  return devkey


def remove_access_token(service, user):
  """Remove an auth token for a particular user and service."""
  import pickle
  token_path = get_data_path(TOKENS_FILENAME_FORMAT % user)
  success = False
  file_invalid = False
  if os.path.exists(token_path):
    with open(token_path, 'r+') as token_file:
      try:
        token_dict = pickle.load(token_file)
      except ImportError, err:
        LOG.error(err)
        LOG.info('You probably have been using different versions of gdata.')
        _move_failed_token_file(token_path)
        return False

      try:
        del token_dict[service.lower()]
      except KeyError:
        LOG.debug('No token for ' + service)
      else:
        try:
          pickle.dump(token_dict, token_file)
        except EnvironmentError, err:
          # IOError (extends enverror) shouldn't happen, but I've seen 
	  # IOError Errno 0 pop up on Windows XP with Python 2.5.
          LOG.error(err)
          if err.errno == 0:
            _move_failed_token_file(token_path)
        else:
          success = True
  return success


def safe_encode(string, target_encoding=TERMINAL_ENCODING,
                errors='backslashreplace'):
  """Encode a unicode string to target_encoding.

  If given a str type, check to see that target_encoding can decode it
  without an error. Raises a SafeEncodeError if it can't.
  Given any other type, returns str() version of it.

  Args:
    string: unicode String to encode.
    target_encoding: str Encoding to encode to. Default TERMINAL_ENCODING.
    errors: str Name of the error handler to call if something goes wrong.
            See docs on the codecs module. Default 'backslashreplace'.

  Returns:
    A string encoded with target_encoding, or raises an error.

  """
  if isinstance(string, unicode):
    return string.encode(target_encoding, errors)
  elif isinstance(string, str):
    try:
      string.decode(target_encoding)
    except UnicodeDecodeError:
      raise SafeEncodeError('Passed a non-unicode string to safe_encode!')
    else:
      return string
  else:
    # Got something else, probably an int or bool or the like.
    return str(string)


def safe_decode(string, current_encoding='utf-8', errors='strict'):
  """Decode a byte string.

  Raises a SafeDecodeError if current_encoding cannot decode the string and
  the value of errors causes an exception to be raised.
  If given a unicde type, returns it immediately.
  Given any other type, returns unicode() version of it.

  Args:
    string: str String to decode.
    target_encoding: str Encoding to decode with. Default 'utf-8'.
    errors: str Name of the error handler to call if something goes wrong.
            See docs on the codecs module. Default 'strict'.

  Returns:
    A unicode string, or raises an error.

  """
  if isinstance(string, str):
    try:
      return string.decode(current_encoding, errors)
    except UnicodeDecodeError:
      raise SafeDecodeError(current_encoding + ' could not decode ' +
                            repr(string))
  elif isinstance(string, unicode):
    return string
  else:
    # Got something elese, probably an int or bool or the like.
    return unicode(string)


def write_access_token(service, user, token):
  """Write an authorization token to a file.

  Keyword arguments:
    service: Service the token is for. E.g. 'picasa', 'docs', 'blogger'.
    user: Username / email the token is associated with.

  """
  import pickle
  import stat
  token_path = get_data_path(TOKENS_FILENAME_FORMAT % user,
                             create_missing_dir=True)
  LOG.debug('Writing access token to ' + token_path)
  if os.path.exists(token_path):
    with open(token_path, 'rb') as token_file:
      try:
        token_dict = pickle.load(token_file)
      except (KeyError, IndexError), err:
        LOG.error(err)
        LOG.error('Failed to load token_file (may be corrupted?)')
        file_invalid = True
      except ImportError, err:
        LOG.error(err)
        LOG.info('You probably have been using different versions of gdata.')
        file_invalid = True
      else:
        file_invalid = False
    if file_invalid:
      _move_failed_token_file(token_path)
      token_dict = {}
  else:
    token_dict = {}
  token_dict[service] = token
  if token_path:
    with open(token_path, 'wb') as token_file:
      # Ensure only the owner of the file has read/write permission
      os.chmod(token_path, stat.S_IRUSR | stat.S_IWUSR)
      pickle.dump(token_dict, token_file)
  else:
    LOG.debug('Cannot save access token!')


def write_devkey(devkey):
  """Write the devkey to the youtube devkey file."""
  import stat
  key_path = get_data_path(DEVKEY_FILENAME)
  with open(key_path, 'w') as key_file:
    os.chmod(key_path, stat.S_IRUSR | stat.S_IWUSR)
    key_file.write(devkey)
