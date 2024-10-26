import os
import sys
import platform
import tempfile
import subprocess
from typing import Literal, Optional, Union

from .config import VS_PATH, BIN_UTILS_PATH
from pwnlib.binary.encoding import bytes2str, str2bytes


x86 = ("intel", "intel32", "i386", "x86")
x64 = ("intel64", "x64", "x86-64", "amd","amd64")

def detect_arch() -> Literal[32, 64, -1]:
    arch =  platform.machine()
    arch = arch.lower().replace(" ", "").replace("_", "-")

    if arch in x86:
        return 32
    elif arch in x64:
        return 64
    else:
        return -1

def whereis(file: Union[str, bytes],
            env: Optional[Union[str, bytes]]=None,
            recursive: Optional[bool]=False
            )-> Optional[str]:
    assert file is None or isinstance(env, (str, bytes)), \
            "`file` must be 'str' or 'bytes'"

    assert env is None or isinstance(env, (str, bytes)), \
            "`env` must be 'str' or 'bytes'"

    cmd = ["where.exe"]
    if env is not None:
        cmd.append(bytes2str(env))

    if recursive:
        cmd.append("/R")

    cmd.append(bytes2str(file))

    try:
        return subprocess.check_output(cmd).decode().rstrip()
    except subprocess.CalledProcessError:
        return None

def get_env_bat_path(target_arch: str="x64") -> Optional[str]:
    vcvarsxx = "vcvars64.bat" if target_arch == "x64" else  "vcvars32.bat"
    vcvarsxx_path = os.path.join(VS_PATH,
                            "VC" ,
                            "Auxiliary",
                            "Build",
                            vcvarsxx)

    if not os.path.isfile(vcvarsxx_path):
        print("Error file not found {}".format(vcvarsxx_path))
        return None

    return vcvarsxx_path



def assemble(asm_code: Union[bytes, str], target_arch: str="x64") -> Optional[bytes]:
    assert isinstance(asm_code, (bytes, str)), \
            "`asm_code` must be 'bytes' or 'str'"

    bits = detect_arch()
    if bits == -1:
        print("Error detecting the architecture")
        return None


    if target_arch == "x64":
        vcvarsxx = "vcvars64.bat"
        arch = "x64"
        ml = "ml64"
    elif target_arch == "x86":
        vcvarsxx = "vcvars32.bat"
        arch = "x86"
        ml = "ml"
    else:
        print("Unknow target architecture {}".format(target_arch))
        return None

    fname = os.urandom(8).hex()
    asm_file_path = os.path.join(tempfile.gettempdir(), fname+".asm")
    obj_file_path = os.path.join(tempfile.gettempdir(), fname+".obj")
    bin_file_path = os.path.join(tempfile.gettempdir(), fname+".bin")

    def del_tmp_files():
        try:
            os.unlink(asm_file_path)
            os.unlink(obj_file_path)
            os.unlink(bin_file_path)
        except:
            pass

    vcvarsxx_path = os.path.join(VS_PATH,
                            "VC" ,
                            "Auxiliary",
                            "Build",
                            vcvarsxx)

    if not os.path.isfile(vcvarsxx_path):
        print("Visual studio path doesn't exist: {}".format(vcvarsxx_path))
        return None

    objcopy_path = os.path.join(BIN_UTILS_PATH, "objcopy.exe")
    if not os.path.isfile(objcopy_path):
        print("Bin utils path doesn't exist: {}".format(objcopy_path))
        return None

    code = b".code\nmain proc\n"
    code += str2bytes(asm_code)
    code += b"main endp\nend"

    with open(asm_file_path,"wb") as f:
        f.write(code)

    cmd = [vcvarsxx_path, ">NUL","&&", ml, "/Fo", obj_file_path, "/c" , asm_file_path, ">NUL"]
    if subprocess.Popen(cmd, shell=True).wait() != 0:
        print("Assembled failed")
        del_tmp_files()
        return None

    if not os.path.isfile(obj_file_path):
        print("Object not builded")
        del_tmp_files()
        return None

    cmd  = [
        objcopy_path,
        '-O', 'binary',
        '-j', '.text$mn',
        obj_file_path, bin_file_path
    ]
    if subprocess.Popen(cmd).wait() != 0:
        del_tmp_files()
        print("Error extracting the shellcode")
        return None

    if not os.path.isfile(bin_file_path):
        del_tmp_files()
        print("Binary file doesn't exist")
        return None

    shellcode = None
    with open(bin_file_path, "rb") as f:
        shellcode = f.read()

    del_tmp_files()

    return shellcode
