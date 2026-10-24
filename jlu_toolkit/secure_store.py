"""本地凭据 / 会话的加密存储。

方案：随机 32 字节主密钥存进系统钥匙串（keyring：Windows 凭据管理器 / macOS 钥匙串 /
Linux Secret Service；Android/Chaquopy 下改为用 Android Keystore 包裹后存文件），数据用 AES-256-GCM 加密后写到 ``<config>/<name>.enc``。
会话 cookie 往往超过 Windows 凭据管理器的单条大小上限，所以钥匙串里只放密钥。

钥匙串或 cryptography 不可用（如 Termux、无桌面的 Linux）时会话退回明文 JSON 文件（不保存密码），
权限 0600，并在 stderr 提示一次。设 ``JLU_TOOLKIT_NO_KEYRING=1`` 可强制使用文件。

旧版明文 ``<name>.json`` 会在第一次读取时透明迁移为加密文件并删除明文。
"""
from __future__ import annotations

import base64
import json
import os
import secrets
import sys
from pathlib import Path
from typing import Any, Optional

SERVICE = "jlu-toolkit"
KEY_ENTRY = "storage-key"
_MAGIC = b"JLUT1"
_warned = False
last_error: Optional[str] = None


def _warn(msg: str) -> None:
    if os.environ.get("JLU_TOOLKIT_QUIET_STORE"):
        return
    print(f"[jlu-toolkit] 警告：{msg}", file=sys.stderr)


class SecureStoreError(Exception):
    """加密文件无法解密（钥匙串里的密钥丢失或被换掉）。"""


def _chmod600(path: Path) -> None:
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def _keyring():
    if os.environ.get("JLU_TOOLKIT_NO_KEYRING"):
        return None
    try:
        import keyring
        from keyring.backends import fail
    except Exception:  # noqa: BLE001
        return None
    try:
        kr = keyring.get_keyring()
    except Exception:  # noqa: BLE001
        return None
    if isinstance(kr, fail.Keyring):
        return None
    try:
        if float(getattr(kr, "priority", 1)) <= 0:
            return None
    except Exception:  # noqa: BLE001
        pass
    return keyring


def _aesgcm():
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except Exception:  # noqa: BLE001
        return None
    return AESGCM


# ───────── Android（Chaquopy）：主密钥由 Android Keystore 的 AES 密钥包裹 ─────────

ANDROID_ALIAS = "jlu-toolkit-storage"
WRAPPED_FILE = "storage-key.wrapped"
_WRAP_MAGIC = b"JLUK1"


def _config_dir() -> Path:
    # 与 jwxt.config_dir() 一致（避免循环导入）；Chaquopy 下 HOME 是应用私有目录
    base = os.environ.get("XDG_CONFIG_HOME")
    return (Path(base) if base else Path.home() / ".config") / "jlu-toolkit"


def _jbytes(arr) -> bytes:
    try:
        return bytes(arr)
    except (TypeError, ValueError):
        return bytes((b + 256) % 256 for b in arr)  # Java byte 是有符号的


class AndroidKeystore:
    """用 Chaquopy 的 Java 桥调用 AndroidKeyStore（AES-256/GCM/NoPadding，别名 jlu-toolkit-storage）。"""

    def __init__(self, jclass):
        self.jclass = jclass

    def _secret_key(self, create: bool):
        J = self.jclass
        ks = J("java.security.KeyStore").getInstance("AndroidKeyStore")
        ks.load(None)
        if ks.containsAlias(ANDROID_ALIAS):
            return ks.getKey(ANDROID_ALIAS, None)
        if not create:
            return None
        KP = J("android.security.keystore.KeyProperties")
        spec = (J("android.security.keystore.KeyGenParameterSpec$Builder")(
            ANDROID_ALIAS, KP.PURPOSE_ENCRYPT | KP.PURPOSE_DECRYPT)
            .setBlockModes([KP.BLOCK_MODE_GCM]).setEncryptionPaddings([KP.ENCRYPTION_PADDING_NONE])
            .setKeySize(256).build())
        kg = J("javax.crypto.KeyGenerator").getInstance(KP.KEY_ALGORITHM_AES, "AndroidKeyStore")
        kg.init(spec)
        return kg.generateKey()

    def wrap(self, key: bytes) -> bytes:
        Cipher = self.jclass("javax.crypto.Cipher")
        c = Cipher.getInstance("AES/GCM/NoPadding")
        c.init(Cipher.ENCRYPT_MODE, self._secret_key(create=True))
        iv = _jbytes(c.getIV())
        return _WRAP_MAGIC + bytes([len(iv)]) + iv + _jbytes(c.doFinal(key))

    def unwrap(self, blob: bytes) -> Optional[bytes]:
        if not blob.startswith(_WRAP_MAGIC):
            raise ValueError("包裹密钥文件格式不对")
        sk = self._secret_key(create=False)
        if sk is None:
            return None
        n = len(_WRAP_MAGIC)
        ivl = blob[n]
        iv, ct = blob[n + 1:n + 1 + ivl], blob[n + 1 + ivl:]
        Cipher = self.jclass("javax.crypto.Cipher")
        c = Cipher.getInstance("AES/GCM/NoPadding")
        c.init(Cipher.DECRYPT_MODE, sk, self.jclass("javax.crypto.spec.GCMParameterSpec")(128, iv))
        return _jbytes(c.doFinal(ct))


def _android() -> Optional[AndroidKeystore]:
    if os.environ.get("JLU_TOOLKIT_NO_KEYRING"):
        return None
    if not (os.environ.get("ANDROID_ROOT") or os.environ.get("ANDROID_DATA") or "chaquopy" in sys.modules):
        return None
    try:
        from java import jclass  # type: ignore  # Chaquopy
    except Exception:  # noqa: BLE001
        return None
    return AndroidKeystore(jclass)


def _android_key(ak: AndroidKeystore, create: bool) -> Optional[bytes]:
    global last_error
    f = _config_dir() / WRAPPED_FILE
    try:
        if f.is_file():
            key = ak.unwrap(f.read_bytes())
            if key is not None and len(key) == 32:
                return key
            last_error = "Android Keystore 中的包裹密钥不可用"
            return None
        if not create:
            return None
        key = secrets.token_bytes(32)
        blob = ak.wrap(key)
        if ak.unwrap(blob) != key:
            last_error = "Android Keystore 包裹后回读不一致"
            return None
        f.parent.mkdir(parents=True, exist_ok=True)
        tmp = f.with_suffix(".tmp")
        tmp.write_bytes(blob)
        _chmod600(tmp)
        os.replace(tmp, f)
        return key
    except Exception as e:  # noqa: BLE001
        last_error = f"Android Keystore 读写失败：{type(e).__name__}: {e}"
        return None


def _has_backend() -> bool:
    return _android() is not None or _keyring() is not None


def backend_name() -> str:
    if _android() is not None and _aesgcm() is not None:
        return "android-keystore"
    kr = _keyring()
    if kr is None or _aesgcm() is None:
        return "file"
    return "keyring:" + type(kr.get_keyring()).__name__


def _get_key(create: bool) -> Optional[bytes]:
    global last_error
    ak = _android()
    if ak is not None:
        return _android_key(ak, create)
    kr = _keyring()
    if kr is None:
        return None
    try:
        raw = kr.get_password(SERVICE, KEY_ENTRY)
        if raw:
            return base64.b64decode(raw)
        if not create:
            return None
        key = secrets.token_bytes(32)
        kr.set_password(SERVICE, KEY_ENTRY, base64.b64encode(key).decode())
        # 回读确认真的写进去了（有些后端静默失败）
        if kr.get_password(SERVICE, KEY_ENTRY) is None:
            last_error = "写入钥匙串后回读为空（后端静默失败）"
            return None
        return key
    except Exception as e:  # noqa: BLE001
        last_error = f"钥匙串读写失败：{type(e).__name__}: {e}"
        return None


def can_encrypt() -> bool:
    """当前能否加密保存（钥匙串 / Android Keystore 与 cryptography 均可用）。"""
    return _aesgcm() is not None and _get_key(create=True) is not None


def _warn_plain(path: Path) -> None:
    global _warned
    if _warned or os.environ.get("JLU_TOOLKIT_QUIET_STORE"):
        return
    _warned = True
    print(
        f"[jlu-toolkit] 警告：系统钥匙串不可用，凭据/会话以明文保存在 {path}（权限 600）。"
        "请勿在多人共用的设备上保存密码；装好 keyring 与 cryptography 后会自动改为加密存储。",
        file=sys.stderr,
    )


class SecretFile:
    """一个具名的秘密 JSON 对象，例如 SecretFile(dir, "session")。"""

    def __init__(self, directory: Path, name: str):
        self.dir = Path(directory)
        self.name = name

    @property
    def enc_path(self) -> Path:
        return self.dir / f"{self.name}.enc"

    @property
    def plain_path(self) -> Path:
        return self.dir / f"{self.name}.json"

    def exists(self) -> bool:
        return self.enc_path.is_file() or self.plain_path.is_file()

    def save(self, obj: Any) -> Path:
        self.dir.mkdir(parents=True, exist_ok=True)
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        AESGCM = _aesgcm()
        key = _get_key(create=True) if AESGCM else None
        if key is not None:
            nonce = secrets.token_bytes(12)
            ct = AESGCM(key).encrypt(nonce, data, (SERVICE + ":" + self.name).encode())
            tmp = self.enc_path.with_suffix(".enc.tmp")
            tmp.write_bytes(_MAGIC + nonce + ct)
            _chmod600(tmp)
            os.replace(tmp, self.enc_path)
            _chmod600(self.enc_path)
            if self.plain_path.is_file():
                self.plain_path.unlink()
            return self.enc_path
        if AESGCM is not None and _has_backend():
            _warn(f"钥匙串后端可用但取不到密钥（{last_error or '原因未知'}），本次以明文保存到 {self.plain_path}")
        else:
            _warn_plain(self.plain_path)
        self.plain_path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
        _chmod600(self.plain_path)
        if self.enc_path.is_file():
            self.enc_path.unlink()
        return self.plain_path

    def load(self) -> Optional[Any]:
        if self.enc_path.is_file():
            blob = self.enc_path.read_bytes()
            AESGCM = _aesgcm()
            key = _get_key(create=False) if AESGCM else None
            if key is None or not blob.startswith(_MAGIC):
                raise SecureStoreError(
                    f"无法解密 {self.enc_path}：系统钥匙串中的密钥不可用。请删除该文件后重新登录。"
                )
            n = len(_MAGIC)
            try:
                data = AESGCM(key).decrypt(blob[n:n + 12], blob[n + 12:], (SERVICE + ":" + self.name).encode())
            except Exception as e:  # noqa: BLE001
                raise SecureStoreError(f"{self.enc_path} 解密失败，请删除该文件后重新登录") from e
            return json.loads(data.decode("utf-8"))
        if self.plain_path.is_file():
            obj = json.loads(self.plain_path.read_text(encoding="utf-8"))
            # 透明迁移：钥匙串可用时改存加密文件（save 会删除明文）
            if backend_name() != "file":
                try:
                    out = self.save(obj)
                    if out != self.enc_path:
                        _warn(f"{self.plain_path} 未能迁移为加密文件，仍是明文")
                except Exception as e:  # noqa: BLE001
                    _warn(f"{self.plain_path} 迁移为加密文件失败：{type(e).__name__}: {e}")
            else:
                _warn_plain(self.plain_path)
            return obj
        return None

    def delete(self) -> None:
        for p in (self.enc_path, self.plain_path):
            if p.is_file():
                p.unlink()


# ───────── 数据缓存（data/*.json）加密 ─────────

# 含个人数值、需要加密的缓存；其余（设置、OA 通知等）保持明文 JSON
PERSONAL_CACHES = frozenset({"official_gpa.json", "completion.json", "plan_courses.json"})
CACHE_META = "cache_meta.json"


def _cache_file(path: Path) -> SecretFile:
    path = Path(path)
    return SecretFile(path.parent, path.stem)


def json_exists(path: Path) -> bool:
    """path 为 xxx.json；加密后的 xxx.enc 也算存在。"""
    return _cache_file(path).exists()


def save_json(path: Path, obj: Any) -> Path:
    """加密保存数据缓存（钥匙串不可用时退回 0600 明文），并在同目录 cache_meta.json 记录 updated_at。"""
    path = Path(path)
    out = _cache_file(path).save(obj)
    touch_cache_meta(path)
    return out


def touch_cache_meta(path: Path) -> None:
    import datetime as _dt
    path = Path(path)
    meta = cache_meta(path.parent)
    meta[path.name] = {"updated_at": _dt.datetime.now().isoformat(timespec="seconds")}
    try:
        (path.parent / CACHE_META).write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def load_json(path: Path, default: Any = None) -> Any:
    """读取数据缓存；旧的明文 xxx.json 会透明迁移为加密文件。解密/解析失败返回 default。"""
    try:
        v = _cache_file(Path(path)).load()
    except (SecureStoreError, ValueError, OSError):
        return default
    return default if v is None else v


def cache_meta(root: Path) -> dict:
    try:
        d = json.loads((Path(root) / CACHE_META).read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}
