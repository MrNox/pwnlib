import os
import subprocess
from typing import Union, Optional, List, Mapping

from .tube import Tube
from pwnlib.binary.encoding import bytes2str

is_windows = os.name == "nt"

if is_windows:
    import win32api
    import win32con
    import win32file
    import win32pipe
    import win32process
    import win32security

class WinPipe(object):
    def __init__(self, size: Optional[int]=0):

        sa = win32security.SECURITY_ATTRIBUTES()
        sa.bInheritHandle = True

        self.hread, self.hwrite = win32pipe.CreatePipe(sa, size)

        assert (self.hread != win32file.INVALID_HANDLE_VALUE or \
                self.hwrite != win32file.INVALID_HANDLE_VALUE), \
                "Could not create a pipe"


    @property
    def read(self):
        return self.hread


    @property
    def write(self):
        return self.hwrite


    def close(self):
        win32api.CloseHandle(self.hread)
        win32api.CloseHandle(self.hwrite)


    def __del__(self):
        self.close()

class WinProcess(Tube):
    def __init__(self,
                 args: Union[bytes, str, List[Union[bytes, str]]],
                 flags: int=0,
                 env: Optional[Union[Mapping[bytes, Union[bytes, str]], \
                         Mapping[str, Union[bytes, str]]]]=None,
                 cwd: Optional[Union[str, bytes]]=None,
                 stdin: Optional[WinPipe]=None,
                 stdout: Optional[WinPipe]=None,
                 stderr: Optional[WinPipe]=None,
                 timeout: Optional[Union[int, float]]=0
                 ):

        self._current_timeout = timeout
        super().__init__(timeout)

        assert isinstance(args, (bytes, str, list)), \
                "`args` is {}, must be 'bytes', 'str' or 'list'".format(type(args))

        assert isinstance(env, dict), \
                "`env` is {}, must be 'dict'".format(type(env))

        assert isinstance(cwd, (bytes, str)), \
                "`cwd` is {}, must be 'bytes' or 'str'".format(type(env))

        if isinstance(args, (str, bytes)):
            args = bytes2str(args)
        else:
            args = subprocess.list2cmdline(args)

        self._stdin = stdin
        self._stdout = stdout
        self._stderr = stderr

        if stdin is None:
            self._stdin = WinPipe()
            win32api.SetHandleInformation(
                    self._stdin.write, win32con.HANDLE_FLAG_INHERIT, 0)

        if stdout is None:
            self._stdout = WinPipe()
            win32api.SetHandleInformation(
                    self._stdout.read, win32con.HANDLE_FLAG_INHERIT, 0)

        # 2>&1 :P
        if stderr is None:
            self._stderr = self._stdout

        info = win32process.STARTUPINFO()
        info.dwFlags = win32con.STARTF_USESTDHANDLES
        info.hStdInput = self._stdin.read
        info.hStdOutput = self._stdout.write
        info.hStdError = self._stderr.write

        self.proc, _, self.pid, _ = win32process.CreateProcess(
                None, args, None, None, True, flags, env, cwd, info)

        self._returncode = None


    def _set_timeout(self, timeout: Union[int, float]=0):
        self._current_time = timeout


    def _is_alive(self) -> bool:
        status = win32process.GetExitCodeProcess(self._proc)
        if status == win32con.STILL_ACTIVE:
            return True
        else:
            self._returncode = status
            return False


    def _recv_raw(self, size: int) -> bytes:
        if self._current_time == 0:
            try:
                _, data = win32file.ReadFile(self._stdout.read)
                return data
            except Exception as err:
                raise err from None

        _, data = win32file.ReadFile(self._stdout.read)
        state = win32event.WaitForSingleObject(
                self._stdout.read, self._current_time)

        if state == win32con.WAIT_OBJECT_0:
            return data
        else:
            raise TimeoutError("Timeout (_recv_raw)")


    def _send_raw(self, data: Union[str, bytes]) -> int:
        try:
            _, n = win32file.WriteFile(self._stdin.write, data)
        except Exception as err:
            raise err from None


    def _close(self):
        win32api.TerminateProcess(self._proc, 0)
        win32api.CloseHandle(self._stdin.read)
        win32api.CloseHandle(self._stdout.write)
        win32api.CloseHandle(self._stderr.write)


    @property
    def returncode(self) -> Optional[int]:
        return self._returncode


    @property
    def pid(self) -> int:
        return self._proc.pid


