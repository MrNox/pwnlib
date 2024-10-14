# -*- coding: utf-8 -*-
import sys
import abc
import time
import queue
import threading
from typing import Union, Optional, List
from concurrent.futures import ThreadPoolExecutor, TimeoutError

from lib.binary.encoding import str2bytes

class TubeThread(metaclass=abc.ABCMeta):
    def __init__(self, timeout: Optional[Union[int, float]]=None):
        # set the default timeout
        self._default_timeout = timeout

        if timeout is not None:
            # pass the default timeout to the child class
            self._set_timeout(timeout)

        self._is_closed = False


    def set_timeout(self,
                    timeout: Optional[Union[int, float]]=None
                    ):
        assert timeout is None or \
                (isinstance(timeout, (int, float)) and timeout >=0), \
                "`timeout` is, must be positive 'int' or 'float'".format(type(timeout))

        if timeout == None:
            self._set_timeout(self._default_timeout)
        else:
            self._set_timeout(timeout)


    def recv(self, size:int=4096,
             timeout: Optional[Union[int, float]]=None
             ) -> bytes:
        assert size is None or (isinstance(size, int) and size >=0), \
                "`size` is {}, must be positive 'int'".format(type(size))

        current_timeout = self._default_timeout
        if timeout is not None:
            self.set_timeout(timeout)
            current_timeout = timeout

        with ThreadPoolExecutor() as executor:
            future = executor.submit(self._recv_raw, size)
            try:
                return future.result(timeout=current_timeout)
            except TimeoutError:
                raise TimeoutError("Timeout (recv)")
            except Exception as err:
                raise err from None
            finally:
                if timeout is not None:
                    self.set_timeout()


    def recvuntil(self,
                  delim: Union[str, bytes, List[Union[str, bytes]]],
                  size: int=4096,
                  timeout: Optional[Union[int, float]]=None,
                  drop: bool=False,
                  interval_time: float=0.01
                  ) -> bytes:
        assert isinstance(delim, (str, bytes, list)), \
                "{} given, must be positive 'str' or 'bytes' or 'list'".format(type(delim))

        if isinstance(delim, list):
            for i, d in enumerate(delim):
                assert isinstance(d, (str, bytes)), \
                        "{}({}) delimter must be 'str' or 'bytes'".format(d, type(d))
                delim[i] = str2bytes(d)
        else:
            delim = [str2bytes(delim)]

        found_delim = None
        data = b""
        while True:
            try:
                data += self.recv(size, timeout)
            except TimeoutError as err:
                raise TimeoutError("Timeout (recvuntil)")
            except Exception as err:
                raise err from None

            for d in delim:
                if d in data:
                    found_delim = d
                    break

            if found_delim is not None:
                break

            time.sleep(interval_time)

        i = data.find(found_delim)
        j = i + len(delim)

        if not drop:
            i = j

        return data[:i]


    def recvline(self, size: int=4096,
                 timeout: Optional[Union[int, float]]=None,
                 drop: bool=False):
        try:
            line = self.recvuntil('\n', size, timeout, drop)
        except TimeoutError as err:
            raise TimeoutError("Timeout (recvline)")

        return line


    def send(self, data: Union[str, bytes],
             timeout: Optional[Union[int, float]]=None
             ) -> int:
        assert isinstance(data, (str, bytes)), "{} given, must be 'str' or 'bytes')".format(type(data))
        data = str2bytes(data)

        current_timeout = self._default_timeout
        if timeout is not None:
            self.set_timeout(timeout)
            current_timeout = timeout

        with ThreadPoolExecutor() as executor:
            future = executor.submit(self._send_raw, data)
            try:
                return future.result(timeout=current_timeout)
            except TimeoutError:
                raise TimeoutError("Timeout (recv)")
            except Exception as err:
                raise err from None
            finally:
                if timeout is not None:
                    self.set_timeout()

    def sendline(self, data: Union[str,bytes],
                 timeout: Optional[Union[int, float]]=None) -> int:
        assert isinstance(data, (str, bytes)), "{} given, 'str' or 'bytes')".format(type(data))

        return self.send(data + b'\n', timeout)


    def sendafter(self, delim: Union[str, bytes],
                  data: Union[str,bytes],
                  size: int=4096,
                  timeout: Optional[Union[int, float]]=None,
                  drop: bool=False,
                  interval_time: float=0.01) -> int:
        recv_data = self.recvuntil(delim, size, timeout, drop, interval_time)
        return self.send(data, timeout)


    def sendlineafter(self, delim, data, size=4096, timeout=None, drop=False, interval_time=0.01) -> int:
        recv_data = self.recvuntil(delim, size, timeout, drop, interval_time)
        return self.sendline(data, timeout)


    def is_alive(self) -> bool:
        if not self._close:
            return self._is_alive()

        return False


    def close(self):
        self._close()
        self._is_closed = True


    @abc.abstractmethod
    def _recv_raw(self, size: int) -> bytes:
        pass


    @abc.abstractmethod
    def _send_raw(self, data: Union[str, bytes]) -> int:
        pass


    @abc.abstractmethod
    def _close(self):
        pass


    @abc.abstractmethod
    def _is_alive(self) -> bool:
        pass


    @abc.abstractmethod
    def _set_timeout(self, timeout: Union[int, float]):
        pass


    @abc.abstractmethod
    def _is_alive(self) -> bool:
        pass

    @abc.abstractmethod
    def _close(self) -> bool:
        pass
