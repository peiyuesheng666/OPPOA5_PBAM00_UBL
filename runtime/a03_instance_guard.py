"""One host-side lock shared by every copy of the portable package."""
from contextlib import contextmanager
import ctypes
import os


@contextmanager
def single_instance():
    if os.name != 'nt':
        raise RuntimeError('此入口仅支持 Windows')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateMutexW.argtypes = (ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p)
    kernel.CreateMutexW.restype = ctypes.c_void_p
    kernel.CloseHandle.argtypes = (ctypes.c_void_p,)
    kernel.ReleaseMutex.argtypes = (ctypes.c_void_p,)
    ctypes.set_last_error(0)
    handle = kernel.CreateMutexW(None, True, 'Local\\OPPOA5_PBAM00_UBL_DeviceOperation_v1')
    error = ctypes.get_last_error()
    if not handle:
        raise ctypes.WinError(error)
    if error == 183:
        kernel.CloseHandle(handle)
        raise RuntimeError('已有解锁或回锁脚本在运行（可能来自另一个目录）；请关闭旧窗口后重试。')
    try:
        yield
    finally:
        kernel.ReleaseMutex(handle)
        kernel.CloseHandle(handle)
