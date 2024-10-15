from .tube import Tube
from subprocess import Popen, PIPE,STDOUT
from typing import List, Optional, Union, Mapping

from pwnlib.binary.encoding import bytes2str

class processerror(Exception):
    pass

class Process(Tube):
    _proc = None

    def __init__(self,
                 args: Union[bytes, str, List[Union[bytes, str]]],
                 stdin: Optional[int]=PIPE,
                 stdout: Optional[int]=PIPE,
                 stderr: Optional[int]=STDOUT,
                 shell: Optional[bool]=False,
                 cwd: Optional[Union[str, bytes]]=None,
                 env: Optional[Union[Mapping[bytes, Union[bytes, str]], \
                         Mapping[str, Union[bytes, str]]]]=None,
                 timeout: Optional[Union[int, float]]=None
                 ):

        self._current_timeout = timeout
        super().__init__(timeout)


        assert isinstance(args, (bytes, str, list)), \
                "`args` is {}, must be 'bytes', 'str' or 'list'"

        assert isinstance(shell, bool), \
                "`shell` is {}, must be 'bool'".format(type(shell))

        if isinstance(args, (str, bytes)):
            args = [bytes2str(args)]
        else:
            args = list(map(bytes2str, args))

        try:

            self._proc = Popen(
                        args=args,
                        stdin=stdin,
                        stdout=stdout,
                        stderr=stderr,
                        shell=shell,
                        cwd=cwd,
                        env=env
                        )

        except FileNotFoundError as err:
            raise ValueError("Could not execute {} ({})".format(args, err))

        """
        only for unix/linux
        if self.proc.stdout:
            fd = self.proc.stdout.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        """

    @property
    def pid(self) -> int:
        return self._proc.pid

    def returncode(self) -> int:
        return self._proc.returncode


    def _set_timeout(self, timeout:Union[int, float]=None):
        self._current_timeout = timeout


    def _is_alive(self) -> bool:
        return self._proc.poll() is None


    def _close(self):
        if self.is_alive():
            self._proc.kill()
            self._proc.wait()

        try:
            if self._proc.stdin is not None:
                self._proc.stdin.close()
        except BrokenPipeError:
            pass

        try:
            if self._proc.stdout is not None:
                self._proc.stdout.close()
        except BrokenPipeError:
            pass

        try:
            if self._proc.stderr is not None:
                self._proc.stderr.close()
        except BrokenPipeError:
            pass


    def _recv_raw(self, size: int) -> bytes:
        data = None

        if not self.is_alive():
            return b''

        try:
            data = self._proc.stdout.read(size)
        except Exception as err:
            raise err from None

        if data is None:
            raise ConnectionAbortedError("Connection closed (_recv_raw)", b'') from None

        return data

    def _send_raw(self, data: Union[str, bytes]) -> int:
        try:
            n = self._proc.stdin.write(data)
            self._proc.stdin.flush()
            return n
        except Exception as err:
            raise err from None
